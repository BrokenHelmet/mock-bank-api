from flask import Blueprint, request, jsonify
from decimal import Decimal, ROUND_HALF_UP
from src.repositories.account_repository import (
    get_account_by_number,
    get_account_balance
)
from src.routes.transfer_routes import validate_account_transfer_status
from src.utils.fee_calculator import calculate_transfer_fee, load_fee_config

quote_bp = Blueprint("quotes", __name__)

def format_money(value):
    return str(
        value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    )

@quote_bp.route("/quotes/transfer", methods=["POST"])
def quote_transfer_endpoint():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    from_account_number = data.get("from_account")
    to_account_number = data.get("to_account")
    amount_raw = data.get("amount")
    currency = data.get("currency", "KES")

    if not from_account_number or not to_account_number or amount_raw is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        amount = Decimal(str(amount_raw))

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400

    except Exception:
        return jsonify({"error": "Invalid amount"}), 400

    from_account = get_account_by_number(from_account_number)
    to_account = get_account_by_number(to_account_number)

    if from_account is None:
        return jsonify({"error": "Invalid source account"}), 400

    if to_account is None:
        return jsonify({"error": "Invalid destination account"}), 400

    bank_charge = calculate_transfer_fee(
        amount,
        to_account[3]
    )

    total_debit = amount + bank_charge
    available_balance = get_account_balance(from_account[0])

    failure_reason = validate_account_transfer_status(
        from_account,
        to_account
    )

    if failure_reason is None and available_balance < total_debit:
        failure_reason = "Insufficient funds"

    return jsonify({
        "from_account": from_account[1],
        "to_account": to_account[1],
        "amount": format_money(amount),
        "bank_charge": format_money(bank_charge),
        "total_debit": format_money(total_debit),
        "recipient_receives": format_money(amount),
        "available_balance": format_money(available_balance),
        "can_transfer": failure_reason is None,
        "failure_reason": failure_reason,
        "currency": currency
    }), 200

@quote_bp.route("/fees/profile", methods=["GET"])
def get_fee_profile_endpoint():
    config = load_fee_config()
    active_profile_name = config["active_profile"]
    active_profile = config["profiles"][active_profile_name]

    return jsonify({
        "active_profile": active_profile_name,
        "profile": active_profile
    }), 200