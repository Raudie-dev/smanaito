from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import User_admin, Suscripcion
from app1.models import User as App1User
import datetime

def login_admin(request):
    # Inicialización perezosa de admin si no existe ninguno
    try:
        if not User_admin.objects.exists():
            User_admin.objects.create(
                nombre='samanito',
                password=make_password('regalito3010**')
            )
    except Exception:
        pass

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        try:
            user = User_admin.objects.get(nombre=nombre)
            if user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif check_password(password, user.password):
                request.session['user_admin_id'] = user.id
                return redirect('control_admin')
            # Soporte temporal para administradores con contraseñas no encriptadas:
            elif not user.password.startswith('pbkdf2_') and user.password == password:
                user.password = make_password(password)
                user.save()
                request.session['user_admin_id'] = user.id
                return redirect('control_admin')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'login_admin.html')
        except User_admin.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return render(request, 'login_admin.html')

    return render(request, 'login_admin.html')

def control_admin(request):
    if 'user_admin_id' not in request.session:
        messages.error(request, 'No autorizado')
        return redirect('login_admin')
        
    clientes = App1User.objects.all().order_by('-id')
    # Auto-crear suscripciones faltantes
    for cliente in clientes:
        if not hasattr(cliente, 'suscripcion_saas'):
            Suscripcion.objects.create(
                usuario=cliente,
                plan='TRIAL',
                estado='ACTIVA',
                fecha_vencimiento=datetime.date.today() + datetime.timedelta(days=14)
            )
            
    context = {
        'clientes': clientes,
    }
    return render(request, 'control_admin.html', context)

def toggle_bloqueo(request, user_id):
    if 'user_admin_id' not in request.session:
        return redirect('login_admin')
    
    try:
        user = App1User.objects.get(id=user_id)
        user.bloqueado = not user.bloqueado
        user.save()
        estado = "bloqueado" if user.bloqueado else "desbloqueado"
        messages.success(request, f"Usuario {user.nombre} {estado} exitosamente.")
    except App1User.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        
    return redirect('control_admin')

def editar_suscripcion(request):
    if 'user_admin_id' not in request.session:
        return redirect('login_admin')
        
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        plan = request.POST.get('plan')
        estado = request.POST.get('estado')
        fecha_vencimiento = request.POST.get('fecha_vencimiento')
        
        try:
            suscripcion = Suscripcion.objects.get(usuario__id=user_id)
            suscripcion.plan = plan
            suscripcion.estado = estado
            if fecha_vencimiento:
                suscripcion.fecha_vencimiento = fecha_vencimiento
            suscripcion.save()
            messages.success(request, f"Suscripción actualizada exitosamente.")
        except Suscripcion.DoesNotExist:
            messages.error(request, "Error al actualizar suscripción.")
            
    return redirect('control_admin')
