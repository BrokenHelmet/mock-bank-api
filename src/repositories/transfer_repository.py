from src.db.connection import get_db_connection


def create_transfer(
    transaction_reference,
    from_account_id,
    to_account_id,
    amount,
    currency="KES",
    description=None,
    bank_charge=None,
    bank_charges_account_id=None
):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (
                    transaction_reference,
                    transaction_type,
                    status,
                    amount,
                    currency,
                    description
                )
                VALUES (%s, 'transfer', 'completed', %s, %s, %s)
                RETURNING id, transaction_reference, transaction_type, status, amount, currency, description, created_at;
                """,
                (transaction_reference, amount, currency, description)
            )

            transaction = cur.fetchone()
            transaction_id = transaction[0]

            cur.execute(
                """
                INSERT INTO ledger_entries (
                    transaction_id,
                    account_id,
                    entry_type,
                    amount,
                    currency
                )
                VALUES (%s, %s, 'debit', %s, %s);
                """,
                (
                    transaction_id,
                    from_account_id,
                    amount + bank_charge if bank_charge else amount,
                    currency
                    )
            )

            cur.execute(
                """
                INSERT INTO ledger_entries (
                    transaction_id,
                    account_id,
                    entry_type,
                    amount,
                    currency
                )
                VALUES (%s, %s, 'credit', %s, %s);
                """,
                (transaction_id, to_account_id, amount, currency)
            )
            
            if bank_charge and bank_charges_account_id:
                cur.execute(
                    """
                    INSERT INTO ledger_entries (
                        transaction_id,
                        account_id,
                        entry_type,
                        amount,
                        currency
                    )
                    VALUES (%s, %s, 'credit', %s, %s);
                    """,
                    (
                        transaction_id,
                        bank_charges_account_id,
                        bank_charge,
                        currency
                    )
                )
            conn.commit()
            return transaction

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def create_funding_transaction(transaction_reference, source_account_id, target_account_id, amount, currency="KES", description=None):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (
                    transaction_reference,
                    transaction_type,
                    status,
                    amount,
                    currency,
                    description
                )
                VALUES (%s, 'deposit', 'completed', %s, %s, %s)
                RETURNING id, transaction_reference, transaction_type, status, amount, currency, description, created_at;
                """,
                (transaction_reference, amount, currency, description)
            )

            transaction = cur.fetchone()
            transaction_id = transaction[0]

            cur.execute(
                """
                INSERT INTO ledger_entries (
                    transaction_id,
                    account_id,
                    entry_type,
                    amount,
                    currency
                )
                VALUES (%s, %s, 'debit', %s, %s);
                """,
                (transaction_id, source_account_id, amount, currency)
            )

            cur.execute(
                """
                INSERT INTO ledger_entries (
                    transaction_id,
                    account_id,
                    entry_type,
                    amount,
                    currency
                )
                VALUES (%s, %s, 'credit', %s, %s);
                """,
                (transaction_id, target_account_id, amount, currency)
            )

            conn.commit()
            return transaction

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def create_reversal_transaction(
    reversal_reference,
    original_transaction_id,
    original_transaction_reference,
    from_account_id,
    to_account_id,
    amount,
    currency="KES",
    description=None
):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (
                    transaction_reference,
                    transaction_type,
                    status,
                    amount,
                    currency,
                    description,
                    reverses_transaction_id
                )
                VALUES (%s, 'reversal', 'completed', %s, %s, %s, %s)
                RETURNING id, transaction_reference, transaction_type, status, amount, currency, description, created_at;
                """,
                (
                    reversal_reference,
                    amount,
                    currency,
                    description or f"Reversal of {original_transaction_reference}",
                    original_transaction_id
                )
            )

            transaction = cur.fetchone()
            transaction_id = transaction[0]

            cur.execute(
                """
                INSERT INTO ledger_entries (
                    transaction_id,
                    account_id,
                    entry_type,
                    amount,
                    currency
                )
                VALUES (%s, %s, 'debit', %s, %s);
                """,
                (transaction_id, from_account_id, amount, currency)
            )

            cur.execute(
                """
                INSERT INTO ledger_entries (
                    transaction_id,
                    account_id,
                    entry_type,
                    amount,
                    currency
                )
                VALUES (%s, %s, 'credit', %s, %s);
                """,
                (transaction_id, to_account_id, amount, currency)
            )

            conn.commit()
            return transaction

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_all_transactions():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, transaction_reference, transaction_type, status, amount, currency, description, created_at
                FROM transactions
                ORDER BY created_at DESC;
                """
            )

            return cur.fetchall()

    finally:
        conn.close()

