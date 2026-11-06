import re
from datetime import timedelta
from odoo import models, fields, api, _

class KamaleonPartnerSalespersonHistory(models.Model):
    _name = 'kamaleon.partner.salesperson.history'
    _description = 'Historial de Vendedores del Cliente'
    _order = 'change_date desc, id desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        ondelete='cascade'
    )
    salesperson_id = fields.Many2one(
        'res.users',
        string='Vendedor Asignado',
        domain="[('share', '=', False)]"
    )
    route_id = fields.Many2one(
        'kamaleon.sale.route',
        string='Ruta de Venta'
    )
    change_date = fields.Datetime(
        string='Fecha y Hora',
        default=fields.Datetime.now,
        required=True
    )
    changed_by_id = fields.Many2one(
        'res.users',
        string='Registrado por',
        default=lambda self: self.env.user
    )
    note = fields.Char(
        string='Detalle / Motivo',
        help='Motivo o causa de la asignación de vendedor/ruta.'
    )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_rif = fields.Char(
        string='RIF / Documento Fiscal', 
        help='RIF de la empresa o persona (ej. J-12345678-9, V-12345678)'
    )
    x_taxpayer_type = fields.Selection([
        ('special', 'Contribuyente Especial'),
        ('ordinary', 'Contribuyente Ordinario'),
        ('natural', 'Persona Natural / No Contribuyente'),
    ], string='Tipo de Contribuyente', default='ordinary')

    x_is_customer = fields.Boolean(
        string='Es Cliente',
        default=True,
        help='Si está marcado como Verdadero, este contacto aparecerá en el Cotizador Touch.'
    )

    x_route_id = fields.Many2one(
        'kamaleon.sale.route',
        string='Ruta de Venta',
        help='Ruta asignada a este cliente. Al seleccionar la ruta, se le asignará el Vendedor correspondiente de forma automática.'
    )

    x_salesperson_history_ids = fields.One2many(
        'kamaleon.partner.salesperson.history',
        'partner_id',
        string='Historial de Vendedores'
    )

    # Bloqueo Automático de Crédito por Factura Vencida (> 3 Días de mora tras vencimiento)
    x_is_credit_blocked = fields.Boolean(
        string='Bloqueado por Mora (>3 Días)',
        compute='_compute_credit_blocked',
        search='_search_credit_blocked',
        help='Indica si el cliente posee facturas de venta publicadas con más de 3 días de vencidas sin cancelar.'
    )
    x_credit_status = fields.Selection([
        ('ok', 'Al Día'),
        ('blocked', 'Bloqueado por Mora'),
        ('override', 'Autorizado por Administración'),
    ], string='Estado de Crédito', compute='_compute_credit_blocked', store=False)
    x_blocked_invoice_info = fields.Char(
        string='Detalle Factura Vencida',
        compute='_compute_credit_blocked'
    )
    x_credit_blocked_override = fields.Boolean(
        string='Autorización Especial de Administración',
        default=False,
        help='Si se activa, el vendedor podrá realizar pedidos a este cliente aunque posea facturas con más de 3 días de emisión o vencimiento.'
    )

    @api.depends_context('company')
    def _compute_credit_blocked(self):
        today = fields.Date.today()
        for partner in self:
            blocked = False
            info = ""
            partner_ids = [partner.id] + partner.child_ids.ids
            invoices = partner.env['account.move'].sudo().search([
                ('partner_id', 'in', partner_ids),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
            ], order='invoice_date_due asc, invoice_date asc')
            
            for inv in invoices:
                term_days = 0
                if inv.invoice_date_due and inv.invoice_date:
                    term_days = max(0, (inv.invoice_date_due - inv.invoice_date).days)
                due_date = (inv.x_delivery_date + timedelta(days=term_days)) if (inv.x_is_delivered and inv.x_delivery_date) else (inv.invoice_date_due or inv.invoice_date or inv.date)
                if due_date and today > due_date:
                    days_overdue = (today - due_date).days
                    status_str = "vencida" if inv.x_is_delivered else "atrasada"
                    if days_overdue > 3:
                        blocked = True
                        date_label = "Entregada" if inv.x_is_delivered else "Emisión"
                        info = f"Factura {inv.name or str(inv.id)} {status_str} hace {days_overdue} días ({date_label}: {due_date.strftime('%d/%m/%Y')})"
                        break
                    elif days_overdue > 0:
                        info = f"Factura {inv.name or str(inv.id)} {status_str} hace {days_overdue} día(s)"
                        
            partner.x_is_credit_blocked = blocked
            partner.x_blocked_invoice_info = info
            
            if partner.x_credit_blocked_override:
                partner.x_credit_status = 'override'
            elif blocked:
                partner.x_credit_status = 'blocked'
            else:
                partner.x_credit_status = 'ok'

    def _search_credit_blocked(self, operator, value):
        today = fields.Date.today()
        invoices = self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
        ])
        blocked_partner_ids = set()
        for inv in invoices:
            term_days = 0
            if inv.invoice_date_due and inv.invoice_date:
                term_days = max(0, (inv.invoice_date_due - inv.invoice_date).days)
            due_date = (inv.x_delivery_date + timedelta(days=term_days)) if (inv.x_is_delivered and inv.x_delivery_date) else (inv.invoice_date_due or inv.invoice_date or inv.date)
            if due_date and (today - due_date).days > 3:
                blocked_partner_ids.add(inv.partner_id.id)
                if inv.partner_id.commercial_partner_id:
                    blocked_partner_ids.add(inv.partner_id.commercial_partner_id.id)
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', list(blocked_partner_ids))]
        else:
            return [('id', 'not in', list(blocked_partner_ids))]

    @api.onchange('x_route_id', 'comment', 'street', 'street2', 'ref')
    def _onchange_x_route_id(self):
        """Asignar el vendedor de la ruta de forma interactiva y detectar texto de ruta"""
        if not self.x_route_id:
            text = f"{self.name or ''} {self.comment or ''} {self.street or ''} {self.street2 or ''} {self.ref or ''}".lower()
            routes = self.env['kamaleon.sale.route'].search([])
            for r in routes:
                clean_name = re.sub(r'^\d+\s*-\s*', '', r.name).strip().lower()
                m_num = re.search(r'^(\d+)', r.name.strip())
                r_num = m_num.group(1) if m_num else None
                
                if (r_num and re.search(rf'ruta[:\s\-]*{r_num}\b', text)) or (clean_name and len(clean_name) > 3 and clean_name in text):
                    self.x_route_id = r
                    if r.user_id:
                        self.user_id = r.user_id
                    break
        elif self.x_route_id and self.x_route_id.user_id:
            self.user_id = self.x_route_id.user_id

    def _log_salesperson_history(self, note=None):
        """Registrar entrada en el historial de vendedores del cliente"""
        for partner in self:
            if partner.x_is_customer or partner.customer_rank > 0 or partner.user_id or partner.x_route_id:
                last = partner.x_salesperson_history_ids[:1]
                if last and last.salesperson_id == partner.user_id and last.route_id == partner.x_route_id:
                    continue
                partner.env['kamaleon.partner.salesperson.history'].sudo().create({
                    'partner_id': partner.id,
                    'salesperson_id': partner.user_id.id if partner.user_id else False,
                    'route_id': partner.x_route_id.id if partner.x_route_id else False,
                    'changed_by_id': partner.env.user.id,
                    'note': note or 'Asignación / Cambio de Vendedor',
                })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('x_route_id') and not vals.get('user_id'):
                route = self.env['kamaleon.sale.route'].browse(vals['x_route_id'])
                if route.exists() and route.user_id:
                    vals['user_id'] = route.user_id.id
        partners = super(ResPartner, self).create(vals_list)

        # Sincronización bidireccional hacia la ruta (partner_ids)
        if not self.env.context.get('_syncing_route'):
            for partner in partners:
                if partner.x_route_id:
                    partner.x_route_id.with_context(_syncing_route=True).sudo().write({
                        'partner_ids': [(4, partner.id)]
                    })

        for partner in partners:
            if partner.user_id or partner.x_route_id:
                partner._log_salesperson_history(note='Registro Inicial de Cliente')
        return partners

    def write(self, vals):
        old_data = {p.id: (p.user_id.id, p.x_route_id.id) for p in self}
        res = super(ResPartner, self).write(vals)

        # Sincronización bidireccional cuando se modifica la ruta en el contacto
        if not self.env.context.get('_syncing_route') and 'x_route_id' in vals:
            new_route_id = vals.get('x_route_id')
            new_route = self.env['kamaleon.sale.route'].browse(new_route_id) if new_route_id else False

            # Si la nueva ruta tiene vendedor asignado y no se pasó user_id explícito, actualizar vendedor
            if new_route and new_route.exists() and new_route.user_id and 'user_id' not in vals:
                partners_to_update_user = self.filtered(lambda p: p.user_id != new_route.user_id)
                if partners_to_update_user:
                    super(ResPartner, partners_to_update_user).write({'user_id': new_route.user_id.id})

            for partner in self:
                old_user_id, old_route_id = old_data.get(partner.id, (False, False))
                # 1. Si cambió de ruta o se quitó la ruta, remover de la ruta anterior
                if old_route_id and old_route_id != new_route_id:
                    old_route = self.env['kamaleon.sale.route'].browse(old_route_id)
                    if old_route.exists() and partner in old_route.partner_ids:
                        old_route.with_context(_syncing_route=True).sudo().write({
                            'partner_ids': [(3, partner.id)]
                        })
                # 2. Agregar a la nueva ruta
                if new_route and new_route.exists() and partner not in new_route.partner_ids:
                    new_route.with_context(_syncing_route=True).sudo().write({
                        'partner_ids': [(4, partner.id)]
                    })

        for partner in self:
            old_user, old_route = old_data.get(partner.id, (False, False))
            curr_user = partner.user_id.id if partner.user_id else False
            curr_route = partner.x_route_id.id if partner.x_route_id else False

            if old_user != curr_user or old_route != curr_route:
                motivo = "Cambio de Ruta" if old_route != curr_route else "Reasignación de Vendedor"
                partner._log_salesperson_history(note=motivo)

        return res
