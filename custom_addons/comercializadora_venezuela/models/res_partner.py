# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    rif = fields.Char(
        string='RIF', 
        help='Registro de Información Fiscal (ej. J-12345678-9)',
        copy=False
    )
    
    contribuyente_type = fields.Selection([
        ('ordinario', 'Contribuyente Ordinario'),
        ('especial', 'Contribuyente Especial (Sujeto Pasivo Especial)'),
        ('formal', 'Contribuyente Formal'),
        ('no_contribuyente', 'No Contribuyente / Persona Natural')
    ], string='Tipo de Contribuyente', default='no_contribuyente')

    @api.constrains('rif')
    def _check_rif_format(self):
        for partner in self:
            if partner.rif:
                # Validar formato básico de RIF venezolano: Letra (V, J, G, E, P) seguida de número e indicador de dígito verificador
                pattern = r'^[VJGVEP]-[0-9]{8}-[0-9]$'
                if not re.match(pattern, partner.rif):
                    raise ValidationError(
                        "El formato del RIF es inválido. Debe seguir el formato Letra-Número (ej. J-12345678-9)."
                    )
