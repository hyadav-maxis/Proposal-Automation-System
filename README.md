# Proposal Automation System

Automated proposal and purchase order generation system with bulk complexity-based pricing for BIRT reports.

## Features

- ✅ Automatic pricing calculation based on multiple factors
- ✅ **Bulk complexity analysis** - Import complexity distribution from your existing tool
- ✅ CSV import for complexity data
- ✅ Proposal generation with **PDF and Excel download**
- ✅ **AI Assistant** - Create proposals via natural language chat (OpenAI)
- ✅ Purchase Order (PO) creation
- ✅ PostgreSQL database integration
- ✅ Web-based UI for easy use
- ✅ RESTful API for integration

## Architecture

The project follows a **Layered (Clean) Architecture** to ensure separation of concerns, scalability, and testability:

- **API Layer**: Route handlers that validate input but contain no business logic.
- **Service Layer**: Core business logic (pricing, proposal orchestration, document generation).
- **Repository Layer**: Data access layer (SQL) using the Repository Pattern.
- **Schema Layer**: Pydantic models for request/response validation.
- **Core Layer**: Centralized configuration, database connection, and exception management.

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database

1. Create PostgreSQL database:
```sql
CREATE DATABASE proposal_db;
```

2. Run the schema (located in `sql/`):
```bash
psql -U postgres -d proposal_db -f sql/database_schema.sql
```

### 3. Configure Environment

1. Copy `.env.example` to `.env`.
2. Update `.env` with your database credentials and OpenAI key.

### 4. Run the Application

```bash
python run.py
```
The server will start on `http://localhost:8000`. Hot-reload is enabled for the `app/` folder.

---

## Technical Stack

- **Backend**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL
- **AI Agent**: OpenAI GPT-4o
- **Documents**: ReportLab (PDF) & OpenPyXL (Excel)
- **Validation**: Pydantic v2

---

## File Structure

```text
proposal-automation/
├── app/                  # REST API & Business Logic
│   ├── api/              # Route definitions (v1)
│   ├── core/             # Config, DB, Exceptions
│   ├── repositories/     # SQLite/PostgreSQL Queries
│   ├── schemas/          # Pydantic Request/Response Models
│   ├── services/         # Business Logic & Orchestration
│   ├── prompts/          # AI System Prompts
│   └── main.py           # Application Factory
├── frontend/             # Static HTML Pages
├── sql/                  # Database Migration Scripts
├── scripts/              # Setup & Utility Utilities
├── tests/                # Unit & Integration Tests
├── static/               # Assets (Logos, etc.)
├── contracts/            # Generated PDF Documents
├── run.py                # Entry Point
├── .env                  # Environment Variables
├── pytest.ini            # Test Configuration
└── README.md             # This file
```

---

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run specific service tests
pytest tests/test_pricing_service.py
```

---

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
