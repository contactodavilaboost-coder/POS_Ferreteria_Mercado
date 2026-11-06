# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_ves_rate = fields.Float(
        string="Tasa BCV / VES (Bs/$)",
        default=65.0,
        digits=(12, 4),
        help="Tasa de cambio del día en Bolívares por Dólar (USD). Se utiliza para la conversión en pantalla y la impresión de recibos en Bolívares."
    )
    x_enable_dual_currency = fields.Boolean(
        string="Habilitar Doble Moneda ($ / Bs.)",
        default=True,
        help="Muestra precios y totales simultáneamente en Dólares ($) y Bolívares (Bs.) en la interfaz del Punto de Venta."
    )
    x_print_receipt_in_bs = fields.Boolean(
        string="Imprimir Boleta Solo en Bolívares",
        default=True,
        help="Si está activado, la boleta / recibo impreso del POS mostrará todos los montos directamente en Bolívares (Bs.)."
    )
    x_secondary_currency_symbol = fields.Char(
        string="Símbolo Moneda Secundaria",
        default="Bs.",
        help="Símbolo a mostrar para la moneda secundaria (ej: Bs., Bs.S, VES)."
    )
    x_rz_receipt = fields.Boolean(
        string="Boleta Especial RZ Marquet (r* ... z*)",
        default=False,
        help="Si está activado, la boleta imprimirá exclusivamente el formato compacto simplificado con r* y z*."
    )

    @api.model
    def set_ves_rate(self, config_id, rate):
        """Permite actualizar la tasa del día directamente desde la interfaz del POS y sincronizarla con la compañía y todos los puntos de venta.
        ESTRICTAMENTE RESTRINGIDO A ADMINISTRADORES."""
        if not self.env.user.has_group('base.group_system') and not self.env.is_superuser():
            from odoo.exceptions import AccessError
            raise AccessError("Acceso denegado: Solo los usuarios con rol de Administrador pueden actualizar la tasa de cambio.")

        pos_config = self.browse(config_id)
        if pos_config.exists() and rate > 0:
            pos_config.sudo().write({'x_ves_rate': rate})
            if pos_config.company_id:
                pos_config.company_id.sudo().write({'x_ves_rate': rate})
                # Sincronizar todos los demás POS de la misma compañía
                other_pos = self.search([('company_id', '=', pos_config.company_id.id), ('id', '!=', pos_config.id)])
                if other_pos:
                    other_pos.sudo().write({'x_ves_rate': rate})
            _logger.info("[POS Dual Currency] Tasa actualizada a %.4f para POS %s (ID %d) y compañía por el admin %s", rate, pos_config.name, pos_config.id, self.env.user.name)
            return {'success': True, 'rate': rate}
        return {'success': False, 'error': 'Invalid config or rate'}


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _load_pos_data_fields(self, model):
        fields = super()._load_pos_data_fields(model)
        if model == 'pos.config':
            fields = list(set(fields + [
                'x_ves_rate',
                'x_enable_dual_currency',
                'x_print_receipt_in_bs',
                'x_secondary_currency_symbol',
                'x_rz_receipt',
            ]))
        if model == 'product.product':
            fields = list(set(fields + [
                'x_open_price_ves',
                'x_is_price_in_ves',
                'x_price_ves',
            ]))
        return fields
