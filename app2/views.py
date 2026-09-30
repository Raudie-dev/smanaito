from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Sum, Count, Q
from .models import User_admin, Suscripcion, PlanSaaS, PagoSuscripcion, LogSistemaAdmin
from app1.models import User as App1User, LogActividad
import datetime

def registrar_log_admin(admin_user, tipo, descripcion, request=None):
    ip = None
    if request:
        ip = request.META.get('REMOTE_ADDR')
    LogSistemaAdmin.objects.create(
        admin_user=admin_user,
        tipo=tipo,
        descripcion=descripcion,
        ip=ip
    )

def login_admin(request):
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
                registrar_log_admin(user, 'SISTEMA', f"Inicio de sesión master admin exitoso ({user.nombre})", request)
                return redirect('control_admin')
            elif not user.password.startswith('pbkdf2_') and user.password == password:
                user.password = make_password(password)
                user.save()
                request.session['user_admin_id'] = user.id
                registrar_log_admin(user, 'SISTEMA', f"Inicio de sesión master admin exitoso ({user.nombre})", request)
                return redirect('control_admin')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'login_admin.html')
        except User_admin.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return render(request, 'login_admin.html')

    return render(request, 'login_admin.html')

def logout_admin(request):
    request.session.pop('user_admin_id', None)
    messages.info(request, "Sesión de administración cerrada.")
    return redirect('login_admin')

def get_admin_base_context(request):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return None, None
        
    admin_user = User_admin.objects.get(id=admin_id)

    # Inicializar planes por defecto si no existen
    if not PlanSaaS.objects.exists():
        PlanSaaS.objects.create(codigo='TRIAL', nombre='Plan Prueba (Trial)', precio_mensual=0, badge='Gratis', descripcion='Ideal para probar la plataforma y organizar tu primera finca.', caracteristicas_list='Hasta 1 Finca\nHasta 50 Animales\nControl de producción lechera básica\nAcceso móvil PWA', destacado=False)
        PlanSaaS.objects.create(codigo='BASICO', nombre='Plan Básico', precio_mensual=29, badge='Pequeño Productor', descripcion='Perfecto para fincas medianas con control zootécnico esencial.', caracteristicas_list='Hasta 2 Fincas\nHasta 250 Animales\nControl de leche + Gastos recurrentes\nAlertas de farmacia y vacunas\nSoporte por correo', destacado=False)
        PlanSaaS.objects.create(codigo='PLUS', nombre='Plan Plus', precio_mensual=59, badge='El Más Popular', descripcion='Para fincas en crecimiento con requerimientos financieros completos.', caracteristicas_list='Fincas Ilimitadas\nHasta 1,000 Animales\nFinanzas avanzadas + Liquidez en caja\nBiometría PWA (Huella dactilar)\nMódulo de Nómina y Empleados\nSoporte prioritario por WhatsApp', destacado=True)
        PlanSaaS.objects.create(codigo='PREMIUM', nombre='Plan Premium / VIP', precio_mensual=99, badge='Empresarial', descripcion='Para grandes operaciones agropecuarias y consorcios ganaderos.', caracteristicas_list='Todo lo del Plan Plus\nAnimales Ilimitados\nAuditoría completa de actividades\nReportes exportables en Excel / PDF\nAsesoría técnica ganadera personalizada', destacado=False)

    clientes = App1User.objects.all().order_by('-id')
    # Auto-crear suscripciones faltantes
    for cliente in clientes:
        if not hasattr(cliente, 'suscripcion_saas'):
            trial_plan = PlanSaaS.objects.filter(codigo='TRIAL').first()
            Suscripcion.objects.create(
                usuario=cliente,
                plan='TRIAL',
                plan_obj=trial_plan,
                estado='ACTIVA',
                monto_mensual=0,
                fecha_vencimiento=datetime.date.today() + datetime.timedelta(days=15)
            )

    planes = PlanSaaS.objects.all().order_by('precio_mensual')
    suscripciones = Suscripcion.objects.select_related('usuario').all()
    pagos = PagoSuscripcion.objects.select_related('suscripcion__usuario').order_by('-id')
    
    # Métricas de Finanzas SaaS
    total_clientes = clientes.count()
    clientes_al_dia = suscripciones.filter(estado='ACTIVA').exclude(plan='TRIAL').count()
    clientes_deudores = suscripciones.filter(Q(estado='VENCIDA') | Q(estado='SUSPENDIDA')).count()
    clientes_trial = suscripciones.filter(plan='TRIAL').count()

    # Estimado de Ganancia Mensual Recurrente (MRR)
    mrr_estimado = 0
    for s in suscripciones.filter(estado='ACTIVA'):
        if s.plan_obj and s.plan_obj.precio_mensual > 0:
            mrr_estimado += s.plan_obj.precio_mensual
        elif s.plan == 'BASICO':
            mrr_estimado += 29
        elif s.plan == 'PLUS':
            mrr_estimado += 59
        elif s.plan in ['PREMIUM', 'VIP']:
            mrr_estimado += 99

    total_recaudado = PagoSuscripcion.objects.filter(estado='AL_DIA').aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'admin_user': admin_user,
        'clientes': clientes,
        'planes': planes,
        'suscripciones': suscripciones,
        'pagos': pagos,
        'total_clientes': total_clientes,
        'clientes_al_dia': clientes_al_dia,
        'clientes_deudores': clientes_deudores,
        'clientes_trial': clientes_trial,
        'mrr_estimado': mrr_estimado,
        'total_recaudado': total_recaudado,
    }
    return admin_user, context

