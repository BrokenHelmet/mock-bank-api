ALTER TABLE ledger_entries
ADD CONSTRAINT ledger_entries_entry_type_check
CHECK (entry_type IN ('debit', 'credit'));

ALTER TABLE ledger_entries
ADD CONSTRAINT ledger_entries_amount_positive_check
CHECK (amount > 0);
