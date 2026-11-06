# -*- coding: utf-8 -*-
import odoo
from odoo import api
import re

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    routes = env['kamaleon.sale.route'].search([])
    
    # Map by route number and route name keywords
    route_by_id = {r.id: r for r in routes}
    route_by_number = {}
    route_by_keyword = {}
    
    for r in routes:
        # Extract number from name (e.g. "2 - San Antonio" -> 2)
        match_num = re.search(r'^(\d+)', r.name.strip())
        if match_num:
            num = int(match_num.group(1))
            route_by_number[num] = r
            
        # Key words (e.g. "san antonio", "san gabriel", "cumarebo", etc.)
        clean_name = re.sub(r'^\d+\s*-\s*', '', r.name).strip().lower()
        if clean_name:
            route_by_keyword[clean_name] = r
            
    print(f"Loaded {len(routes)} routes into matcher.")
    print("  Numbers mapped:", {k: v.name for k, v in route_by_number.items()})
    print("  Keywords mapped:", {k: v.name for k, v in route_by_keyword.items()})
    
    partners = env['res.partner'].search([('x_is_customer', '=', True)])
    updated_count = 0
    route_stats = {r.name: 0 for r in routes}
    
    for p in partners:
        target_route = None
        
        # Combined text to inspect
        full_text = f"{p.name or ''} {p.comment or ''} {p.street or ''} {p.street2 or ''} {p.ref or ''}".lower()
        
        # 1. Look for explicit pattern "ruta: X" or "ruta X" or "r-X" or "r: X"
        m_ruta = re.search(r'ruta[:\s\-]*(\d+)', full_text)
        if m_ruta:
            r_num = int(m_ruta.group(1))
            if r_num in route_by_number:
                target_route = route_by_number[r_num]
                
        # 2. Look for keyword match if not matched by number
        if not target_route:
            for kw, r_obj in route_by_keyword.items():
                if kw in full_text:
                    target_route = r_obj
                    break
                    
        # 3. If partner currently has x_route_id, sync route.user_id if available
        if not target_route and p.x_route_id:
            target_route = p.x_route_id
            
        if target_route:
            vals_to_write = {}
            if p.x_route_id != target_route:
                vals_to_write['x_route_id'] = target_route.id
            if target_route.user_id and p.user_id != target_route.user_id:
                vals_to_write['user_id'] = target_route.user_id.id
                
            if vals_to_write:
                p.write(vals_to_write)
                updated_count += 1
                
            route_stats[target_route.name] = route_stats.get(target_route.name, 0) + 1

    cr.commit()
    print(f"\nSUCCESS: Matched and synchronized {updated_count} partner route/salesperson records!")
    print("\nCURRENT CLIENT BREAKDOWN PER ROUTE:")
    for r_name, count in sorted(route_stats.items()):
        print(f"  - {r_name}: {count} clientes")
