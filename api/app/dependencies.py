from typing_extensions import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .constants import AUTH_ALGORITHM, AUTH_SECRET_KEY
from .models import User, UserInDB, get_user_from_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def require_existing_username(username: Annotated[str, Path()]) -> UserInDB:
    if user := get_user_from_db(username):
        return user

    raise HTTPException(status_code=404, detail="User not found")


async def require_signed_in_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_from_db(username)
    if user is None:
        raise credentials_exception

    return user


async def require_admin_user(user: Annotated[UserInDB, Depends(require_signed_in_user)]) -> UserInDB:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Operation requires admin rights.")

    return user


ExistingUser = Annotated[UserInDB, Depends(require_existing_username)]
SignedInUser = Annotated[UserInDB, Depends(require_signed_in_user)]
AdminUser = Annotated[UserInDB, Depends(require_admin_user)]
