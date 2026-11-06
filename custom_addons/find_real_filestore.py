# -*- coding: utf-8 -*-
import os

def main():
    base = "/var/lib/odoo/filestore"
    print("=== EXPLORANDO CONTENIDO REAL DE /var/lib/odoo/filestore ===")

    # Listar estructura hasta 3 niveles
    for root, dirs, files in os.walk(base):
        rel = os.path.relpath(root, base)
        depth = rel.count(os.sep)
        if depth <= 2:
            print(f"Directorio: {rel} (Subcarpetas: {len(dirs)}, Archivos: {len(files)})")
            if files:
                print(f"  Ejemplos de archivos en {rel}: {files[:3]}")

    # Buscar si existe alguno de los hashes
    sample_hash = "6acefd2a8a974ee45150fa4fe5ec7d8e5de496d0"
    print(f"\nBuscando hash '{sample_hash[:10]}' en todo el disco...")
    found = []
    for root, dirs, files in os.walk("/var/lib/odoo"):
        for f in files:
            if sample_hash in f or f in sample_hash:
                found.append(os.path.join(root, f))
    print(f"Coincidencias encontradas: {found}")

    # Mostrar 10 rutas relativas reales de archivos en said_express
    real_paths = []
    se = "/var/lib/odoo/filestore/said_express"
    if os.path.exists(se):
        for root, dirs, files in os.walk(se):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), se)
                real_paths.append(rel)
                if len(real_paths) >= 10:
                    break
            if len(real_paths) >= 10:
                break
    print(f"\n10 rutas reales de archivos existentes en said_express:\n{real_paths}")

if __name__ == '__main__':
    main()
