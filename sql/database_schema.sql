-- Proposal Automation Database Schema
-- Run this in your PostgreSQL database

CREATE TABLE IF NOT EXISTS proposals (
    id SERIAL PRIMARY KEY,
    proposal_number VARCHAR(50) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_email VARCHAR(255),
    project_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft', -- draft, sent, approved, rejected
    total_price DECIMAL(12, 2),
    currency VARCHAR(10) DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS proposal_details (
    id SERIAL PRIMARY KEY,
    proposal_id INTEGER REFERENCES proposals(id) ON DELETE CASCADE,
    database_size_gb DECIMAL(10, 2),
    number_of_runs INTEGER DEFAULT 1,
    deployment_type VARCHAR(50) NOT NULL, -- 'inhouse_vm' or 'client_premises'
    has_where_clauses BOOLEAN DEFAULT FALSE,
    has_birt_reports BOOLEAN DEFAULT FALSE,
    complexity_score INTEGER DEFAULT 0, -- 0-5 from AI analysis (if used)
    complexity_reason TEXT,
    source_dialect VARCHAR(50),
    target_dialect VARCHAR(50),
    sql_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing report complexity breakdown
CREATE TABLE IF NOT EXISTS report_complexity_breakdown (
    id SERIAL PRIMARY KEY,
    proposal_id INTEGER REFERENCES proposals(id) ON DELETE CASCADE,
    complexity_score INTEGER NOT NULL CHECK (complexity_score >= 0 AND complexity_score <= 5),
    number_of_reports INTEGER NOT NULL DEFAULT 0,
    price_per_report DECIMAL(10, 2),
    total_price DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pricing_components (
    id SERIAL PRIMARY KEY,
    proposal_id INTEGER REFERENCES proposals(id) ON DELETE CASCADE,
    component_type VARCHAR(100) NOT NULL, -- 'database_size', 'runs', 'deployment', 'where_clauses', 'birt_reports', 'complexity'
    component_name VARCHAR(255),
    quantity DECIMAL(10, 2),
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(12, 2),
    description TEXT
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    proposal_id INTEGER REFERENCES proposals(id),
    client_name VARCHAR(255) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, sent, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    po_document_path VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS contracts (
    id SERIAL PRIMARY KEY,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    proposal_id INTEGER REFERENCES proposals(id),
    po_id INTEGER REFERENCES purchase_orders(id),
    client_name VARCHAR(255) NOT NULL,
    contract_type VARCHAR(50), -- 'proposal', 'purchase_order'
    document_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS pricing_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_client ON proposals(client_name);
CREATE INDEX IF NOT EXISTS idx_proposal_details_proposal ON proposal_details(proposal_id);
CREATE INDEX IF NOT EXISTS idx_pricing_components_proposal ON pricing_components(proposal_id);
CREATE INDEX IF NOT EXISTS idx_report_complexity_proposal ON report_complexity_breakdown(proposal_id);
CREATE INDEX IF NOT EXISTS idx_po_proposal ON purchase_orders(proposal_id);
CREATE INDEX IF NOT EXISTS idx_contracts_proposal ON contracts(proposal_id);

-- Insert default pricing configuration
INSERT INTO pricing_config (config_key, config_value, description) VALUES
('database_size_pricing', '{"base_price": 100, "price_per_gb": 50, "tiers": [{"max_gb": 10, "price_per_gb": 50}, {"max_gb": 50, "price_per_gb": 45}, {"max_gb": 100, "price_per_gb": 40}, {"max_gb": null, "price_per_gb": 35}]}', 'Pricing based on database size in GB'),
('runs_pricing', '{"base_price": 200, "price_per_run": 100, "bulk_discount": {"min_runs": 10, "discount_percent": 10}}', 'Pricing for number of runs'),
('deployment_pricing', '{"inhouse_vm": 500, "client_premises": 1000}', 'Pricing based on deployment type'),
('where_clauses_pricing', '{"base_price": 300, "complexity_multiplier": 1.2}', 'Additional pricing for WHERE clauses'),
('birt_reports_pricing', '{"base_price": 0, "complexity_pricing": {"0": {"price_per_report": 50, "description": "No conversion needed"}, "1": {"price_per_report": 75, "description": "Minimal effort"}, "2": {"price_per_report": 100, "description": "Simple conversion"}, "3": {"price_per_report": 150, "description": "Moderate effort"}, "4": {"price_per_report": 250, "description": "Complex conversion"}, "5": {"price_per_report": 400, "description": "Very complex"}}}', 'Complexity-based pricing for BIRT reports'),
('complexity_pricing', '{"multipliers": {"0": 1.0, "1": 1.1, "2": 1.2, "3": 1.4, "4": 1.6, "5": 2.0}}', 'Complexity-based pricing multipliers'),
('maximo_upgrade_pricing', '{"base_price": 500, "price_per_feature": 200}', 'Pricing for Maximo upgrade features'),
('addon_installation_pricing', '{"db2_installation": 500, "birt_installation": 500, "maximo_installation": 500}', 'Pricing for Add-On Installation Services'),
('usa_resource_pricing', '{"surcharge_multiplier": 1.35}', 'Multiplier for USA-based resources')
ON CONFLICT (config_key) DO NOTHING;
