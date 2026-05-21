from flask import Blueprint, request, jsonify
from src.repositories.account_repository import create_account, update_account, get_account_by_number, get_account_balance, get_all_accounts
from src.repositories.transfer_repository import get_transactions_by_account, create_funding_transaction
from src.utils.response_helpers import format_account_response, format_transaction_response
from uuid import uuid4
from decimal import Decimal

account_bp = Blueprint("accounts", __name__)


@account_bp.route("/accounts", methods=["POST"])
def create_account_endpoint():
    data = request.get_json()

    account_number = data.get("account_number")
    account_name = data.get("account_name")
    account_type = data.get("account_type")
    currency = data.get("currency", "KES")

    try:
        account = create_account(
            account_number,
            account_name,
            account_type,
            currency
        )

        return jsonify(format_account_response(account)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@account_bp.route("/accounts", methods=["GET"])
def get_accounts_endpoint():

    accounts = get_all_accounts()

    return jsonify([
        format_account_response(account)
        for account in accounts
    ]), 200

@account_bp.route("/accounts/<account_number>", methods=["GET"])
def get_account_endpoint(account_number):
    account = get_account_by_number(account_number)

    if account is None:
        return jsonify({"error": "Account not found"}), 404

    return jsonify(format_account_response(account)), 200

@account_bp.route("/accounts/<account_number>", methods=["PATCH"])
def update_account_endpoint(account_number):

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    account_name = data.get("account_name")
    status = data.get("status")

    if status is not None:
        allowed_statuses = ["active", "inactive", "closed"]

        if status not in allowed_statuses:
            return jsonify({
                "error": "Invalid status"
            }), 400

    updated_account = update_account(
        account_number,
        account_name,
        status
    )

    if updated_account is None:
        return jsonify({
            "error": "Account not found"
        }), 404

    return jsonify(
        format_account_response(updated_account)
    ), 200

@account_bp.route("/accounts/<account_number>/balance", methods=["GET"])
def get_account_balance_endpoint(account_number):
    account = get_account_by_number(account_number)

    if account is None:
        return jsonify({"error": "Account not found"}), 404

    balance = get_account_balance(account[0])

    return jsonify({
        "account_number": account[1],
        "currency": account[4],
        "balance": str(balance)
    }), 200

@account_bp.route("/accounts/<account_number>/transactions", methods=["GET"])
def get_account_transactions_endpoint(account_number):
    account = get_account_by_number(account_number)

    if account is None:
        return jsonify({"error": "Account not found"}), 404

    transactions = get_transactions_by_account(account[0])

    return jsonify([
        format_transaction_response(t) for t in transactions
    ]), 200

@account_bp.route("/accounts/<account_number>/fund", methods=["POST"])
def fund_account_endpoint(account_number):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    amount_raw = data.get("amount")
    description = data.get("description", "Account funding")

    if amount_raw is None:
        return jsonify({"error": "Missing amount"}), 400

    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
    except Exception:
        return jsonify({"error": "Invalid amount"}), 400

    # Get target account
    target_account = get_account_by_number(account_number)
    if target_account is None:
        return jsonify({"error": "Account not found"}), 404

    # Get funding source
    source_account = get_account_by_number("EXT-FUNDING-001")
    if source_account is None:
        return jsonify({"error": "Funding source not configured"}), 500

    transaction_reference = f"FUND-{uuid4()}"

    try:
        transaction = create_funding_transaction(
            transaction_reference,
            source_account[0],
            target_account[0],
            amount,
            target_account[4],
            description
        )

        return jsonify(format_transaction_response(transaction)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400