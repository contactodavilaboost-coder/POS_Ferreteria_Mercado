# -*- coding: utf-8 -*-
from odoo import models, api

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _filter_visible_menus(self):
        res = super(IrUiMenu, self)._filter_visible_menus()
        # Superuser siempre ve todo
        if self.env.is_superuser():
            return res
        # Usar sudo() para leer flags del usuario sin errores de acceso
        user = self.env.user.sudo()
        if not user:
            return res

        # 1. Filtro para Vendedores Cotizador Touch: SOLO ven Cotizador Touch
        if getattr(user, 'x_is_vendedor_touch', False):
            touch_menu = self.env.ref('kamaleon_erp.menu_kamaleon_touch_sales_root', raise_if_not_found=False)
            if touch_menu:
                allowed_ids = set(
                    self.env['ir.ui.menu'].sudo().search([('id', 'child_of', touch_menu.id)]).ids
                )
                allowed_ids.add(touch_menu.id)
                return res.filtered(lambda m: m.id in allowed_ids)

        # 2. Filtro para Cajeros (Usuario CAJAS): SOLO ven Punto de Venta (POS)
        is_cajas = False
        if hasattr(user, '_is_cajero_pos_user'):
            is_cajas = user._is_cajero_pos_user()
        else:
            is_cajas = getattr(user, 'x_is_cajero_pos', False) or (user.login and user.login.strip().lower() in ('cajas', 'caja')) or (user.name and user.name.strip().upper() in ('CAJAS', 'CAJA'))

        if is_cajas:
            pos_menu = self.env.ref('point_of_sale.menu_point_root', raise_if_not_found=False)
            if pos_menu:
                allowed_ids = set(
                    self.env['ir.ui.menu'].sudo().search([('id', 'child_of', pos_menu.id)]).ids
                )
                allowed_ids.add(pos_menu.id)
                return res.filtered(lambda m: m.id in allowed_ids)

        return res
