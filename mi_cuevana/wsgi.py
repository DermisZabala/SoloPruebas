# Archivo: mi_cuevana/wsgi.py (MODIFICADO PARA VERCEL)

"""
WSGI config for mi_cuevana project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_cuevana.settings')

# Esta es la línea original de Django
application = get_wsgi_application()

# --- LÍNEA AÑADIDA PARA VERCEL ---
# Vercel busca una variable llamada 'app'. Le damos lo que quiere.
app = application