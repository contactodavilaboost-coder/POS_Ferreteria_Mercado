# -*- coding: utf-8 -*-
"""
Script para sincronizar y recalcular el inventario 'A la mano' de TODOS los productos
estrictamente a partir de las FACTURAS CONFIRMADAS (account.move posted) y RECEPCIONES DE COMPRA,
llevando el stock a negativo cuando se ha vendido sin inventario inicial.
"""
import odoo
from odoo import api

def main():
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, 1, {})

        print("=" * 75)
        print("1. UBICACIONES DE INVENTARIO Y REGLAS DE STOCK...")
        print("=" * 75)

        stock_location = env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [False, env.company.id])
        ], limit=1)

        print(f"Ubicación Principal de Stock: {stock_location.name} (ID: {stock_location.id})")

        # 1. Totalizar cantidades recibidas en compras (stock.picking incoming en estado 'done')
        incoming_pickings = env['stock.picking'].search([
            ('picking_type_code', '=', 'incoming'),
            ('state', '=', 'done')
        ])
        purchased_quantities = {}
        for p in incoming_pickings:
            for sm in p.move_ids:
                if sm.product_id:
                    purchased_quantities[sm.product_id.id] = purchased_quantities.get(sm.product_id.id, 0.0) + sm.quantity

        print(f"Total recepciones de compra registradas: {len(incoming_pickings)} albaranes")

        # 2. Totalizar cantidades facturadas en facturas confirmadas (out_invoice posted)
        posted_invoices = env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])
        print(f"Total Facturas de Venta Publicadas: {len(posted_invoices)}")

        invoiced_quantities = {}
        for inv in posted_invoices:
            # Validar albaranes de salida vinculados para no dejar entregas en espera
            so = inv.line_ids.sale_line_ids.order_id
            if so:
                for pick in so.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                    for sm in pick.move_ids:
                        if sm.product_uom_qty > 0:
                            sm.quantity = sm.product_uom_qty
                    try:
                        res = pick.with_context(skip_sms=True).button_validate()
                        if isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
                            wiz = env['stock.backorder.confirmation'].browse(res.get('res_id'))
                            wiz.process()
                    except Exception:
                        pass

            prod_lines = inv.line_ids.filtered(
                lambda l: l.display_type in ('product', False) and l.product_id and l.quantity > 0 and not l.account_id.account_type == 'asset_receivable'
            )
            for line in prod_lines:
                pid = line.product_id.id
                invoiced_quantities[pid] = invoiced_quantities.get(pid, 0.0) + line.quantity

            # Marcar factura como descontada
            inv.x_stock_deducted = True

        print(f"Total productos distintos facturados: {len(invoiced_quantities)}")

        print("\n" + "=" * 75)
        print("2. ACTUALIZANDO STOCK 'A LA MANO' SEGÚN LO FACTURADO...")
        print("=" * 75)

        # Buscar todos los productos que han sido facturados o comprados
        all_product_ids = set(invoiced_quantities.keys()).union(set(purchased_quantities.keys()))
        products = env['product.product'].browse(list(all_product_ids))

        # En Odoo 18, asegurar que todas las plantillas de productos físicos tengan is_storable = True
        if hasattr(env['product.template'], 'is_storable'):
            templates_to_update = products.mapped('product_tmpl_id').filtered(lambda t: t.type != 'service' and not t.is_storable)
            if templates_to_update:
                templates_to_update.write({'is_storable': True})
                print(f"Activado seguimiento de stock (is_storable) para {len(templates_to_update)} productos.")

        updated_count = 0
        negative_count = 0

        for prod in products:
            if prod.type == 'service':
                continue

            # En Odoo 18, asegurar que el producto sea almacenable para permitir quants de inventario
            if hasattr(prod, 'is_storable') and not prod.is_storable:
                try:
                    prod.product_tmpl_id.is_storable = True
                except Exception:
                    pass

            qty_invoiced = invoiced_quantities.get(prod.id, 0.0)
            qty_purchased = purchased_quantities.get(prod.id, 0.0)

            # Saldo exacto: Compras - Facturación
            target_stock = qty_purchased - qty_invoiced

            # Buscar quant actual
            quant = env['stock.quant'].search([
                ('product_id', '=', prod.id),
                ('location_id', '=', stock_location.id)
            ], limit=1)

            current_qty = quant.quantity if quant else 0.0
            diff = target_stock - current_qty

            if abs(diff) > 0.0001:
                try:
                    env['stock.quant']._update_available_quantity(
                        prod,
                        stock_location,
                        diff
                    )
                    updated_count += 1
                    if target_stock < 0:
                        negative_count += 1
                    print(f"  • {prod.display_name[:40]:<40} | Facturado: {qty_invoiced:>5.0f} | Stock Actualizado: {target_stock:>6.0f}")
                except Exception as e:
                    print(f"  ⚠ Saltando {prod.display_name[:35]}: {e}")

        # Recalcular valoración de venta de todos los quants
        all_quants = env['stock.quant'].search([('location_id.usage', '=', 'internal')])
        for q in all_quants:
            if q.product_id:
                q.total_sale_value = q.quantity * (q.product_id.lst_price or 0.0)

        cr.commit()
        print("\n" + "=" * 75)
        print(f"¡SINCRONIZACIÓN EXITOSA! {updated_count} productos actualizados ({negative_count} en saldo negativo).")
        print("De ahora en adelante, cada factura confirmada descuenta el stock de forma automática.")
        print("=" * 75)

if __name__ == '__main__':
    main()
