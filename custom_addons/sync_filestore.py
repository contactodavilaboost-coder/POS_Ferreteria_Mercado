# -*- coding: utf-8 -*-
import os
import shutil
import odoo
from odoo import api, SUPERUSER_ID

def copy_tree(src, dst):
    if not os.path.exists(src):
        return 0
    copied = 0
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            src_file = os.path.join(root, f)
            dest_file = os.path.join(dest_dir, f)
            if not os.path.exists(dest_file):
                shutil.copy2(src_file, dest_file)
                copied += 1
    return copied

def main():
    target = "/var/lib/odoo/filestore/said_express"
    src_local = "/var/lib/odoo/.local/share/Odoo/filestore/said_express"
    src_nested = "/var/lib/odoo/filestore/said_express/filestore"

    print("=== SINCRONIZANDO Y RESTAURANDO FILESTORE DE ODOO ===")
    print(f"Destino oficial: {target}")

    os.makedirs(target, exist_ok=True)

    # 1. Copiar desde .local/share/Odoo/filestore/said_express
    c1 = copy_tree(src_local, target)
    print(f"Archivos recuperados de .local/share/Odoo: {c1}")

    # 2. Copiar desde el anidado said_express/filestore
    c2 = copy_tree(src_nested, target)
    print(f"Archivos recuperados del directorio anidado: {c2}")

    # 3. Ajustar permisos
    for root, dirs, files in os.walk(target):
        for d in dirs:
            try:
                os.chmod(os.path.join(root, d), 0o777)
            except Exception:
                pass
        for f in files:
            try:
                os.chmod(os.path.join(root, f), 0o666)
            except Exception:
                pass

    print("Permisos ajustados correctamente.")

    # 4. Verificar con la base de datos si las fotos ahora sí existen
    registry = odoo.modules.registry.Registry('said_express')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        cr.execute("""
            SELECT count(*)
            FROM ir_attachment
            WHERE res_model IN ('product.template', 'product.product')
              AND res_field LIKE 'image_%';
        """)
        total_atts = cr.fetchone()[0]

        cr.execute("""
            SELECT store_fname
            FROM ir_attachment
            WHERE res_model IN ('product.template', 'product.product')
              AND res_field LIKE 'image_%'
              AND store_fname IS NOT NULL;
        """)
        fnames = [r[0] for r in cr.fetchall()]
        existentes = sum(1 for fn in fnames if os.path.exists(os.path.join(target, fn)))

        print(f"\nTotal fotos registradas en BD: {total_atts}")
        print(f"Fotos que AHORA SÍ existen físicamente en disco: {existentes} de {len(fnames)}")

        # Probar Acetona
        cr.execute("SELECT store_fname FROM ir_attachment WHERE res_model='product.template' AND res_id=1479 AND res_field='image_1920';")
        r_ace = cr.fetchone()
        if r_ace and r_ace[0]:
            ace_path = os.path.join(target, r_ace[0])
            print(f"\n¿Foto de Acetona 1x6 existe en disco?: {os.path.exists(ace_path)} ({ace_path})")

if __name__ == '__main__':
    main()
