import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Response
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.api_core.client_options import ClientOptions
from google.cloud import artifactregistry_v1 as ar
from google.cloud import logging as cloud_logging
from google.cloud import storage
from google.cloud.devtools import cloudbuild_v1
from pydantic import BaseModel
from supabase import Client, create_client

cloud_logging_client = cloud_logging.Client()
cloud_logging_client.setup_logging()

GCP_PROJECT = "germina-461108"
GCR_LOCATION = "europe-west1"
GCR_REPOSITORY = "germina-user-interface"  # Your Artifact Registry repository name
GCR_REPO_PATH = f"{GCR_LOCATION}-docker.pkg.dev/{GCP_PROJECT}/{GCR_REPOSITORY}"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Erreur : SUPABASE_URL et SUPABASE_KEY doivent être définis dans .env")
    raise RuntimeError("Configuration Supabase manquante")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

security = HTTPBearer()

# Middleware CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Modèles Pydantic
class BuildPayload(BaseModel):
    user_id: str
    title: str
    schema: dict
    ui_schema: dict


class DeployScriptPayload(BaseModel):
    image: str
    port: Optional[int] = 5000
    volume_path: Optional[str] = "~/docker_data"
    os: str
    qid: Optional[str] = "unknown"


def prepare_build_context(qid: str, user_id: str) -> str:
    """Prépare et upload le contexte de build vers GCS"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(__file__).parent / "survey_template"
        build_dir = Path(tmp_dir) / "custom_build_context"
        shutil.copytree(base, build_dir, dirs_exist_ok=True)
        print(list(build_dir.iterdir()))
        archive_name = f"context_{qid}_{user_id}.tar.gz"
        archive_path = Path(tmp_dir) / archive_name
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(build_dir, arcname="custom_build_context")

        storage_client = storage.Client()
        bucket = storage_client.bucket("germina-build-context")
        blob = bucket.blob(archive_name)
        blob.upload_from_filename(archive_path)

    return archive_name


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    """Récupère l'utilisateur via token Supabase"""
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
    if current >= 1000:
        raise HTTPException(status_code=429, detail="Quota dépassé")

    supabase.table("api_usage").upsert(
        {"user_id": user.id, "count": current + 1}
    ).execute()

    return user


def get_user_images(user_id: str):
    """Récupère les images Docker de l'utilisateur depuis Artifact Registry"""
    client = ar.ArtifactRegistryClient()
    parent = (
        f"projects/{GCP_PROJECT}/locations/{GCR_LOCATION}/repositories/{GCR_REPOSITORY}"
    )
    images = []
    try:
        request = ar.ListDockerImagesRequest(parent=parent)
        page_result = client.list_docker_images(request=request)
        for image in page_result:
            image_name = image.uri.split("/")[-1].split(":")[0]
            if image_name.startswith(f"user_{user_id}_q_"):
                print(f"Image trouvée : {image.uri}")
                images.append(image)
    except Exception as e:
        logger.error(f"Erreur Artifact Registry: {str(e)}")
        raise HTTPException(500, "Erreur de listing des images")

    return images


# Routes API
@app.post("/build/{questionnaire_id}", status_code=202)
def build_image(
    questionnaire_id: str,
    payload: BuildPayload,
    bg: BackgroundTasks,
    user=Depends(get_current_user),
):
    # check if user can build
    total_users_images = get_user_images(user.id)
    print('User has already', total_users_images)
    if len(total_users_images) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Vous avez atteint la limite de 5 interfaces, supprimez-en une pour en créer une nouvelle.",
        )
    context_object = prepare_build_context(questionnaire_id, user.id)

    supabase.table("questionnaires").update(
        {"docker_status": "pending", "docker_image": None}
    ).eq("id", questionnaire_id).eq("user_id", user.id).execute()

    bg.add_task(launch_build, questionnaire_id, payload, user.id, context_object)
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
    """Liste les images dans Artifact Registry pour le questionnaire"""
    image_prefix = f"user_{user.id}_q_{questionnaire_id}"

    client = ar.ArtifactRegistryClient()
    parent = (
        f"projects/{GCP_PROJECT}/locations/{GCR_LOCATION}/repositories/{GCR_REPOSITORY}"
    )

    images = []
    try:
        request = ar.ListDockerImagesRequest(parent=parent)
        page_result = client.list_docker_images(request=request)
        for image in page_result:
            image_name = image.uri.split("/")[-1].split("@")[0]
            if image_name.startswith(image_prefix):
                for tag in image.tags:
                    images.append(
                        {
                            "name": f"{image_name}",
                            "tag": tag,
                            "updated_at": image.upload_time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                        }
                    )
    except Exception as e:
        logger.error(f"Erreur Artifact Registry: {str(e)}")
        raise HTTPException(500, "Erreur de listing des images")

    return {"images": images}


