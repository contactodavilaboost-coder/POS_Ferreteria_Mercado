# -*- coding: utf-8 -*-
import os
import odoo
from odoo import api, SUPERUSER_ID

def main():
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})

        print("\n=== REVISIÓN ESPECÍFICA DE ACETONA 1x6 Y FILESTORE ===")

        # 1. Acetona 1x6 (ID 1479)
        prod = env['product.template'].browse(1479)
        print(f"Producto: {prod.name} (ID: {prod.id}, Activo: {prod.active})")
        print(f"image_1920: {bool(prod.image_1920)}")
        print(f"image_128: {bool(prod.image_128)}")

        # Ver sus adjuntos exactos
        cr.execute("""
            SELECT id, name, res_field, store_fname, file_size, checksum, mimetype
            FROM ir_attachment
            WHERE res_model = 'product.template' AND res_id = 1479;
        """)
        atts = cr.fetchall()
        print(f"\nTotal adjuntos de Acetona: {len(atts)}")
        for a in atts:
            aid, aname, res_field, store_fname, fsize, csum, mtype = a
            fpath = os.path.join("/var/lib/odoo/filestore/said_express", store_fname) if store_fname else ""
            exists = os.path.exists(fpath) if fpath else False
            readable = os.access(fpath, os.R_OK) if exists else False
            print(f"- Adjunto ID {aid}: campo='{res_field}', store_fname='{store_fname}'")
            print(f"  Tamaño: {fsize} bytes | Mime: {mtype} | ¿Existe en disco?: {exists} | ¿Legible?: {readable}")
            if exists:
                print(f"  Ruta física: {fpath}")

        # 2. Revisar si hay otras carpetas filestore
        filestores = os.listdir("/var/lib/odoo/filestore")
        print(f"\nCarpetas en /var/lib/odoo/filestore/: {filestores}")

        # 3. Contar cuántos archivos físicos hay en said_express
        total_files = 0
        total_bytes = 0
        se_path = "/var/lib/odoo/filestore/said_express"
        if os.path.exists(se_path):
            for root, dirs, files in os.walk(se_path):
                total_files += len(files)
                for f in files:
                    total_bytes += os.path.getsize(os.path.join(root, f))
        print(f"Total archivos en /var/lib/odoo/filestore/said_express: {total_files} ({total_bytes / (1024*1024):.2f} MB)")

        # 4. Ver si los productos activos tienen image_1920 asignado en la tabla de Odoo
        cr.execute("""
            SELECT count(*)
            FROM product_template
            WHERE active = True;
        """)
        total_activos = cr.fetchone()[0]

        cr.execute("""
            SELECT count(*)
            FROM ir_attachment
            WHERE res_model = 'product.template'
              AND res_field = 'image_1920'
              AND res_id IN (SELECT id FROM product_template WHERE active = True);
        """)
        activos_con_foto = cr.fetchone()[0]

        print(f"\nProductos activos: {total_activos}")
        print(f"Productos activos con registro image_1920 en ir_attachment: {activos_con_foto}")

        # Listar 5 productos activos que sí tienen foto
        cr.execute("""
            SELECT p.id, p.name, a.store_fname
            FROM product_template p
            JOIN ir_attachment a ON a.res_model = 'product.template' AND a.res_id = p.id AND a.res_field = 'image_1920'
            WHERE p.active = True
            LIMIT 5;
        """)
        ejemplos = cr.fetchall()
        print("\nEjemplos de productos activos con foto:")
        for eid, ename, efname in ejemplos:
            epath = os.path.join(se_path, efname) if efname else ""
            eexists = os.path.exists(epath) if epath else False
            print(f"- ID {eid}: '{ename}' -> store_fname: {efname} | ¿Existe en disco?: {eexists}")

if __name__ == '__main__':
    main()
