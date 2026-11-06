# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    ICP = env['ir.config_parameter']
    ICP.set_param('bus.longpolling.port', '8069')
    cr.commit()
    print("SUCCESSFULLY SET bus.longpolling.port TO 8069!")
