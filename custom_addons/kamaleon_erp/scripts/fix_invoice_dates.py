# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

DATES_MAPPING = {
    'ZE/2026/00002': {'date': '2026-08-20', 'due_date': '2026-09-04'},
    'ZE/2026/00003': {'date': '2026-08-21', 'due_date': '2026-09-05'},
    'ZE/2026/00004': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00005': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00006': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00007': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00008': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00009': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00010': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00011': {'date': '2026-08-24', 'due_date': '2026-09-08'},
    'ZE/2026/00012': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00013': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00014': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00015': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00016': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00017': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00018': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00019': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00020': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00021': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00022': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00023': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00024': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'ZE/2026/00025': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    'S00038': {'date': '2026-08-20', 'due_date': '2026-09-04'},
    '44': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    '95': {'date': '2026-08-25', 'due_date': '2026-09-09'},
    '102': {'date': '2026-08-25', 'due_date': '2026-09-09'},
}

def update_invoice_dates():
    config_path = '/etc/odoo/odoo.conf'
    odoo.tools.config.parse_config(['-c', config_path])
    
    registry = odoo.registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=== ACTUALIZANDO FECHAS DE EMISIÓN Y VENCIMIENTO DE FACTURAS ===")
        updated_count = 0
        
        for num, dates in DATES_MAPPING.items():
            inv_date = dates['date']
            due_date = dates['due_date']
            
            # Search move by name
            moves = env['account.move'].search([('name', '=', num)])
            if not moves:
                moves = env['account.move'].search([('payment_reference', 'ilike', num)])
                
            for move in moves:
                # Update move header
                cr.execute("""
                    UPDATE account_move 
                    SET invoice_date = %s,
                        invoice_date_due = %s,
                        date = %s
                    WHERE id = %s
                """, (inv_date, due_date, inv_date, move.id))
                
                # Update move lines (date and date_maturity for receivable accounts)
                cr.execute("""
                    UPDATE account_move_line 
                    SET date = %s,
                        date_maturity = %s
                    WHERE move_id = %s
                """, (inv_date, due_date, move.id))
                
                updated_count += 1
                print(f"  [OK] {num} -> Emisión: {inv_date} | Vencimiento: {due_date}")
                
        cr.commit()
        print(f"\nTotal facturas actualizadas: {updated_count}")

if __name__ == '__main__':
    update_invoice_dates()
