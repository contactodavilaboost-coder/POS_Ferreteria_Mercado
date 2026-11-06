# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class TouchSalesService(models.TransientModel):
    _name = 'kamaleon.touch.sales'
    _description = 'Servicio Backend para Cotizador Touch'

    @api.model
    def get_touch_init_data(self):
        """Carga datos iniciales con sudo() para asegurar lectura impecable sin bloqueos de grupos."""
        try:
            user = self.env.user.sudo()
            is_vendedor = bool(user.x_is_vendedor_touch)
            is_su = self.env.is_superuser()
            
            _logger.info("=========================================")
            _logger.info("GET TOUCH INIT DATA CALLED")
            _logger.info("Env User ID: %s, Name: %s, Login: %s", self.env.user.id, self.env.user.name, self.env.user.login)
            _logger.info("Is Vendedor Touch: %s", is_vendedor)
            _logger.info("Is Superuser: %s", is_su)

            comp_domain = [('company_id', 'in', [False, user.company_id.id])]

            partner_read_fields = [
                'id', 'name', 'vat', 'x_rif', 'email', 'phone', 'mobile',
                'street', 'street2', 'city', 'state_id', 'contact_address',
                'x_route_id', 'property_product_pricelist',
                'x_is_credit_blocked', 'x_credit_blocked_override', 'x_blocked_invoice_info'
            ]

            if is_vendedor and not is_su:
                user_routes = self.env['kamaleon.sale.route'].sudo().search([('user_id', '=', user.id)])
                assigned_domain = [
                    ('active', '=', True),
                    ('parent_id', '=', False),
                    '|', '|',
                    ('user_id', '=', user.id),
                    ('x_route_id.user_id', '=', user.id),
                    ('x_route_id', 'in', user_routes.ids)
                ] + comp_domain
                _logger.info("User Routes IDs: %s", user_routes.ids)
                partners = self.env['res.partner'].sudo().search_read(
                    assigned_domain,
                    partner_read_fields,
                    order='name asc'
                )
                _logger.info("Partners found by assigned_domain: %s", len(partners))
                # Si no hay clientes asignados en sus rutas, fallback a clientes generales de la compañía
                if not partners:
                    partners = self.env['res.partner'].sudo().search_read(
                        [('active', '=', True), ('parent_id', '=', False), ('x_is_customer', '=', True)] + comp_domain,
                        partner_read_fields,
                        order='name asc'
                    )
                    _logger.info("Fallback activated, partners found: %s", len(partners))
            else:
                partners = self.env['res.partner'].sudo().search_read(
                    [('active', '=', True), ('parent_id', '=', False), ('x_is_customer', '=', True)] + comp_domain,
                    partner_read_fields,
                    order='name asc'
                )
                _logger.info("Not a vendedor or is superuser, partners found: %s", len(partners))

            # Formatear dirección, ruta y teléfonos para visualización limpia en cotizador y directorio
            for p in partners:
                addr_parts = []
                if p.get('street'):
                    addr_parts.append(str(p['street']).strip())
                if p.get('street2'):
                    addr_parts.append(str(p['street2']).strip())
                if p.get('city'):
                    addr_parts.append(str(p['city']).strip())
                if p.get('state_id') and isinstance(p['state_id'], (list, tuple)):
                    addr_parts.append(str(p['state_id'][1]).strip())

                full_address = ', '.join(addr_parts) if addr_parts else (str(p.get('contact_address') or '')).replace('\n', ', ').strip()
                p['address'] = full_address or _('Sin dirección registrada')
                p['route_name'] = p['x_route_id'][1] if p.get('x_route_id') and isinstance(p['x_route_id'], (list, tuple)) else ''
                p['phone_display'] = p.get('phone') or p.get('mobile') or ''
                p['vat_display'] = p.get('vat') or p.get('x_rif') or ''
                p['pricelist_name'] = p['property_product_pricelist'][1] if p.get('property_product_pricelist') and isinstance(p['property_product_pricelist'], (list, tuple)) else ''

            _logger.info("Cotizador Touch init for User %s (%s). Vendedor Touch: %s. Partners loaded: %s", user.id, user.name, is_vendedor, len(partners))

            pricelists = self.env['product.pricelist'].sudo().search_read(
                [('active', '=', True)] + comp_domain,
                ['id', 'name', 'currency_id'],
                order='name asc'
            )

            products = self.env['product.product'].sudo().search_read(
                [('sale_ok', '=', True), ('active', '=', True), ('is_available_in_touch', '=', True)] + comp_domain,
                ['id', 'name', 'display_name', 'lst_price', 'categ_id', 'default_code', 'barcode', 'qty_available'],
                order='name asc'
            )

            used_categ_ids = list({
                p['categ_id'][0]
                for p in products
                if p.get('categ_id') and isinstance(p['categ_id'], (list, tuple))
            })
            categories = self.env['product.category'].sudo().search_read(
                [('id', 'in', used_categ_ids)],
                ['id', 'name'],
                order='name asc'
            )

            # Calcular precios iniciales y reglas de volumen
            default_pl = pricelists[0]['id'] if pricelists else False
            prices_data = self.get_pricelist_prices(default_pl) if default_pl else {'prices': {}, 'volume_rules': {}}

            return {
                'partners': partners or [],
                'pricelists': pricelists or [],
                'categories': categories or [],
                'products': products or [],
                'product_prices': prices_data.get('prices', {}),
                'volume_rules': prices_data.get('volume_rules', {}),
                'is_vendedor_touch': is_vendedor,
            }
        except Exception as e:
            _logger.error("Error initializing Cotizador Touch data: %s", e, exc_info=True)
            return {
                'partners': [],
                'pricelists': [],
                'categories': [],
                'products': [],
                'product_prices': {},
                'volume_rules': {},
                'is_vendedor_touch': False,
                'error': str(e),
            }

    @api.model
    def get_pricelist_prices(self, pricelist_id, partner_id=False):
        """Calcula el precio unitario exacto y las reglas por volumen según la lista de precios seleccionada."""
        pricelist = self.env['product.pricelist'].sudo().browse(pricelist_id) if pricelist_id else False
        partner = self.env['res.partner'].sudo().browse(partner_id) if partner_id else False

        user = self.env.user.sudo()
        comp_domain = [('company_id', 'in', [False, user.company_id.id])]
        products = self.env['product.product'].sudo().search([
            ('sale_ok', '=', True), ('active', '=', True), ('is_available_in_touch', '=', True)
        ] + comp_domain)

        prices = {}
        volume_rules = {}

        if pricelist and pricelist.exists():
            items = self.env['product.pricelist.item'].sudo().search([
                ('pricelist_id', '=', pricelist.id),
                ('min_quantity', '>', 1.0)
            ], order='min_quantity asc')

            for item in items:
                for prod in products:
                    applies = False
                    if item.applied_on == '3_global':
                        applies = True
                    elif item.applied_on == '2_product_category' and prod.categ_id and (prod.categ_id.id == item.categ_id.id or (prod.categ_id.parent_path and str(item.categ_id.id) in prod.categ_id.parent_path)):
                        applies = True
                    elif item.applied_on == '1_product' and prod.product_tmpl_id.id == item.product_tmpl_id.id:
                        applies = True
                    elif item.applied_on == '0_product_variant' and prod.id == item.product_id.id:
                        applies = True

                    if applies:
                        try:
                            tier_price = pricelist._get_product_price(prod, item.min_quantity, partner=partner)
                            if prod.id not in volume_rules:
                                volume_rules[prod.id] = []
                            volume_rules[prod.id].append({
                                'min_qty': item.min_quantity,
                                'price': round(tier_price or 0.0, 3)
                            })
                        except Exception:
                            pass

        for product in products:
            if pricelist and pricelist.exists():
                try:
                    price = pricelist._get_product_price(product, 1.0, partner=partner)
                except Exception:
                    price = product.lst_price
            else:
                price = product.lst_price
            prices[product.id] = round(price or 0.0, 3)

        return {
            'prices': prices,
            'volume_rules': volume_rules,
        }

    @api.model
    def create_and_confirm_touch_order(self, partner_id, pricelist_id, lines, note=False):
        """Crea un Pedido de Venta (sale.order) y lo confirma automáticamente."""
        if not partner_id:
            raise UserError(_("Debe seleccionar un cliente antes de procesar el pedido."))

        if not lines:
            raise UserError(_("No ha seleccionado ningún producto para la venta."))

        partner = self.env['res.partner'].sudo().browse(partner_id)
        if not partner.exists():
            raise UserError(_("El cliente seleccionado no existe."))

        # Verificar bloqueo de crédito por morosidad (> 3 días)
        if partner.x_is_credit_blocked and not partner.x_credit_blocked_override:
            raise UserError(_(
                "⛔ CLIENTE BLOQUEADO POR MOROSIDAD:\n\nEl cliente '%s' posee facturas sin cancelar emitidas hace más de 3 días (%s).\n\nConsulte a Administración para otorgar el permiso de autorización especial para poder procesar la venta.",
                partner.name, partner.x_blocked_invoice_info
            ))

        pricelist = None
        if pricelist_id:
            pricelist = self.env['product.pricelist'].sudo().browse(pricelist_id)

        order_lines = []
        for line in lines:
            product_id = line.get('product_id')
            qty = line.get('qty', 1)
            price_unit = line.get('price_unit')

            if not product_id or qty <= 0:
                continue

            product = self.env['product.product'].sudo().browse(product_id)
            if not product.exists():
                continue

            # Si hay lista de precios, calcular el precio exacto por volumen
            if pricelist and pricelist.exists():
                try:
                    price_unit = pricelist._get_product_price(product, qty, partner=partner)
                except Exception:
                    pass

            line_vals = {
                'product_id': product_id,
                'product_uom_qty': qty,
            }
            if price_unit is not None:
                line_vals['price_unit'] = price_unit

            order_lines.append((0, 0, line_vals))

        if not order_lines:
            raise UserError(_("Las líneas del pedido no son válidas."))

        order_vals = {
            'partner_id': partner_id,
            'user_id': self.env.user.id,
            'company_id': self.env.user.company_id.id,
            'order_line': order_lines,
        }
        if pricelist and pricelist.exists():
            order_vals['pricelist_id'] = pricelist.id

        if note and str(note).strip():
            order_vals['note'] = str(note).strip()

        sale_order = self.env['sale.order'].sudo().create(order_vals)
        sale_order.sudo().action_confirm()

        return {
            'order_id': sale_order.id,
            'order_name': sale_order.name,
            'amount_total': sale_order.amount_total,
        }

    @api.model
    def get_seller_orders(self):
        """Retorna los pedidos de venta del vendedor autenticado con su estatus y detalle de facturación."""
        try:
            user = self.env.user
            is_su = self.env.is_superuser()

            domain = [('company_id', 'in', [False, user.company_id.id])]
            if not is_su and user.x_is_vendedor_touch:
                domain += ['|', ('user_id', '=', user.id), ('create_uid', '=', user.id)]
            elif not is_su:
                domain += ['|', ('user_id', '=', user.id), ('create_uid', '=', user.id)]

            orders = self.env['sale.order'].sudo().search(domain, order='date_order desc, id desc', limit=150)

            payment_state_labels = {
                'not_paid': 'No Pagada',
                'in_payment': 'En Proceso de Pago',
                'paid': 'Pagada',
                'partial': 'Pago Parcial',
                'reversed': 'Revertida',
                'invoicing_legacy': 'Facturación Antigua',
            }

            result = []
            for o in orders:
                invoices = []
                for inv in o.invoice_ids:
                    if inv.state == 'cancel':
                        continue
                    invoices.append({
                        'id': inv.id,
                        'name': inv.name if inv.name and inv.name != '/' else _('Borrador'),
                        'state': inv.state,
                        'payment_state': inv.payment_state or 'not_paid',
                        'payment_state_label': payment_state_labels.get(inv.payment_state, 'No Pagada'),
                        'amount_total': round(inv.amount_total or 0.0, 2),
                        'invoice_date': inv.invoice_date.strftime('%d/%m/%Y') if inv.invoice_date else '',
                    })

                lines = []
                for l in o.order_line:
                    if l.display_type:
                        continue
                    lines.append({
                        'id': l.id,
                        'product_name': l.product_id.display_name if l.product_id else (l.name or ''),
                        'qty': l.product_uom_qty,
                        'price_unit': round(l.price_unit or 0.0, 2),
                        'price_subtotal': round(l.price_subtotal or 0.0, 2),
                    })

                # Determine human friendly status
                # State: draft, sent, sale, cancel
                # Invoice status: upselling, invoiced, to invoice, no
                if o.state == 'cancel':
                    calc_status = 'cancel'
                    calc_status_label = 'Cancelado'
                    badge_class = 'danger'
                elif o.invoice_status == 'invoiced' or (o.invoice_ids and any(inv.state != 'cancel' and inv.move_type in ('out_invoice', 'out_refund') for inv in o.invoice_ids)):
                    calc_status = 'invoiced'
                    calc_status_label = 'Facturado'
                    badge_class = 'success'
                elif o.invoice_status == 'to invoice' or o.state == 'sale':
                    calc_status = 'to_invoice'
                    calc_status_label = 'Por Facturar'
                    badge_class = 'warning'
                elif o.state in ('draft', 'sent'):
                    calc_status = 'draft'
                    calc_status_label = 'Cotización'
                    badge_class = 'info'
                else:
                    calc_status = 'no'
                    calc_status_label = 'Sin Facturar'
                    badge_class = 'secondary'

                result.append({
                    'id': o.id,
                    'name': o.name,
                    'date_order': o.date_order.strftime('%d/%m/%Y %H:%M') if o.date_order else '',
                    'partner_id': o.partner_id.id if o.partner_id else False,
                    'partner_name': o.partner_id.name if o.partner_id else _('Cliente no asignado'),
                    'partner_vat': o.partner_id.vat or '',
                    'amount_total': round(o.amount_total or 0.0, 2),
                    'state': o.state,
                    'invoice_status': o.invoice_status,
                    'calc_status': calc_status,
                    'calc_status_label': calc_status_label,
                    'badge_class': badge_class,
                    'note': o.note or '',
                    'invoices': invoices,
                    'lines': lines,
                })

            return result
        except Exception as e:
            _logger.error("Error cargando pedidos de vendedor: %s", e, exc_info=True)
            return []
