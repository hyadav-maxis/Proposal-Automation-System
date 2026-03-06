-- Table to store client-specific email template overrides
CREATE TABLE IF NOT EXISTS client_email_templates (
    id SERIAL PRIMARY KEY,
    client_email VARCHAR(255) UNIQUE NOT NULL,
    subject TEXT,
    body TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_client_email ON client_email_templates(client_email);
