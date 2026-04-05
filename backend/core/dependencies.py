from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from core.security import decode_token
from models.user import User

# This tells FastAPI: "To authenticate, clients must send a Bearer token
# in the Authorization header. The token URL (where they get a token) is /auth/login."
#
# When a route uses this, FastAPI will:
#   1. Look at the incoming request's Authorization header
#   2. Extract the token after "Bearer "
#   3. Pass that raw token string to whichever function Depends() is used in
#
# If the header is missing entirely, FastAPI auto-returns a 401 before your
# function even runs. You don't have to check for that yourself.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),  # FastAPI extracts the Bearer token for us
    db: Session = Depends(get_db),         # FastAPI gives us a DB session
) -> User:
    """
    A reusable dependency that:
      1. Receives the raw JWT string from the Authorization header
      2. Decodes it to get the user's email
      3. Looks the user up in the database
      4. Returns the User object — or raises 401 if anything is wrong

    Any route that puts `current_user: User = Depends(get_current_user)` in its
    parameters is now a *protected route*. Only valid JWT holders can access it.
    """

    # decode_token() returns the email from the JWT payload, or None if
    # the token is expired, tampered with, or just invalid.
    email = decode_token(token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
        # The WWW-Authenticate header is part of the HTTP spec — it tells the
        # client *how* to authenticate (Bearer token in this case).
    )

    if email is None:
        raise credentials_exception

    # Look up the user in the DB using the email from the token
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise credentials_exception

    return user
