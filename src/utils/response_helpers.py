def format_account_response(account):
    return {
        "id": account[0],
        "account_number": account[1],
        "account_name": account[2],
        "account_type": account[3],
        "currency": account[4],
        "created_at": account[5].isoformat(),
        "status": account[6]
    }

def format_transaction_response(transaction):
    return {
        "id": transaction[0],
        "transaction_reference": transaction[1],
        "transaction_type": transaction[2],
        "status": transaction[3],
        "amount": str(transaction[4]),
        "currency": transaction[5],
        "description": transaction[6],
        "created_at": transaction[7].isoformat()
    }
