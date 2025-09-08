import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client
from supabase_auth.types import User as SupabaseUser

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> SupabaseUser:
    """Récupère l'utilisateur via token Supabase JWT.

    Args:
        creds (HTTPAuthorizationCredentials): Informations d'identification contenant le JWT.
    Returns:
        user (User): Les informations de l'utilisateur récupérées depuis Supabase.
    Raises:
        HTTPException: Si le token est invalide, expiré ou si l'utilisateur n'existe pas.
    """
    token = creds.credentials
    try:
        response = supabase.auth.get_user(token)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré",
        ) from e
    if response is None or response.user is None:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur non trouvé ou token invalide",
        )
    return response.user