def control_admin(request):
    return redirect('admin_clientes')

def admin_clientes(request):
    admin_user, context = get_admin_base_context(request)
    if not admin_user:
        messages.error(request, 'No autorizado')
        return redirect('login_admin')
    
    context['current_tab'] = 'clientes'
    return render(request, 'admin_clientes.html', context)

def admin_finanzas(request):
    admin_user, context = get_admin_base_context(request)
    if not admin_user:
        messages.error(request, 'No autorizado')
        return redirect('login_admin')
    
    context['current_tab'] = 'finanzas'
    return render(request, 'admin_finanzas.html', context)

def admin_planes(request):
    admin_user, context = get_admin_base_context(request)
    if not admin_user:
        messages.error(request, 'No autorizado')
        return redirect('login_admin')
    
    context['current_tab'] = 'planes'
    return render(request, 'admin_planes.html', context)

def admin_logs(request):
    admin_user, context = get_admin_base_context(request)
    if not admin_user:
        messages.error(request, 'No autorizado')
        return redirect('login_admin')
    
    # Logs del sistema unificados (Master Admin + Usuarios de la PWA)
    logs_admin = LogSistemaAdmin.objects.select_related('admin_user').order_by('-timestamp')[:50]
    logs_app1 = LogActividad.objects.select_related('usuario', 'finca').order_by('-fecha_hora')[:50]

    logs_unificados = []
    for l in logs_admin:
        logs_unificados.append({
            'fecha_hora': l.timestamp,
            'origen': 'MASTER_ADMIN',
            'usuario': l.admin_user.nombre if l.admin_user else 'Sistema',
            'modulo': l.tipo,
            'accion': 'ADMIN',
            'descripcion': l.descripcion,
            'ip': l.ip or '127.0.0.1'
        })

    for l in logs_app1:
        finca_nombre = f" ({l.finca.nombre})" if l.finca else ""
        logs_unificados.append({
            'fecha_hora': l.fecha_hora,
            'origen': 'PWA_GANADERO',
            'usuario': f"{l.usuario.nombre}{finca_nombre}",
            'modulo': l.modulo,
            'accion': l.accion,
            'descripcion': l.descripcion,
            'ip': 'Cliente PWA'
        })

    # Ordenar cronológicamente descendente
    logs_unificados.sort(key=lambda x: x['fecha_hora'], reverse=True)
    logs_unificados = logs_unificados[:100]

    context['logs_unificados'] = logs_unificados
    context['current_tab'] = 'logs'
    return render(request, 'admin_logs.html', context)

def toggle_bloqueo(request, user_id):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return redirect('login_admin')
    admin_user = User_admin.objects.get(id=admin_id)
    
    try:
        user = App1User.objects.get(id=user_id)
        user.bloqueado = not user.bloqueado
        user.save()
        estado = "bloqueado" if user.bloqueado else "desbloqueado"
        registrar_log_admin(admin_user, 'CLIENTES', f"Usuario {user.nombre} {estado}", request)
        messages.success(request, f"Usuario {user.nombre} {estado} exitosamente.")
    except App1User.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        
    return redirect(request.META.get('HTTP_REFERER', 'admin_clientes'))

