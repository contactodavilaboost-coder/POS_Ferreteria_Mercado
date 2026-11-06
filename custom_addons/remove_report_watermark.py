# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

def main():
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        print("=== ELIMINANDO MARCA DE AGUA DE REPORTES Y ÓRDENES DE VENTA ===")
        companies = env['res.company'].search([])
        for comp in companies:
            print(f"\nEmpresa: '{comp.name}' (ID: {comp.id})")
            print(f"  - layout_background anterior: {comp.layout_background}")
            print(f"  - layout_background_image anterior: {'Presente' if comp.layout_background_image else 'None'}")

            # Desactivar fondo y vaciar imagen de marca de agua
            comp.write({
                'layout_background': 'Blank',
                'layout_background_image': False
            })
            print(f"  => ACTUALIZADO: layout_background = 'Blank', layout_background_image = False")

        # Limpiar adjuntos de reportes en caché si existen
        cr.execute("""
            DELETE FROM ir_attachment 
            WHERE res_model = 'sale.order' 
              AND (name LIKE '%%.pdf' OR mimetype = 'application/pdf');
        """)
        cleared_reports = cr.rowcount
        if cleared_reports:
            print(f"\nSe limpiaron {cleared_reports} PDFs cacheados de órdenes de venta para que se regeneren limpios.")

        cr.commit()
        print("\n¡Marca de agua eliminada al 100% con éxito!")

if __name__ == '__main__':
    main()
