# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    sale_price_unit = fields.Float(
        string="Precio Venta Unitario",
        related="product_id.lst_price",
        store=True,
        readonly=True,
    )

    total_sale_value = fields.Monetary(
        string="Valor Total Venta",
        compute="_compute_total_sale_value",
        currency_field="currency_id",
        store=True,
    )

    @api.depends('quantity', 'product_id', 'product_id.lst_price')
    def _compute_total_sale_value(self):
        for record in self:
            qty = record.quantity or 0.0
            price = record.product_id.lst_price or 0.0
            record.total_sale_value = qty * price
