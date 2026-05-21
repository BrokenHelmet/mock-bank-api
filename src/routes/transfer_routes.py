from decimal import Decimal
from uuid import uuid4

from flask import Blueprint, request, jsonify

from src.repositories.account_repository import get_account_by_number, get_account_balance
from src.repositories.transfer_repository import (
    create_transfer,
    get_account_balance_for_update,
    get_all_transactions,
    log_transaction_attempt,
    get_all_transaction_attempts,
    get_transaction_by_reference,
    get_transaction_movement_by_reference,
    get_transaction_attempt_by_idempotency_key,
    create_reversal_transaction,
    get_transaction_accounts_by_reference,
    get_reversal_by_original_transaction_id,
    mark_transaction_as_reversed
)
from src.utils.response_helpers import format_transaction_response
from src.utils.fee_calculator import calculate_transfer_fee

transfer_bp = Blueprint("transfers", __name__)

def validate_account_transfer_status(from_account, to_account):
    # Repository account rows are tuple-based; index 6 stores the account status.
    from_status = from_account[6]
    to_status = to_account[6]

    if from_status != "active":
        return "Source account is not active"

    if to_status == "closed":
        return "Destination account is closed"

    return None

@transfer_bp.route("/transfers", methods=["POST"])
def create_transfer_endpoint():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    # Pull out the client-facing transfer fields before converting/validating them.
    from_account_number = data.get("from_account")
    to_account_number = data.get("to_account")
    amount_raw = data.get("amount")
    currency = data.get("currency", "KES")
    description = data.get("description")

    if not from_account_number or not to_account_number or amount_raw is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Decimal avoids floating-point rounding issues for money values.
        amount = Decimal(str(amount_raw))

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400

    except Exception:
        return jsonify({"error": "Invalid amount"}), 400

    transaction_reference = f"TX-{uuid4()}"

    try:
        from_account = get_account_by_number(from_account_number)
        to_account = get_account_by_number(to_account_number)

        # Log failed attempts as well as successful transfers so clients/operators
        # can audit why a transfer request did not create a transaction.
        if from_account is None or to_account is None:
            log_transaction_attempt(
                transaction_reference,
                from_account_number,
                to_account_number,
                amount,
                currency,
                "failed",
                "Invalid account"
            )

            return jsonify({"error": "Invalid account"}), 400

        status_error = validate_account_transfer_status(from_account, to_account)

        if status_error:
            log_transaction_attempt(
                transaction_reference,
                from_account_number,
                to_account_number,
                amount,
                currency,
                "failed",
                status_error
            )

            return jsonify({"error": status_error}), 400

        bank_charge = calculate_transfer_fee(
            amount,
            # Account row index 3 identifies the destination account type/category
            # used by the fee calculator.
            to_account[3]
        )

        # The source account must cover both the transfer amount and bank charge.
        total_debit = amount + bank_charge

        bank_charges_account = get_account_by_number("BANK-CHARGES-001")

        if bank_charges_account is None:
            return jsonify({"error": "Bank charges account not configured"}), 500

        from_balance = get_account_balance_for_update(from_account[0])

        if from_balance < total_debit:
            log_transaction_attempt(
                transaction_reference,
                from_account_number,
                to_account_number,
                amount,
                currency,
                "failed",
                "Insufficient funds"
            )

            return jsonify({"error": "Insufficient funds"}), 400

        transaction = create_transfer(
            transaction_reference,
            from_account[0],
            to_account[0],
            amount,
            currency,
            description,
            bank_charge,
            bank_charges_account[0]
        )

        log_transaction_attempt(
            transaction_reference,
            from_account_number,
            to_account_number,
            amount,
            currency,
            "success"
        )

        return jsonify(format_transaction_response(transaction)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@transfer_bp.route("/idempotent-transfers", methods=["POST"])
def create_idempotent_transfer_endpoint():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    # Idempotency prevents duplicate transfers when clients retry the same request.
    idempotency_key = data.get("idempotency_key")

    if not idempotency_key:
        return jsonify({"error": "idempotency_key is required"}), 400

    existing_attempt = get_transaction_attempt_by_idempotency_key(idempotency_key)

    if existing_attempt is not None:
        existing_transaction_reference = existing_attempt[1]

        # A previous attempt may have failed before a transaction was created.
        if existing_transaction_reference is None:
            return jsonify({
                "message": "Request already attempted",
                "status": existing_attempt[6],
                "failure_reason": existing_attempt[7],
                "idempotency_key": existing_attempt[9]
            }), 200

        transaction = get_transaction_by_reference(existing_transaction_reference)

        # Return the original result instead of creating a second transfer.
        return jsonify({
            "message": "Request already processed",
            "transaction": format_transaction_response(transaction),
            "idempotency_key": idempotency_key
        }), 200

    from_account_number = data.get("from_account")
    to_account_number = data.get("to_account")
    amount_raw = data.get("amount")
    currency = data.get("currency", "KES")
    description = data.get("description")

    if not from_account_number or not to_account_number or amount_raw is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Keep amount parsing consistent with the non-idempotent transfer endpoint.
        amount = Decimal(str(amount_raw))

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400

    except Exception:
        return jsonify({"error": "Invalid amount"}), 400

    transaction_reference = f"TX-{uuid4()}"

    try:
        from_account = get_account_by_number(from_account_number)
        to_account = get_account_by_number(to_account_number)

        # Store the idempotency key with failure attempts so retries receive the
        # same failure response instead of re-running validation as a new request.
        if from_account is None or to_account is None:
            log_transaction_attempt(
                transaction_reference,
                from_account_number,
                to_account_number,
                amount,
                currency,
                "failed",
                "Invalid account",
                idempotency_key
            )

            return jsonify({"error": "Invalid account"}), 400

        status_error = validate_account_transfer_status(from_account, to_account)

        if status_error:
            log_transaction_attempt(
                transaction_reference,
                from_account_number,
                to_account_number,
                amount,
                currency,
                "failed",
                status_error,
                idempotency_key
            )

            return jsonify({"error": status_error}), 400

        from_balance = get_account_balance_for_update(from_account[0])

        bank_charge = calculate_transfer_fee(
            amount,
            to_account[3]
        )

        total_debit = amount + bank_charge

        bank_charges_account = get_account_by_number("BANK-CHARGES-001")

        if bank_charges_account is None:
            return jsonify({"error": "Bank charges account not configured"}), 500

        if from_balance < total_debit:
            log_transaction_attempt(
                transaction_reference,
                from_account_number,
                to_account_number,
                amount,
                currency,
                "failed",
                "Insufficient funds",
                idempotency_key,
            )

            return jsonify({"error": "Insufficient funds"}), 400

        transaction = create_transfer(
            transaction_reference,
            from_account[0],
            to_account[0],
            amount,
            currency,
            description,
            bank_charge,
            bank_charges_account[0]
        )

        log_transaction_attempt(
            transaction_reference,
            from_account_number,
            to_account_number,
            amount,
            currency,
            "success",
            None,
            idempotency_key
        )

        return jsonify(format_transaction_response(transaction)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@transfer_bp.route("/transactions/<transaction_reference>/reverse", methods=["POST"])
def reverse_transaction_endpoint(transaction_reference):

    original = get_transaction_accounts_by_reference(transaction_reference)

    if original is None:
        return jsonify({"error": "Transaction not found"}), 404

    original_transaction_id = original[0]

    existing_reversal = get_reversal_by_original_transaction_id(
        original_transaction_id
    )

    if existing_reversal is not None:
        return jsonify({
            "error": "Transaction has already been reversed",
            "reversal_reference": existing_reversal[1]
        }), 400

    original_transaction_reference = original[1]

    original_transaction_type = original[2]
    original_status = original[3]

    if original_transaction_type != "transfer":
        return jsonify({"error": "Only transfer transactions can be reversed"}), 400

    if original_status != "completed":
        return jsonify({"error": "Only completed transactions can be reversed"}), 400

    reversal_reference = f"REV-{uuid4()}"

    original_amount = original[4]
    currency = original[5]

    original_from_account_id = original[6]
    original_to_account_id = original[7]

    reversal = create_reversal_transaction(
        reversal_reference,
        original_transaction_id,
        original_transaction_reference,
        original_to_account_id,
        original_from_account_id,
        original_amount,
        currency
    )

    mark_transaction_as_reversed(
        original_transaction_id
    )

    return jsonify(format_transaction_response(reversal)), 201

@transfer_bp.route("/transactions", methods=["GET"])
def get_transactions_endpoint():
    transactions = get_all_transactions()

    return jsonify([
        format_transaction_response(t) for t in transactions
    ]), 200

@transfer_bp.route("/transaction-attempts", methods=["GET"])
def get_transaction_attempts_endpoint():
    # Limit keeps the audit endpoint bounded while still allowing callers to page
    # through recent attempts manually.
    limit = request.args.get("limit", default=50, type=int)

    attempts = get_all_transaction_attempts(limit)

    results = []

    for attempt in attempts:
        results.append({
            "id": attempt[0],
            "transaction_reference": attempt[1],
            "from_account_number": attempt[2],
            "to_account_number": attempt[3],
            "amount": str(attempt[4]),
            "currency": attempt[5],
            "status": attempt[6],
            "failure_reason": attempt[7],
            "created_at": attempt[8].isoformat()
        })

    return jsonify(results), 200

@transfer_bp.route("/transaction-attempts/idempotency/<idempotency_key>", methods=["GET"])
def get_transaction_attempt_by_idempotency_key_endpoint(idempotency_key):
    attempt = get_transaction_attempt_by_idempotency_key(idempotency_key)

    if attempt is None:
        return jsonify({"error": "Idempotency key not found"}), 404

    return jsonify({
        "id": attempt[0],
        "transaction_reference": attempt[1],
        "from_account_number": attempt[2],
        "to_account_number": attempt[3],
        "amount": str(attempt[4]),
        "currency": attempt[5],
        "status": attempt[6],
        "failure_reason": attempt[7],
        "created_at": attempt[8].isoformat(),
        "idempotency_key": attempt[9]
    }), 200

@transfer_bp.route("/transactions/<transaction_reference>", methods=["GET"])
def get_transaction_by_reference_endpoint(transaction_reference):

    # Fetch the transaction together with account movement details for the response.
    transaction = get_transaction_movement_by_reference(
        transaction_reference
    )

    if transaction is None:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({
        "transaction": {
            "id": transaction[0],
            "transaction_reference": transaction[1],
            "transaction_type": transaction[2],
            "status": transaction[3],
            "amount": str(transaction[4]),
            "currency": transaction[5],
            "description": transaction[6],
            "created_at": transaction[7].isoformat()
        },

        "movement": {
            "from": {
                "account_number": transaction[8],
                "account_name": transaction[9]
            },

            "to": {
                "account_number": transaction[10],
                "account_name": transaction[11]
            }
        },

        "fees": {
            "bank_charge": str(transaction[12]),
            "total_debit": str(transaction[4] + transaction[12])
        }
    }), 200
