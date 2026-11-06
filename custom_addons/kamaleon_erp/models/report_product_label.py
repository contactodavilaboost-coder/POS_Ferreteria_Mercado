# -*- coding: utf-8 -*-
from odoo import api, models


class ReportProductLabel6x4(models.AbstractModel):
    _name = 'report.kamaleon_erp.report_product_label_6x4'
    _description = 'Reporte Etiquetas de Precios Góndola 6x4 cm (3x6)'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        raw_items = []

        # 1. Obtener pares de (producto exacto, cantidad)
        if data.get('template_ids'):
            qty_map = data.get('quantity_by_product', {})
            for tmpl_id in data.get('template_ids'):
                tmpl = self.env['product.template'].browse(tmpl_id)
                if tmpl.exists():
                    count = qty_map.get(tmpl_id) or qty_map.get(str(tmpl_id)) or 1
                    for _ in range(max(1, int(count))):
                        raw_items.append(tmpl)

        elif data.get('product_ids'):
            qty_map = data.get('quantity_by_product', {})
            for prod_id in data.get('product_ids'):
                prod = self.env['product.product'].browse(prod_id)
                if prod.exists():
                    count = qty_map.get(prod_id) or qty_map.get(str(prod_id)) or 1
                    for _ in range(max(1, int(count))):
                        raw_items.append(prod)

        elif data.get('quantity_by_product'):
            # Fallback si viene de otro flujo
            active_model = data.get('active_model') or self.env.context.get('active_model') or self._context.get('active_model')
            for p_id_str, qty in data.get('quantity_by_product').items():
                try:
                    p_id = int(p_id_str)
                    count = int(qty)
                except (ValueError, TypeError):
                    continue
                if count <= 0:
                    continue

                if active_model == 'product.template':
                    record = self.env['product.template'].browse(p_id)
                else:
                    record = self.env['product.product'].browse(p_id)
                    if not record.exists():
                        record = self.env['product.template'].browse(p_id)

                if record and record.exists():
                    for _ in range(count):
                        raw_items.append(record)

        elif docids:
            active_model = self.env.context.get('active_model') or self._context.get('active_model')
            if active_model == 'product.product':
                records = self.env['product.product'].browse(docids)
            else:
                records = self.env['product.template'].browse(docids)
            for record in records:
                if record.exists():
                    raw_items.append(record)

        # 2. Procesar datos de cada etiqueta (Código de barras, Nombre, REF)
        processed_labels = []
        for prod in raw_items:
            # Obtener precio de venta en USD ($)
            price_val = getattr(prod, 'list_price', 0.0) or 0.0
            price_str = f"{price_val:,.2f}"

            # Código de barras (solo número/texto)
            barcode = (prod.barcode or '').strip()

            # Nombre limpio y referencia
            name = prod.name or ''
            # Si tiene atributos de variante, añadirlos al nombre
            if hasattr(prod, 'product_template_attribute_value_ids') and prod.product_template_attribute_value_ids:
                attr_str = ", ".join(prod.product_template_attribute_value_ids.mapped('name'))
                if attr_str:
                    name = f"{name} ({attr_str})"

            name = name.strip()
            price_int, _, price_dec = price_str.partition('.')

            # Tamaños dinámicos para la etiqueta de Ofertas 19x15 (en mm)
            name_len = len(name)
            if name_len <= 8:
                name_size = 19
            elif name_len <= 14:
                name_size = 16
            elif name_len <= 22:
                name_size = 13.5
            elif name_len <= 32:
                name_size = 11.5
            elif name_len <= 45:
                name_size = 9.5
            elif name_len <= 60:
                name_size = 8
            else:
                name_size = 6.8

            int_len = len(price_int)
            if int_len <= 2:
                price_size = 54
            elif int_len == 3:
                price_size = 44
            elif int_len <= 5:
                price_size = 34
            else:
                price_size = 26

            processed_labels.append({
                'name': name,
                'barcode': barcode,
                'default_code': (prod.default_code or '').strip(),
                'price': price_str,
                'price_int': price_int,
                'price_dec': price_dec or '00',
                'name_size': name_size,
                'price_size': price_size,
            })

        # 3. Paginación estricta en páginas de 18 etiquetas (3 columnas x 6 filas)
        # Esto previene el 100% de los errores de wkhtmltopdf con saltos de tabla
        PAGE_SIZE = 18
        pages = []
        for i in range(0, len(processed_labels), PAGE_SIZE):
            page_chunk = processed_labels[i:i + PAGE_SIZE]
            # Armar exactamente 6 filas de 3 columnas
            rows = []
            for r in range(6):
                row_cells = []
                for c in range(3):
                    idx = r * 3 + c
                    if idx < len(page_chunk):
                        row_cells.append(page_chunk[idx])
                    else:
                        row_cells.append(None)
                rows.append(row_cells)
            pages.append(rows)

        return {
            'doc_ids': docids,
            'doc_model': 'product.template',
            'docs': raw_items,
            'pages': pages,
            'labels': processed_labels,
            'total_labels': len(processed_labels),
            'company': self.env.company,
        }


class ReportProductLabelOferta19x15(models.AbstractModel):
    """Etiqueta de Ofertas RZ Marquet (2 por página Letter/Carta)."""
    _name = 'report.kamaleon_erp.report_product_label_oferta_19x15'
    _inherit = 'report.kamaleon_erp.report_product_label_6x4'
    _description = 'Reporte Etiquetas de Ofertas RZ Marquet (2 por hoja)'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super(ReportProductLabelOferta19x15, self)._get_report_values(docids, data)
        processed = res.get('labels', [])

        # Agrupar en páginas de 2 etiquetas exactamente para imprimir 2 por hoja
        pages_oferta = []
        for i in range(0, len(processed), 2):
            pages_oferta.append(processed[i:i + 2])

        res['pages_oferta'] = pages_oferta
        return res

