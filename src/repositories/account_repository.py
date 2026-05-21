from src.db.connection import get_db_connection

def create_account(account_number, account_name, account_type, currency="KES"):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO accounts (
                    account_number,
                    account_name,
                    account_type,
                    currency
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id, account_number, account_name, account_type, currency, created_at, status;
                """,
                (account_number, account_name, account_type, currency)
            )

            account = cur.fetchone()
            conn.commit()

            return account

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_account_by_number(account_number):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_number, account_name, account_type, currency, created_at, status
                FROM accounts
                WHERE account_number = %s;
                """,
                (account_number,)
            )

            return cur.fetchone()

    finally:
        conn.close()

def get_account_by_id(account_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_number, account_name, account_type, currency, created_at, status
                FROM accounts
                WHERE id = %s;
                """,
                (account_id,)
            )

            return cur.fetchone()

    finally:
        conn.close()

def get_account_balance(account_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(
                        CASE
                            WHEN entry_type = 'credit' THEN amount
                            WHEN entry_type = 'debit' THEN -amount
                        END
                    ), 0) AS balance
                FROM ledger_entries
                WHERE account_id = %s;
                """,
                (account_id,)
            )

            return cur.fetchone()[0]

    finally:
        conn.close()

def get_all_accounts():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, account_number, account_name, account_type, currency, created_at, status
                FROM accounts
                ORDER BY id ASC;
                """
            )

            return cur.fetchall()

    finally:
        conn.close()

def update_account(account_number, account_name=None, status=None):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE accounts
                SET
                    account_name = COALESCE(%s, account_name),
                    status = COALESCE(%s, status)
                WHERE account_number = %s
                RETURNING id, account_number, account_name, account_type, currency, created_at, status;
                """,
                (account_name, status, account_number)
            )

            updated_account = cur.fetchone()
            conn.commit()

            return updated_account

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()