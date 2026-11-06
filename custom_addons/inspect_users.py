# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    users = env['res.users'].search([])
    for u in users:
        groups = [g.name for g in u.groups_id]
        print(f"User ID {u.id}: {u.name} ({u.login}) | Action: {u.action_id.name if u.action_id else 'Default'}")
