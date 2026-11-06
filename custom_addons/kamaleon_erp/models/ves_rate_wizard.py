# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class KamaleonVesRateWizard(models.TransientModel):
    _name = 'kamaleon.ves.rate.wizard'
    _description = 'Actualizar Tasa del Día BCV (Bs/$)'

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env['res.company'].search([('name', 'ilike', 'RZ MARQUET')], limit=1) or self.env.company
    )
    current_rate = fields.Float(
        string='Tasa Actual (Bs/$)',
        related='company_id.x_ves_rate',
        readonly=True,
        digits=(12, 4)
    )
    new_rate = fields.Float(
        string='Nueva Tasa BCV (Bs/$)',
        required=True,
        digits=(12, 4),
        help='Ingrese la nueva tasa oficial del BCV o del día en Bolívares por Dólar.'
    )
    date = fields.Date(
        string='Fecha',
        default=fields.Date.today,
        required=True
    )
    sync_pos = fields.Boolean(
        string='Sincronizar Cajas (POS)',
        default=True,
        help='Actualiza la tasa inmediatamente en todas las sesiones y cajas de Punto de Venta de la empresa.'
    )
    recalculate_produce = fields.Boolean(
        string='Ajustar Precios de Frutas y Hortalizas',
        default=True,
        help='Ajusta el precio en dólares ($) de los productos cotizados en Bolívares para que su precio en Bs. se mantenga exacto en las cajas.'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        comp = self.env['res.company'].search([('name', 'ilike', 'RZ MARQUET')], limit=1) or self.env.company
        if comp and hasattr(comp, 'x_ves_rate'):
            res['company_id'] = comp.id
            res['new_rate'] = comp.x_ves_rate or 65.0
        return res

    def action_apply_rate(self):
        self.ensure_one()
        if self.new_rate <= 0:
            raise UserError("La nueva tasa debe ser mayor a 0.0000.")

        company = self.company_id
        old_rate = company.x_ves_rate
        new_rate = self.new_rate

        # 1. Actualizar tasa en la compañía
        company.sudo().write({'x_ves_rate': new_rate})

        # 2. Sincronizar todas las cajas (POS) de la compañía
        updated_pos_count = 0
        if self.sync_pos:
            pos_configs = self.env['pos.config'].sudo().search([('company_id', '=', company.id)])
            if pos_configs:
                pos_configs.write({'x_ves_rate': new_rate})
                updated_pos_count = len(pos_configs)

        # 3. Recalcular precios en $ de Frutas y Hortalizas para mantener su precio en Bs exacto
        updated_produce_count = 0
        if self.recalculate_produce:
            produce_products = self.env['product.template'].sudo().search([
                ('company_id', 'in', [company.id, False]),
                ('x_is_price_in_ves', '=', True),
                ('x_price_ves', '>', 0)
            ])
            for prod in produce_products:
                prod.write({
                    'list_price': round(prod.x_price_ves / new_rate, 4)
                })
            updated_produce_count = len(produce_products)

        msg = (
            f"Tasa actualizada a {new_rate:.4f} Bs/$ para {company.name}.\n"
            f"• Cajas POS sincronizadas: {updated_pos_count}\n"
            f"• Productos (Frutas y Hortalizas) recalculados: {updated_produce_count}"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Tasa del Día Actualizada',
                'message': msg,
                'type': 'success',
                'sticky': False,
            }
        }
