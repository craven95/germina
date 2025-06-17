import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from fastapi import HTTPException
from fastapi.logger import logger
from google.api_core.client_options import ClientOptions
from google.cloud import artifactregistry_v1 as ar
from google.cloud import logging as cloud_logging
from google.cloud import storage
from google.cloud.devtools import cloudbuild_v1

# Configuration
GCP_PROJECT: str = os.getenv("GCP_PROJECT", "")
GCR_LOCATION: str = os.getenv("GCR_LOCATION", "")
GCR_REPOSITORY: str = os.getenv("GCR_REPOSITORY", "")
GCR_REPO_PATH: str = f"{GCR_LOCATION}-docker.pkg.dev/{GCP_PROJECT}/{GCR_REPOSITORY}"

# Initialize Cloud Logging
cloud_logging_client = cloud_logging.Client()
cloud_logging_client.setup_logging()


def get_user_images(image_prefix: str) -> List[ar.DockerImage]:
    """Récupère les images Docker de l'utilisateur depuis Artifact Registry
    Args:
        image_prefix (str): Le préfixe des noms d'images à rechercher.
    Returns:
        list: Une liste d'objets DockerImage correspondant au préfixe donné.
    Raises:
        HTTPException: Si une erreur se produit lors de la récupération des images.
    """
    client = ar.ArtifactRegistryClient()
    parent: str = f"projects/{GCP_PROJECT}/locations/{GCR_LOCATION}/repositories/{GCR_REPOSITORY}"
    images: List[ar.DockerImage] = []
    try:
        request = ar.ListDockerImagesRequest(parent=parent)
        for image in client.list_docker_images(request=request):
            name = image.uri.split("/")[-1].split(":")[0]
            if name.startswith(image_prefix):
                images.append(image)
    except Exception as e:
        logger.error(f"Erreur Artifact Registry: {e}")
        raise HTTPException(status_code=500, detail="Erreur de listing des images")

    return images


def delete_package_from_package_name(package_name: str) -> Union[str, Dict[str, str]]:
    """Supprime un package complet dans Artifact Registry
    Args:
        package_name (str): Le nom du package à supprimer.
    Returns:
        str: Un message de succès si la suppression est réussie.
    Raises:
        HTTPException: Si package n'existe pas ou si une erreur se produit lors de suppression.
    """
    client = ar.ArtifactRegistryClient()
    pkg_path: str = (
        f"projects/{GCP_PROJECT}/"
        f"locations/{GCR_LOCATION}/"
        f"repositories/{GCR_REPOSITORY}/"
        f"packages/{package_name}"
    )

    try:
        client.get_package(name=pkg_path)
    except ar.exceptions.NotFound:
        logger.error(f"Aucun package trouvé : {pkg_path}")
        return "no_images_found"
    except ar.exceptions.PermissionDenied as e:
        logger.error(f"PermissionDenied get_package({pkg_path}): {e}")
        raise HTTPException(status_code=403, detail="Permission refusée pour get_package")
    except Exception as e:
        logger.error(f"Erreur get_package({pkg_path}): {type(e).__name__} {e}")
        raise HTTPException(
            status_code=500, detail="Erreur interne lors de la vérification du package"
        )

    try:
        op = client.delete_package(name=pkg_path)
        op.result()
        logger.info(f"✅ Package supprimé : {pkg_path}")
        return {"status": "success", "deleted_package": package_name}
    except ar.exceptions.PermissionDenied as e:
        logger.error(f"PermissionDenied delete_package({pkg_path}): {e}")
        raise HTTPException(status_code=403, detail="Permission refusée pour delete_package")
    except Exception as e:
        logger.error(f"Erreur delete_package({pkg_path}): {type(e).__name__} {e}")
        raise HTTPException(
            status_code=500, detail="Erreur interne lors de la suppression du package"
        )


