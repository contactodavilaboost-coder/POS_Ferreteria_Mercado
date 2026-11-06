from datetime import timedelta
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_ids = fields.One2many(
        'sale.commission',
        'invoice_id',
        string='Comisiones Generadas'
    )
    x_commission_rate = fields.Float(
        string='% Comisión',
        compute='_compute_commission_fields',
        store=True,
        readonly=False,
        help='Porcentaje de comisión calculado automáticamente según días de cobro y reglas de productos (BSF max 5%, BBR max 3%).'
    )
    x_commission_amount = fields.Monetary(
        string='Monto Comisión',
        currency_field='currency_id',
        compute='_compute_commission_fields',
        store=True,
        readonly=False,
        help='Monto resultante de comisión para el vendedor.'
    )
    x_fortnight = fields.Selection([
        ('q1', '1ª Quincena (Días 1-15)'),
        ('q2', '2ª Quincena (Días 16-Fin de mes)'),
    ], string='Quincena', compute='_compute_fortnight', store=True, help='Indica si la factura pertenece a la 1ª o 2ª quincena del mes.')

    # ─── Control de Stock por Facturación ─────────────────────────────────────
    x_stock_deducted = fields.Boolean(
        string='Stock Descontado',
        default=False,
        copy=False,
        help='Indica si esta factura ya descontó sus productos del inventario en almacén.'
    )

    # ─── Campos de Entrega ────────────────────────────────────────────────────
    x_is_delivered = fields.Boolean(
        string='Entregada',
        default=False,
        copy=False,
        help='Indica si la mercancía de esta factura fue entregada al cliente.'
    )
    x_delivery_date = fields.Date(
        string='Fecha de Entrega',
        copy=False,
        help='Fecha en que se entregó físicamente la mercancía al cliente. '
             'La comisión del vendedor se calculará desde esta fecha hasta la fecha de pago.'
    )
    x_delivered_by = fields.Many2one(
        'res.users',
        string='Entregado por',
        copy=False,
        help='Usuario que registró la entrega.'
    )
    x_days_overdue = fields.Integer(
        string='Días Vencido',
        compute='_compute_days_overdue',
        help='Días transcurridos desde la fecha de entrega (o fecha de factura si no tiene entrega).'
    )
    x_overdue_info = fields.Char(
        string='Atraso / Vencimiento',
        compute='_compute_days_overdue',
        help='Estado de vencimiento y atraso de la factura.'
    )
    x_effective_due_date = fields.Date(
        string='Fecha Base Atraso',
        compute='_compute_days_overdue',
        help='Fecha desde la cual se cuenta el atraso (Entrega o Emisión).'
    )

    @api.depends('state', 'payment_state', 'move_type', 'invoice_date', 'invoice_date_due', 'x_delivery_date', 'x_is_delivered')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for move in self:
            if move.move_type == 'out_invoice' and move.state == 'posted':
                if move.payment_state in ('paid', 'reversed'):
                    move.x_days_overdue = 0
                    move.x_overdue_info = 'Pagada'
                    move.x_effective_due_date = move.invoice_date_due or move.x_delivery_date or move.invoice_date
                    continue

                # ── Calcular Fecha de Vencimiento Efectiva ────────────────────────
                # Plazo de crédito en días (ej: 15 días, 30 días)
                term_days = 0
                if move.invoice_date_due and move.invoice_date:
                    term_days = max(0, (move.invoice_date_due - move.invoice_date).days)

                # Si la mercancía fue entregada y tiene fecha de entrega registrada,
                # el vencimiento corre a partir de la fecha de entrega + días de crédito
                if move.x_is_delivered and move.x_delivery_date:
                    effective_due = move.x_delivery_date + timedelta(days=term_days)
                elif move.invoice_date_due:
                    effective_due = move.invoice_date_due
                elif move.x_delivery_date:
                    effective_due = move.x_delivery_date
                else:
                    effective_due = move.invoice_date

                move.x_effective_due_date = effective_due

                if not effective_due:
                    move.x_days_overdue = 0
                    move.x_overdue_info = 'Sin fecha'
                    continue

                diff = (today - effective_due).days
                if diff > 0:
                    # Superó el plazo de crédito: FACTURA VENCIDA / EN MORA
                    move.x_days_overdue = diff
                    status_word = "vencido" if move.x_is_delivered else "atrasado"
                    move.x_overdue_info = f"{diff} día{'s' if diff > 1 else ''} {status_word}"
                elif diff == 0:
                    move.x_days_overdue = 0
                    move.x_overdue_info = 'Vence hoy'
                else:
                    # Aún dentro del plazo de crédito: NO ESTÁ VENCIDA
                    move.x_days_overdue = 0
                    days_left = abs(diff)
                    move.x_overdue_info = f"En {days_left} día{'s' if days_left > 1 else ''}"
            else:
                move.x_days_overdue = 0
                move.x_overdue_info = ''
                move.x_effective_due_date = False

    @api.onchange('x_is_delivered')
    def _onchange_x_is_delivered(self):
        for move in self:
            if move.x_is_delivered:
                if not move.x_delivery_date:
                    move.x_delivery_date = fields.Date.today()
                if not move.x_delivered_by:
                    move.x_delivered_by = self.env.user
            else:
                move.x_delivery_date = False
                move.x_delivered_by = False

    @api.onchange('x_delivery_date')
    def _onchange_x_delivery_date(self):
        for move in self:
            if move.x_delivery_date:
                move.x_is_delivered = True
                if not move.x_delivered_by:
                    move.x_delivered_by = self.env.user

    # ─── Acción: Marcar como Entregada ────────────────────────────────────────
    def action_mark_delivered(self):
        """Marca la factura como entregada y registra la fecha de entrega."""
        for move in self:
            target_date = move.x_delivery_date or fields.Date.today()
            move.write({
                'x_is_delivered': True,
                'x_delivery_date': target_date,
                'x_delivered_by': move.x_delivered_by.id if move.x_delivered_by else self.env.user.id,
            })
            move._compute_commission_fields()

    def action_unmark_delivered(self):
        """Revierte la marca de entregada (por error u otro motivo)."""
        for move in self:
            move.write({
                'x_is_delivered': False,
                'x_delivery_date': False,
                'x_delivered_by': False,
            })
            move._compute_commission_fields()

    def _deduct_invoice_stock(self):
        """Descuenta del inventario 'A la mano' los productos facturados (permite stock negativo)."""
        stock_loc = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [False, self.env.company.id])
        ], limit=1)
        if not stock_loc:
            return

        for move in self:
            if move.move_type == 'out_invoice' and not move.x_stock_deducted and move.state == 'posted':
                so = move.line_ids.sale_line_ids.order_id
                pickings_handled = False
                if so:
                    pending_pickings = so.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
                    for picking in pending_pickings:
                        for sm in picking.move_ids:
                            if sm.product_uom_qty > 0:
                                sm.quantity = sm.product_uom_qty
                        try:
                            res = picking.with_context(skip_sms=True).button_validate()
                            if isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
                                wiz = self.env['stock.backorder.confirmation'].browse(res.get('res_id'))
                                wiz.process()
                            pickings_handled = True
                        except Exception:
                            pass

                if not pickings_handled:
                    prod_lines = move.line_ids.filtered(
                        lambda l: l.display_type in ('product', False) and l.product_id and l.quantity > 0 and not l.account_id.account_type == 'asset_receivable'
                    )
                    for line in prod_lines:
                        prod = line.product_id
                        if prod.type == 'service':
                            continue
                        if hasattr(prod, 'is_storable') and not prod.is_storable:
                            try:
                                prod.product_tmpl_id.is_storable = True
                            except Exception:
                                pass
                        try:
                            self.env['stock.quant']._update_available_quantity(
                                prod,
                                stock_loc,
                                -line.quantity
                            )
                        except Exception:
                            pass

                move.x_stock_deducted = True

    def _revert_invoice_stock(self):
        """Devuelve las existencias a 'A la mano' si la factura se cancela o regresa a borrador."""
        stock_loc = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [False, self.env.company.id])
        ], limit=1)
        if not stock_loc:
            return

        for move in self:
            if move.move_type == 'out_invoice' and move.x_stock_deducted:
                prod_lines = move.line_ids.filtered(
                    lambda l: l.display_type in ('product', False) and l.product_id and l.quantity > 0 and not l.account_id.account_type == 'asset_receivable'
                )
                for line in prod_lines:
                    prod = line.product_id
                    if prod.type == 'service':
                        continue
                    try:
                        self.env['stock.quant']._update_available_quantity(
                            prod,
                            stock_loc,
                            line.quantity
                        )
                    except Exception:
                        pass
                move.x_stock_deducted = False

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self._deduct_invoice_stock()
        return res

    def button_draft(self):
        self._revert_invoice_stock()
        return super(AccountMove, self).button_draft()

    def button_cancel(self):
        self._revert_invoice_stock()
        return super(AccountMove, self).button_cancel()

    def write(self, vals):
        if 'x_delivery_date' in vals and vals['x_delivery_date']:
            vals['x_is_delivered'] = True
            if 'x_delivered_by' not in vals and not self.env.context.get('skip_delivered_by'):
                vals['x_delivered_by'] = self.env.user.id
        elif 'x_is_delivered' in vals and not vals['x_is_delivered']:
            vals['x_delivery_date'] = False
            vals['x_delivered_by'] = False

        res = super().write(vals)
        if any(k in vals for k in ('x_delivery_date', 'x_is_delivered', 'payment_state', 'invoice_date')):
            for move in self:
                move._compute_commission_fields()
        return res

    @api.depends('invoice_date', 'date')
    def _compute_fortnight(self):
        for move in self:
            target_date = move.invoice_date or move.date
            if target_date:
                move.x_fortnight = 'q1' if target_date.day <= 15 else 'q2'
            else:
                move.x_fortnight = False

    @api.depends('state', 'move_type', 'payment_state', 'line_ids.matched_debit_ids', 'line_ids.matched_credit_ids', 'line_ids.price_subtotal', 'line_ids.product_id')
    def _compute_payments_widget_reconciled_info(self):
        super()._compute_payments_widget_reconciled_info()
        for move in self:
            if move.invoice_payments_widget and isinstance(move.invoice_payments_widget, dict) and move.invoice_payments_widget.get('content'):
                new_content = []
                for item in move.invoice_payments_widget['content']:
                    pay_id = item.get('account_payment_id')
                    if pay_id:
                        pay = move.env['account.payment'].sudo().browse(pay_id)
                        if pay.exists():
                            actual_paid = pay.amount
                            reconciled_amt = item.get('amount', 0.0)
                            diff = round(reconciled_amt - actual_paid, 2)
                            if diff > 0.01:
                                symbol = move.currency_id.symbol or '$'

                                item_paid = dict(item)
                                item_paid['name'] = "Pago Recibido (Cliente)"
                                item_paid['amount'] = actual_paid
                                item_paid['amount_company_currency'] = f"{symbol} {actual_paid:.2f}"

                                item_disc = dict(item)
                                item_disc['name'] = "Descuento Pronto Pago (5%)"
                                item_disc['amount'] = diff
                                item_disc['journal_name'] = "Descuento"
                                item_disc['amount_company_currency'] = f"{symbol} {diff:.2f}"

                                new_content.append(item_paid)
                                new_content.append(item_disc)
                                continue
                    new_content.append(item)
                move.invoice_payments_widget['content'] = new_content

    @api.depends(
        'payment_state', 'amount_residual', 'invoice_date', 'amount_untaxed', 'user_id',
        'line_ids.matched_debit_ids', 'line_ids.matched_credit_ids',
        'line_ids.price_subtotal', 'line_ids.product_id',
        'x_delivery_date', 'x_is_delivered',
    )
    def _compute_commission_fields(self):
        for move in self:
            # La comisión se calcula ÚNICA y EXCLUSIVAMENTE cuando la factura está 100% pagada (saldo residual = 0)
            is_fully_paid = (
                move.move_type == 'out_invoice'
                and move.payment_state in ('paid', 'in_payment')
                and (move.amount_residual == 0 or abs(move.amount_residual) < 0.001)
                and move.invoice_date
            )

            if is_fully_paid:

                # ── Fecha base para el cálculo de comisión ──────────────────
                # Si la factura fue marcada como entregada, la comisión corre
                # desde la fecha de entrega. Si no, desde la fecha de factura.
                commission_base_date = move.x_delivery_date if (move.x_is_delivered and move.x_delivery_date) else move.invoice_date

                # 1. Obtener apuntes de la cuenta por cobrar
                lines = move.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')

                # 2. Obtener fechas de los pagos conciliados
                reconciled_lines = lines.matched_debit_ids.debit_move_id + lines.matched_credit_ids.credit_move_id
                payment_moves = reconciled_lines.filtered(lambda l: l.move_id != move).mapped('move_id')
                payment_dates = payment_moves.mapped('date')

                # Si no hay fecha de pago explícita, usar la fecha de hoy
                payment_date = max(payment_dates) if payment_dates else fields.Date.today()

                # 3. Calcular días transcurridos desde la fecha base
                days = max(0, (payment_date - commission_base_date).days)

                # Regla base de comisión por días:
                # 0 a 20 días: 7%
                # 21 a 25 días: 5%
                # > 25 días: 2%
                if days <= 20:
                    tier_rate = 7.0
                elif days <= 25:
                    tier_rate = 5.0
                else:
                    tier_rate = 2.0

                # 4. Cálculo de comisión línea por línea:
                # - Productos con 'BBR': tope máximo de 3.0% comisión.
                # - Productos con 'BSF': tope máximo de 5.0% comisión.
                # - Productos normales: porcentaje normal según días (7%, 5% o 2%).
                prod_lines = move.line_ids.filtered(
                    lambda l: l.display_type in ('product', False) and l.product_id and not l.account_id.account_type == 'asset_receivable'
                )

                total_comm_amount = 0.0
                total_product_subtotal = 0.0
                has_capped = False

                for line in prod_lines:
                    subtotal = line.price_subtotal
                    total_product_subtotal += subtotal

                    prod = line.product_id
                    barcode = (prod.barcode or '').strip().upper()
                    code = (prod.default_code or '').strip().upper()

                    is_bbr = barcode.endswith('BBR') or code.endswith('BBR') or 'BBR' in barcode or 'BBR' in code
                    is_bsf = barcode.endswith('BSF') or code.endswith('BSF') or 'BSF' in barcode or 'BSF' in code

                    if is_bbr:
                        has_capped = True
                        line_rate = min(tier_rate, 3.0)
                    elif is_bsf:
                        has_capped = True
                        line_rate = min(tier_rate, 5.0)
                    else:
                        line_rate = tier_rate

                    total_comm_amount += subtotal * (line_rate / 100.0)

                amount_untaxed = total_product_subtotal or move.amount_untaxed
                comm_amount = round(total_comm_amount, 2)

                if not has_capped or (tier_rate <= 2.0):
                    effective_rate = tier_rate
                else:
                    effective_rate = round((total_comm_amount / amount_untaxed * 100.0), 2) if amount_untaxed else tier_rate

                move.x_commission_rate = effective_rate
                move.x_commission_amount = comm_amount

                # Crear o actualizar registro en sale.commission
                if move.user_id:
                    existing = move.env['sale.commission'].sudo().search([('invoice_id', '=', move.id)], limit=1)
                    if not existing:
                        move.env['sale.commission'].sudo().create({
                            'name': f"COM/{move.name or str(move.id)}",
                            'salesperson_id': move.user_id.id,
                            'invoice_id': move.id,
                            'delivery_date': move.x_delivery_date,
                            'payment_date': payment_date,
                            'commission_base_date': commission_base_date,
                            'days_to_pay': days,
                            'invoice_amount': amount_untaxed,
                            'commission_rate': effective_rate,
                            'state': 'draft',
                        })
                    else:
                        existing.sudo().write({
                            'delivery_date': move.x_delivery_date,
                            'payment_date': payment_date,
                            'commission_base_date': commission_base_date,
                            'days_to_pay': days,
                            'invoice_amount': amount_untaxed,
                            'commission_rate': effective_rate,
                        })
            else:
                move.x_commission_rate = 0.0
                move.x_commission_amount = 0.0
                # Si no está 100% pagada y existía una comisión en borrador, removerla
                if move.user_id:
                    existing = move.env['sale.commission'].sudo().search([('invoice_id', '=', move.id)], limit=1)
                    if existing and existing.state == 'draft':
                        existing.sudo().unlink()

