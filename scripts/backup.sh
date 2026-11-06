#!/bin/bash

# ==============================================================================
# Script de Respaldo Automatizado para Odoo 18 en Producción
# ==============================================================================
# Guarda la base de datos PostgreSQL y el directorio filestore de Odoo
# con fecha/hora en la carpeta ./backups/ y elimina respaldos mayores a 7 días.

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONTAINER_DB="odoo_postgres_db"
CONTAINER_WEB="odoo_web_app"
DB_USER="odoo"

mkdir -p "$BACKUP_DIR"

echo "--------------------------------------------------------"
echo "[$(date)] Iniciando copia de seguridad de Odoo..."
echo "--------------------------------------------------------"

# 1. Respaldo de la Base de Datos PostgreSQL
echo "[1/3] Exportando Base de Datos PostgreSQL..."
docker exec -t $CONTAINER_DB pg_dumpall -c -U $DB_USER | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

if [ $? -eq 0 ]; then
    echo "✓ BD respaldada exitosamente: db_backup_$TIMESTAMP.sql.gz"
else
    echo "❌ Error al respaldar la base de datos."
    exit 1
fi

# 2. Respaldo del Filestore de Odoo (imágenes, adjuntos, PDFs)
echo "[2/3] Empaquetando Filestore de Odoo..."
tar -czf "$BACKUP_DIR/filestore_$TIMESTAMP.tar.gz" -C ./ config/ custom_addons/

if [ $? -eq 0 ]; then
    echo "✓ Filestore respaldado exitosamente: filestore_$TIMESTAMP.tar.gz"
else
    echo "❌ Error al respaldar el filestore."
    exit 1
fi

# 3. Limpieza de respaldos antiguos (más de 7 días)
echo "[3/3] Aplicando política de rotación (eliminando respaldos > 7 días)..."
find "$BACKUP_DIR" -type f -mtime +7 -name "*.gz" -exec rm -f {} \;

echo "--------------------------------------------------------"
echo "✅ ¡Respaldo completado con éxito a las $(date +"%H:%M:%S")!"
echo "--------------------------------------------------------"
