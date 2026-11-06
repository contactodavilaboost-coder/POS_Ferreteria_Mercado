# 🚀 Guía de Despliegue en Producción para Odoo 18

Esta guía contiene las instrucciones paso a paso para desplegar el sistema Odoo 18 de tu cliente en un servidor VPS en producción de forma rápida, segura y profesional.

---

## 1. Recomendación de VPS (Servidor)

Para Odoo 18 con pocos/medianos usuarios y tus módulos personalizados:

* **Proveedor Recomendado:** **Hetzner Cloud** (Excelente calidad/precio) o **DigitalOcean / Vultr**.
* **Plan Mínimo Recomendado:**
  * **vCPU:** 2 Cores
  * **RAM:** 4 GB (Añadir 4 GB de SWAP en el VPS)
  * **Disco:** 40 GB NVMe / SSD
  * **Sistema Operativo:** Ubuntu 22.04 LTS o Ubuntu 24.04 LTS
  * **Costo aprox:** ~$6 - $12 USD/mes.

---

## 2. Preparación del Servidor (Una sola vez)

Conéctate a tu VPS por SSH e instala Docker y Docker Compose:

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar tu usuario al grupo Docker
sudo usermod -aG docker $USER
newgrp docker

# Crear memoria de intercambio (SWAP) de 4GB para evitar caídas por RAM
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 3. Subir el Proyecto y Configurar Entorno

1. Sube tu carpeta de Odoo al VPS (mediante `git clone`, `scp` o SFTP).
2. Entra a la carpeta del proyecto en el VPS:
   ```bash
   cd /ruta/de/tu/proyecto/Odoo
   ```
3. Copia el archivo de variables de entorno y edítalo:
   ```bash
   cp .env.example .env
   nano .env
   ```
4. Configura los siguientes campos en `.env`:
   - `DOMAIN_NAME`: El dominio de tu cliente (ej. `erp.cliente.com`).
   - `ACME_EMAIL`: Tu correo o el del cliente para alertas SSL.
   - `POSTGRES_PASSWORD`: Genera una contraseña segura para PostgreSQL.
   - `ODOO_ADMIN_PASSWORD`: Genera una contraseña maestra para la gestión de BDs en Odoo.

---

## 4. Configurar el Dominio (DNS)

En el panel donde tu primo gestiona el dominio (ej. GoDaddy, Namecheap, Cloudflare, etc.):
* Crea un registro de tipo **A**:
  * **Nombre/Host:** `@` o `erp` (ej. `erp.cliente.com`)
  * **Valor/IP:** La dirección IP pública de tu servidor VPS.

---

## 5. Iniciar la Aplicación en Producción

Ejecuta el siguiente comando para levantar la pila en segundo plano:

```bash
docker compose -f docker-compose.prod.yml up -d
```

> **¿Por qué Caddy?**
> Caddy detectará automáticamente cuando apuntes el dominio a la IP del VPS y obtendrá un certificado SSL **HTTPS gratuito y válido** de Let's Encrypt sin que tengas que hacer nada.

Para verificar que los contenedores están corriendo correctamente:
```bash
docker compose -f docker-compose.prod.yml ps
```

---

## 6. Configurar Respaldos Automáticos (Cron)

Otorga permisos de ejecución al script de respaldo:

```bash
chmod +x scripts/backup.sh
```

Añade una tarea programada en el servidor para ejecutar el respaldo todas las noches a las 2:00 AM:

```bash
crontab -e
```

Añade la siguiente línea al final:
```cron
0 2 * * * cd /ruta/de/tu/proyecto/Odoo && ./scripts/backup.sh >> /var/log/odoo_backup.log 2>&1
```

---

---

## 7. Flujo Oficial de Actualización en Producción (Subida de Cambios)

Cada vez que subas cambios al repositorio GitHub y necesites aplicarlos en el servidor de producción del cliente, ejecuta este flujo:

```bash
# 1. Traer los últimos cambios y forzar la sincronización exacta con GitHub
git fetch origin
git reset --hard origin/main

# 2. Actualizar los módulos en la base de datos sin conflicto de puertos (--no-http)
docker exec odoo-web-1 odoo -u kamaleon_erp,kamaleon_dashboard --no-http --stop-after-init -d said_express

# 3. Reiniciar el contenedor web para aplicar cambios en memoria
docker restart odoo-web-1
```

> **Comando rápido en una sola línea:**
> ```bash
> git fetch origin && git reset --hard origin/main && docker exec odoo-web-1 odoo -u kamaleon_erp,kamaleon_dashboard --no-http --stop-after-init -d said_express && docker restart odoo-web-1
> ```

---

## 8. Comandos Útiles de Mantenimiento

* **Ver logs en tiempo real:**
  ```bash
  docker compose -f docker-compose.prod.yml logs -f web
  ```
  *(o `docker logs -f --tail=50 odoo-web-1`)*
* **Reiniciar el sistema:**
  ```bash
  docker compose -f docker-compose.prod.yml restart
  ```
* **Detener el sistema:**
  ```bash
  docker compose -f docker-compose.prod.yml down
  ```