def get_transactions_by_account(account_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, t.transaction_reference, t.transaction_type, t.status,
                       t.amount, t.currency, t.description, t.created_at
                FROM transactions t
                JOIN ledger_entries le ON t.id = le.transaction_id
                WHERE le.account_id = %s
                ORDER BY t.created_at DESC;
                """,
                (account_id,)
            )

            return cur.fetchall()

    finally:
        conn.close()

def log_transaction_attempt(
    transaction_reference,
    from_account_number,
    to_account_number,
    amount,
    currency,
    status,
    failure_reason=None,
    idempotency_key=None
):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transaction_attempts (
                    transaction_reference,
                    from_account_number,
                    to_account_number,
                    amount,
                    currency,
                    status,
                    failure_reason,
                    idempotency_key
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    transaction_reference,
                    from_account_number,
                    to_account_number,
                    amount,
                    currency,
                    status,
                    failure_reason,
                    idempotency_key
                )
            )

            conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_all_transaction_attempts(limit=50):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, transaction_reference, from_account_number, to_account_number,
                amount, currency, status, failure_reason, created_at
                FROM transaction_attempts
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (limit,)    
            )

            return cur.fetchall()

    finally:
        conn.close()

def get_transaction_by_reference(transaction_reference):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, transaction_reference, transaction_type, status,
                       amount, currency, description, created_at
                FROM transactions
                WHERE transaction_reference = %s;
                """,
                (transaction_reference,)
            )

            return cur.fetchone()

    finally:
        conn.close()

def get_transaction_movement_by_reference(transaction_reference):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.id,
                    t.transaction_reference,
                    t.transaction_type,
                    t.status,
                    t.amount,
                    t.currency,
                    t.description,
                    t.created_at,

                    from_account.account_number AS from_account_number,
                    from_account.account_name AS from_account_name,

                    to_account.account_number AS to_account_number,
                    to_account.account_name AS to_account_name,

                    COALESCE(bank_charge_entry.amount, 0) AS bank_charge

                FROM transactions t

                JOIN ledger_entries from_entry
                    ON from_entry.transaction_id = t.id
                    AND from_entry.entry_type = 'debit'

                JOIN accounts from_account
                    ON from_account.id = from_entry.account_id

                JOIN ledger_entries to_entry
                    ON to_entry.transaction_id = t.id
                    AND to_entry.entry_type = 'credit'

                JOIN accounts to_account
                    ON to_account.id = to_entry.account_id
                
                LEFT JOIN ledger_entries bank_charge_entry
                    ON bank_charge_entry.transaction_id = t.id
                    AND bank_charge_entry.entry_type = 'credit'
                    AND bank_charge_entry.account_id != to_account.id                    

                WHERE t.transaction_reference = %s;
                """,
                (transaction_reference,)
            )

            return cur.fetchone()

    finally:
        conn.close()

def get_transaction_attempt_by_idempotency_key(idempotency_key):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, transaction_reference, from_account_number, to_account_number,
                       amount, currency, status, failure_reason, created_at, idempotency_key
                FROM transaction_attempts
                WHERE idempotency_key = %s;
                """,
                (idempotency_key,)
            )

            return cur.fetchone()

    finally:
        conn.close()

def get_transaction_accounts_by_reference(transaction_reference):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.id,
                    t.transaction_reference,
                    t.transaction_type,
                    t.status,
                    t.amount,
                    t.currency,

                    from_account.id AS from_account_id,
                    to_account.id AS to_account_id

                FROM transactions t

                JOIN ledger_entries from_entry
                    ON from_entry.transaction_id = t.id
                    AND from_entry.entry_type = 'debit'

                JOIN accounts from_account
                    ON from_account.id = from_entry.account_id

                JOIN ledger_entries to_entry
                    ON to_entry.transaction_id = t.id
                    AND to_entry.entry_type = 'credit'

                JOIN accounts to_account
                    ON to_account.id = to_entry.account_id

                WHERE t.transaction_reference = %s
                LIMIT 1;
                """,
                (transaction_reference,)
            )

            return cur.fetchone()

    finally:
        conn.close()

def get_reversal_by_original_transaction_id(original_transaction_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, transaction_reference
                FROM transactions
                WHERE reverses_transaction_id = %s
                LIMIT 1;
                """,
                (original_transaction_id,)
            )

            return cur.fetchone()

    finally:
        conn.close()

def mark_transaction_as_reversed(transaction_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE transactions
                SET status = 'reversed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, transaction_reference, transaction_type, status, amount, currency, description, created_at;
                """,
                (transaction_id,)
            )

            updated_transaction = cur.fetchone()
            conn.commit()

            return updated_transaction

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_account_balance_for_update(account_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            # Lock account row to prevent concurrent spending
            cur.execute(
                """
                SELECT id
                FROM accounts
                WHERE id = %s
                FOR UPDATE;
                """,
                (account_id,)
            )

            # After lock, safely calculate balance
            cur.execute(
                """
                SELECT COALESCE(
                    SUM(
                        CASE
                            WHEN entry_type = 'credit' THEN amount
                            WHEN entry_type = 'debit' THEN -amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS balance
                FROM ledger_entries
                WHERE account_id = %s;
                """,
                (account_id,)
            )

            result = cur.fetchone()
            return result[0]

    finally:
        conn.close()
