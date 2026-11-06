# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_ids = fields.One2many(
        'sale.commission', 
        'invoice_id', 
        string='Comisiones Generadas'
    )

    def write(self, vals):
        # Guardar los estados antes del cambio
        before_states = {move.id: move.payment_state for move in self}
        res = super(AccountMove, self).write(vals)
        # Verificar si cambió el estado de pago a pagado/en proceso de pago
        for move in self:
            if move.move_type == 'out_invoice' and move.payment_state in ('paid', 'in_payment'):
                if before_states.get(move.id) not in ('paid', 'in_payment'):
                    move._generate_commission()
        return res

    def _generate_commission(self):
        self.ensure_one()
        # Evitar crear duplicados de comisiones ya existentes
        existing = self.env['sale.commission'].search([('invoice_id', '=', self.id)])
        if existing:
            return

        # El vendedor se obtiene del comercial asignado a la factura
        salesperson = self.user_id
        if not salesperson:
            return

        invoice_date = self.invoice_date
        if not invoice_date:
            return

        # 1. Obtener las líneas de diario de la cuenta por cobrar (receivable)
        lines = self.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
        
        # 2. Obtener las líneas conciliadas de crédito y débito
        reconciled_lines = lines.matched_debit_ids.debit_move_id + lines.matched_credit_ids.credit_move_id
        
        # 3. Filtrar para obtener los movimientos de diario de pago (excluyendo la factura misma)
        payment_moves = reconciled_lines.filtered(lambda l: l.move_id != self).mapped('move_id')
        
        # 4. Mapear las fechas de pago
        payment_dates = payment_moves.mapped('date')
        
        # Si no hay fecha de pago (por conciliaciones manuales atípicas), se asume la fecha de hoy
        payment_date = max(payment_dates) if payment_dates else fields.Date.today()
        
        # Calcular los días transcurridos
        days = (payment_date - invoice_date).days
        
        # Regla de comisión por días de cobro:
        # - Hasta 20 días: 7%
        # - De 21 a 25 días: 5%
        # - Más de 25 días: 2%
        if days <= 20:
            rate = 7.0
        elif days <= 25:
            rate = 5.0
        else:
            rate = 2.0

        # Monto neto de la factura (sin impuestos - base imponible)
        amount_untaxed = self.amount_untaxed

        # Crear el registro de comisión
        self.env['sale.commission'].create({
            'name': f"COM/{self.name or str(self.id)}",
            'salesperson_id': salesperson.id,
            'invoice_id': self.id,
            'payment_date': payment_date,
            'days_to_pay': days,
            'invoice_amount': amount_untaxed,
            'commission_rate': rate,
            'state': 'draft',
        })
