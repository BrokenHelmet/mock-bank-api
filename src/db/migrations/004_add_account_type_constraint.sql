ALTER TABLE accounts
ADD CONSTRAINT accounts_type_check
CHECK (
    account_type IN (
        'customer',
        'merchant',
        'float',
        'fees',
        'merchant_commission',
        'settlement',
        'bank',
        'internal'
    )
);
