# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

def main():
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        print("=== CAMPOS DE LAYOUT / MARCA DE AGUA EN RES.COMPANY ===")
        companies = env['res.company'].search([])
        for comp in companies:
            print(f"\nEmpresa: {comp.name} (ID: {comp.id})")
            # Verificar campos relacionados con layout / background
            for field in ['layout_background', 'layout_background_image', 'report_header', 'report_footer']:
                if hasattr(comp, field):
                    val = getattr(comp, field)
                    if field == 'layout_background_image':
                        print(f"  - {field}: {'Tiene Imagen' if val else 'False'}")
                    else:
                        print(f"  - {field}: {val}")

            # Buscar otros campos que contengan 'background' o 'watermark'
            bg_fields = [f for f in comp._fields if 'background' in f or 'watermark' in f or 'logo' in f]
            print(f"  Campos relevantes encontrados: {bg_fields}")
            for bf in bg_fields:
                bval = getattr(comp, bf)
                if isinstance(bval, bytes) or (isinstance(bval, str) and len(str(bval)) > 50):
                    print(f"    * {bf}: [Dato binario / largo]")
                else:
                    print(f"    * {bf}: {bval}")

if __name__ == '__main__':
    main()
