# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].search([])
    
    for comp in companies:
        bank_journal = env['account.journal'].search([('company_id', '=', comp.id), ('type', '=', 'bank')], limit=1)
        if not bank_journal:
            bank_journal = env['account.journal'].search([('company_id', '=', comp.id)], limit=1)
            
        pago_movil = env['pos.payment.method'].search([('company_id', '=', comp.id), ('name', 'ilike', 'Pago M')], limit=1)
        if not pago_movil:
            pago_movil = env['pos.payment.method'].create({
                'name': 'Pago Móvil',
                'company_id': comp.id,
                'journal_id': bank_journal.id if bank_journal else False,
                'is_cash_count': False,
            })
            print(f'Created Pago Móvil (ID: {pago_movil.id}) for {comp.name}')
        else:
            print(f'Pago Móvil exists (ID: {pago_movil.id}) for {comp.name}')
            
        pos_configs = env['pos.config'].search([('company_id', '=', comp.id)])
        for pos in pos_configs:
            cr.execute("""
                INSERT INTO pos_config_pos_payment_method_rel (pos_config_id, pos_payment_method_id)
                SELECT %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM pos_config_pos_payment_method_rel 
                    WHERE pos_config_id = %s AND pos_payment_method_id = %s
                );
            """, (pos.id, pago_movil.id, pos.id, pago_movil.id))
            print(f'Linked Pago Móvil to POS {pos.name} (ID: {pos.id})')
            
    env.invalidate_all()
    cr.commit()
    print('SUCCESS: Pago Móvil configured for all companies and POS configs!')
