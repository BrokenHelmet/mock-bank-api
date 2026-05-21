CREATE TABLE IF NOT EXISTS transaction_attempts (
    id SERIAL PRIMARY KEY,
    transaction_reference TEXT,
    from_account_number TEXT,
    to_account_number TEXT,
    amount NUMERIC(12,2),
    currency TEXT NOT NULL DEFAULT 'KES',
    status TEXT NOT NULL,
    failure_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT transaction_attempts_status_check
        CHECK (status IN ('success', 'failed'))
);