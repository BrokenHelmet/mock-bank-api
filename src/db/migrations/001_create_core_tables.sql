CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    account_number TEXT NOT NULL UNIQUE,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'KES',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_reference TEXT NOT NULL UNIQUE,
    transaction_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    amount NUMERIC(12,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'KES',
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('debit','credit')),
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'KES',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_transaction
        FOREIGN KEY(transaction_id)
        REFERENCES transactions(id),

    CONSTRAINT fk_account
        FOREIGN KEY(account_id)
        REFERENCES accounts(id)
);
