-- Add Maximo Upgrade Pricing Configuration
INSERT INTO pricing_config (config_key, config_value, description) 
VALUES (
    'maximo_upgrade_pricing', 
    '{"base_price": 500, "price_per_feature": 200}'::jsonb, 
    'Pricing for Maximo upgrade features'
)
ON CONFLICT (config_key) DO UPDATE 
SET config_value = EXCLUDED.config_value, 
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;
