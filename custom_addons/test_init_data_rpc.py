# -*- coding: utf-8 -*-
import odoo
from odoo import api
import json

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 12, {})
    try:
        data = env['kamaleon.touch.sales'].get_touch_init_data()
        # Test json dump
        dumped = json.dumps(data)
        print("JSON serialization SUCCESS! Payload length:", len(dumped))
    except Exception as e:
        print("EXACT EXCEPTION:", e)
        import traceback
        traceback.print_exc()
