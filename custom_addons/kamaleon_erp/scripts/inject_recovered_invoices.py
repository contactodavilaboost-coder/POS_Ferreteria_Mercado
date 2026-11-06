# -*- coding: utf-8 -*-
import json
import re
import os
import odoo
from odoo import api, SUPERUSER_ID

def parse_odoo_date(d_str):
    if not d_str:
        return '2026-08-25'
    d_str = str(d_str).strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', d_str):
        return d_str
    m = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', d_str)
    if m:
        p1, p2, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if p1 > 12:
            day, month = p1, p2
        elif p2 > 12:
            month, day = p1, p2
        else:
            day, month = p1, p2
        return f"{year:04d}-{month:02d}-{day:02d}"
    return '2026-08-25'

def run_injection():
    json_path = os.path.join(os.path.dirname(__file__), 'recovered_invoices_clean.json')
    if not os.path.exists(json_path):
        json_path = '/tmp/recovered_invoices_clean.json'
        
    with open(json_path, 'r', encoding='utf-8') as f:
        invoices_data = json.load(f)

    config_path = '/etc/odoo/odoo.conf'
    odoo.tools.config.parse_config(['-c', config_path])
    
    registry = odoo.registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Currencies
        usd_currency = env.ref('base.USD', raise_if_not_found=False)
        if not usd_currency:
            usd_currency = env['res.currency'].search([('name', '=', 'USD')], limit=1)
            
        company = env.company or env['res.company'].search([], limit=1)
        
        # Default product for fallback
        fallback_product = env['product.product'].search([('sale_ok', '=', True)], limit=1)
        
        created_invoices = 0
        total_invoiced_usd = 0.0
        
        print(f"=== INICIANDO INYECCIÓN DE {len(invoices_data)} DOCUMENTOS RECUPERADOS ===")
        
        for key, doc in invoices_data.items():
            try:
                num = doc.get('number') or key
                date = parse_odoo_date(doc.get('date'))
                client_name = doc.get('client') or 'Cliente General'
                rif = doc.get('rif') or ''
                vendedor_name = doc.get('vendedor') or ''
                doc_total = doc.get('total') or 0.0
                lines = doc.get('lines') or []
                
                if doc_total <= 0 or not lines:
                    continue
                    
                # 1. Partner
                partner = None
                if rif and rif != 'N/A':
                    clean_rif = rif.replace('-', '').replace(' ', '').upper()
                    partner = env['res.partner'].search([('vat', 'ilike', clean_rif)], limit=1)
                    if not partner:
                        partner = env['res.partner'].search([('vat', '=', rif)], limit=1)
                if not partner and client_name and len(client_name) > 3:
                    partner = env['res.partner'].search([('name', 'ilike', client_name[:20])], limit=1)
                    
                if not partner:
                    partner = env['res.partner'].create({
                        'name': client_name if client_name and 'Nombre' not in client_name else f"Cliente {rif}",
                        'vat': rif if rif and rif != 'N/A' else False,
                        'customer_rank': 1,
                        'company_id': company.id,
                    })
                    print(f"  [+] Nuevo cliente creado: {partner.name} ({rif})")
                    
                # 2. Salesperson / User
                user = False
                if vendedor_name and 'N/A' not in vendedor_name:
                    first_name = vendedor_name.split()[0]
                    user = env['res.users'].search([('name', 'ilike', first_name)], limit=1)
                    
                # 3. Check if document already exists
                existing_move = env['account.move'].search([('name', '=', num)], limit=1)
                if existing_move:
                    print(f"  [!] Factura {num} ya existe en el sistema. Omitiendo.")
                    continue
                    
                # 4. Prepare invoice lines
                invoice_lines = []
                for item in lines:
                    desc = item.get('description') or 'Producto'
                    qty = item.get('qty') or 1.0
                    price = item.get('price') or 0.0
                    
                    code_match = re.search(r'\[(.*?)\]', desc)
                    product = None
                    if code_match:
                        code = code_match.group(1).strip()
                        product = env['product.product'].search([('default_code', '=', code)], limit=1)
                        
                    if not product:
                        clean_name = re.sub(r'\[.*?\]', '', desc).strip()
                        if clean_name:
                            product = env['product.product'].search([('name', 'ilike', clean_name[:25])], limit=1)
                            
                    if not product:
                        product = fallback_product
                        
                    line_vals = {
                        'name': desc,
                        'quantity': qty,
                        'price_unit': price,
                        'product_id': product.id if product else False,
                        'tax_ids': False,
                    }
                    invoice_lines.append((0, 0, line_vals))
                    
                # 5. Create account.move (Invoice)
                move_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': partner.id,
                    'invoice_date': date,
                    'date': date,
                    'company_id': company.id,
                    'invoice_line_ids': invoice_lines,
                }
                if user:
                    move_vals['invoice_user_id'] = user.id
                    move_vals['user_id'] = user.id
                    
                move = env['account.move'].create(move_vals)
                
                try:
                    move.action_post()
                    if num and ('ZE/' in num or 'S00' in num):
                        cr.execute("UPDATE account_move SET name = %s WHERE id = %s", (num, move.id))
                except Exception as post_err:
                    print(f"  [!] Factura {num} creada en borrador: {post_err}")
                    
                created_invoices += 1
                total_invoiced_usd += move.amount_total or doc_total
                print(f"  [OK] Creada {num} - {partner.name[:25]} - Total: ${doc_total:.2f} USD")
            except Exception as e:
                print(f"  [x] Error procesando documento {key}: {e}")

        cr.commit()
        print(f"\n=======================================================")
        print(f"RESUMEN FINAL DE INYECCIÓN:")
        print(f"Facturas creadas con éxito: {created_invoices}")
        print(f"Monto total registrado: ${total_invoiced_usd:.2f} USD")
        print(f"=======================================================")

if __name__ == '__main__':
    run_injection()
