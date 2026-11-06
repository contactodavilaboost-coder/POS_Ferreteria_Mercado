# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_check_block(self):
        if self.partner_id and self.partner_id.x_is_credit_blocked and not self.partner_id.x_credit_blocked_override:
            return {
                'warning': {
                    'title': '⛔ CLIENTE BLOQUEADO POR MOROSIDAD',
                    'message': f"El cliente {self.partner_id.name} se encuentra BLOQUEADO por poseer facturas sin cancelar emitidas hace más de 3 días ({self.partner_id.x_blocked_invoice_info}).\n\nRequiere autorización de Administración para procesar la venta.",
                }
            }

    def action_confirm(self):
        for order in self:
            if order.partner_id and order.partner_id.x_is_credit_blocked and not order.partner_id.x_credit_blocked_override:
                raise UserError(_(
                    "⛔ Imposible Confirmar Pedido:\n\nEl cliente '%s' se encuentra BLOQUEADO por morosidad.\n\nDetalle: %s.\n\nPor favor consulte con Administración para otorgar el permiso de autorización especial.",
                    order.partner_id.name, order.partner_id.x_blocked_invoice_info
                ))
        res = super(SaleOrder, self).action_confirm()

        # Auto-validar entregas para descontar de inmediato la cantidad en 'A la mano' (permitiendo stock negativo)
        for order in self:
            order._auto_validate_delivery_pickings()

        return res

    def _auto_validate_delivery_pickings(self):
        """Valida automáticamente las entregas de salida para que el stock 'A la mano'
        se descuente de inmediato en negativo si no hay existencias iniciales."""
        for order in self:
            pending_pickings = order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            for picking in pending_pickings:
                for move in picking.move_ids:
                    if move.product_uom_qty > 0:
                        move.quantity = move.product_uom_qty
                try:
                    res = picking.with_context(skip_sms=True).button_validate()
                    if isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
                        wiz = self.env['stock.backorder.confirmation'].browse(res.get('res_id'))
                        wiz.process()
                except Exception:
                    pass

    @api.depends('state', 'order_line.invoice_status', 'invoice_ids', 'invoice_ids.state', 'invoice_ids.move_type')
    def _compute_invoice_status(self):
        super(SaleOrder, self)._compute_invoice_status()
        for order in self:
            # Si la orden ya posee al menos una factura vinculada no cancelada,
            # marcarla automáticamente como facturada ('invoiced'), sin importar si fue parcial
            valid_invoices = order.invoice_ids.filtered(
                lambda inv: inv.state != 'cancel' and inv.move_type in ('out_invoice', 'out_refund')
            )
            if valid_invoices:
                order.invoice_status = 'invoiced'

