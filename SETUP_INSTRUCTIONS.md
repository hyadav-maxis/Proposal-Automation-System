# Setup Instructions

## What’s already done

- Python dependencies are installed (`pip install -r requirements.txt`).
- `.env` exists (copy of `.env.example`). **You must set your Postgres password in `.env`.**
- `contracts` folder exists for generated PDFs.
- `setup_db.bat` and `run_setup.py` are ready for database setup.

## What you need to do

### 1. Set your Postgres password in `.env`

Edit `proposal-automation\.env` and set your actual Postgres password:

```env
DB_PASSWORD=your_actual_postgres_password
```

Keep the rest as-is (host, port, user, DB name) unless your setup is different.

### 2. Create the database and tables

**Option A – Using the batch file (recommended)**

1. Open a command prompt in the project folder:
   ```cmd
   cd d:\Contracts_workspace\proposal-automation
   ```
2. Run:
   ```cmd
   setup_db.bat
   ```
3. When prompted, enter your **PostgreSQL password** (same as in `.env`).
4. The script will create the `proposal_db` database and apply the schema.

**Option B – Using Python (after setting `DB_PASSWORD` in `.env`)**

1. Ensure `.env` has `DB_PASSWORD=your_actual_postgres_password`.
2. Run:
   ```cmd
   cd d:\Contracts_workspace\proposal-automation
   python run_setup.py
   ```

**Option C – Using psql manually**

```cmd
psql -U postgres -f create_db.sql
psql -U postgres -d proposal_db -f database_schema.sql
```

Enter your Postgres password when prompted.

### 3. Start the API

```cmd
cd d:\Contracts_workspace\proposal-automation
python main.py
```

The API will be at: **http://localhost:8000**

### 4. Open the Web UI

- Open `index.html` in your browser, or  
- Run: `python -m http.server 8080` in the project folder and go to:  
  **http://localhost:8080/index.html**

## Quick checklist

- [ ] `DB_PASSWORD` set in `.env`
- [ ] `setup_db.bat` run (or `run_setup.py` / manual psql)
- [ ] `python main.py` runs without connection errors
- [ ] Opened `index.html` and created a test proposal

## Troubleshooting

- **“no password supplied”**  
  Set `DB_PASSWORD` in `.env` and, for DB creation, use `setup_db.bat` and type the same password when prompted.

- **“database proposal_db already exists”**  
  Normal if you ran setup before. Just run the schema on the existing DB:
  ```cmd
  psql -U postgres -d proposal_db -f database_schema.sql
  ```

- **“relation already exists”**  
  Schema was already applied. Safe to ignore for existing tables; you can start the API with `python main.py`.
