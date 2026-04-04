from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from core.security import hash_password, verify_password, create_access_token

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    existing_user = get_user_by_email(db,user.email)
    if existing_user:
        return None
    hashed = hash_password(user.password)
    new_user = User(email = user.email, hashed_password = hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def login_user(db: Session, email: str, password: str):
    user = authenticate_user(db, email, password)
    if not user:
        return None
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
