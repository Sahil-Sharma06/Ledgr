from sqlalchemy.orm import Session
from models.transaction import Transaction, TransactionType
from schemas.transaction import TransactionCreate, TransactionUpdate
from typing import Optional

def get_transactions(
    db: Session,
    user_id: int,
    type_filter: Optional[TransactionType] = None,  # "income" or "expense" — optional
    category: Optional[str] = None,                 # exact category name — optional
    skip: int = 0,                                  # how many records to skip (offset)
    limit: int = 20,                                # max records to return per page
):
    # Start building the query — this doesn't hit the DB yet.
    # SQLAlchemy builds queries lazily; .all() at the end triggers the actual SQL.
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    # Conditionally chain filter() calls — each one adds a WHERE clause
    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    if category:
        query = query.filter(Transaction.category == category)

    # order_by newest first, then slice with offset+limit for pagination
    return (
        query
        .order_by(Transaction.date.desc())
        .offset(skip)   # SQL: OFFSET — skip the first N rows
        .limit(limit)   # SQL: LIMIT  — return at most N rows
        .all()
    )

def create_transaction(db: Session, transaction: TransactionCreate, user_id: int):
    new_transaction = Transaction(**transaction.model_dump(), user_id=user_id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

def update_transaction(db: Session, transaction_id: int, data: TransactionUpdate, user_id: int):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()
    if not transaction:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(transaction, key, value)
    db.commit()
    db.refresh(transaction)
    return transaction

def delete_transaction(db: Session, transaction_id: int, user_id: int):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()
    if not transaction:
        return None
    db.delete(transaction)
    db.commit()
    return True

def get_balance(db: Session, user_id: int):
    transactions = get_transactions(db, user_id)
    income = sum(t.amount for t in transactions if t.type.value == "income")
    expense = sum(t.amount for t in transactions if t.type.value == "expense")
    return {"income": income, "expense": expense, "balance": income - expense}