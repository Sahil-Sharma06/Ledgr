from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.transaction import TransactionType
from schemas.transaction import TransactionCreate, TransactionOut, TransactionUpdate
from services.transaction_service import (
    get_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_balance,
)
from typing import List, Optional

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/balance")
def read_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns total income, total expense, and net balance for the current user."""
    return get_balance(db, current_user.id)


# ---------------------------------------------------------------------------
# GET /transactions/?type=income&category=Food&skip=0&limit=20
#
# Query parameters are any extra key=value pairs after the "?" in the URL.
# FastAPI detects them automatically — if a param isn't a path param ({id})
# and isn't a request body, FastAPI treats it as a query param.
#
# Optional[str] = Query(None) means the param is not required.
# If the client doesn't send it, it defaults to None.
# Query() lets you add extra metadata like description (shown in /docs).
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[TransactionOut])
def read_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    # ge=0 means "greater than or equal to 0" — FastAPI validates this automatically.
    # If the client sends skip=-1, FastAPI returns a 422 error before the function runs.
    # le=100 means limit cannot exceed 100 — prevents a client from fetching huge pages.
):
    """Returns transactions with optional filtering by type/category and pagination."""
    return get_transactions(db, current_user.id, type_filter=type, category=category, skip=skip, limit=limit)


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
