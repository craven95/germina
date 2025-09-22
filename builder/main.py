from dotenv import load_dotenv

load_dotenv()

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from gcp import (
    delete_package_from_package_name,
    generate_deploy_script,
    get_user_images,
    launch_build,
    upload_image_bytes_to_gcp,
)
from image import encode_image_array, extract_image_array, pdf_to_image_array
from pydantic import BaseModel
from users import get_current_user

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
    schema: Dict[str, Any]  # type: ignore[assignment]
    ui_schema: Dict[str, Any]


class DeployScriptPayload(BaseModel):  # type: ignore[misc]
    image: str
    port: Optional[int] = 5000
    volume_path: Optional[str] = "~/docker_data"
    os: str
    qid: Optional[str] = "unknown"


@app.post("/upload_file", status_code=201)
def upload_survey_template(
    file: UploadFile = File(...),
    questionnaire_id: str = Form(...),
    user: Any = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Upload de template pour un questionnaire.
    Attend multipart/form-data avec:
      - questionnaire_id (champ form)
      - file (fichier)
    Le fichier est stocké dans le bucket GCP configuré via SURVEY_TEMPLATE_BUCKET.
    Retourne le chemin de l'objet stocké (ex: photos/user_<id>_q_<qid>/uuid.jpg)
    """
    if not file:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")
    filename = getattr(file, "filename", "") or "uploaded"
    ext = Path(filename).suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".pdf"]:
        raise HTTPException(
            status_code=415, detail=f"Extension non supportée: {ext}. Seuls png/jpg autorisés."
        )
    if file.content_type and file.content_type.lower() not in [
        "image/png",
        "image/jpeg",
        "application/pdf",
    ]:
        raise HTTPException(status_code=415, detail=f"MIME non supporté: {file.content_type}.")
    if ext == ".pdf" or (file.content_type and file.content_type.lower() == "application/pdf"):
        image_array, metadatas = pdf_to_image_array(file)
    else:
        image_array, metadatas = extract_image_array(file)

    bucket_saving_path = f"user_{user.id}_q_{questionnaire_id}"

    encoder = "png" if ext == ".png" else "jpg"

    upload_image_bytes_to_gcp(
        encode_image_array(image_array, encoder=encoder, color_space="BGR"), bucket_saving_path
    )

    return {"path": bucket_saving_path}


@app.post("/build/{questionnaire_id}", status_code=202)  # type: ignore[misc]
def build_image(
    questionnaire_id: str,
    payload: BuildPayload,
    bg: BackgroundTasks,
    user: Any = Depends(get_current_user),
) -> Dict[str, Any]:
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
            detail=(
                "Vous avez atteint la limite de 5 interfaces, "
                "supprimez-en une pour en créer une nouvelle."
            ),
        )

    bg.add_task(launch_build, user.id, questionnaire_id, payload)
    return {"status": "pending", "questionnaire_id": questionnaire_id}


@app.get("/build_status")  # type: ignore[misc]
def build_status(
    questionnaire_id: str,
    user: Any = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Vérifie le statut des builds pour un questionnaire donné.

    Args:
        questionnaire_id (str): L'ID du questionnaire pour lequel vérifier le statut.
        user: L'utilisateur actuel, récupéré via Supabase.

    Returns:
        dict: Un dictionnaire contenant le statut des builds et les images associées.

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
            "message": (f"{len(images)} builds trouvés pour le questionnaire {questionnaire_id}."),
            "images": [
                {
                    "name": img.uri.split("/")[-1].split("@")[0],
                    "tags": img.tags,
                    "updated_at": img.upload_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                for img in images
            ],
        }


@app.get("/list")  # type: ignore[misc]
def list_images(
    questionnaire_id: str,
    user: Any = Depends(get_current_user),
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Liste les images dans Artifact Registry pour le questionnaire donné.

    Args:
        questionnaire_id (str): L'ID du questionnaire pour lequel lister les images.
        user: L'utilisateur actuel, récupéré via Supabase.

    Returns:
        dict: Un dictionnaire contenant les images et leurs tags.
    """
    image_prefix = f"user_{user.id}_q_{questionnaire_id}"

    images = get_user_images(image_prefix)
    to_return_images: List[Dict[str, Any]] = []
    for image in images:
        for tag in image.tags:
            to_return_images.append(
                {
                    "name": image.uri.split("/")[-1].split("@")[0],
                    "tag": tag,
                    "updated_at": image.upload_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )

    return {"images": to_return_images}


@app.delete("/delete_image", status_code=200)  # type: ignore[misc]
def delete_image(
    questionnaire_id: str,
    user: Any = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Supprime un package complet dans Artifact Registry pour un questionnaire donné.

    Args:
        questionnaire_id (str): L'ID du questionnaire pour lequel supprimer le package.
        user: L'utilisateur actuel, récupéré via Supabase.

    Returns:
        dict: Un dictionnaire contenant le statut de la suppression.

    Raises:
        HTTPException: Si le package n'existe pas ou en cas d'erreur.
    """
    package_name = f"user_{user.id}_q_{questionnaire_id}"
    try:
        delete_package_from_package_name(package_name)
        return {"status": "success", "message": f"Package {package_name} supprimé."}
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}


@app.post("/generate_deploy_script")  # type: ignore[misc]
def get_deploy_script(
    p: DeployScriptPayload,
) -> Response:
    """
    Gènère le script de déploiement pour l'image Docker spécifiée.

    Args:
        p (DeployScriptPayload): Les paramètres nécessaires pour générer le script.

    Returns:
        Response: Un objet Response contenant le script en texte brut.

    Raises:
        HTTPException: Si l'image n'est pas spécifiée ou en cas d'erreur.
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
