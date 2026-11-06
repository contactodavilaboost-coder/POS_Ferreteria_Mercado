# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_migrate(cr, registry):
    """
    Hook que se ejecuta automáticamente después de cada actualización del módulo.
    - Sincroniza empleados Vendedores Touch.
    - Asegura la moneda base USD en todas las compañías.
    - Configura métodos de pago requeridos en POS (Pago Móvil con referencia/banco, Transferencia, Zelle, Efectivo Bs, Efectivo Divisas).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    employees = env['hr.employee'].sudo().search([])

    activados = 0
    desactivados = 0

    for employee in employees:
        if not employee.user_id:
            continue
        antes = employee.user_id.sudo().x_is_vendedor_touch
        employee._sync_vendedor_touch()
        despues = employee.user_id.sudo().x_is_vendedor_touch
        if not antes and despues:
            activados += 1
        elif antes and not despues:
            desactivados += 1

    _logger.info(
        "[KamaleonERP] post_migrate: %d empleados activados como Vendedor Touch, "
        "%d desactivados. Total procesados: %d",
        activados, desactivados, len(employees),
    )

    # Asignar productos globales / sin compañía a Zais Express C.A si existen
    zais_company = env['res.company'].sudo().search([('name', 'ilike', 'Zais Express')], limit=1)
    if not zais_company:
        zais_company = env['res.company'].sudo().browse(1)

    if zais_company and zais_company.exists():
        unassigned_products = env['product.template'].sudo().search([('company_id', '=', False)])
        if unassigned_products:
            unassigned_products.write({'company_id': zais_company.id})
            _logger.info(
                "[KamaleonERP] post_migrate: %d productos asignados a la compañía %s (ID %d)",
                len(unassigned_products), zais_company.name, zais_company.id,
            )

        # Asignar clientes y contactos globales / sin compañía a Zais Express C.A para separarlos de RZ MARQUET
        excluded_partners = set(env['res.company'].sudo().search([]).mapped('partner_id').ids)
        rz_company = env['res.company'].sudo().search([('name', 'ilike', 'RZ MARQUET')], limit=1)
        if rz_company:
            rz_users = env['res.users'].sudo().search([('company_id', '=', rz_company.id)])
            excluded_partners.update(rz_users.mapped('partner_id').ids)

        unassigned_clients = env['res.partner'].sudo().search([
            ('company_id', '=', False),
            ('id', 'not in', list(excluded_partners)),
        ])
        if unassigned_clients:
            cr.execute("""
                UPDATE res_partner
                SET company_id = %s
                WHERE company_id IS NULL
                  AND id NOT IN %s;
            """, (zais_company.id, tuple(excluded_partners) if excluded_partners else (0,)))
            _logger.info(
                "[KamaleonERP] post_migrate: %d clientes/contactos asignados a la compañía %s (ID %d) para separarlos de RZ Marquet",
                len(unassigned_clients), zais_company.name, zais_company.id,
            )

    # Asegurar que todas las compañías (Zais Express, RZ MARQUET, etc.) tengan su moneda base en USD ($)
    usd = env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
    if usd:
        companies = env['res.company'].sudo().search([])
        for comp in companies:
            if comp.currency_id != usd:
                cr.execute("UPDATE res_company SET currency_id = %s WHERE id = %s;", (usd.id, comp.id))
                cr.execute("UPDATE account_journal SET currency_id = NULL WHERE company_id = %s AND currency_id IN (SELECT id FROM res_currency WHERE name = 'VEF');", (comp.id,))
                cr.execute("UPDATE product_pricelist SET currency_id = %s WHERE company_id = %s;", (usd.id, comp.id))
                _logger.info("[KamaleonERP] post_migrate: Moneda de %s actualizada a USD ($)", comp.name)

    # Configurar tasa inicial en compañías y métodos de pago en POS
    companies = env['res.company'].sudo().search([])
    for comp in companies:
        if hasattr(comp, 'x_ves_rate') and (not comp.x_ves_rate or comp.x_ves_rate <= 0):
            comp.write({'x_ves_rate': 65.0})

        # Buscar diarios de banco y efectivo
        bank_journal = env['account.journal'].sudo().search([('company_id', '=', comp.id), ('type', '=', 'bank')], limit=1)
        if not bank_journal:
            bank_journal = env['account.journal'].sudo().search([('company_id', '=', comp.id)], limit=1)
        cash_journal = env['account.journal'].sudo().search([('company_id', '=', comp.id), ('type', '=', 'cash')], limit=1)

        payment_methods_to_ensure = [
            ('Pago Móvil', bank_journal, False),
            ('Transferencia', bank_journal, False),
            ('Zelle', bank_journal, False),
            ('Efectivo Bs', cash_journal or bank_journal, True),
            ('Efectivo Divisas ($)', cash_journal or bank_journal, True),
        ]

        pos_configs = env['pos.config'].sudo().search([('company_id', '=', comp.id)])

        for pm_name, pm_journal, is_cash in payment_methods_to_ensure:
            pm = env['pos.payment.method'].sudo().search([
                ('company_id', '=', comp.id),
                ('name', 'ilike', pm_name)
            ], limit=1)
            if not pm and pm_journal:
                pm = env['pos.payment.method'].sudo().create({
                    'name': pm_name,
                    'company_id': comp.id,
                    'journal_id': pm_journal.id,
                    'is_cash_count': is_cash,
                })

            if pm:
                for pos in pos_configs:
                    cr.execute("""
                        INSERT INTO pos_config_pos_payment_method_rel (pos_config_id, pos_payment_method_id)
                        SELECT %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM pos_config_pos_payment_method_rel 
                            WHERE pos_config_id = %s AND pos_payment_method_id = %s
                        );
                    """, (pos.id, pm.id, pos.id, pm.id))

    # Activar Boleta Especial RZ Marquet para los POS de RZ Marquet
    rz_company = env['res.company'].sudo().search([('name', 'ilike', 'RZ MARQUET')], limit=1)
    if rz_company:
        rz_pos = env['pos.config'].sudo().search([('company_id', '=', rz_company.id)])
        if rz_pos:
            rz_pos.write({'x_rz_receipt': True})
            _logger.info("[KamaleonERP] post_migrate: Boleta especial RZ Marquet activada para %d puntos de venta", len(rz_pos))

    # Activar Monto Abierto en Bolívares para productos comodín tipo VERDURAS SURTIDAS
    surtidos = env['product.template'].sudo().search([
        '|',
        ('name', 'ilike', 'SURTID'),
        ('name', 'ilike', 'VERDURAS SURTIDAS'),
    ])
    if surtidos:
        surtidos.write({'x_open_price_ves': True})
        _logger.info("[KamaleonERP] post_migrate: %d productos surtidos configurados con Monto Abierto en Bs.", len(surtidos))

    # Sincronizar y restringir usuario CAJAS para que SOLO vea Punto de Venta (POS)
    cajas_users = env['res.users'].sudo().search([
        '|', '|',
        ('login', '=ilike', 'cajas'),
        ('name', '=ilike', 'cajas'),
        ('x_is_cajero_pos', '=', True),
    ])
    for c_user in cajas_users:
        if not c_user.x_is_cajero_pos:
            c_user.write({'x_is_cajero_pos': True})
        c_user._apply_cajero_pos_restrictions()
        _logger.info("[KamaleonERP] post_migrate: Usuario %s (ID %d) configurado en modo Solo Punto de Venta (POS)", c_user.name, c_user.id)



