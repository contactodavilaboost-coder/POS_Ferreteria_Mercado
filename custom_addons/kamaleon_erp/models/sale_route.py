# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KamaleonSaleRoute(models.Model):
    _name = 'kamaleon.sale.route'
    _description = 'Ruta de Venta'
    _order = 'name'

    name = fields.Char(string='Nombre / Número de Ruta', required=True)
    code = fields.Char(string='Código de Ruta')
    user_id = fields.Many2one('res.users', string='Vendedor Asignado')
    active = fields.Boolean(string='Activo', default=True)
    notes = fields.Text(string='Notas / Observaciones')
    partner_ids = fields.Many2many(
        'res.partner',
        'kamaleon_route_partner_rel',
        'route_id',
        'partner_id',
        string='Clientes en esta Ruta',
        domain="[('x_is_customer', '=', True)]"
    )
    partner_count = fields.Integer(string='Cantidad de Clientes', compute='_compute_partner_count')

    @api.depends('partner_ids')
    def _compute_partner_count(self):
        for record in self:
            record.partner_count = len(record.partner_ids)

    @api.model_create_multi
    def create(self, vals_list):
        routes = super(KamaleonSaleRoute, self).create(vals_list)
        for route in routes:
            route.with_context(_syncing_route=True)._sync_partner_route_and_user()
        return routes

    def write(self, vals):
        res = super(KamaleonSaleRoute, self).write(vals)
        if ('user_id' in vals or 'partner_ids' in vals) and not self.env.context.get('_syncing_route'):
            self.with_context(_syncing_route=True)._sync_partner_route_and_user()
        return res

    def unlink(self):
        # Desvincular clientes antes de eliminar la ruta
        for route in self:
            partners = self.env['res.partner'].sudo().search([('x_route_id', '=', route.id)])
            if partners:
                partners.with_context(_syncing_route=True).write({'x_route_id': False})
        return super(KamaleonSaleRoute, self).unlink()

    def _sync_partner_route_and_user(self):
        """Sincronizar la ruta y el vendedor en la ficha individual de cada cliente seleccionado"""
        for route in self:
            current_partner_ids = set(route.partner_ids.ids)

            # 1. Clientes que tenían esta ruta pero fueron removidos de partner_ids en la vista de la ruta
            orphaned_partners = self.env['res.partner'].sudo().search([
                ('x_route_id', '=', route.id),
                ('id', 'not in', list(current_partner_ids))
            ])
            if orphaned_partners:
                orphaned_partners.with_context(_syncing_route=True).write({'x_route_id': False})

            # 2. Clientes actualmente en la ruta que necesitan actualizarse
            if not current_partner_ids:
                continue

            updates = {'x_route_id': route.id}
            if route.user_id:
                updates['user_id'] = route.user_id.id

            partners_to_update = route.partner_ids.filtered(
                lambda p: p.x_route_id.id != route.id
                or (route.user_id and p.user_id.id != route.user_id.id)
            )

            if partners_to_update:
                partners_to_update.with_context(_syncing_route=True).write(updates)

