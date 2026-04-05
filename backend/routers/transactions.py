from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from core.dependencies import get_current_user
from models.user import User
from schemas.transaction import TransactionCreate, TransactionOut, TransactionUpdate
from services.transaction_service import (
    get_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_balance,
)
from typing import List

# Same pattern as auth.py — we create a router with a prefix and a tag.
# All routes here will be under /transactions/...
# The tag "transactions" groups them separately in the Swagger UI at /docs.
router = APIRouter(prefix="/transactions", tags=["transactions"])


# ---------------------------------------------------------------------------
# GET /transactions/balance
# MUST be defined BEFORE GET /transactions/{transaction_id}
# Why? FastAPI matches routes top-to-bottom. If /{transaction_id} came first,
# then a request to /transactions/balance would try to use "balance" as an
# integer ID and fail.
# ---------------------------------------------------------------------------

@router.get("/balance")
def read_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # ↑ This single line is all it takes to protect a route.
    #   FastAPI calls get_current_user(), which calls decode_token() + DB lookup.
    #   If the token is missing/invalid, a 401 is raised BEFORE this function runs.
    #   If everything is fine, `current_user` is the logged-in User object.
):
    """Returns total income, total expense, and net balance for the current user."""
    return get_balance(db, current_user.id)
    # current_user.id — we got the full User object from the dependency,
    # so we can access any field on it.


# ---------------------------------------------------------------------------
# GET /transactions/
# Returns a list of all transactions for the current user.
# response_model=List[TransactionOut] tells FastAPI to:
#   1. Serialize each Transaction ORM object as a TransactionOut schema
#   2. Filter out any fields not in TransactionOut (good for security)
#   3. Auto-generate the correct response shape in /docs
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[TransactionOut])
def read_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all transactions belonging to the currently logged-in user."""
    return get_transactions(db, current_user.id)


# ---------------------------------------------------------------------------
# POST /transactions/
# Creates a new transaction for the current user.
# status_code=201 means "Created" — the HTTP convention for successful creation.
# ---------------------------------------------------------------------------

@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def add_transaction(
    transaction: TransactionCreate,
    # ↑ FastAPI reads the request BODY and validates it against TransactionCreate.
    #   If `amount` is missing or `type` is not "income"/"expense", it returns
    #   a 422 Unprocessable Entity automatically — no manual validation needed.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a new transaction linked to the currently logged-in user."""
    return create_transaction(db, transaction, current_user.id)


# ---------------------------------------------------------------------------
# PUT /transactions/{transaction_id}
# Updates a specific transaction.
# {transaction_id} is a PATH PARAMETER — it's part of the URL itself.
# FastAPI automatically converts it to an int and passes it to the function.
# Example URL: PUT /transactions/42  →  transaction_id = 42
# ---------------------------------------------------------------------------

@router.put("/{transaction_id}", response_model=TransactionOut)
def edit_transaction(
    transaction_id: int,
    # ↑ The name here MUST match the {transaction_id} in the route decorator.
    data: TransactionUpdate,
    # ↑ TransactionUpdate has all optional fields — the client only sends
    #   the fields they want to change (partial update / PATCH-style PUT).
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates a transaction. Only updates the fields provided in the request body."""
    updated = update_transaction(db, transaction_id, data, current_user.id)
    if not updated:
        # The service returns None if either:
        #   a) The transaction doesn't exist
        #   b) It belongs to a different user (the service checks both!)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /transactions/{transaction_id}
# Deletes a specific transaction.
# status_code=204 means "No Content" — successful but nothing to return.
# ---------------------------------------------------------------------------

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes the specified transaction if it belongs to the current user."""
    result = delete_transaction(db, transaction_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )
    # For 204 responses, we return nothing — FastAPI handles the empty body.
