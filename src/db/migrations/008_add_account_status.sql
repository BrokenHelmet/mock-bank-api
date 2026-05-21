ALTER TABLE accounts
ADD COLUMN status TEXT NOT NULL DEFAULT 'active';

ALTER TABLE accounts
ADD CONSTRAINT accounts_status_check
CHECK (status IN ('active', 'inactive', 'closed'));