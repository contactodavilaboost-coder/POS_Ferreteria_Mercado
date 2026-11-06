# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    # Test for user 12 (Jorge Arevalo)
    env12 = api.Environment(cr, 12, {})
    service12 = env12['kamaleon.touch.sales']
    data12 = service12.get_touch_init_data()
    
    print(f"User 12 (Jorge Arevalo):")
    print(f"  - env.user.id: {env12.user.id}")
    print(f"  - env.user.name: {env12.user.name}")
    print(f"  - env.user.x_is_vendedor_touch: {env12.user.sudo().x_is_vendedor_touch}")
    print(f"  - env.is_admin(): {env12.is_admin()}")
    print(f"  - env.is_superuser(): {env12.is_superuser()}")
    print(f"  - Loaded partners count: {len(data12.get('partners', []))}")

    # Test for user 2 (Admin)
    env2 = api.Environment(cr, 2, {})
    service2 = env2['kamaleon.touch.sales']
    data2 = service2.get_touch_init_data()
    print(f"\nUser 2 (Admin):")
    print(f"  - env.user.id: {env2.user.id}")
    print(f"  - env.is_admin(): {env2.is_admin()}")
    print(f"  - Loaded partners count: {len(data2.get('partners', []))}")
