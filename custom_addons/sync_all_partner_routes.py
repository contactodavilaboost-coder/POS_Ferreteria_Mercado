# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

def main():
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})

        print("\n=======================================================")
        print("  SINCRONIZACIÓN MASIVA DE CLIENTES A SUS RUTAS DE VENTA")
        print("=======================================================\n")

        # 1. Obtener todas las rutas de venta
        routes = env['kamaleon.sale.route'].search([])
        print(f"Total rutas registradas en el sistema: {len(routes)}")

        total_partners_linked = 0
        total_salespersons_updated = 0

        print("\n--- Procesando cada Ruta ---")
        for route in routes:
            # Buscar todos los clientes que tienen x_route_id apuntando a esta ruta
            assigned_partners = env['res.partner'].search([
                ('x_route_id', '=', route.id),
                ('active', '=', True)
            ])
            partner_ids = assigned_partners.ids
            count = len(partner_ids)

            # Sincronizar Many2many de la ruta
            route.with_context(_syncing_route=True).write({
                'partner_ids': [(6, 0, partner_ids)]
            })

            # Sincronizar vendedor si la ruta tiene vendedor asignado
            if route.user_id:
                partners_need_user = assigned_partners.filtered(lambda p: p.user_id != route.user_id)
                if partners_need_user:
                    partners_need_user.with_context(_syncing_route=True).write({
                        'user_id': route.user_id.id
                    })
                    total_salespersons_updated += len(partners_need_user)

            total_partners_linked += count
            vendedor_str = route.user_id.name if route.user_id else "Sin Vendedor"
            print(f"- Ruta: '{route.name}' (ID: {route.id}) | Vendedor: {vendedor_str} -> {count} clientes vinculados")

        # 2. Caso específico: Jesús Dávila
        print("\n--- Verificación de 'Jesus Davila' ---")
        jd_partners = env['res.partner'].search([('name', 'ilike', 'Jesus Davila')])
        if jd_partners:
            for jd in jd_partners:
                r_name = jd.x_route_id.name if jd.x_route_id else "Sin Ruta"
                u_name = jd.user_id.name if jd.user_id else "Sin Vendedor"
                en_lista = jd.id in jd.x_route_id.partner_ids.ids if jd.x_route_id else False
                print(f"Cliente: {jd.name} (ID: {jd.id}) | Ruta: {r_name} | Vendedor: {u_name} | ¿Está en Clientes de la Ruta?: {en_lista}")
        else:
            print("No se encontró ningún contacto con el nombre 'Jesus Davila'")

        # 3. Limpiar cualquier cliente huérfano en kamaleon_route_partner_rel
        cr.execute("""
            DELETE FROM kamaleon_route_partner_rel rel
            WHERE NOT EXISTS (
                SELECT 1 FROM res_partner p
                WHERE p.id = rel.partner_id AND p.x_route_id = rel.route_id
            );
        """)
        orphaned_deleted = cr.rowcount
        if orphaned_deleted > 0:
            print(f"\nSe limpiaron {orphaned_deleted} asignaciones desincronizadas en la tabla relacional.")

        cr.commit()

        print("\n=======================================================")
        print("  RESUMEN FINAL DE LA SINCRONIZACIÓN:")
        print(f"  - Total clientes vinculados a rutas: {total_partners_linked}")
        print(f"  - Vendedores sincronizados en fichas: {total_salespersons_updated}")
        print("  - ¡Base de datos guardada y confirmada con éxito!")
        print("=======================================================\n")

if __name__ == '__main__':
    main()
