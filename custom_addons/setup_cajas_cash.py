# -*- coding: utf-8 -*-
"""
Script para configurar Efectivo exclusivo por caja:
- Caja 1 -> 'Efectivo'
- Caja 2 -> 'Efectivo 2'
- Caja 3 -> 'Efectivo 3'
Y vincular los métodos bancarios / Pago Móvil a todas las cajas.
"""
import odoo
from odoo import api, SUPERUSER_ID

def run():
    db_name = 'said_express'
    registry = odoo.modules.registry.Registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        print("=== CONFIGURACIÓN DE EFECTIVO EXCLUSIVO POR CAJA ===")

        # 1. Obtener todas las cajas activas
        cajas = env['pos.config'].with_context(active_test=False).search([])
        print(f"Cajas encontradas: {[c.name for c in cajas]}")

        # 2. Identificar Caja 1, Caja 2, Caja 3
        caja1 = env['pos.config'].search([('name', '=ilike', '%caja%1%')], limit=1) or (cajas[0] if len(cajas) > 0 else False)
        caja2 = env['pos.config'].search([('name', '=ilike', '%caja%2%')], limit=1) or (cajas[1] if len(cajas) > 1 else False)
        caja3 = env['pos.config'].search([('name', '=ilike', '%caja%3%')], limit=1) or (cajas[2] if len(cajas) > 2 else False)

        cajas_map = [
            (caja1, "Efectivo", "CSH1"),
            (caja2, "Efectivo 2", "CSH2"),
            (caja3, "Efectivo 3", "CSH3"),
        ]

        # Guardar IDs de métodos de efectivo creados/actualizados
        cash_pm_ids = {}

        for caja, target_cash_name, journal_code in cajas_map:
            if not caja:
                continue

            comp = caja.company_id or env['res.company'].browse(1)
            print(f"\nProcesando {caja.name} (Empresa: {comp.name}):")

            # A) Diario de efectivo exclusivo para esta caja
            cash_journal = env['account.journal'].search([
                ('company_id', '=', comp.id),
                ('type', '=', 'cash'),
                ('code', '=', journal_code),
            ], limit=1)

            if not cash_journal:
                # Buscar o crear
                cash_journal = env['account.journal'].search([
                    ('company_id', '=', comp.id),
                    ('type', '=', 'cash'),
                    ('name', '=ilike', f'%{target_cash_name}%')
                ], limit=1)

            if not cash_journal:
                cash_journal = env['account.journal'].create({
                    'name': f"{target_cash_name} {comp.name}",
                    'code': journal_code,
                    'type': 'cash',
                    'company_id': comp.id,
                })
                print(f"  + Creado Diario: {cash_journal.name} (Código: {journal_code})")
            else:
                print(f"  -> Usando Diario: {cash_journal.name} (ID: {cash_journal.id})")

            # B) Método de pago de efectivo exclusivo
            cash_pm = env['pos.payment.method'].search([
                ('company_id', '=', comp.id),
                ('name', '=', target_cash_name),
            ], limit=1)

            if not cash_pm:
                # Buscar por nombre global
                cash_pm = env['pos.payment.method'].search([
                    ('name', '=', target_cash_name)
                ], limit=1)

            if not cash_pm:
                cash_pm = env['pos.payment.method'].create({
                    'name': target_cash_name,
                    'company_id': comp.id,
                    'journal_id': cash_journal.id,
                    'is_cash_count': True,
                    'active': True,
                })
                print(f"  + Creado Método de Pago: '{cash_pm.name}' (ID: {cash_pm.id})")
            else:
                cash_pm.write({
                    'name': target_cash_name,
                    'company_id': comp.id,
                    'journal_id': cash_journal.id,
                    'is_cash_count': True,
                    'active': True,
                })
                print(f"  * Actualizado Método de Pago: '{cash_pm.name}' (ID: {cash_pm.id})")

            cash_pm_ids[caja.id] = cash_pm.id

        # 3. Métodos compartidos (no-efectivo, e.g. Pago Móvil, Bancos, Tarjetas)
        all_cash_ids = list(cash_pm_ids.values())

        for caja, target_cash_name, _ in cajas_map:
            if not caja:
                continue

            comp = caja.company_id or env['res.company'].browse(1)
            own_cash_id = cash_pm_ids[caja.id]

            # Buscar métodos no-efectivo de la empresa (Pago Móvil, Transferencias, etc.)
            other_pms = env['pos.payment.method'].search([
                ('company_id', '=', comp.id),
                ('is_cash_count', '=', False),
                ('active', '=', True),
            ])

            # Lista final de métodos para esta caja: SU propio efectivo + los métodos bancarios
            final_pm_ids = [own_cash_id] + [p.id for p in other_pms if p.id not in all_cash_ids]

            # Asignar a la caja
            caja.write({'payment_method_ids': [(6, 0, final_pm_ids)]})

            # Forzar en base de datos pos_config_pos_payment_method_rel
            cr.execute("DELETE FROM pos_config_pos_payment_method_rel WHERE pos_config_id = %s;", (caja.id,))
            for p_id in final_pm_ids:
                cr.execute("""
                    INSERT INTO pos_config_pos_payment_method_rel (pos_config_id, pos_payment_method_id)
                    VALUES (%s, %s);
                """, (caja.id, p_id))

            assigned_names = [env['pos.payment.method'].browse(pid).name for pid in final_pm_ids]
            print(f"\n-> Caja '{caja.name}': Métodos asignados = {assigned_names}")

        cr.commit()
        print("\n=== CONFIGURACIÓN FINALIZADA CON ÉXITO ===")

if __name__ == '__main__':
    run()
