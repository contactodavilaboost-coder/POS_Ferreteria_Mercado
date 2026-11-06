# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

PAYMENT_METHOD_TYPES = [
    ('pago_movil', 'Pago Móvil'),
    ('transferencia', 'Transferencia Bancaria'),
    ('zelle', 'Zelle ($)'),
    ('efectivo_bs', 'Efectivo Bolívares'),
    ('efectivo_divisas', 'Efectivo Divisas ($)'),
    ('other', 'Otro Método'),
]

BANK_SELECTION = [
    ('0102', 'Banco de Venezuela (0102)'),
    ('0105', 'Banco Mercantil (0105)'),
    ('0108', 'Banco Provincial (0108)'),
    ('0134', 'Banesco (0134)'),
    ('0191', 'BNC Banco Nacional de Crédito (0191)'),
    ('0172', 'Bancamiga (0172)'),
    ('0114', 'Bancaribe (0114)'),
    ('0115', 'Banco Exterior (0115)'),
    ('0137', 'Banco Sofitasa (0137)'),
    ('0138', 'Banco Plaza (0138)'),
    ('0151', 'BFC Banco Fondo Común (0151)'),
    ('0174', 'Banplus (0174)'),
    ('0175', 'Bicentenario (0175)'),
    ('0177', 'BANFANB (0177)'),
    ('0169', 'Mi Banco (0169)'),
    ('0128', 'Banco Caroní (0128)'),
    ('other', 'Otro Banco'),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_ves_rate = fields.Float(
        string='Tasa BCV / VES (Bs/$)',
        default=65.0,
        digits=(12, 4),
        help='Tasa de cambio del día en Bolívares por Dólar (USD).'
    )


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_payment_method_type = fields.Selection(
        selection=PAYMENT_METHOD_TYPES,
        string='Método de Pago',
        default='efectivo_divisas',
        help='Método de pago utilizado para cancelar la factura.'
    )
    x_exchange_rate = fields.Float(
        string='Tasa de Cambio (Bs/$)',
        digits=(12, 4),
        help='Tasa de cambio opcional.'
    )
    x_amount_ves = fields.Float(
        string='Monto en Bolívares (Bs.)',
        digits=(12, 2),
        help='Monto equivalente o referencial en Bolívares.'
    )
    x_payment_reference_num = fields.Char(
        string='Número de Referencia',
        help='Número de la referencia de Pago Móvil, Transferencia o Zelle.'
    )
    x_origin_bank = fields.Selection(
        selection=BANK_SELECTION,
        string='Banco de Origen'
    )
    x_zelle_holder = fields.Char(
        string='Titular / Correo Zelle',
        help='Nombre del titular o correo electrónico asociado a la cuenta Zelle emisora.'
    )
    x_payer_holder = fields.Char(
        string='Titular / Teléfono Emisor',
        help='Nombre del titular o número de teléfono del pagador.'
    )
    x_is_pago_movil = fields.Boolean(
        compute='_compute_is_pago_movil',
        string='Es Pago Móvil'
    )

    @api.depends('x_payment_method_type', 'journal_id', 'journal_id.name')
    def _compute_is_pago_movil(self):
        for pay in self:
            if pay.x_payment_method_type == 'pago_movil':
                pay.x_is_pago_movil = True
            else:
                name = (pay.journal_id.name or '').lower() if pay.journal_id else ''
                pay.x_is_pago_movil = ('pago' in name and 'movil' in name) or 'movil' in name or 'pago movil' in name


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    x_payment_method_type = fields.Selection(
        selection=PAYMENT_METHOD_TYPES,
        string='Método de Pago',
        default='pago_movil',
        required=True,
        help='Seleccione el método de pago utilizado por el cliente.'
    )
    x_payment_reference_num = fields.Char(
        string='Número de Referencia',
        help='Número de la referencia de Pago Móvil, Transferencia o Zelle.'
    )
    x_origin_bank = fields.Selection(
        selection=BANK_SELECTION,
        string='Banco de Origen'
    )
    x_zelle_holder = fields.Char(
        string='Titular / Correo Zelle',
        help='Nombre del titular o correo electrónico asociado a la cuenta Zelle emisora.'
    )
    x_payer_holder = fields.Char(
        string='Titular / Teléfono Emisor',
        help='Nombre del titular o número de teléfono del pagador.'
    )
    x_is_pago_movil = fields.Boolean(
        compute='_compute_is_pago_movil',
        string='Es Pago Móvil'
    )

    # Descuento por Pronto Pago (5% dentro de 5 días)
    x_early_discount_eligible = fields.Boolean(
        compute='_compute_early_discount_info',
        string='Elegible para Pronto Pago (5%)'
    )
    x_apply_early_discount = fields.Boolean(
        string='Aplicar Descuento Pronto Pago (5%)',
        default=False,
        help='Si se activa y se cancela el saldo total, el cliente paga el 95% y el 5% de descuento no afecta la comisión del vendedor.'
    )
    x_early_discount_amount = fields.Monetary(
        compute='_compute_early_discount_info',
        string='Monto del Descuento (5%)',
        currency_field='currency_id'
    )

    def _get_discount_account(self):
        return self.env['account.account'].search([
            ('account_type', 'in', ('expense', 'expense_direct_cost', 'income_other', 'income')),
            ('name', 'ilike', 'Discount')
        ], limit=1) or self.env['account.account'].search([
            ('account_type', 'in', ('expense', 'expense_direct_cost', 'income_other', 'income')),
            ('name', 'ilike', 'descuento')
        ], limit=1) or self.env['account.account'].search([
            ('account_type', 'in', ('expense', 'expense_direct_cost'))
        ], limit=1)

    @api.depends('x_payment_method_type', 'journal_id', 'journal_id.name')
    def _compute_is_pago_movil(self):
        for wizard in self:
            if wizard.x_payment_method_type == 'pago_movil':
                wizard.x_is_pago_movil = True
            else:
                name = (wizard.journal_id.name or '').lower() if wizard.journal_id else ''
                wizard.x_is_pago_movil = ('pago' in name and 'movil' in name) or 'movil' in name or 'pago movil' in name

    @api.depends('line_ids', 'payment_date')
    def _compute_early_discount_info(self):
        for wizard in self:
            eligible = False
            disc_amt = 0.0
            moves = wizard.line_ids.mapped('move_id').filtered(lambda m: m.is_invoice())
            if moves:
                inv = moves[0]
                pay_date = wizard.payment_date or fields.Date.today()
                base_date = inv.x_delivery_date if (inv.x_is_delivered and inv.x_delivery_date) else inv.invoice_date
                if base_date and (pay_date - base_date).days <= 5:
                    eligible = True
                    disc_amt = inv.amount_residual * 0.05
            wizard.x_early_discount_eligible = eligible
            wizard.x_early_discount_amount = disc_amt

    @api.depends('line_ids', 'payment_date', 'currency_id', 'x_apply_early_discount')
    def _compute_amount(self):
        super()._compute_amount()
        for wizard in self:
            if wizard.x_apply_early_discount and wizard.x_early_discount_eligible:
                moves = wizard.line_ids.mapped('move_id').filtered(lambda m: m.is_invoice())
                if moves:
                    inv = moves[0]
                    # Solo sugerir el 95% del saldo pendiente si se aplica pronto pago
                    wizard.amount = round(inv.amount_residual * 0.95, 2)
                    wizard.payment_difference_handling = 'reconcile'
                    wizard.writeoff_label = 'Descuento por Pronto Pago (5%)'
                    disc_account = wizard._get_discount_account()
                    if disc_account:
                        wizard.writeoff_account_id = disc_account.id

    @api.onchange('x_payment_method_type')
    def _onchange_payment_method_type(self):
        """Sugerir diario contable adecuado según el método de pago seleccionado, sin alterar el monto."""
        if self.x_payment_method_type == 'pago_movil':
            pm_journal = self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', 'bank'),
                ('name', 'ilike', 'pago movil')
            ], limit=1) or self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', 'bank')
            ], limit=1)
            if pm_journal:
                self.journal_id = pm_journal
        elif self.x_payment_method_type == 'transferencia':
            bank_journal = self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', 'bank')
            ], limit=1)
            if bank_journal:
                self.journal_id = bank_journal
        elif self.x_payment_method_type == 'efectivo_bs':
            cash_journal = self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', 'cash')
            ], limit=1)
            if cash_journal:
                self.journal_id = cash_journal
        elif self.x_payment_method_type == 'zelle':
            zelle_journal = self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('name', 'ilike', 'zelle')
            ], limit=1) or self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', 'bank')
            ], limit=1)
            if zelle_journal:
                self.journal_id = zelle_journal
        elif self.x_payment_method_type == 'efectivo_divisas':
            cash_journal = self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', 'cash')
            ], limit=1)
            if cash_journal:
                self.journal_id = cash_journal

    @api.onchange('x_apply_early_discount')
    def _onchange_apply_early_discount(self):
        moves = self.line_ids.mapped('move_id').filtered(lambda m: m.is_invoice())
        if moves:
            inv = moves[0]
            if self.x_apply_early_discount and self.x_early_discount_eligible:
                self.amount = round(inv.amount_residual * 0.95, 2)
                self.payment_difference_handling = 'reconcile'
                self.writeoff_label = 'Descuento por Pronto Pago (5%)'
                disc_account = self._get_discount_account()
                if disc_account:
                    self.writeoff_account_id = disc_account.id
            else:
                self.amount = inv.amount_residual
                self.payment_difference_handling = 'open'

    @api.onchange('amount')
    def _onchange_amount(self):
        """
        Si el usuario ingresa un monto menor al saldo (pago parcial),
        asegurar que la diferencia permanezca como saldo abierto ('open')
        y NUNCA se marque la factura como pagada total.
        """
        moves = self.line_ids.mapped('move_id').filtered(lambda m: m.is_invoice())
        if moves:
            inv = moves[0]
            expected_full = round(inv.amount_residual * 0.95, 2) if (self.x_apply_early_discount and self.x_early_discount_eligible) else inv.amount_residual
            if self.amount < expected_full:
                self.payment_difference_handling = 'open'

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        
        # Guardar campos personalizados en account.payment
        vals['x_payment_method_type'] = self.x_payment_method_type
        vals['x_origin_bank'] = self.x_origin_bank
        vals['x_payment_reference_num'] = self.x_payment_reference_num
        vals['x_zelle_holder'] = self.x_zelle_holder
        vals['x_payer_holder'] = self.x_payer_holder

        # Memo claro y limpio sin interferencia de conversiones de tasa
        bank_labels = dict(BANK_SELECTION)
        memo_parts = []
        orig_memo = vals.get('memo') or vals.get('communication') or ''
        if orig_memo:
            memo_parts.append(orig_memo)

        mtype = self.x_payment_method_type
        if mtype == 'pago_movil':
            bank_name = bank_labels.get(self.x_origin_bank, self.x_origin_bank or '')
            b_str = f" ({bank_name})" if bank_name else ""
            ref_str = f"Ref: {self.x_payment_reference_num}" if self.x_payment_reference_num else ""
            details = " | ".join(filter(None, [f"Pago Móvil{b_str}", ref_str]))
            if details:
                memo_parts.append(f"[{details}]")
        elif mtype == 'transferencia':
            bank_name = bank_labels.get(self.x_origin_bank, self.x_origin_bank or '')
            b_str = f" ({bank_name})" if bank_name else ""
            ref_str = f"Ref: {self.x_payment_reference_num}" if self.x_payment_reference_num else ""
            details = " | ".join(filter(None, [f"Transferencia{b_str}", ref_str]))
            if details:
                memo_parts.append(f"[{details}]")
        elif mtype == 'zelle':
            ref_str = f"Ref: {self.x_payment_reference_num}" if self.x_payment_reference_num else ""
            holder_str = f"Titular/Email: {self.x_zelle_holder}" if self.x_zelle_holder else ""
            details = " | ".join(filter(None, ["Zelle", ref_str, holder_str]))
            if details:
                memo_parts.append(f"[{details}]")
        elif mtype == 'efectivo_bs':
            memo_parts.append("[Efectivo Bs]")
        elif mtype == 'efectivo_divisas':
            memo_parts.append("[Efectivo Divisas ($)]")

        if memo_parts:
            vals['memo'] = " - ".join(memo_parts)

        return vals
