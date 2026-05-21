ALTER TABLE transactions
ADD COLUMN reverses_transaction_id INTEGER;

ALTER TABLE transactions
ADD CONSTRAINT fk_reverses_transaction
FOREIGN KEY (reverses_transaction_id)
REFERENCES transactions(id);

CREATE UNIQUE INDEX transactions_reversal_unique
ON transactions (reverses_transaction_id)
WHERE reverses_transaction_id IS NOT NULL;