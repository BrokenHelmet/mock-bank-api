ALTER TABLE transactions
ADD CONSTRAINT transactions_amount_positive_check
CHECK (amount > 0);

ALTER TABLE transactions
ADD CONSTRAINT transactions_status_check
CHECK (status IN ('pending', 'completed', 'failed', 'reversed'));

ALTER TABLE transactions
ADD CONSTRAINT transactions_type_check
CHECK (transaction_type IN ('transfer', 'deposit', 'withdrawal'));
