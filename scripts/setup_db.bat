@echo off
cd /d "%~dp0"
echo Creating database and running schema...
echo You may be prompted for your PostgreSQL password.
echo.

psql -U postgres -c "CREATE DATABASE proposal_db;" 2>nul
if errorlevel 1 (
  echo Database proposal_db may already exist. Continuing...
) else (
  echo Database proposal_db created.
)

echo.
echo Applying schema to proposal_db...
psql -U postgres -d proposal_db -f database_schema.sql
if errorlevel 1 (
  echo Schema apply failed. Check your connection and password.
  pause
  exit /b 1
)

echo.
echo Done. Create .env with DB_PASSWORD=your_password and run: python main.py
pause
