from pydantic import BaseModel
from datetime import datetime
from models.transaction import TransactionType

class TransactionCreate(BaseModel):
    amount: float
    type: TransactionType
    category: str
    note: str | None = None
    date: datetime | None = None

class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: str
    note: str | None = None
    date: datetime
    user_id: int

    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    amount: float | None = None
    type: TransactionType | None = None
    category: str | None = None
    note: str | None = None
    date: datetime | None = None

    