@app.delete("/delete_image", status_code=200)
def delete_image(
    questionnaire_id: str = Query(...),
    user=Depends(get_current_user),
):
    """
    Supprime toutes les versions (manifests) d'un package Artifact Registry,
    en supprimant d'abord tous les tags Docker associés.
    """
    package_name = f"user_{user.id}_q_{questionnaire_id}"
    full_package_path = (
        f"projects/{GCP_PROJECT}/"
        f"locations/{GCR_LOCATION}/"
        f"repositories/{GCR_REPOSITORY}/"
        f"packages/{package_name}"
    )

    client = ar.ArtifactRegistryClient()

    try:
        client.get_package(name=full_package_path)
    except ar.exceptions.NotFound:
        logger.error(f"Aucun package trouvé : {full_package_path}")
        return {"status": "no_images_found", "package": package_name}
    except ar.exceptions.PermissionDenied as e:
        logger.error(f"PermissionDenied get_package({full_package_path}) : {e}")
        raise HTTPException(
            status_code=403, detail="Permission refusée pour get_package"
        )
    except Exception as e:
        logger.error(
            f"Erreur inattendue get_package({full_package_path}) : {type(e).__name__} {e}"
        )
        raise HTTPException(
            status_code=500, detail="Erreur interne lors de la vérification du package"
        )

    try:
        op = client.delete_package(name=full_package_path)
        op.result()  # on attend la fin de l'opération
        logger.info(f"✅ Package supprimé entièrement : {full_package_path}")
        return {"status": "success", "deleted_package": package_name}
    except ar.exceptions.PermissionDenied as e:
        logger.error(f"PermissionDenied delete_package({full_package_path}) : {e}")
        raise HTTPException(
            status_code=403, detail="Permission refusée pour delete_package"
        )
    except Exception as e:
        logger.error(
            f"Erreur delete_package({full_package_path}) : {type(e).__name__} {e}"
        )
        raise HTTPException(
            status_code=500, detail="Erreur interne lors de la suppression du package"
        )


@app.post("/generate_deploy_script")
def generate_deploy_script(p: DeployScriptPayload):
    """Génère le script de déploiement"""
    image_full = f"{GCR_REPO_PATH}/{p.image}"
    pull_cmd = f"docker pull {image_full}"
    run_cmd = (
        f"docker run -d --restart unless-stopped "
        f"-v {p.volume_path}:/app/data -p {p.port}:5000 "
        f"--name germina_survey_local {image_full}"
    )

    if p.os == "linux":
        script = f"""#!/bin/bash
{pull_cmd}
if ! command -v docker &> /dev/null; then
    sudo apt update && sudo apt install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
fi
{run_cmd}
echo "Accès : http://localhost:{p.port}"
"""
        ext = "sh"
    elif p.os == "mac":
        script = f"""#!/bin/zsh
{pull_cmd}
if ! docker info &> /dev/null; then
    open -a Docker
    echo "Docker démarre... patientez 30s"
    sleep 30
fi
{run_cmd}
echo "Accès : http://localhost:{p.port}"
"""
        ext = "sh"
    else:  # windows
        script = f"""# PowerShell
{pull_cmd}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {{
    winget install Docker.DockerDesktop
    Start-Sleep -Seconds 30
}}
{run_cmd}
Write-Host "Accès : http://localhost:{p.port}"
"""
        ext = "ps1"

    return Response(
        script,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=deploy_{p.qid}.{ext}"},
    )


# Fonction de build principale
def launch_build(qid: str, payload: BuildPayload, user_id: str, context_object: str):
    """Lance le build via Google Cloud Build"""
    # Configuration du client Cloud Build
    client_options = ClientOptions(
        api_endpoint=f"{GCR_LOCATION}-cloudbuild.googleapis.com"
    )
    cloudbuild_client = cloudbuild_v1.CloudBuildClient(client_options=client_options)

    # Nom de l'image
    image_name = f"user_{user_id}_q_{qid}"
    image_tag = f"{GCR_REPO_PATH}/{image_name}:latest"

    # Configuration du build
    build_config = cloudbuild_v1.Build(
        steps=[
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=[
                    "build",
                    "-t",
                    image_tag,
                    "--build-arg",
                    f"Q_SCHEMA={json.dumps(payload.schema)}",
                    "--build-arg",
                    f"Q_UI_SCHEMA={json.dumps(payload.ui_schema)}",
                    "--build-arg",
                    f"Q_ID={qid}",
                    "--build-arg",
                    f"Q_TITLE={payload.title}",
                    ".",
                ],
                dir="custom_build_context",
            ),
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker", args=["push", image_tag]
            ),
        ],
        source=cloudbuild_v1.Source(
            storage_source=cloudbuild_v1.StorageSource(
                bucket="germina-build-context",
                object=context_object,
            )
        ),
        images=[image_tag],
        options=cloudbuild_v1.BuildOptions(logging="CLOUD_LOGGING_ONLY"),
    )

    try:
        print(f"prépa fini pour {image_tag}...")
        logger.info(f"Lancement du build pour {image_tag}...")
        operation = cloudbuild_client.create_build(
            project_id=GCP_PROJECT, build=build_config
        )
        print("Build lancé, en attente du résultat...")
        result = operation.result()
        print("Build terminé, traitement du résultat...")
        logger.info(f"Build terminé : {result.status}")
        print(result.status_detail)

        if result.status == cloudbuild_v1.Build.Status.SUCCESS:
            logger.info(f"Build réussi : {image_tag}")
            supabase.table("questionnaires").update(
                {"docker_status": "built", "docker_image": image_tag}
            ).eq("id", qid).eq("user_id", user_id).execute()
        else:
            error_msg = f"Build failed: {result.status_detail}"
            logger.error(error_msg)
            supabase.table("questionnaires").update({"docker_status": "failed"}).eq(
                "id", qid
            ).eq("user_id", user_id).execute()

    except Exception as e:
        print("Exception inattendue durant launch_build", e)
        logger.exception("Exception inattendue durant launch_build")

        supabase.table("questionnaires").update({"docker_status": "failed"}).eq(
            "id", qid
        ).eq("user_id", user_id).execute()
        raise HTTPException(status_code=500, detail="Erreur lors du lancement du build")
