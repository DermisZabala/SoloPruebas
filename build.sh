#!/bin/bash

# build_files.sh

# Salir inmediatamente si un comando falla
set -e

echo "BUILD START"

# 1. Instalar dependencias de Python
echo "Instalando dependencias de Python..."
pip install -r requirements.txt

# 2. Recolectar archivos estáticos de Django
echo "Ejecutando collectstatic..."
# Usamos python3.12 para ser explícitos, ya que es el runtime de Vercel
python3.12 manage.py collectstatic --no-input --clear

echo "BUILD END"