def editar_suscripcion(request):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return redirect('login_admin')
    admin_user = User_admin.objects.get(id=admin_id)
        
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        plan_codigo = request.POST.get('plan')
        estado = request.POST.get('estado')
        fecha_vencimiento = request.POST.get('fecha_vencimiento')
        
        try:
            suscripcion = Suscripcion.objects.get(usuario__id=user_id)
            suscripcion.plan = plan_codigo
            suscripcion.estado = estado
            
            plan_obj = PlanSaaS.objects.filter(codigo=plan_codigo).first()
            if plan_obj:
                suscripcion.plan_obj = plan_obj
                suscripcion.monto_mensual = plan_obj.precio_mensual
                
            if fecha_vencimiento:
                suscripcion.fecha_vencimiento = fecha_vencimiento
            suscripcion.save()

            registrar_log_admin(admin_user, 'FINANZAS', f"Actualizó suscripción de {suscripcion.usuario.nombre} a Plan {plan_codigo} ({estado})", request)
            messages.success(request, f"Suscripción actualizada exitosamente.")
        except Suscripcion.DoesNotExist:
            messages.error(request, "Error al actualizar suscripción.")
            
    return redirect(request.META.get('HTTP_REFERER', 'admin_clientes'))

def guardar_plan_saas(request):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return redirect('login_admin')
    admin_user = User_admin.objects.get(id=admin_id)

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        codigo = request.POST.get('codigo', '').upper().strip()
        nombre = request.POST.get('nombre', '').strip()
        precio_mensual = request.POST.get('precio_mensual', 0)
        badge = request.POST.get('badge', 'Popular').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        caracteristicas_list = request.POST.get('caracteristicas_list', '').strip()
        limite_fincas = request.POST.get('limite_fincas', 1)
        limite_animales = request.POST.get('limite_animales', 100)
        destacado = 'destacado' in request.POST
        activo = 'activo' in request.POST
        
        mod_reproduccion = 'mod_reproduccion' in request.POST
        mod_genetica = 'mod_genetica' in request.POST
        mod_engorde = 'mod_engorde' in request.POST
        mod_crianza = 'mod_crianza' in request.POST
        mod_potreros = 'mod_potreros' in request.POST
        mod_vacunacion = 'mod_vacunacion' in request.POST
        mod_incidentes = 'mod_incidentes' in request.POST
        mod_empleados = 'mod_empleados' in request.POST
        mod_inventario = 'mod_inventario' in request.POST
        mod_finanzas = 'mod_finanzas' in request.POST
        mod_estructura_costos = 'mod_estructura_costos' in request.POST
        mod_auditoria = 'mod_auditoria' in request.POST

        if plan_id:
            plan = get_object_or_404(PlanSaaS, id=plan_id)
            plan.codigo = codigo
            plan.nombre = nombre
            plan.precio_mensual = precio_mensual
            plan.badge = badge
            plan.descripcion = descripcion
            plan.caracteristicas_list = caracteristicas_list
            plan.limite_fincas = limite_fincas
            plan.limite_animales = limite_animales
            plan.destacado = destacado
            plan.activo = activo
            
            plan.mod_reproduccion = mod_reproduccion
            plan.mod_genetica = mod_genetica
            plan.mod_engorde = mod_engorde
            plan.mod_crianza = mod_crianza
            plan.mod_potreros = mod_potreros
            plan.mod_vacunacion = mod_vacunacion
            plan.mod_incidentes = mod_incidentes
            plan.mod_empleados = mod_empleados
            plan.mod_inventario = mod_inventario
            plan.mod_finanzas = mod_finanzas
            plan.mod_estructura_costos = mod_estructura_costos
            plan.mod_auditoria = mod_auditoria
            
            plan.save()
            registrar_log_admin(admin_user, 'PLANES', f"Modificó plan SaaS: {plan.nombre} (${plan.precio_mensual}/mes)", request)
            messages.success(request, f"Plan '{plan.nombre}' actualizado correctamente.")
        else:
            plan = PlanSaaS.objects.create(
                codigo=codigo,
                nombre=nombre,
                precio_mensual=precio_mensual,
                badge=badge,
                descripcion=descripcion,
                caracteristicas_list=caracteristicas_list,
                limite_fincas=limite_fincas,
                limite_animales=limite_animales,
                destacado=destacado,
                activo=activo,
                mod_reproduccion=mod_reproduccion,
                mod_genetica=mod_genetica,
                mod_engorde=mod_engorde,
                mod_crianza=mod_crianza,
                mod_potreros=mod_potreros,
                mod_vacunacion=mod_vacunacion,
                mod_incidentes=mod_incidentes,
                mod_empleados=mod_empleados,
                mod_inventario=mod_inventario,
                mod_finanzas=mod_finanzas,
                mod_estructura_costos=mod_estructura_costos,
                mod_auditoria=mod_auditoria
            )
            registrar_log_admin(admin_user, 'PLANES', f"Creó nuevo plan SaaS: {plan.nombre} (${plan.precio_mensual}/mes)", request)
            messages.success(request, f"Nuevo plan '{plan.nombre}' creado con éxito.")

    return redirect(request.META.get('HTTP_REFERER', 'admin_planes'))

