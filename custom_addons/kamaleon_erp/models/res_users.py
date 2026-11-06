# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    x_is_vendedor_touch = fields.Boolean(
        string="Vendedor (Solo Cotizador Touch)",
        help="Si está marcado, este usuario es un Vendedor que SOLO tendrá acceso al Cotizador Touch. Se eliminarán automáticamente los permisos administrativos de otras aplicaciones."
    )
    x_is_cajero_pos = fields.Boolean(
        string="Cajero (Solo Punto de Venta)",
        help="Si está marcado, o si el usuario es 'CAJAS', este usuario es un Cajero que SOLO tendrá acceso al Punto de Venta (POS). Se ocultarán y eliminarán las demás aplicaciones."
    )

    def _is_cajero_pos_user(self):
        self.ensure_one()
        if self.x_is_cajero_pos:
            return True
        login = (self.login or '').strip().lower()
        name = (self.name or '').strip().upper()
        if login in ('cajas', 'caja') or name in ('CAJAS', 'CAJA'):
            return True
        return False

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self).create(vals_list)
        for user in users:
            if user.x_is_vendedor_touch:
                user._apply_vendedor_touch_restrictions()
            if user._is_cajero_pos_user():
                user._apply_cajero_pos_restrictions()
        return users

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        fields_to_check = ('x_is_vendedor_touch', 'x_is_cajero_pos', 'groups_id', 'login', 'name')
        if any(f in vals for f in fields_to_check):
            for user in self:
                if user.x_is_vendedor_touch:
                    user._apply_vendedor_touch_restrictions()
                if user._is_cajero_pos_user():
                    user._apply_cajero_pos_restrictions()
        return res

    def _apply_vendedor_touch_restrictions(self):
        self.ensure_one()
        touch_action = self.env.ref('kamaleon_erp.action_kamaleon_touch_sales', raise_if_not_found=False)
        vendedor_group = self.env.ref('kamaleon_erp.group_vendedor_cotizador_touch', raise_if_not_found=False)
        
        # Grupos que se deben ELIMINAR del usuario Vendedor Touch.
        # IMPORTANTE: group_sale_salesman y group_stock_user se eliminan porque
        # son los que muestran los menús de Ventas e Inventario en Odoo.
        # El Cotizador Touch usa sudo() en todas sus operaciones, por lo que
        # NO necesita estos grupos para funcionar.
        admin_group_xmlids = [
            'sales_team.group_sale_salesman',       # muestra menú Ventas
            'sales_team.group_sale_manager',
            'sales_team.group_sale_salesman_all_leads',
            'stock.group_stock_user',               # muestra menú Inventario
            'stock.group_stock_manager',
            'account.group_account_manager',
            'account.group_account_user',
            'account.group_account_invoice',
            'purchase.group_purchase_manager',
            'purchase.group_purchase_user',
            'point_of_sale.group_pos_manager',
            'point_of_sale.group_pos_user',
            'mrp.group_mrp_manager',
            'mrp.group_mrp_user',
            'hr.group_hr_manager',
            'hr.group_hr_user',
            'base.group_system',
        ]
        
        groups_to_remove = []
        for xmlid in admin_group_xmlids:
            g = self.env.ref(xmlid, raise_if_not_found=False)
            if g and g in self.groups_id:
                groups_to_remove.append((3, g.id))

        vals = {}
        if touch_action and self.action_id != touch_action:
            vals['action_id'] = touch_action.id

        group_cmds = list(groups_to_remove)
        if vendedor_group and vendedor_group not in self.groups_id:
            group_cmds.append((4, vendedor_group.id))

        if group_cmds:
            vals['groups_id'] = group_cmds

        if vals:
            super(ResUsers, self.sudo()).write(vals)

    def _apply_cajero_pos_restrictions(self):
        self.ensure_one()
        pos_action = self.env.ref('point_of_sale.action_pos_config_kanban', raise_if_not_found=False)
        pos_user_group = self.env.ref('point_of_sale.group_pos_user', raise_if_not_found=False)

        # Grupos de administración y back-office a eliminar del usuario CAJAS
        admin_group_xmlids = [
            'sales_team.group_sale_salesman',
            'sales_team.group_sale_manager',
            'sales_team.group_sale_salesman_all_leads',
            'stock.group_stock_user',
            'stock.group_stock_manager',
            'account.group_account_manager',
            'account.group_account_user',
            'account.group_account_invoice',
            'purchase.group_purchase_manager',
            'purchase.group_purchase_user',
            'point_of_sale.group_pos_manager',  # Se remueve POS Manager, queda únicamente como Cajero (group_pos_user)
            'mrp.group_mrp_manager',
            'mrp.group_mrp_user',
            'hr.group_hr_manager',
            'hr.group_hr_user',
            'base.group_system',
        ]

        groups_to_remove = []
        for xmlid in admin_group_xmlids:
            g = self.env.ref(xmlid, raise_if_not_found=False)
            if g and g in self.groups_id:
                groups_to_remove.append((3, g.id))

        vals = {}
        if pos_action and self.action_id != pos_action:
            vals['action_id'] = pos_action.id

        group_cmds = list(groups_to_remove)
        if pos_user_group and pos_user_group not in self.groups_id:
            group_cmds.append((4, pos_user_group.id))

        if group_cmds:
            vals['groups_id'] = group_cmds

        if vals:
            super(ResUsers, self.sudo()).write(vals)
