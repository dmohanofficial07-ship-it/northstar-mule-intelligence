from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid access token is required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized
    try:
        user_id = int(decode_access_token(credentials.credentials))
    except Exception:
        raise unauthorized
    user = db.get(User, user_id)
    if not user:
        raise unauthorized
    return user
