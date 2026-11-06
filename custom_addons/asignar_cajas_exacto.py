# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

def main():
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        print("\n=== ASIGNACIÓN EXACTA DE MÉTODOS DE PAGO POR CAJA ===")

        caja1_id = 9   # Caja1 - RZ Marquet
        caja2_id = 10  # Caja2 - Rz Marquet
        caja3_id = 11  # Caja3 - Rz Marquet

        # Métodos de pago exactos
        # ID 52: Efectivo
        # ID 56: Efectivo 2
        # ID 57: Efectivo 3
        # ID 53: Tarjeta
        # ID 55: Pago Movil
        # ID 60: Pago Móvil
        shared_pm_ids = [53, 55, 60]

        c1_methods = [52] + shared_pm_ids
        c2_methods = [56] + shared_pm_ids
        c3_methods = [57] + shared_pm_ids

        # 1. Asegurar diarios de cada efectivo
        # Efectivo 1 -> Diario Efectivo
        # Efectivo 2 -> Diario Cash
        # Efectivo 3 -> Diario Efectivo 3
        cr.execute("UPDATE pos_payment_method SET is_cash_count = true, active = true WHERE id IN (52, 56, 57);")
        cr.execute("UPDATE pos_payment_method SET is_cash_count = false, active = true WHERE id IN (53, 55, 60);")

        # 2. Borrar las asignaciones viejas de estas 3 cajas para evitar conflicto de sesión abierta
        print("Borrando asignaciones anteriores de Caja 1, 2 y 3...")
        cr.execute("DELETE FROM pos_config_pos_payment_method_rel WHERE pos_config_id IN (%s, %s, %s);", (caja1_id, caja2_id, caja3_id))

        # 3. Asignar Caja 1 -> Efectivo (52) + compartidos
        for pid in c1_methods:
            cr.execute("INSERT INTO pos_config_pos_payment_method_rel (pos_config_id, pos_payment_method_id) VALUES (%s, %s);", (caja1_id, pid))
        c1_names = [env['pos.payment.method'].browse(p).name for p in c1_methods]
        print(f"[OK] Caja 1 (ID 9) asignada con: {c1_names}")

        # 4. Asignar Caja 2 -> Efectivo 2 (56) + compartidos
        for pid in c2_methods:
            cr.execute("INSERT INTO pos_config_pos_payment_method_rel (pos_config_id, pos_payment_method_id) VALUES (%s, %s);", (caja2_id, pid))
        c2_names = [env['pos.payment.method'].browse(p).name for p in c2_methods]
        print(f"[OK] Caja 2 (ID 10) asignada con: {c2_names}")

        # 5. Asignar Caja 3 -> Efectivo 3 (57) + compartidos
        for pid in c3_methods:
            cr.execute("INSERT INTO pos_config_pos_payment_method_rel (pos_config_id, pos_payment_method_id) VALUES (%s, %s);", (caja3_id, pid))
        c3_names = [env['pos.payment.method'].browse(p).name for p in c3_methods]
        print(f"[OK] Caja 3 (ID 11) asignada con: {c3_names}")

        # 6. Sincronizar diarios de extractos para las sesiones abiertas de Caja 2 y Caja 3
        # Para que el control de apertura y cierre use el diario correcto de cada efectivo
        cr.execute("""
            UPDATE account_bank_statement_line
            SET journal_id = (SELECT journal_id FROM pos_payment_method WHERE id = 52)
            WHERE pos_session_id IN (SELECT id FROM pos_session WHERE config_id = %s AND state != 'closed');
        """, (caja1_id,))

        cr.execute("""
            UPDATE account_bank_statement_line
            SET journal_id = (SELECT journal_id FROM pos_payment_method WHERE id = 56)
            WHERE pos_session_id IN (SELECT id FROM pos_session WHERE config_id = %s AND state != 'closed');
        """, (caja2_id,))

        cr.execute("""
            UPDATE account_bank_statement_line
            SET journal_id = (SELECT journal_id FROM pos_payment_method WHERE id = 57)
            WHERE pos_session_id IN (SELECT id FROM pos_session WHERE config_id = %s AND state != 'closed');
        """, (caja3_id,))

        cr.commit()
        print("\n==================================================")
        print("¡ASIGNACIÓN COMPLETADA EXITOSAMENTE SIN ERRORES!")
        print("==================================================")

if __name__ == '__main__':
    main()
