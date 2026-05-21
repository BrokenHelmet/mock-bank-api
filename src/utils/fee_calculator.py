import json
from decimal import Decimal, ROUND_HALF_UP


def load_fee_config():
    with open("src/config/fees.json", "r") as file:
        return json.load(file)


def get_active_fee_profile():
    config = load_fee_config()

    active_profile_name = config["active_profile"]

    return config["profiles"][active_profile_name]


def calculate_transfer_fee(amount, to_account_type):
    profile = get_active_fee_profile()

    if to_account_type == "external":
        fee = Decimal(
            str(profile["external_transfer_flat_fee"])
        )

        percentage = profile.get(
            "external_transfer_percentage"
        )

        if percentage is not None:
            percentage_fee = (
                amount * Decimal(str(percentage))
            ) / Decimal("100")

            fee += percentage_fee

    else:
        fee = Decimal(
            str(profile["internal_transfer_flat_fee"])
        )

    return fee.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )