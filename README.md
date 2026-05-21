# Mock Bank API

A Dockerized, ledger-based mock banking API designed for internal fintech testing, sandbox simulations, reconciliation practice, and API workflow development.

---

## Overview

Mock Bank API simulates realistic banking operations while maintaining lightweight architecture suitable for:

- Internal QA environments
- Finend / middleware integration testing
- Payment workflow simulations
- Ledger and reconciliation exercises
- Sandbox banking infrastructure prototypes
- Developer onboarding and experimentation

This project emphasizes:

- Double-entry ledger integrity
- Transaction traceability
- Fee configuration
- Idempotent transaction safety
- Reversal controls
- Basic concurrency safeguards

---

## Core Features

### Accounts

- Account creation
- Balance inquiry
- Internal customer accounts
- Float/master operational accounts
- Bank fee collection accounts

### Transactions

- Deposits
- Transfers
- Internal transfers
- External transfer fee simulation
- Immutable ledger entries
- Transaction history retrieval
- Transaction lookup by reference

### Fees

- Configurable fee profiles
- Internal transfer flat fees
- External transfer flat fees
- Dedicated fee collection ledgering

### Reversals

- Transfer reversals
- Reversal transaction linking
- Double reversal prevention
- Original transaction status marking (`reversed`)

### Safety Controls

- Idempotency support for safe retries
- Transaction attempts audit trail
- Minimum viable anti-double-spend row locking
- Database constraints for integrity

---

## Tech Stack

| Component | Technology |
|----------|------------|
| Backend API | Python (Flask) |
| Database | PostgreSQL |
| Containerization | Docker + Docker Compose |
| DB Driver | Psycopg |
| Migrations | SQL migration scripts |
| Testing | cURL + jq |

---

## Project Structure

```text
mock-bank-api/
│
├── src/
│   ├── routes/
│   ├── repositories/
│   ├── services/
│   ├── db/
│   │   └── migrations/
│   └── utils/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Git
- cURL
- jq (recommended)

---

### Clone Repository

```bash
git clone <your-repo-url>
cd mock-bank-api
```

---

### Start Services

```bash
sudo docker compose up -d
```

---

### Verify Running Containers

```bash
sudo docker compose ps
```

Expected:

- API service on port `5000`
- PostgreSQL on port `5432`

---

## Database Migrations

Run migrations manually inside the DB container:

```bash
sudo docker compose exec db psql -U mock_bank_user -d mock_bank -f src/db/migrations/001_init.sql
```

Repeat sequentially for all migration files.

### Recommended Future Improvement

Implement a migration runner for automated ordered execution.

---

## Environment Configuration

Typical environment variables:

```env
DB_HOST=db
DB_PORT=5432
DB_NAME=mock_bank
DB_USER=mock_bank_user
DB_PASSWORD=mock_bank_password
FLASK_ENV=development
```

---

## Key API Endpoints

### Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accounts` | Create account |
| GET | `/accounts/<account_number>/balance` | Get balance |

---

### Deposits

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/deposits` | Deposit funds |

---

### Transfers

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transfers` | Create transfer |
| POST | `/transfers/idempotent` | Safe retry transfer |
| GET | `/transactions` | List transactions |
| GET | `/transactions/<transaction_reference>` | Detailed transaction lookup |

---

### Reversals

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transactions/<transaction_reference>/reverse` | Reverse transfer |

---

### Fees

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fees/profile` | Active fee profile |

---

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transaction-attempts` | Failed + successful attempts |

---

## Example Usage

### Transfer Example

```bash
curl -s -X POST http://localhost:5000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account": "FLOAT-MAIN-001",
    "to_account": "INT-CUST-001",
    "amount": 100.00,
    "currency": "KES",
    "description": "Sandbox transfer"
  }' | jq
```

---

### Reverse Transaction

```bash
curl -s -X POST \
  http://localhost:5000/transactions/TX-REFERENCE/reverse | jq
```

---

### Check Balances

```bash
curl -s http://localhost:5000/accounts/FLOAT-MAIN-001/balance | jq
```

---

## Transaction Integrity Model

### Double-entry ledger

Every transaction creates:

- Debit entry
- Credit entry
- Optional fee ledger entry

---

### Reversal model

Reversals:

- Create new reversal transaction
- Link via `reverses_transaction_id`
- Prevent duplicate reversals via unique constraint
- Mark original transaction status as `reversed`

---

### Idempotency

Prevents duplicate execution from:

- Network retries
- API timeouts
- Client re-submissions

---

### Anti-double-spend safeguard

Uses row-level locking:

```sql
SELECT id FROM accounts WHERE id = ? FOR UPDATE;
```

This ensures concurrent requests cannot overspend the same balance during testing scenarios.

---

## Known Limitations

This project is **not production banking infrastructure**.

### Current limitations:

- Manual migration execution
- No authentication / RBAC
- No rate limiting
- No distributed transaction coordination
- No full serializable isolation
- No production WSGI deployment
- Limited pagination
- No webhook/event system

---

## Production Expansion Opportunities

Potential future upgrades:

- JWT authentication
- Admin dashboards
- Full sandbox customer APIs
- Automated migrations
- CI/CD pipelines
- Kubernetes deployment
- Transaction webhooks
- Multi-currency support
- AML simulation
- Fraud detection layers
- Regulatory reporting modules

---

## Testing Recommendations

Recommended tools:

- Postman
- cURL
- jq
- Docker logs
- PostgreSQL direct inspection

Useful log command:

```bash
sudo docker compose logs api --tail=50
```

---

## Contribution Guidelines

Suggested workflow:

1. Fork repository
2. Create feature branch
3. Add migration if schema changes
4. Test with Docker
5. Submit pull request

---

## License

Recommended:

```text
MIT License
```

Suitable for sandbox, educational, and internal development use.

---

## Final Notes

Mock Bank API is intentionally designed as:

```text
A realistic banking simulation foundation,
not a regulated production banking core.
```

It balances:

- Simplicity
- Ledger realism
- Operational safety
- Expandability

making it ideal for organizations seeking a customizable internal banking sandbox.

