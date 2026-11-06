# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleCommission(models.Model):
    _name = 'sale.commission'
    _description = 'Comisiones de Vendedores por Días de Cobro'
    _order = 'payment_date desc, id desc'

    name = fields.Char(
        string='Referencia', 
        required=True, 
        copy=False, 
        default='Nuevo'
    )
    salesperson_id = fields.Many2one(
        'res.users', 
        string='Vendedor', 
        required=True,
        domain="[('share', '=', False)]"
    )
    invoice_id = fields.Many2one(
        'account.move', 
        string='Factura', 
        required=True,
        domain="[('move_type', '=', 'out_invoice')]"
    )
    invoice_date = fields.Date(
        string='Fecha de Factura', 
        related='invoice_id.invoice_date', 
        store=True
    )
    payment_date = fields.Date(
        string='Fecha de Pago', 
        required=True
    )
    days_to_pay = fields.Integer(
        string='Días en Pagar', 
        required=True,
        help='Días transcurridos entre la fecha de factura y la fecha de pago.'
    )
    invoice_amount = fields.Monetary(
        string='Base Imponible', 
        currency_field='currency_id',
        help='Monto neto de la factura (sin impuestos).'
    )
    commission_rate = fields.Float(
        string='% Comisión', 
        required=True
    )
    commission_amount = fields.Monetary(
        string='Monto Comisión', 
        currency_field='currency_id',
        compute='_compute_commission_amount',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', 
        related='invoice_id.currency_id', 
        store=True
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', required=True)

    @api.depends('invoice_amount', 'commission_rate')
    def _compute_commission_amount(self):
        for rec in self:
            rec.commission_amount = rec.invoice_amount * (rec.commission_rate / 100.0)

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_pay(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})
