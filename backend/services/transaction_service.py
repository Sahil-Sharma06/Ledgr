from sqlalchemy.orm import Session
from models.transaction import Transaction
from schemas.transaction import TransactionCreate, TransactionUpdate

def get_transactions(db: Session, user_id: int):
    return db.query(Transaction).filter(Transaction.user_id == user_id).all()

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