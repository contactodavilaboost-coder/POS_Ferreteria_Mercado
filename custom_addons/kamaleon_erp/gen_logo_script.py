import base64

logo_path = r'd:\monke\antigravityqlq\Odoo\custom_addons\kamaleon_erp\static\src\img\zais_logo.png'

with open(logo_path, 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode('utf-8')

runner_script = f"""import odoo
import base64
import sys

db_name = sys.argv[1] if len(sys.argv) > 1 else 'said_express'
print(f"Updating company logo and favicon on {{db_name}}...")
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', db_name])
db = odoo.sql_db.db_connect(db_name)
registry = odoo.modules.registry.Registry.new(db_name)

logo_data = "{logo_b64}"

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {{}})
    # 1. Update company logo
    companies = env['res.company'].search([])
    for comp in companies:
        comp.write({{
            'logo': logo_data,
            'logo_web': logo_data,
            'uses_default_logo': False,
        }})
        if comp.partner_id:
            comp.partner_id.write({{'image_1920': logo_data}})
            
    # 2. Update system parameter for web favicon
    env['ir.config_parameter'].sudo().set_param('web.favicon.url', '/kamaleon_erp/static/src/img/company_favicon.ico')
    
    cr.commit()
    print(f"Updated {{len(companies)}} companies and web.favicon.url on {{db_name}} successfully!")
"""

with open(r'd:\monke\antigravityqlq\Odoo\custom_addons\kamaleon_erp\update_logo.py', 'w') as f:
    f.write(runner_script)
print("update_logo.py generated successfully!")
