import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import docker
import requests
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.logger import logger
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client, create_client

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

SCW_REGION = "fr-par"
SCW_API_BASE = f"https://api.scaleway.com/registry/v1/regions/{SCW_REGION}"
SCW_NAMESPACE_ID = "a19516b3-bd56-4d61-8df6-2833cfd5324c"
SCW_REGISTRY_DOMAIN = "rg.fr-par.scw.cloud"
SCW_REGISTRY_NS = "germina-namespace"
SCW_SECRET_KEY = os.getenv("SCW_SECRET_KEY", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(
        "Erreur : Les variables d'environnement SUPABASE_URL et SUPABASE_KEY doivent être définies."
        " Veuillez les configurer dans votre fichier .env."
    )

if not SCW_SECRET_KEY:
    print(
        "Erreur : La variable d'environnement SCW_SECRET_KEY doit être définie."
        " Veuillez la configurer dans votre fichier .env."
    )


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
docker_client = docker.from_env()

security = HTTPBearer()


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    """Récupère l'utilisateur via token Supabase et vérifie le quota d'usage."""
    token = creds.credentials
    try:
        user = supabase.auth.get_user(token).user
        if user is None:
            raise
    except:
        raise HTTPException(status_code=401, detail="Token invalide")

    stat = (
        supabase.table("api_usage")
        .select("count")
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
        .data
    )
    current = stat["count"] if stat else 0
    if current >= 605:
        raise HTTPException(status_code=429, detail="Quota d’usage dépassé")
    supabase.table("api_usage").upsert(
        {"user_id": user.id, "count": current + 1}
    ).execute()
    supabase.auth.session = {"access_token": token}
    return user


def check_registry_access(user_id: str, questionnaire_id: str):
    """
    S'assure que le questionnaire appartient bien à l'utilisateur.
    """
    rec = (
        supabase.table("questionnaires")
        .select("id")
        .eq("id", questionnaire_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
        .data
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : questionnaire non trouvé ou pas à vous.",
        )


class BuildPayload(BaseModel):
    user_id: str
    title: str
    schema: dict
    ui_schema: dict


class DeployScriptPayload(BaseModel):
    image: str
    port: Optional[int] = 8000
    volume_path: Optional[str] = "~/docker_data"
    os: str
    qid: Optional[str] = "unknown"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
def docker_login():
    """Login dans le SCR au démarrage."""
    try:
        docker_client.login(
            username="nologin",
            password=SCW_SECRET_KEY,
            registry=f"{SCW_REGISTRY_DOMAIN}/{SCW_REGISTRY_NS}",
        )
    except docker.errors.APIError as e:
        logger.error(f"Erreur de connexion au registre : {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur de connexion au registre",
        )
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur inattendue",
        )


# ————— Routes —————


@app.post("/build/{questionnaire_id}", status_code=202)
def build_image(
    questionnaire_id: str,
    payload: BuildPayload,
    bg: BackgroundTasks,
    user=Depends(get_current_user),
):
    # TODO : For the moment user cannot updata supabese tableor read them..
    supabase.table("questionnaires").update(
        {"docker_status": "pending", "docker_image": None}
    ).eq("id", questionnaire_id).eq("user_id", user.id).execute()

    bg.add_task(launch_build, questionnaire_id, payload, user.id)
    return {"status": "pending", "questionnaire_id": questionnaire_id}


@app.get("/build_status")
def build_status(questionnaire_id: str = Query(...), user=Depends(get_current_user)):
    rec = (
        supabase.table("questionnaires")
        .select("docker_status", "docker_image")
        .eq("id", questionnaire_id)
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
        .data
    )
    if rec is None:
        raise HTTPException(404, "Questionnaire introuvable")
    return {"status": rec["docker_status"], "image": rec["docker_image"]}


@app.get("/list")
def list_images(questionnaire_id: str, user=Depends(get_current_user)):
    prefix = f"user_{user.id}_q_{questionnaire_id}"
    headers = {"X-Auth-Token": SCW_SECRET_KEY}
    resp = requests.get(
        f"{SCW_API_BASE}/images",
        headers=headers,
        params={"namespace_id": SCW_NAMESPACE_ID, "order_by": "created_at_desc"},
    )
    resp.raise_for_status()

    out = []
    for img in resp.json().get("images", []):
        if img["name"].startswith(prefix):
            for tag in img.get("tags", []):
                out.append(
                    {
                        "name": f"{img['name']}:{tag}",
                        "tag": tag,
                        "updated_at": img.get("updated_at"),
                    }
                )
    return {"images": out}


@app.delete("/delete_image", status_code=200)
def delete_image(
    questionnaire_id: str = Query(...),
    tag: str = Query(...),
    user=Depends(get_current_user),
):
    prefix = f"user_{user.id}_q_{questionnaire_id}"
    headers = {"X-Auth-Token": SCW_SECRET_KEY}
    resp = requests.get(
        f"{SCW_API_BASE}/images",
        headers=headers,
        params={"namespace_id": SCW_NAMESPACE_ID},
    )
    resp.raise_for_status()
    images = resp.json().get("images", [])
    image_id = None
    for img in images:
        if img["name"] == prefix:
            image_id = img["id"]
            break

    if not image_id:
        raise HTTPException(status_code=404, detail="Image non trouvée")

    del_url = f"{SCW_API_BASE}/images/{image_id}"
    del_resp = requests.delete(del_url, headers=headers)
    if del_resp.status_code not in (200, 204):
        raise HTTPException(
            status_code=del_resp.status_code,
            detail=f"Erreur suppression: {del_resp.text}",
        )

    return {"status": "deleted", "image_id": image_id}


@app.post("/generate_deploy_script")
def generate_deploy_script(p: DeployScriptPayload):
    image_full = f"{SCW_REGISTRY_DOMAIN}/{SCW_REGISTRY_NS}/{p.image}"
    pull_cmd = f"docker pull {image_full}"
    run_cmd = (
        f"docker run -d --restart unless-stopped "
        f"-v {p.volume_path}:/app/data -p {p.port}:8000 "
        f"--name germina_survey_local {image_full}"
    )

    if p.os == "linux":
        shebang = "#!/bin/bash"
        install = f"{pull_cmd}\nif ! command -v docker; then sudo apt update && sudo apt install -y docker.io; fi"
        footer = f'echo "Accès : http://localhost:{p.port}"'
    elif p.os == "mac":
        shebang = "#!/bin/zsh"
        install = f"{pull_cmd}\nif ! docker info; then open -a Docker; exit 1; fi"
        footer = f'echo "http://localhost:{p.port}"'
    else:  # windows
        shebang = ""
        install = f"{pull_cmd}\nif (-not (Get-Command docker -ErrorAction SilentlyContinue)) {{ winget install Docker.DockerDesktop }}"
        footer = f'Write-Host "http://localhost:{p.port}"'

    script = "\n".join(filter(None, [shebang, install, run_cmd, footer]))
    ext = "ps1" if p.os == "windows" else "sh"
    return Response(
        script,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=deploy_{p.qid}.{ext}"},
    )


def launch_build(qid: str, payload: BuildPayload, user_id: str):
    tmp = tempfile.mkdtemp()
    try:
        base = Path(__file__).parent / "survey_template"
        shutil.copytree(base, tmp, dirs_exist_ok=True)

        remote = f"{SCW_REGISTRY_DOMAIN}/{SCW_REGISTRY_NS}/user_{user_id}_q_{qid}"
        remote_tag = f"{remote}:latest"

        image, logs = docker_client.images.build(
            path=tmp,
            tag=remote_tag,
            buildargs={
                "Q_SCHEMA": json.dumps(payload.schema),
                "Q_UI_SCHEMA": json.dumps(payload.ui_schema),
                "Q_ID": qid,
                "Q_TITLE": payload.title,
            },
            rm=True,
        )

        for chunk in docker_client.images.push(
            remote, tag="latest", stream=True, decode=True
        ):
            logger.info(chunk)

        logger.info("Image envoyée au registre")
        docker_client.images.remove(remote_tag, force=True)
        logger.info("Image supprimée localement")

    except Exception as e:
        logger.error(f"Erreur lors de la construction de l'image : {e}")
    finally:
        shutil.rmtree(tmp)
