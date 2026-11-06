# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, date, timedelta

class KamaleonSalesDashboard(models.TransientModel):
    _name = 'kamaleon.sales.dashboard'
    _description = 'Zais Express Executive Sales Analytics Dashboard'

    @api.model
    def get_dashboard_analytics_data(self, *args, **kwargs):
        today = date.today()
        current_company_id = self.env.company.id

        # Safely extract positional or keyword parameters
        date_from = args[0] if len(args) > 0 and args[0] else kwargs.get('date_from')
        date_to = args[1] if len(args) > 1 and args[1] else kwargs.get('date_to')
        preset = args[2] if len(args) > 2 and args[2] else kwargs.get('preset')

        # Handle quick presets
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

        # ── EXCLUSIÓN MULTIEMPRESA: RZ MARQUET / TRASPASOS INTERNOS ───────────
        # Identificar todas las empresas y contactos vinculados a RZ Marquet
        rz_companies = self.env['res.company'].search([
            '|', ('name', 'ilike', 'RZ MARQUET'), ('name', 'ilike', 'RZ MARKET')
        ])
        rz_partner_ids = set(rz_companies.mapped('partner_id').ids)
        rz_partners = self.env['res.partner'].search([
            '|', '|',
            ('name', 'ilike', 'RZ MARQUET'),
            ('name', 'ilike', 'RZ MARKET'),
            ('name', 'ilike', 'RZ MINI%')
        ])
        rz_partner_ids.update(rz_partners.ids)
        if rz_partner_ids:
            all_rz_contacts = self.env['res.partner'].search([
                ('id', 'child_of', list(rz_partner_ids))
            ])
            rz_partner_ids.update(all_rz_contacts.ids)
        rz_partner_list = list(rz_partner_ids)

        # ── DOMINIOS FILTRADOS POR EMPRESA ACTUAL Y SIN RZ MARQUET ─────────────
        domain_so = [
            ('state', 'in', ['sale', 'done']),
            ('company_id', '=', current_company_id),
            '|',
                '&', ('date_order', '!=', False), '&', ('date_order', '>=', date_from + ' 00:00:00'), ('date_order', '<=', date_to + ' 23:59:59'),
                '&', ('date_order', '=', False), '&', ('create_date', '>=', date_from + ' 00:00:00'), ('create_date', '<=', date_to + ' 23:59:59'),
        ]
        if rz_partner_list:
            domain_so.append(('partner_id', 'not in', rz_partner_list))

        domain_inv = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('company_id', '=', current_company_id),
            '|',
                '&', ('invoice_date', '!=', False), '&', ('invoice_date', '>=', date_from), ('invoice_date', '<=', date_to),
                '&', ('invoice_date', '=', False), '&', ('date', '>=', date_from), ('date', '<=', date_to),
        ]
        if rz_partner_list:
            domain_inv.append(('partner_id', 'not in', rz_partner_list))

        domain_refund = [
            ('move_type', '=', 'out_refund'),
            ('state', '=', 'posted'),
            ('company_id', '=', current_company_id),
            '|',
                '&', ('invoice_date', '!=', False), '&', ('invoice_date', '>=', date_from), ('invoice_date', '<=', date_to),
                '&', ('invoice_date', '=', False), '&', ('date', '>=', date_from), ('date', '<=', date_to),
        ]
        if rz_partner_list:
            domain_refund.append(('partner_id', 'not in', rz_partner_list))

        domain_date_pay = [
            ('payment_type', '=', 'inbound'),
            ('state', 'in', ['posted', 'paid', 'in_process']),
            ('company_id', '=', current_company_id),
            '|',
                '&', ('date', '!=', False), '&', ('date', '>=', date_from), ('date', '<=', date_to),
                '&', ('date', '=', False), '&', ('create_date', '>=', date_from + ' 00:00:00'), ('create_date', '<=', date_to + ' 23:59:59'),
        ]
        if rz_partner_list:
            domain_date_pay.append(('partner_id', 'not in', rz_partner_list))

        domain_po = [
            ('state', 'in', ['purchase', 'done']),
            ('company_id', '=', current_company_id),
            '|',
                '&', ('date_approve', '!=', False), '&', ('date_approve', '>=', date_from + ' 00:00:00'), ('date_approve', '<=', date_to + ' 23:59:59'),
                '&', ('date_approve', '=', False), '&', ('create_date', '>=', date_from + ' 00:00:00'), ('create_date', '<=', date_to + ' 23:59:59'),
        ]

        domain_bill = [
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('company_id', '=', current_company_id),
            '|',
                '&', ('invoice_date', '!=', False), '&', ('invoice_date', '>=', date_from), ('invoice_date', '<=', date_to),
                '&', ('invoice_date', '=', False), '&', ('date', '>=', date_from), ('date', '<=', date_to),
        ]

        # ── 1. RESUMEN DE VENTAS VS FACTURADO ─────────────────────────────────
        sales_orders = self.env['sale.order'].search(domain_so)
        invoices = self.env['account.move'].search(domain_inv)
        refunds = self.env['account.move'].search(domain_refund)

        total_so_amount = sum(sales_orders.mapped('amount_total'))
        total_so_count = len(sales_orders)

        total_inv_amount = sum(invoices.mapped('amount_total'))
        total_ref_amount = sum(refunds.mapped('amount_total'))
        # Total facturado neto (Facturas - Notas de crédito)
        total_invoiced_amount = max(0.0, total_inv_amount - total_ref_amount)

        # Ventas totales mayoristas = Pedidos de venta confirmados (sin RZ Marquet ni POS)
        total_sales_amount = total_so_amount
        total_orders_count = total_so_count

        avg_ticket = (total_sales_amount / total_orders_count) if total_orders_count > 0 else 0.0

        # Tendencia Diaria de Ventas
        daily_sales = {}
        if sales_orders:
            for order in sales_orders:
                order_dt = order.date_order or order.create_date
                day_str = order_dt.strftime('%Y-%m-%d') if order_dt else today.strftime('%Y-%m-%d')
                daily_sales[day_str] = daily_sales.get(day_str, 0.0) + order.amount_total
        else:
            for inv in invoices:
                inv_dt = inv.invoice_date or inv.date
                day_str = inv_dt.strftime('%Y-%m-%d') if inv_dt else today.strftime('%Y-%m-%d')
                daily_sales[day_str] = daily_sales.get(day_str, 0.0) + inv.amount_total

        sorted_days = sorted(daily_sales.keys())
        sales_trend_chart = {
            'labels': [datetime.strptime(d, '%Y-%m-%d').strftime('%d %b') for d in sorted_days],
            'data': [round(daily_sales[d], 2) for d in sorted_days]
        }

        # ── 2. COMPRAS VS VENTAS (MENSUAL) ────────────────────────────────────
        vendor_bills = self.env['account.move'].search(domain_bill)
        purchase_orders = self.env['purchase.order'].search(domain_po)

        MONTH_NAMES = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        period_data = {}
        if sales_orders:
            for so in sales_orders:
                so_dt = so.date_order or (so.create_date.date() if so.create_date else today)
                key = so_dt.strftime('%Y-%m')
                label = f"{MONTH_NAMES.get(so_dt.month, '')} {so_dt.year}"
                if key not in period_data:
                    period_data[key] = {'label': label, 'sales': 0.0, 'purchases': 0.0}
                period_data[key]['sales'] += so.amount_total
        else:
            for inv in invoices:
                inv_dt = inv.invoice_date or inv.date or (inv.create_date.date() if inv.create_date else today)
                key = inv_dt.strftime('%Y-%m')
                label = f"{MONTH_NAMES.get(inv_dt.month, '')} {inv_dt.year}"
                if key not in period_data:
                    period_data[key] = {'label': label, 'sales': 0.0, 'purchases': 0.0}
                period_data[key]['sales'] += inv.amount_total

        for bill in vendor_bills:
            b_dt = bill.invoice_date or bill.date or (bill.create_date.date() if bill.create_date else today)
            key = b_dt.strftime('%Y-%m')
            label = f"{MONTH_NAMES.get(b_dt.month, '')} {b_dt.year}"
            if key not in period_data:
                period_data[key] = {'label': label, 'sales': 0.0, 'purchases': 0.0}
            period_data[key]['purchases'] += bill.amount_total

        for po in purchase_orders:
            po_invoices = po.invoice_ids.filtered(lambda m: m.state == 'posted' and m.move_type == 'in_invoice')
            if not po_invoices:
                po_dt = po.date_approve or (po.date_order.date() if po.date_order else (po.create_date.date() if po.create_date else today))
                key = po_dt.strftime('%Y-%m') if isinstance(po_dt, (date, datetime)) else str(po_dt)[:7]
                label = f"{MONTH_NAMES.get(po_dt.month, '')} {po_dt.year}" if isinstance(po_dt, (date, datetime)) else key
                if key not in period_data:
                    period_data[key] = {'label': label, 'sales': 0.0, 'purchases': 0.0}
                period_data[key]['purchases'] += po.amount_total

        total_purchases_amount = sum(d['purchases'] for d in period_data.values())

        sorted_keys = sorted(period_data.keys())
        purchases_vs_sales_chart = {
            'labels': [period_data[k]['label'] for k in sorted_keys] if sorted_keys else ['Mes Actual'],
            'sales_data': [round(period_data[k]['sales'], 2) for k in sorted_keys] if sorted_keys else [round(total_sales_amount, 2)],
            'purchases_data': [round(period_data[k]['purchases'], 2) for k in sorted_keys] if sorted_keys else [round(total_purchases_amount, 2)],
            'total_sales': round(total_sales_amount, 2),
            'total_purchases': round(total_purchases_amount, 2),
        }

        # ── 3. VALORACIÓN TOTAL DE INVENTARIO ─────────────────────────────────
        internal_quants = self.env['stock.quant'].search([
            ('location_id.usage', '=', 'internal'),
            ('company_id', 'in', [False, current_company_id]),
            ('quantity', '>', 0)
        ])
        total_inv_cost = sum(q.quantity * (q.product_id.standard_price or 0.0) for q in internal_quants)
        total_inv_sale = sum(q.quantity * (q.product_id.lst_price or getattr(q.product_id, 'list_price', 0.0) or 0.0) for q in internal_quants)

        # ── 4. TOP 50 PRODUCTOS MÁS VENDIDOS ──────────────────────────────────
        product_totals = {}
        if sales_orders:
            order_lines = self.env['sale.order.line'].search([
                ('order_id', 'in', sales_orders.ids),
                ('display_type', '=', False),
                ('product_id', '!=', False)
            ])
            for line in order_lines:
                pid = line.product_id.id
                pname = line.product_id.display_name
                if pid not in product_totals:
                    product_totals[pid] = {'name': pname, 'qty': 0.0, 'amount': 0.0}
                product_totals[pid]['qty'] += line.product_uom_qty
                product_totals[pid]['amount'] += line.price_subtotal
        else:
            invoice_lines = self.env['account.move.line'].search([
                ('move_id', 'in', invoices.ids),
                ('display_type', '=', 'product'),
                ('product_id', '!=', False)
            ])
            for line in invoice_lines:
                pid = line.product_id.id
                pname = line.product_id.display_name
                if pid not in product_totals:
                    product_totals[pid] = {'name': pname, 'qty': 0.0, 'amount': 0.0}
                product_totals[pid]['qty'] += line.quantity
                product_totals[pid]['amount'] += line.price_subtotal

        top_products = sorted(product_totals.values(), key=lambda x: x['qty'], reverse=True)[:50]
        top_50_chart = {
            'labels': [p['name'][:30] for p in top_products],
            'qty_data': [round(p['qty'], 2) for p in top_products],
            'amount_data': [round(p['amount'], 2) for p in top_products]
        }

        # ── 5. COBRANZA EXITOSA DEL MES ───────────────────────────────────────
        payments = self.env['account.payment'].search(domain_date_pay)
        total_payments_collected = sum(payments.mapped('amount'))
        
        # Facturas con pagos registrados
        total_invoiced_collected = sum(
            (inv.amount_total - inv.amount_residual) for inv in invoices if (inv.amount_total - inv.amount_residual) > 0
        )
        
        total_collected = max(total_payments_collected, total_invoiced_collected)
        pending_collection = max(0.0, total_invoiced_amount - total_collected)
        collection_rate = (total_collected / total_invoiced_amount * 100) if total_invoiced_amount > 0 else 0.0

        collection_chart = {
            'labels': ['Facturado', 'Cobrado', 'Pendiente de Cobro'],
            'data': [round(total_invoiced_amount, 2), round(total_collected, 2), round(pending_collection, 2)],
            'rate': round(collection_rate, 1)
        }

        # ── 6. RESUMEN POR RUTAS ──────────────────────────────────────────────
        route_sales = {}
        if sales_orders:
            for order in sales_orders:
                route_name = order.partner_id.x_route_id.name if hasattr(order.partner_id, 'x_route_id') and order.partner_id.x_route_id else (
                    order.partner_id.route_id.name if hasattr(order.partner_id, 'route_id') and order.partner_id.route_id else _('Sin Ruta')
                )
                route_sales[route_name] = route_sales.get(route_name, 0.0) + order.amount_total
        else:
            for inv in invoices:
                route_name = inv.partner_id.x_route_id.name if hasattr(inv.partner_id, 'x_route_id') and inv.partner_id.x_route_id else (
                    inv.partner_id.route_id.name if hasattr(inv.partner_id, 'route_id') and inv.partner_id.route_id else _('Sin Ruta')
                )
                route_sales[route_name] = route_sales.get(route_name, 0.0) + inv.amount_total

        routes_sorted = sorted(route_sales.items(), key=lambda x: x[1], reverse=True)
        routes_chart = {
            'labels': [r[0] for r in routes_sorted],
            'data': [round(r[1], 2) for r in routes_sorted]
        }

        # ── 7. RESUMEN POR VENDEDOR ────────────────────────────────────────────
        seller_sales = {}
        if sales_orders:
            for order in sales_orders:
                seller_name = order.user_id.name if order.user_id else _('Sin Vendedor')
                seller_sales[seller_name] = seller_sales.get(seller_name, 0.0) + order.amount_total
        else:
            for inv in invoices:
                seller_name = inv.invoice_user_id.name if inv.invoice_user_id else (inv.user_id.name if hasattr(inv, 'user_id') and inv.user_id else _('Sin Vendedor'))
                seller_sales[seller_name] = seller_sales.get(seller_name, 0.0) + inv.amount_total

        sellers_sorted = sorted(seller_sales.items(), key=lambda x: x[1], reverse=True)
        sellers_chart = {
            'labels': [s[0] for s in sellers_sorted],
            'data': [round(s[1], 2) for s in sellers_sorted]
        }

        # ── 8. FILL RATE (MONTO SOLICITADO VS ENTREGADO EN $) ──────────────────
        if sales_orders:
            order_lines = self.env['sale.order.line'].search([
                ('order_id', 'in', sales_orders.ids),
                ('display_type', '=', False),
                ('product_id', '!=', False)
            ])
            total_ordered_amount = 0.0
            total_delivered_amount = 0.0

            for line in order_lines:
                line_ordered_val = line.price_subtotal or (line.product_uom_qty * line.price_unit)
                total_ordered_amount += line_ordered_val

                qty_del = line.qty_delivered or 0.0
                qty_inv = line.qty_invoiced or 0.0
                effective_qty = max(qty_del, qty_inv)
                if effective_qty == 0.0 and line.order_id.state == 'done':
                    effective_qty = line.product_uom_qty

                # Ratio de entrega limitado al 100% por item para no ocultar faltantes
                if line.product_uom_qty > 0:
                    line_ratio = min(effective_qty, line.product_uom_qty) / line.product_uom_qty
                    line_delivered_val = line_ordered_val * line_ratio
                else:
                    line_delivered_val = line_ordered_val if effective_qty > 0 else 0.0

                total_delivered_amount += line_delivered_val

            total_delivered_amount = min(total_delivered_amount, total_ordered_amount)
            fill_rate_percent = (total_delivered_amount / total_ordered_amount * 100) if total_ordered_amount > 0 else 100.0

            fill_rate_chart = {
                'ordered': round(total_ordered_amount, 2),
                'delivered': round(total_delivered_amount, 2),
                'percent': round(fill_rate_percent, 1)
            }
        else:
            fill_rate_chart = {
                'ordered': 0.0,
                'delivered': 0.0,
                'percent': 100.0
            }

        # ── 9. ANÁLISIS DE CARTERA VENCIDA (AGING RECEIVABLES) ────────────────
        # Cartera Vencida calculada ESTRICTAMENTE desde la Fecha de Entrega (x_delivery_date),
        # que es el origen de la columna 'Atraso / Vencimiento' (x_overdue_info).
        # Solo aplica a facturas marcadas como entregadas (x_is_delivered) y con fecha de entrega anterior a hoy.
        domain_unpaid = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('company_id', '=', current_company_id),
            ('payment_state', 'in', ['not_paid', 'partial', 'in_payment']),
            ('amount_residual', '>', 0)
        ]
        if rz_partner_list:
            domain_unpaid.append(('partner_id', 'not in', rz_partner_list))

        unpaid_invoices = self.env['account.move'].search(domain_unpaid, order='invoice_date asc')

        aging_buckets = {
            '1_7': {'label': '1-7 días de mora', 'amount': 0.0, 'color': '#34d399'},
            '8_15': {'label': '8-15 días de mora', 'amount': 0.0, 'color': '#f59e0b'},
            '16_30': {'label': '16-30 días de mora', 'amount': 0.0, 'color': '#f97316'},
            '30_plus': {'label': '+30 días (Crítico)', 'amount': 0.0, 'color': '#ef4444'}
        }

        total_overdue = 0.0
        overdue_invoices_list = []
        for inv in unpaid_invoices:
            # Plazo de crédito en días
            term_days = 0
            if inv.invoice_date_due and inv.invoice_date:
                term_days = max(0, (inv.invoice_date_due - inv.invoice_date).days)

            # Fecha de vencimiento efectiva (si fue entregada, desde fecha de entrega + días de crédito)
            if getattr(inv, 'x_is_delivered', False) and inv.x_delivery_date:
                effective_due = inv.x_delivery_date + timedelta(days=term_days)
            elif inv.invoice_date_due:
                effective_due = inv.invoice_date_due
            elif getattr(inv, 'x_delivery_date', False):
                effective_due = inv.x_delivery_date
            else:
                effective_due = inv.invoice_date

            if not effective_due:
                continue

            days_overdue = (today - effective_due).days
            # Si NO ha superado la fecha de vencimiento (days_overdue <= 0), la factura está vigente (NO VENCIDA)
            if days_overdue <= 0:
                continue

            amount = inv.amount_residual if inv.amount_residual > 0 else inv.amount_total
            total_overdue += amount

            if days_overdue <= 7:
                aging_buckets['1_7']['amount'] += amount
            elif days_overdue <= 15:
                aging_buckets['8_15']['amount'] += amount
            elif days_overdue <= 30:
                aging_buckets['16_30']['amount'] += amount
            else:
                aging_buckets['30_plus']['amount'] += amount

            delivery_str = inv.x_delivery_date.strftime('%d/%m/%Y') if getattr(inv, 'x_delivery_date', False) else ''
            due_str = effective_due.strftime('%d/%m/%Y')

            overdue_invoices_list.append({
                'id': inv.id,
                'name': inv.name or '',
                'partner_name': inv.partner_id.name or _('Sin Nombre'),
                'invoice_date': inv.invoice_date.strftime('%d/%m/%Y') if inv.invoice_date else '',
                'delivery_date': delivery_str or due_str,
                'due_date': due_str,
                'days_overdue': days_overdue,
                'amount_residual': round(amount, 2),
                'amount_total': round(inv.amount_total, 2),
                'overdue_info': f"{days_overdue} día{'s' if days_overdue > 1 else ''} vencido",
            })

        # Ordenar facturas vencidas por días de atraso descendente (las más urgentes primero)
        overdue_invoices_list = sorted(overdue_invoices_list, key=lambda x: x['days_overdue'], reverse=True)

        aging_chart = {
            'labels': [b['label'] for b in aging_buckets.values()],
            'data': [round(b['amount'], 2) for b in aging_buckets.values()],
            'colors': [b['color'] for b in aging_buckets.values()],
            'total_overdue': round(total_overdue, 2),
            'count': len(overdue_invoices_list),
        }

        # ── 10. RANKING TOP 30 CLIENTES VIP (EXCLUYENDO RZ MARQUET) ───────────
        client_sales = {}
        source_records = sales_orders if sales_orders else invoices
        for rec in source_records:
            cid = rec.partner_id.id
            if not cid or cid in rz_partner_ids:
                continue
            if getattr(rec.partner_id, 'commercial_partner_id', False) and rec.partner_id.commercial_partner_id.id in rz_partner_ids:
                continue

            cname = rec.partner_id.name or _('Sin Nombre')
            cname_upper = cname.upper()
            if 'RZ MARQUET' in cname_upper or 'RZ MARKET' in cname_upper or cname_upper.startswith('RZ '):
                continue

            if cid not in client_sales:
                client_sales[cid] = {'name': cname, 'amount': 0.0, 'count': 0}
            client_sales[cid]['amount'] += rec.amount_total
            client_sales[cid]['count'] += 1

        top_clients = sorted(client_sales.values(), key=lambda x: x['amount'], reverse=True)[:30]
        top_clients_chart = {
            'labels': [c['name'][:30] for c in top_clients],
            'data': [round(c['amount'], 2) for c in top_clients],
            'counts': [c['count'] for c in top_clients]
        }

        # ── 11. ALERTA DE PRODUCTOS PRÓXIMOS A AGOTARSE ───────────────────────
        low_stock_products = []
        storable_products = self.env['product.product'].search([
            ('is_storable', '=', True),
            '|', ('company_id', '=', False), ('company_id', '=', current_company_id)
        ], limit=100)

        for prod in storable_products:
            stock = prod.qty_available
            min_stock = prod.reordering_min_qty if hasattr(prod, 'reordering_min_qty') and prod.reordering_min_qty > 0 else 10.0
            if stock <= min_stock:
                low_stock_products.append({
                    'id': prod.id,
                    'name': prod.display_name,
                    'code': prod.default_code or '',
                    'stock': round(stock, 2),
                    'min_stock': round(min_stock, 2),
                    'uom': prod.uom_id.name
                })

        low_stock_products = sorted(low_stock_products, key=lambda x: x['stock'])[:15]

        return {
            'kpis': {
                'total_sales': round(total_sales_amount, 2),
                'total_purchases': round(total_purchases_amount, 2),
                'total_invoiced': round(total_invoiced_amount, 2),
                'total_collected': round(total_collected, 2),
                'total_orders': total_orders_count,
                'avg_ticket': round(avg_ticket, 2),
                'collection_rate': round(collection_rate, 1),
                'fill_rate': round(fill_rate_chart['percent'], 1),
                'total_overdue': aging_chart['total_overdue'],
                'overdue_count': aging_chart['count'],
                'low_stock_count': len(low_stock_products),
                'total_inv_cost': round(total_inv_cost, 2),
                'total_inv_sale': round(total_inv_sale, 2),
            },
            'sales_trend': sales_trend_chart,
            'purchases_vs_sales': purchases_vs_sales_chart,
            'top_50_products': top_50_chart,
            'collection': collection_chart,
            'routes': routes_chart,
            'sellers': sellers_chart,
            'fill_rate': fill_rate_chart,
            'aging_receivables': aging_chart,
            'overdue_invoices': overdue_invoices_list,
            'rz_partner_ids': rz_partner_list,
            'top_clients': top_clients_chart,
            'low_stock_products': low_stock_products,
            'date_from': date_from,
            'date_to': date_to,
            'today': today.strftime(DEFAULT_SERVER_DATE_FORMAT),
        }
