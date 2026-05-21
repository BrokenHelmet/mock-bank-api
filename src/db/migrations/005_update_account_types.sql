ALTER TABLE accounts
DROP CONSTRAINT IF EXISTS accounts_type_check;

ALTER TABLE accounts
ADD CONSTRAINT accounts_type_check
CHECK (
    account_type IN (
        'float',
        'internal',
        'external',
        'bank_charges'
    )
);
