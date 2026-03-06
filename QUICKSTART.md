# Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Setup Database

### Option A: Using PostgreSQL Command Line

```bash
# Create database
createdb proposal_db

# Run schema
psql -U postgres -d proposal_db -f database_schema.sql
```

### Option B: Using Python Setup Script

```bash
python setup.py
```

### Option C: Manual Setup

1. Connect to PostgreSQL:
```bash
psql -U postgres
```

2. Create database:
```sql
CREATE DATABASE proposal_db;
\c proposal_db
```

3. Run the SQL file:
```sql
\i database_schema.sql
```

## Step 3: Configure Environment

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and update database credentials:
```env
DB_HOST=localhost
DB_NAME=proposal_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_PORT=5432
```

## Step 4: Start the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

You can also use:
```bash
uvicorn main:app --reload
```

## Step 5: Open Web UI

1. Open `index.html` in your web browser
2. Or serve it using a simple HTTP server:
```bash
# Python 3
python -m http.server 8080

# Then open: http://localhost:8080/index.html
```

## Step 6: Create Your First Proposal

### Using Web UI:

1. Fill in client information
2. Enter database size and number of runs
3. Select deployment type
4. Check "BIRT Reports conversion required"
5. **Enter complexity distribution:**
   - Option A: Manually enter counts for each complexity level (0-5)
   - Option B: Click "Import CSV" and upload `sample_complexity.csv`
6. Click "Generate Proposal"
7. View the pricing breakdown

### Using API:

```bash
curl -X POST "http://localhost:8000/api/proposals/create" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "project_name": "Test Project",
    "database_size_gb": 50,
    "number_of_runs": 5,
    "deployment_type": "client_premises",
    "has_where_clauses": true,
    "has_birt_reports": true,
    "birt_complexity_distribution": {
      "0": 50,
      "1": 30,
      "2": 100,
      "3": 50,
      "4": 10
    }
  }'
```

## Testing CSV Import

1. Use the provided `sample_complexity.csv` file
2. In the web UI, check "BIRT Reports conversion required"
3. Click "Import CSV" button
4. Select `sample_complexity.csv`
5. The complexity distribution will be automatically populated

## API Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Database Connection Error

- Check PostgreSQL is running: `pg_isready`
- Verify database credentials in `.env`
- Ensure database exists: `psql -U postgres -l`

### Port Already in Use

Change the port in `main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Module Not Found

Make sure you're in the project directory:
```bash
cd proposal-automation
pip install -r requirements.txt
```

## Next Steps

- Review `README.md` for detailed documentation
- Customize pricing in the `pricing_config` table
- Integrate with your existing complexity analysis tool
- Generate PDF proposals and purchase orders
