import os
import sys
# Agrega la ruta principal del proyecto
sys.path.insert(0, '/home/raudajly/smanaito')
# (Opcional) Si tu servidor lo requiere, también puedes agregar la ruta de la carpeta interna
# sys.path.insert(1, '/home/raudajly/smanaito/proyecto')
# Apunta al módulo de settings correcto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()