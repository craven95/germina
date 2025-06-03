import logging

from fastapi import HTTPException
from google.api_core import exceptions as core_exceptions
from google.cloud import artifactregistry as ar


def delete_package(
    to_delete_prefix: str,
    repo_parent: str,
):
    client = ar.ArtifactRegistryClient()

    matching_images = []
    try:
        page_result = client.list_docker_images(parent=repo_parent)
        for image in page_result:
            full_uri = image.uri
            package_part = full_uri.split("/")[-1].split("@")[0]
            if package_part.startswith(to_delete_prefix):
                matching_images.append(
                    {
                        "docker_image_name": image.name,
                        "package_name": package_part,
                        "digest": full_uri.split("@")[-1],
                        "tags": list(image.tags),
                    }
                )
    except Exception as e:
        logging.error(f"Erreur lors de la liste des images Docker : {e}")
        raise HTTPException(
            status_code=500, detail="Échec de la récupération des images Docker"
        )

    # 4) Aucun résultat → on renvoie “no_images_found”
    if not matching_images:
        logging.warning(f"Aucune image trouvée pour le préfixe '{to_delete_prefix}'.")
        return {"status": "no_images_found", "prefix": to_delete_prefix}

    if len(matching_images) > 1:
        logging.warning(
            f"Plusieurs images trouvées pour '{to_delete_prefix}' : "
            f"{[img['docker_image_name'] for img in matching_images]}. Suppression de toutes."
        )

    deleted = []
    errors = []

    for img_info in matching_images:
        package_name = img_info["package_name"]  # ex. "user_…_q_…"
        digest = img_info["digest"]  # ex. "sha256:8287…"
        full_docker_path = img_info["docker_image_name"]
        img_identifier = f"{package_name}@{digest}"

        logging.info(f"---\nTraitement de l'image Docker '{full_docker_path}'")

        if img_info["tags"]:
            for tag in img_info["tags"]:
                tag_resource = (
                    f"{repo_parent}/" f"packages/{package_name}/" f"tags/{tag}"
                )
                try:
                    client.delete_tag(name=tag_resource)
                    logging.info(f"Tag supprimé : {tag_resource}")
                except core_exceptions.NotFound:
                    logging.warning(f"Tag déjà absent (NotFound) : {tag_resource}")
                except core_exceptions.PermissionDenied as e:
                    msg = f"PermissionDenied lors de delete_tag({tag_resource}) : {e}"
                    logging.error(msg)
                    errors.append(
                        {
                            "stage": "delete_tag",
                            "resource": tag_resource,
                            "error": str(e),
                        }
                    )
                except Exception as e:
                    msg = f"Erreur inattendue delete_tag({tag_resource}) : {type(e).__name__} {e}"
                    logging.error(msg)
                    errors.append(
                        {
                            "stage": "delete_tag",
                            "resource": tag_resource,
                            "error": str(e),
                        }
                    )
        else:
            logging.warning(
                f"Aucun tag trouvé pour '{img_identifier}', on passe directement à la version."
            )

        version_resource = (
            f"{repo_parent}/" f"packages/{package_name}/" f"versions/{digest}"
        )
        try:
            op = client.delete_version(name=version_resource)
            op.result()
            logging.info(f"Version supprimée : {version_resource}")
            deleted.append(img_identifier)
        except core_exceptions.NotFound:
            logging.warning(f"Version déjà absente (NotFound) : {version_resource}")
            deleted.append(img_identifier + " (already absent)")
        except core_exceptions.PermissionDenied as e:
            msg = f"PermissionDenied lors de delete_version({version_resource}) : {e}"
            logging.error(msg)
            errors.append(
                {
                    "stage": "delete_version",
                    "resource": version_resource,
                    "error": str(e),
                }
            )
        except core_exceptions.FailedPrecondition as e:
            msg = (
                f"FailedPrecondition (toujours taggée ?) pour {version_resource} : {e}"
            )
            logging.error(msg)
            errors.append(
                {
                    "stage": "delete_version",
                    "resource": version_resource,
                    "error": str(e),
                }
            )
        except Exception as e:
            msg = f"Erreur inattendue delete_version({version_resource}) : {type(e).__name__} {e}"
            logging.error(msg)
            errors.append(
                {
                    "stage": "delete_version",
                    "resource": version_resource,
                    "error": str(e),
                }
            )

    if errors:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=207,
            content={"status": "partial_failure", "deleted": deleted, "errors": errors},
        )

    return {"status": "success", "deleted": deleted}
