# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    # Run as Jorge Arevalo (User ID 12)
    env = api.Environment(cr, 12, {})
    print(f"Testing get_touch_init_data as user {env.user.name} ({env.user.login}):")
    try:
        res = env['kamaleon.touch.sales'].get_touch_init_data()
        print("SUCCESS! Returned:")
        print("  - Partners count:", len(res.get('partners', [])))
        print("  - Pricelists count:", len(res.get('pricelists', [])))
        print("  - Categories count:", len(res.get('categories', [])))
        print("  - Products count:", len(res.get('products', [])))
    except Exception as e:
        print("EXACT EXCEPTION ENCOUNTERED:", type(e), e)
        import traceback
        traceback.print_exc()
