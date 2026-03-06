-- Add default email template settings to pricing_config table
-- Run this once against your PostgreSQL database

INSERT INTO pricing_config (config_key, config_value, description)
VALUES
(
    'email_template_subject',
    '"Proposal {{proposal_number}} — {{project_name}}"',
    'Subject line for proposal emails. Supports placeholders: {{client_name}}, {{proposal_number}}, {{project_name}}'
),
(
    'email_template_body',
    '"<html>\n  <body style=\"margin:0;padding:0;background:#f5f6fa;font-family:Arial,sans-serif;\">\n    {{logo_block}}\n    <div style=\"max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);\">\n      <div style=\"background:linear-gradient(135deg,#6366f1,#4f46e5);padding:32px 36px;\">\n        <h1 style=\"color:#fff;margin:0;font-size:1.4rem;font-weight:700;\">Proposal Ready</h1>\n        <p style=\"color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:0.9rem;\">{{proposal_number}}</p>\n      </div>\n      <div style=\"padding:32px 36px;\">\n        <p style=\"font-size:1rem;color:#1e2433;margin:0 0 16px;\">Dear <strong>{{client_name}}</strong>,</p>\n        <p style=\"color:#4b5563;line-height:1.7;margin:0 0 16px;\">Please find attached the proposal for the project <strong>{{project_name}}</strong>.</p>\n        <p style=\"color:#4b5563;line-height:1.7;margin:0;\">If you have any questions, feel free to reply to this email.</p>\n      </div>\n      <div style=\"background:#f8f9fc;padding:20px 36px;border-top:1px solid #e8eaf0;\">\n        <p style=\"margin:0;font-size:0.85rem;color:#9ca3af;\">Best regards,<br><strong style=\"color:#6366f1;\">Proposal Automation System</strong></p>\n      </div>\n    </div>\n  </body>\n</html>"',
    'HTML body for proposal emails. Supports placeholders: {{client_name}}, {{proposal_number}}, {{project_name}}, {{logo_block}}'
)
ON CONFLICT (config_key) DO NOTHING;
