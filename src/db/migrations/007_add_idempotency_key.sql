ALTER TABLE transaction_attempts
ADD COLUMN idempotency_key TEXT;

CREATE UNIQUE INDEX transaction_attempts_idempotency_key_unique
ON transaction_attempts (idempotency_key)
WHERE idempotency_key IS NOT NULL;