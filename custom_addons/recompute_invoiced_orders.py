# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

def main():
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        print("\n=== RECALCULANDO ESTADO DE FACTURACIÓN EN ÓRDENES DE VENTA ===")

        orders = env['sale.order'].search([('state', '=', 'sale')])
        print(f"Total órdenes de venta confirmadas a revisar: {len(orders)}")

        updated_count = 0
        already_invoiced = 0

        for order in orders:
            valid_invoices = order.invoice_ids.filtered(
                lambda inv: inv.state != 'cancel' and inv.move_type in ('out_invoice', 'out_refund')
            )
            if valid_invoices:
                if order.invoice_status != 'invoiced':
                    order.invoice_status = 'invoiced'
                    updated_count += 1
                else:
                    already_invoiced += 1

        cr.commit()

        print("\n=======================================================")
        print(f"  - Órdenes que tenían factura y se pasaron a 'Facturado': {updated_count}")
        print(f"  - Órdenes que ya estaban en 'Facturado': {already_invoiced}")
        print("  - ¡Base de datos actualizada con éxito!")
        print("=======================================================\n")

if __name__ == '__main__':
    main()
