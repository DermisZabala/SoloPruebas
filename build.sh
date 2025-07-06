#!/bin/bash
set -e
echo "Compilando SASS..."
sass static/scss:static/css
echo "Minificando JS..."
uglifyjs static/js/main.js -o static/js/main.min.js
echo "Recolectando estáticos..."
python manage.py collectstatic --noinput