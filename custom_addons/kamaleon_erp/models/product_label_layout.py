# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(
        selection_add=[
            ('6x4_price', 'Etiquetas Góndola 6x3.8 cm (Grandes sin recuadro)'),
            ('19x15_oferta', 'Etiqueta de OFERTAS RZ Marquet (2 en 1 hoja horizontal)'),
        ],
        ondelete={'6x4_price': 'set default', '19x15_oferta': 'set default'},
        default='6x4_price'
    )

    def _prepare_report_data(self):
        if self.print_format in ('6x4_price', '19x15_oferta'):
            qty = self.custom_quantity if (self.custom_quantity and self.custom_quantity > 0) else 1

            if self.product_tmpl_ids:
                quantity_by_product = {tmpl.id: qty for tmpl in self.product_tmpl_ids}
                data = {
                    'active_model': 'product.template',
                    'template_ids': self.product_tmpl_ids.ids,
                    'quantity_by_product': quantity_by_product,
                    'price_included': True,
                }
            elif self.product_ids:
                quantity_by_product = {prod.id: qty for prod in self.product_ids}
                data = {
                    'active_model': 'product.product',
                    'product_ids': self.product_ids.ids,
                    'quantity_by_product': quantity_by_product,
                    'price_included': True,
                }
            else:
                data = {'quantity_by_product': {}}

            if self.print_format == '19x15_oferta':
                return 'kamaleon_erp.action_report_product_template_label_oferta_19x15', data
            return 'kamaleon_erp.action_report_product_template_label_6x4', data

        return super()._prepare_report_data()
