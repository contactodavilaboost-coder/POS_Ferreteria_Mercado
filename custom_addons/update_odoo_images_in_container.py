# -*- coding: utf-8 -*-
import os
import base64
from PIL import Image
import odoo
from odoo import api, SUPERUSER_ID

# Render and crop PDF inside container
import fitz # PyMuPDF
pdf_path = '/mnt/extra-addons/pdf_catalog.pdf'
doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(dpi=300)
page_path = '/tmp/page_1_300dpi.png'
pix.save(page_path)

img = Image.open(page_path)

product_crops = {
    'ES001': {'box': (250, 715, 770, 1195), 'name': 'Uñas postizas degrade azul', 'price': 2.43},
    'ES015': {'box': (1060, 740, 1550, 1195), 'name': 'Pinzas para cabello de bebe color pastel x par', 'price': 1.86},
    'ES003': {'box': (1870, 740, 2350, 1195), 'name': 'Pestañas de media banda 3D x10 pares', 'price': 3.96},
    'ES007': {'box': (300, 1550, 750, 2030), 'name': 'Esponja de maquillaje ultrasuave', 'price': 1.20},
    'ES018': {'box': (1060, 1550, 1550, 2030), 'name': 'Cepillo versatil para limpieza de ranuras', 'price': 1.93},
    'ES013': {'box': (1800, 1550, 2380, 2030), 'name': 'Liguitas color gelatina en cartuchera x 1000pzas', 'price': 2.24},
    'ES011': {'box': (300, 2380, 750, 2870), 'name': 'Ligas de cabello 400 pza gruesas, alta elasticidad', 'price': 2.27},
}

b64_images = {}
for code, info in product_crops.items():
    cropped = img.crop(info['box'])
    save_path = f'/tmp/{code}.png'
    cropped.save(save_path, 'PNG')
    
    with open(save_path, 'rb') as f:
        b64_images[code] = base64.b64encode(f.read()).decode('utf-8')
    print(f"Cropped {code} -> {save_path}")

# Update Odoo database records
registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    for code, info in product_crops.items():
        # Search by code (default_code or barcode) or partial name
        products = env['product.product'].search([
            '|', '|', ('default_code', '=', code), ('barcode', '=', code), ('name', 'ilike', info['name'][:15])
        ])
        
        b64_data = b64_images[code]

        if products:
            for p in products:
                p.write({
                    'image_1920': b64_data,
                    'default_code': p.default_code or code,
                    'barcode': p.barcode or code,
                })
                print(f"SUCCESS: UPDATED product ID {p.id}: {p.name} (Code: {code}) with HD image!")
        else:
            # Create product if not existing yet
            new_p = env['product.product'].create({
                'name': info['name'],
                'default_code': code,
                'barcode': code,
                'lst_price': info['price'],
                'is_storable': True,
                'image_1920': b64_data,
            })
            print(f"SUCCESS: CREATED new product ID {new_p.id}: {new_p.name} (Code: {code}) with HD image!")

    cr.commit()
    print("Database transaction committed successfully!")
