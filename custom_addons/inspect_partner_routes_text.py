# -*- coding: utf-8 -*-
import odoo
from odoo import api
import re

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    routes = env['kamaleon.sale.route'].search([])
    print("ALL ROUTES IN DATABASE:")
    route_map = {}
    for r in routes:
        user_name = r.user_id.name if r.user_id else "No Vendedor"
        print(f"  - Route ID {r.id}: '{r.name}' (Code: '{r.code}') | Vendedor: {user_name} | Partners count: {len(r.partner_ids)}")
        route_map[r.id] = r
        
    print("\nINSPECTING PARTNER FIELDS FOR ROUTE REFERENCES:")
    all_partners = env['res.partner'].search([('x_is_customer', '=', True)])
    print(f"Total Customer Partners: {len(all_partners)}")
    
    partners_with_route_id = [p for p in all_partners if p.x_route_id]
    print(f"Partners with x_route_id currently set: {len(partners_with_route_id)}")
    
    # Inspect sample partner fields to see where route names/text appear
    sample_texts = []
    for p in all_partners:
        text_content = f"Name: {p.name} | Comment: {p.comment or ''} | Street: {p.street or ''} | Ref: {p.ref or ''}"
        if re.search(r'ruta|san antonio|moron|coro|caracas|maracaibo|\d+', text_content, re.IGNORECASE):
            sample_texts.append((p.id, p.name, p.x_route_id.name if p.x_route_id else 'None', p.comment, p.street, p.ref))
            
    print(f"\nSample partners mentioning keywords ({len(sample_texts)}):")
    for st in sample_texts[:20]:
        print(f"  ID {st[0]}: '{st[1]}' | Route: {st[2]} | Comment: '{st[3]}' | Street: '{st[4]}' | Ref: '{st[5]}'")
