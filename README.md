# 🛠️ Ferretería Mercado — Sistema POS & ERP Integral

Sistema especializado para Ferretería Mercado basado en Odoo 18, adaptado exclusivamente para operación ágil en mostrador / punto de venta físico, control de stock y facturación con localización venezolana.

---

## 🌟 Características Principales

1. **Punto de Venta Bimonetario ($ / Bs.):**
   - Muestra precios y totales simultáneamente en Dólares ($) y Bolívares (Bs.).
   - Tasa BCV/del día editable al instante por administradores con cálculo en tiempo real.
2. **Calculadora Rápida de Efectivo $ con Vuelto en Bs.:**
   - Botones rápidos de denominaciones: `$5`, `$10`, `$20`, `$50`, `$100` y tecla `[D]` para otro monto.
   - Calcula y muestra en pantalla grande el vuelto exacto a entregar en Bolívares sin usar calculadora externa.
3. **Atajos de Teclado Completos (Operación 100% sin mouse):**
   - `F1`: Guía interactiva de atajos.
   - `F2`: Buscar producto en inventario.
   - `F3`: Seleccionar cliente / RIF.
   - `F4`: Pasar a cobrar.
   - `F8`: Validar y facturar orden.
   - `F9`: Siguiente venta.
   - `F10 / P`: Imprimir ticket de caja.
   - `E, T, M, Z, B`: Métodos de cobro rápidos (Efectivo, Tarjeta, Pago Móvil, Zelle, Banco).
4. **Boleta Térmica de Caja Optimizada:**
   - 100% en Bolívares (sin menciones a dólares ni divisas).
   - Formato compacto de 58mm / 80mm con desglose claro de Recibido y Vuelto.
5. **Módulos Core para Ferretería:**
   - **Punto de Venta (POS):** Atención rápida de clientes en mostrador.
   - **Inventario:** Stock en tiempo real, valoración y alerta de reposición.
   - **Compras:** Registro de proveedores y recepción de mercancía.
   - **Facturación / Cobros:** Control de cuentas y libros de venta.
6. **Diseño Visual Slate / Gris Neutro:**
   - Paleta profesional de alto contraste para reducir fatiga visual en jornadas largas de caja.

---

## 🚀 Despliegue Rápido con Docker

### Requisitos:
- Docker Desktop instalado y corriendo.
- Git.

### Pasos para iniciar en el local:
```powershell
# 1. Clonar el repositorio
git clone https://github.com/contactodavilaboost-coder/POS_Ferreteria_Mercado.git "Ferreteria Mercado"
cd "Ferreteria Mercado"

# 2. Levantar los contenedores de Odoo y PostgreSQL
docker compose up -d

# 3. Abrir en el navegador
# http://localhost:8069 o http://localhost:8072
```

---

## 💾 Respaldo Automático Blindado en la Nube

Para programar copias diarias automáticas hacia el disco local, Google Drive / OneDrive y GitHub:

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar_tarea_backup.ps1
```

---

## 🌐 Conexión Remota con Cloudflare Tunnel

Para acceder desde cualquier lugar o conectar sucursales:

```powershell
powershell -ExecutionPolicy Bypass -File .\conectar_cloudflare.ps1
```