def prepare_build_context(qid: str, user_id: str) -> str:
    """Prépare et upload le contexte de build vers GCS
    Args:
        qid (str): L'ID du questionnaire.
        user_id (str): L'ID de l'utilisateur.
    Returns:
        str: Le nom de l'archive uploadée dans GCS.
    Raises:
        HTTPException: Si une erreur se produit lors de la préparation du contexte de build.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(__file__).parent / "survey_template"
        build_dir = Path(tmp_dir) / "custom_build_context"
        shutil.copytree(base, build_dir, dirs_exist_ok=True)
        archive_name: str = f"context_{qid}_{user_id}.tar.gz"
        archive_path = Path(tmp_dir) / archive_name
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(build_dir, arcname="custom_build_context")

        bucket = storage.Client().bucket("germina-build-context")
        blob = bucket.blob(archive_name)
        blob.upload_from_filename(str(archive_path))

    return archive_name


def launch_build(user_id: str, qid: str, payload: Any) -> Dict[str, Any]:
    """Lance le build via Google Cloud Build
    Args:
        user_id (str): L'ID de l'utilisateur.
        qid (str): L'ID du questionnaire.
        payload: Le payload contenant les schémas et le titre du questionnaire.
    Returns:
        dict: Un dictionnaire contenant le statut du build et l'image Docker créée.
    Raises:
        HTTPException: Si une erreur se produit lors du lancement du build.
    """
    context_obj: str = prepare_build_context(qid, user_id)
    opts = ClientOptions(api_endpoint=f"{GCR_LOCATION}-cloudbuild.googleapis.com")
    cb_client = cloudbuild_v1.CloudBuildClient(client_options=opts)

    image_name = f"user_{user_id}_q_{qid}:latest"
    full_tag: str = f"{GCR_REPO_PATH}/{image_name}"

    build = cloudbuild_v1.Build(
        steps=[
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=[
                    "build",
                    "-t",
                    full_tag,
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
            cloudbuild_v1.BuildStep(name="gcr.io/cloud-builders/docker", args=["push", full_tag]),
        ],
        source=cloudbuild_v1.Source(
            storage_source=cloudbuild_v1.StorageSource(
                bucket="germina-build-context", object=context_obj
            )
        ),
        images=[full_tag],
        options=cloudbuild_v1.BuildOptions(logging="CLOUD_LOGGING_ONLY"),
    )

    try:
        logger.info(f"Lancement du build pour {full_tag}...")
        op = cb_client.create_build(project_id=GCP_PROJECT, build=build)
        res = op.result()
        logger.info(f"Statut du build : {res.status}")
        if res.status == cloudbuild_v1.Build.Status.SUCCESS:
            return {"status": "success", "image": full_tag}
        return {"status": "failed", "error": res.status_detail}
    except Exception:
        logger.exception("Erreur inattendue dans launch_build")
        raise HTTPException(status_code=500, detail="Erreur lors du lancement du build")


def generate_deploy_script(
    docker_image_name: str, local_port: int, volume_path: str, os: str
) -> Tuple[str, str]:
    """Génère un script de déploiement pour l'image Docker
    Args:
        docker_image_name (str): Le nom de l'image Docker à déployer.
        local_port (int): Le port local sur lequel l'application sera accessible.
        volume_path (str): Le chemin du volume à monter dans le conteneur.
        os (str): Système d'exploitation pour le script généré ("linux", "mac", "windows").
    Returns:
        Tuple[str, str]: Un dictionnaire contenant le script de déploiement et son extension.
    Raises:
        HTTPException: Si le système d'exploitation n'est pas supporté.
    """
    image_full = f"{GCR_REPO_PATH}/{docker_image_name}"
    pull_cmd = f"docker pull {image_full}"
    run_cmd = (
        f"docker run -d --restart unless-stopped "
        f"-v {volume_path}:/app/data -p {local_port}:5000 "
        f"--name germina_survey_local {image_full}"
    )

    if os == "linux":
        script = f"""#!/bin/bash
        {pull_cmd}
        if ! command -v docker &> /dev/null; then
            sudo apt update && sudo apt install -y docker.io
            sudo systemctl start docker
            sudo systemctl enable docker
        fi
        {run_cmd}
        echo "Accès : http://localhost:{local_port}"
        """
        ext = "sh"
    elif os == "mac":
        script = f"""#!/bin/zsh
        {pull_cmd}
        if ! docker info &> /dev/null; then
            open -a Docker
            echo "Docker démarre... patientez 30s"
            sleep 30
        fi
        {run_cmd}
        echo "Accès : http://localhost:{local_port}"
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
        Write-Host "Accès : http://localhost:{local_port}"
        """
        ext = "ps1"
    return script, ext