def eliminar_plan_saas(request, plan_id):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return redirect('login_admin')
    admin_user = User_admin.objects.get(id=admin_id)

    plan = get_object_or_404(PlanSaaS, id=plan_id)
    nombre_plan = plan.nombre
    plan.delete()
    registrar_log_admin(admin_user, 'PLANES', f"Eliminó el plan SaaS: {nombre_plan}", request)
    messages.success(request, f"Plan '{nombre_plan}' eliminado exitosamente.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_planes'))

def registrar_pago_saas(request):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return redirect('login_admin')
    admin_user = User_admin.objects.get(id=admin_id)

    if request.method == 'POST':
        suscripcion_id = request.POST.get('suscripcion_id')
        monto = request.POST.get('monto')
        fecha_pago = request.POST.get('fecha_pago')
        periodo = request.POST.get('periodo')
        estado = request.POST.get('estado', 'AL_DIA')
        comprobante = request.POST.get('comprobante', '')

        try:
            suscripcion = Suscripcion.objects.get(id=suscripcion_id)
            PagoSuscripcion.objects.create(
                suscripcion=suscripcion,
                monto=monto,
                fecha_pago=fecha_pago,
                periodo_correspondiente=periodo,
                estado=estado,
                comprobante=comprobante,
                registrado_por=admin_user
            )

            if estado == 'AL_DIA':
                suscripcion.estado = 'ACTIVA'
                # Renovar 30 días automáticamente
                if suscripcion.fecha_vencimiento:
                    suscripcion.fecha_vencimiento = suscripcion.fecha_vencimiento + datetime.timedelta(days=30)
                else:
                    suscripcion.fecha_vencimiento = datetime.date.today() + datetime.timedelta(days=30)
                suscripcion.save()

            registrar_log_admin(admin_user, 'FINANZAS', f"Registró cobro/pago de ${monto} a {suscripcion.usuario.nombre} ({periodo})", request)
            messages.success(request, "Pago registrado y suscripción actualizada.")
        except Suscripcion.DoesNotExist:
            messages.error(request, "Error al registrar el pago.")

    return redirect(request.META.get('HTTP_REFERER', 'admin_finanzas'))


# ── Veti IA – Configuración ───────────────────────────────
def admin_veti(request):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return redirect('login_admin')
    admin_user = User_admin.objects.get(id=admin_id)
    from .models import VetiConfig
    config = VetiConfig.get_config()
    return render(request, 'admin_veti.html', {
        'config': config,
        'admin_user': admin_user,
        'current_tab': 'veti',
    })

def guardar_veti_config(request):
    admin_id = request.session.get('user_admin_id')
    if not admin_id:
        return redirect('login_admin')
    admin_user = User_admin.objects.get(id=admin_id)

    if request.method == 'POST':
        from .models import VetiConfig
        config = VetiConfig.get_config()
        config.system_prompt = request.POST.get('system_prompt', config.system_prompt).strip()
        config.modelo         = request.POST.get('modelo', config.modelo).strip()
        try:
            config.temperatura = float(request.POST.get('temperatura', config.temperatura))
            config.temperatura = max(0.0, min(2.0, config.temperatura))
        except (ValueError, TypeError):
            pass
        try:
            config.max_tokens = int(request.POST.get('max_tokens', config.max_tokens))
            config.max_tokens = max(64, min(8192, config.max_tokens))
        except (ValueError, TypeError):
            pass
        config.activo = request.POST.get('activo') == 'on'
        config.save()
        registrar_log_admin(admin_user, 'SISTEMA', "Actualizó la configuración del asistente Veti IA.", request)
        messages.success(request, '✅ Configuración de Veti guardada correctamente.')

    return redirect('admin_veti')
