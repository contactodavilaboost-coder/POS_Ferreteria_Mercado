# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, date, timedelta

class FerreteriaPosDashboard(models.TransientModel):
    _name = 'kamaleon.sales.dashboard'
    _description = 'Ferretería Mercado Executive POS & Retail Analytics Dashboard'

    @api.model
    def get_dashboard_analytics_data(self, *args, **kwargs):
        today = date.today()
        current_company_id = self.env.company.id

        # Extraer parámetros de fecha
        date_from = args[0] if len(args) > 0 and args[0] else kwargs.get('date_from')
        date_to = args[1] if len(args) > 1 and args[1] else kwargs.get('date_to')
        preset = args[2] if len(args) > 2 and args[2] else kwargs.get('preset')

        if preset == 'today':
            date_from = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_to = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif preset == 'week':
            start_week = today - timedelta(days=today.weekday())
            date_from = start_week.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_to = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif preset == 'month':
            date_from = today.replace(day=1).strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_to = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif preset == 'last_month':
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            date_from = last_month_start.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_to = last_month_end.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif preset == 'year':
            date_from = today.replace(month=1, day=1).strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_to = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif preset == 'all':
            date_from = '2020-01-01'
            date_to = '2030-12-31'

        if not date_from:
            date_from = '2020-01-01'
        if not date_to:
            date_to = today.strftime(DEFAULT_SERVER_DATE_FORMAT)

        # ── 1. DOMINIOS BASE POS & COMPRAS ───────────────────────────────────
        domain_pos = [
            ('company_id', '=', current_company_id),
            ('state', 'in', ['paid', 'done', 'invoiced']),
            ('date_order', '>=', date_from + ' 00:00:00'),
            ('date_order', '<=', date_to + ' 23:59:59'),
        ]

        domain_po = [
            ('company_id', '=', current_company_id),
            ('state', 'in', ['purchase', 'done']),
            ('date_approve', '>=', date_from + ' 00:00:00'),
            ('date_approve', '<=', date_to + ' 23:59:59'),
        ]

        pos_orders = self.env['pos.order'].search(domain_pos)
        pos_lines = self.env['pos.order.line'].search([('order_id', 'in', pos_orders.ids)]) if pos_orders else self.env['pos.order.line']
        purchase_orders = self.env['purchase.order'].search(domain_po)

        # ── 2. KPIS PRINCIPALES ──────────────────────────────────────────────
        total_pos_sales = sum(pos_orders.mapped('amount_total'))
        total_orders_count = len(pos_orders)
        avg_ticket = (total_pos_sales / total_orders_count) if total_orders_count > 0 else 0.0
        total_purchases = sum(purchase_orders.mapped('amount_total'))

        # ── 3. VALORACIÓN DE INVENTARIO FERRETERÍA (COSTO VS VENTA) ───────────
        quants = self.env['stock.quant'].search([
            ('company_id', '=', current_company_id),
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0)
        ])
        total_inv_cost = sum(q.quantity * q.product_id.standard_price for q in quants)
        total_inv_sale = sum(q.quantity * q.product_id.lst_price for q in quants)

        # ── 4. STOCK CRÍTICO DE FERRETERÍA ────────────────────────────────────
        all_products = self.env['product.product'].search([
            ('company_id', 'in', [False, current_company_id]),
            ('type', '=', 'consu'),
            ('active', '=', True)
        ])
        low_stock_list = []
        for p in all_products:
            stock = p.qty_available
            if stock <= 5:  # Umbral para ferretería
                low_stock_list.append({
                    'id': p.id,
                    'name': p.display_name,
                    'code': p.default_code or '',
                    'stock': stock,
                    'min_stock': 5,
                    'uom': p.uom_id.name or 'Unid',
                })
        low_stock_list.sort(key=lambda x: x['stock'])
        low_stock_display = low_stock_list[:15]
        low_stock_count = len(low_stock_list)

        # ── 5. MÉTODOS DE COBRO DEL POS (EFECTIVO, PAGO MÓVIL, TARJETA, BIOPAGO) ──
        pos_payments = self.env['pos.payment'].search([
            ('pos_order_id', 'in', pos_orders.ids)
        ]) if pos_orders else self.env['pos.payment']

        payment_method_totals = {}
        for pay in pos_payments:
            m_name = (pay.payment_method_id.name or 'Otro').strip()
            # Estandarizar nombres
            m_lower = m_name.lower()
            if 'efectivo' in m_lower or 'cash' in m_lower:
                cat = 'Efectivo'
            elif 'movil' in m_lower or 'móvil' in m_lower or 'pm' in m_lower:
                cat = 'Pago Móvil'
            elif 'tarjeta' in m_lower or 'punto' in m_lower or 'card' in m_lower:
                cat = 'Tarjeta / Punto'
            elif 'bio' in m_lower:
                cat = 'BioPago'
            elif 'zelle' in m_lower:
                cat = 'Zelle ($)'
            else:
                cat = m_name
            payment_method_totals[cat] = payment_method_totals.get(cat, 0.0) + pay.amount

        # ── 6. TENDENCIA DIARIA DE VENTAS DEL POS ─────────────────────────────
        trend_by_date = {}
        for o in pos_orders:
            d_str = fields.Date.to_string(o.date_order)
            trend_by_date[d_str] = trend_by_date.get(d_str, 0.0) + o.amount_total

        sorted_dates = sorted(trend_by_date.keys())
        trend_labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in sorted_dates]
        trend_values = [round(trend_by_date[d], 2) for d in sorted_dates]

        # ── 7. TOP 50 ARTÍCULOS DE FERRETERÍA MÁS VENDIDOS ─────────────────────
        product_sales = {}
        for l in pos_lines:
            p_id = l.product_id.id
            if p_id not in product_sales:
                product_sales[p_id] = {
                    'name': l.product_id.display_name,
                    'code': l.product_id.default_code or '',
                    'qty': 0.0,
                    'total': 0.0,
                }
            product_sales[p_id]['qty'] += l.qty
            product_sales[p_id]['total'] += l.price_subtotal_incl

        top_products = sorted(product_sales.values(), key=lambda x: x['qty'], reverse=True)[:50]

        # ── 8. RENDIMIENTO POR CAJA / CAJERO ──────────────────────────────────
        cashier_sales = {}
        for o in pos_orders:
            c_name = o.user_id.name or (o.config_id.name if o.config_id else 'Caja General')
            cashier_sales[c_name] = cashier_sales.get(c_name, 0.0) + o.amount_total

        # ── 9. TOP 20 CLIENTES VIP DE MOSTRADOR ───────────────────────────────
        client_sales = {}
        for o in pos_orders:
            c_id = o.partner_id.id if o.partner_id else 0
            c_name = o.partner_id.name if o.partner_id else 'Consumidor Final (Mostrador)'
            client_sales[c_name] = client_sales.get(c_name, 0.0) + o.amount_total

        top_clients = sorted(
            [{'name': k, 'total': round(v, 2)} for k, v in client_sales.items()],
            key=lambda x: x['total'],
            reverse=True
        )[:20]

        # ── 10. COMPARACIÓN COMPRAS VS VENTAS (MENSUAL / SEMANAL) ──────────────
        all_period_dates = sorted(list(set(
            list(trend_by_date.keys()) +
            [fields.Date.to_string(po.date_approve) for po in purchase_orders if po.date_approve]
        )))[-12:]  # Últimos 12 puntos de comparación

        po_by_date = {}
        for po in purchase_orders:
            if po.date_approve:
                d_str = fields.Date.to_string(po.date_approve)
                po_by_date[d_str] = po_by_date.get(d_str, 0.0) + po.amount_total

        pv_labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in all_period_dates] if all_period_dates else ['Sin datos']
        pv_sales = [round(trend_by_date.get(d, 0.0), 2) for d in all_period_dates] if all_period_dates else [0.0]
        pv_purchases = [round(po_by_date.get(d, 0.0), 2) for d in all_period_dates] if all_period_dates else [0.0]

        return {
            'kpis': {
                'total_sales': round(total_pos_sales, 2),
                'total_orders': total_orders_count,
                'avg_ticket': round(avg_ticket, 2),
                'total_purchases': round(total_purchases, 2),
                'total_inv_cost': round(total_inv_cost, 2),
                'total_inv_sale': round(total_inv_sale, 2),
                'low_stock_count': low_stock_count,
                'total_collected': round(total_pos_sales, 2),
                'collection_rate': 100.0 if total_pos_sales > 0 else 0.0,
            },
            'sales_trend': {
                'labels': trend_labels or ['Hoy'],
                'values': trend_values or [0.0],
            },
            'payment_methods': {
                'labels': list(payment_method_totals.keys()) or ['Efectivo'],
                'values': [round(v, 2) for v in payment_method_totals.values()] or [0.0],
            },
            'purchases_vs_sales': {
                'labels': pv_labels,
                'sales': pv_sales,
                'purchases': pv_purchases,
            },
            'top_products': top_products,
            'top_clients': top_clients,
            'cashier_sales': {
                'labels': list(cashier_sales.keys()) or ['Caja 1'],
                'values': [round(v, 2) for v in cashier_sales.values()] or [0.0],
            },
            'low_stock_products': low_stock_display,
        }
