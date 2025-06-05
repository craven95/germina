import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    """Récupère l'utilisateur via token Supabase JWT.
    Args:
        creds (HTTPAuthorizationCredentials): Les informations d'identification HTTP contenant le token JWT.
    Returns:
        user (dict): Les informations de l'utilisateur récupérées depuis Supabase.
    Raises:
        HTTPException: Si le token est invalide ou expiré.
    """
    token = creds.credentials
    try:
        user = supabase.auth.get_user(token).user
        if user is None:
            raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expiré",
        ) from e

    return user
