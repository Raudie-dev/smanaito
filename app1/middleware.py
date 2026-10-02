from django.shortcuts import redirect
from django.contrib import messages
import datetime

class SuscripcionActivaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Solo interceptar peticiones dentro de app1 que no sean perfil, auth, etc.
        rutas_permitidas = ['/perfil/', '/login/', '/logout/', '/api/webauthn/', '/admin/', '/admin_saas/', '/app2/']
        
        is_allowed = any(path.startswith(ruta) for ruta in rutas_permitidas)
        
        if not is_allowed and not path.startswith('/static/') and not path.startswith('/media/'):
            user_id = request.session.get('user')
            if user_id:
                try:
                    from app1.models import User
                    from app2.models import Suscripcion
                    
                    user = User.objects.get(id=user_id)
                    suscripcion, _ = Suscripcion.objects.get_or_create(usuario=user)
                    
                    dias_vencimiento = None
                    if suscripcion.fecha_vencimiento:
                        dias_vencimiento = (suscripcion.fecha_vencimiento - datetime.date.today()).days
                    else:
                        dias_vencimiento = (suscripcion.fecha_inicio + datetime.timedelta(days=14) - datetime.date.today()).days
                        
                    # Si la suscripción está vencida (dias < 0)
                    if dias_vencimiento < 0:
                        # Bloquear POST (registro de datos), exportaciones y el asistente
                        if request.method == 'POST' or 'exportar' in path or 'plantilla' in path or 'chat' in path or 'asistente' in path:
                            # Permitir excepciones si el usuario manda POST en rutas no permitidas explícitamente?
                            # En general, bloqueamos cualquier POST que modifique datos en las demás vistas.
                            messages.error(request, "Tu suscripción ha vencido. Por favor, renueva tu plan para utilizar estas funciones.")
                            return redirect('perfil')
                except Exception:
                    pass

        response = self.get_response(request)
        return response
