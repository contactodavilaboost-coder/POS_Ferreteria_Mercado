# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    x_price_in_ves = fields.Boolean(
        string="Fijar Precio en Bolívares (Bs.)",
        default=False,
        help="Si está marcado, los productos de esta categoría (ej: Frutas y Hortalizas) se fijan y editan en Bolívares."
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_available_in_touch = fields.Boolean(
        string="Disponible en Cotizador Touch",
        default=True,
        help="Si está desmarcado, este producto no aparecerá en el catálogo del Cotizador Touch."
    )

    x_is_price_in_ves = fields.Boolean(
        string="Fijar Precio en Bolívares (Bs.)",
        compute="_compute_is_price_in_ves",
        inverse="_inverse_is_price_in_ves",
        store=True,
        help="Si está activo, el precio de venta de este producto se calcula desde el precio en Bolívares (como en Frutas y Hortalizas)."
    )

    x_open_price_ves = fields.Boolean(
        string="Monto Abierto en Bs. (Comodín / Surtidos)",
        default=False,
        help="Al hacer clic en este producto en el Punto de Venta, se solicitará directamente el monto en Bolívares a cobrar."
    )

    x_price_ves = fields.Float(
        string="Precio en Bs.",
        compute="_compute_price_ves",
        inverse="_inverse_price_ves",
        store=True,
        digits=(12, 2),
        help="Precio de venta en Bolívares. Al escribir aquí se calcula el precio en USD ($) según la tasa del día."
    )

    total_cost_value = fields.Monetary(
        string="Valor Total Costo",
        compute="_compute_inventory_values",
        currency_field="currency_id",
        store=False,
    )
    total_sale_value = fields.Monetary(
        string="Valor Total Venta",
        compute="_compute_inventory_values",
        currency_field="currency_id",
        store=False,
    )

    def _get_ves_rate(self):
        """Retorna la tasa del día de RZ Marquet o de la compañía activa."""
        self.ensure_one()
        comp = self.company_id or self.env['res.company'].search([('name', 'ilike', 'RZ MARQUET')], limit=1) or self.env.company
        if comp and hasattr(comp, 'x_ves_rate') and comp.x_ves_rate > 0:
            return comp.x_ves_rate
        return 65.0

    @api.depends('categ_id', 'categ_id.x_price_in_ves', 'categ_id.name')
    def _compute_is_price_in_ves(self):
        for product in self:
            cname = (product.categ_id.name or '').upper()
            keywords = ('FRUTA', 'HORTALIZA', 'VERDURA', 'LEGUMBRE', 'VIVERES FRESCOS')
            matches = any(k in cname for k in keywords)
            if product.categ_id.x_price_in_ves or matches:
                product.x_is_price_in_ves = True
            elif not product.x_is_price_in_ves:
                product.x_is_price_in_ves = False

    def _inverse_is_price_in_ves(self):
        pass  # Permite guardar cambios manuales directos en el checkbox

    @api.depends('list_price', 'company_id.x_ves_rate', 'x_is_price_in_ves')
    def _compute_price_ves(self):
        for product in self:
            rate = product._get_ves_rate()
            if not product.x_is_price_in_ves:
                product.x_price_ves = round((product.list_price or 0.0) * rate, 2)
            else:
                if not product.x_price_ves and product.list_price:
                    product.x_price_ves = round(product.list_price * rate, 2)

    def _inverse_price_ves(self):
        for product in self:
            rate = product._get_ves_rate()
            if rate > 0 and product.x_price_ves:
                product.list_price = round(product.x_price_ves / rate, 4)

    @api.onchange('categ_id')
    def _onchange_categ_id_ves(self):
        if self.categ_id:
            cname = (self.categ_id.name or '').upper()
            keywords = ('FRUTA', 'HORTALIZA', 'VERDURA', 'LEGUMBRE')
            if self.categ_id.x_price_in_ves or any(k in cname for k in keywords):
                self.x_is_price_in_ves = True

    @api.onchange('x_price_ves')
    def _onchange_x_price_ves(self):
        if self.x_price_ves is not None and self.x_price_ves >= 0:
            rate = self._get_ves_rate()
            if rate > 0:
                self.list_price = round(self.x_price_ves / rate, 4)

    @api.onchange('list_price')
    def _onchange_list_price(self):
        if not self.x_is_price_in_ves and self.list_price is not None:
            rate = self._get_ves_rate()
            if rate > 0:
                self.x_price_ves = round(self.list_price * rate, 2)

    @api.depends('qty_available', 'standard_price', 'list_price')
    def _compute_inventory_values(self):
        for product in self:
            qty = product.qty_available or 0.0
            product.total_cost_value = qty * (product.standard_price or 0.0)
            product.total_sale_value = qty * (product.list_price or 0.0)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_is_price_in_ves = fields.Boolean(
        related='product_tmpl_id.x_is_price_in_ves',
        readonly=False,
        store=True,
    )
    x_price_ves = fields.Float(
        related='product_tmpl_id.x_price_ves',
        readonly=False,
        store=True,
        digits=(12, 2),
        string="Precio en Bs."
    )

    total_cost_value = fields.Monetary(
        string="Valor Total Costo",
        compute="_compute_inventory_values",
        currency_field="currency_id",
        store=False,
    )
    total_sale_value = fields.Monetary(
        string="Valor Total Venta",
        compute="_compute_inventory_values",
        currency_field="currency_id",
        store=False,
    )

    @api.depends('qty_available', 'standard_price', 'lst_price')
    def _compute_inventory_values(self):
        for product in self:
            qty = product.qty_available or 0.0
            product.total_cost_value = qty * (product.standard_price or 0.0)
            product.total_sale_value = qty * (product.lst_price or 0.0)
