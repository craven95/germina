from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from builder.clouder import (
    delete_package_from_package_name,
    generate_deploy_script,
    get_user_images,
    launch_build,
)
from builder.supabase import get_current_user

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


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


@app.post("/build/{questionnaire_id}", status_code=202)
def build_image(
    questionnaire_id: str,
    payload: BuildPayload,
    bg: BackgroundTasks,
    user=Depends(get_current_user),
):
    """
    Lance le build d'une image Docker pour le questionnaire donné.

    Args:
        questionnaire_id (str): L'ID du questionnaire pour lequel l'image doit être construite.
        payload (BuildPayload): Les données nécessaires pour construire l'image.
        bg (BackgroundTasks): Tâches en arrière-plan pour exécuter le build de manière asynchrone.
        user: L'utilisateur actuel, récupéré via Supabase.

    Returns:
        dict: Un dictionnaire contenant le statut du build et l'ID du questionnaire.

    Raises:
        HTTPException: Si l'utilisateur a déjà atteint la limite de 5 images.
    """
    total_users_images = get_user_images(f"user_{user.id}_q_")
    if len(total_users_images) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Vous avez atteint la limite de 5 interfaces, supprimez-en une pour en créer une nouvelle.",
        )

    bg.add_task(launch_build, user.id, questionnaire_id, payload)
    return {"status": "pending", "questionnaire_id": questionnaire_id}


@app.get("/build_status")
def build_status(questionnaire_id: str, user=Depends(get_current_user)):
    """
    Vérifie le statut des builds pour un questionnaire donné.
    Args:
        questionnaire_id (str): L'ID du questionnaire pour lequel vérifier le statut.
        user: L'utilisateur actuel, récupéré via Supabase.
    Returns:
        dict: Un dictionnaire contenant le statut des builds et les images associées.
    Raises:
        HTTPException: Si aucune image n'est trouvée pour le questionnaire.
    """
    image_prefix = f"user_{user.id}_q_{questionnaire_id}"

    images = get_user_images(image_prefix)

    if not images:
        return {
            "status": "pending",
            "message": "Aucun build en cours pour ce questionnaire.",
        }
    else:
        return {
            "status": "success",
            "message": f"{len(images)} builds trouvés pour le questionnaire {questionnaire_id}.",
            "images": [
                {
                    "name": image.uri.split("/")[-1].split("@")[0],
                    "tags": image.tags,
                    "updated_at": image.upload_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                for image in images
            ],
        }


@app.get("/list")
def list_images(questionnaire_id: str, user=Depends(get_current_user)):
    """Liste les images dans Artifact Registry pour le questionnaire donné.
    Args:
        questionnaire_id (str): L'ID du questionnaire pour lequel lister les images.
        user: L'utilisateur actuel, récupéré via Supabase.
    Returns:
        dict: Un dictionnaire contenant les images et leurs tags.
    Raises:
        HTTPException: Si aucune image n'est trouvée pour le questionnaire.
    """
    image_prefix = f"user_{user.id}_q_{questionnaire_id}"

    images = get_user_images(image_prefix)

    to_return_images = [
        {
            "name": f"{image.uri.split('/')[-1].split('@')[0]}",
            "tag": tag,
            "updated_at": image.upload_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for image in images
        for tag in image.tags
    ]

    return {"images": to_return_images}


@app.delete("/delete_image", status_code=200)
def delete_image(
    questionnaire_id: str,
    user=Depends(get_current_user),
):
    """
    Supprime un package complet dans Artifact Registry pour un questionnaire donné.
    Args:
        questionnaire_id (str): L'ID du questionnaire pour lequel supprimer le package.
        user: L'utilisateur actuel, récupéré via Supabase.
    Returns:
        dict: Un dictionnaire contenant le statut de la suppression.
    Raises:
        HTTPException: Si le package n'existe pas ou si une erreur se produit lors de la suppression.
    """
    package_name = f"user_{user.id}_q_{questionnaire_id}"
    try:
        delete_package_from_package_name(package_name)
        return {"status": "success", "message": f"Package {package_name} supprimé."}
    except HTTPException as e:
        return {
            "status": "error",
            "message": str(e.detail),
        }


@app.post("/generate_deploy_script")
def get_deploy_script(p: DeployScriptPayload):
    """Génère le script de déploiement pour l'image Docker spécifiée.
    Args:
        p (DeployScriptPayload): Les paramètres nécessaires pour générer le script de déploiement.
    Returns:
        Response: Un objet Response contenant le script de déploiement en texte brut.
    Raises:
        HTTPException: Si l'image n'est pas spécifiée ou si le script ne peut pas être généré.
    """
    script, ext = generate_deploy_script(
        p.image,
        p.port,
        p.volume_path,
        p.os,
    )
    return Response(
        script,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=deploy_{p.qid}.{ext}"},
    )
