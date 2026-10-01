from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q, Sum, F
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
import json
import secrets
import os
import urllib.request
from .models import User, Finca, Animal, Rebaño, ConfiguracionUsuario, VentaAnimal, PlanVacunacion, IncidenteSanitario, GastoFinca, GastoRecurrente, LiquidacionLeche, PrecioLecheConfig, LogActividad, Corral, PesajeAnimal, RegistroAlimentacion, TareaDiaria, HistorialTransferencia, ProtocoloTratamiento, ProtocoloAlimentacion, LecturaComedero, OrdenCargaMixer, ServicioReproductivo, DiagnosticoGestacion, RegistroParto, Potrero, RotacionPotrero, ArticuloInventario, MovimientoInventario, CatalogoSemen, Empleado, PagoNomina, WebAuthnCredential, RegistroOrdeno

from django.core.paginator import Paginator

def registrar_log(usuario, finca_id, accion, modulo, descripcion):
    try:
        LogActividad.objects.create(
            usuario=usuario,
            finca_id=finca_id,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion
        )
    except Exception:
        pass

def login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(nombre=nombre)
            if user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif check_password(password, user.password):
                request.session['user'] = user.id
                ConfiguracionUsuario.objects.get_or_create(user=user)
                registrar_log(user, None, 'LOGIN', 'SEGURIDAD', f"Inicio de sesión exitoso para {user.nombre}")
                return redirect('control')
            # Soporte temporal para contraseñas antiguas no encriptadas:
            elif not user.password.startswith('pbkdf2_') and user.password == password:
                # Encriptamos la contraseña al vuelo para el futuro
                user.password = make_password(password)
                user.save()
                request.session['user'] = user.id
                ConfiguracionUsuario.objects.get_or_create(user=user)
                registrar_log(user, None, 'LOGIN', 'SEGURIDAD', f"Inicio de sesión exitoso para {user.nombre} (encriptada al vuelo)")
                return redirect('control')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'login.html')
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return render(request, 'login.html')

    return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        terminos = request.POST.get('terminos')
        
        if not terminos:
            messages.error(request, 'Debes aceptar los términos y condiciones')
            return redirect('signup')

        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('signup')

        if User.objects.filter(nombre=nombre).exists():
            messages.error(request, 'Este nombre de usuario ya está registrado')
            return redirect('signup')
            
        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'Este correo electrónico ya está registrado')
            return redirect('signup')
            
        # Crear Usuario en app1 con contraseña encriptada
        hashed_password = make_password(password)
        nuevo_user = User.objects.create(nombre=nombre, email=email, password=hashed_password)
        registrar_log(nuevo_user, None, 'CREACION', 'SEGURIDAD', f"Nuevo usuario registrado: {nuevo_user.nombre}")
        
        # Crear Suscripcion Trial en app2 automáticamente (15 días)
        try:
            from app2.models import Suscripcion, PlanSaaS
            import datetime
            trial_plan = PlanSaaS.objects.filter(codigo='TRIAL').first()
            Suscripcion.objects.create(
                usuario=nuevo_user,
                plan='TRIAL',
                plan_obj=trial_plan,
                estado='ACTIVA',
                fecha_vencimiento=datetime.date.today() + datetime.timedelta(days=15)
            )
        except Exception as e:
            # Si falla app2 por alguna razón, no bloqueamos el signup pero el panel no lo verá bien
            print("Error creando suscripción SaaS:", e)

        messages.success(request, 'Cuenta creada exitosamente. Inicie sesión para comenzar.')
        return redirect('login')

    return render(request, 'signup.html')

def index(request):
    # Contador real de usuarios ganaderos registrados e insumos/animales gestionados
    usuarios_activos = User.objects.filter(bloqueado=False).count()
    if usuarios_activos < 12:
        # Base mínima de confianza para demostración comercial
        usuarios_activos = 48 + usuarios_activos

    # Planes SaaS dinámicos definidos en app2
    try:
        from app2.models import PlanSaaS, Suscripcion
        plan_choices = dict(Suscripcion.PLAN_CHOICES)
        db_planes = PlanSaaS.objects.filter(activo=True).order_by('precio_mensual')
        planes_info = []
        for p in db_planes:
            caracts = [c.strip() for c in p.caracteristicas_list.split('\n') if c.strip()] if p.caracteristicas_list else []
            planes_info.append({
                'codigo': p.codigo,
                'nombre': p.nombre,
                'precio': str(int(p.precio_mensual) if p.precio_mensual == int(p.precio_mensual) else p.precio_mensual),
                'moneda': '$',
                'periodo': '15 días' if p.codigo == 'TRIAL' else '/ mes',
                'destacado': p.destacado,
                'badge': p.badge,
                'descripcion': p.descripcion,
                'caracteristicas': caracts
            })
    except Exception as e:
        plan_choices = {'TRIAL': 'Prueba (Trial)', 'BASICO': 'Básico', 'PLUS': 'Plus', 'PREMIUM': 'Premium'}
        planes_info = []

    context = {
        'usuarios_activos': usuarios_activos,
        'planes_info': planes_info,
        'plan_choices': plan_choices,
    }
    return render(request, 'index.html', context)

def robots_txt(request):
    content = """User-agent: *
Allow: /
Disallow: /page/
Disallow: */page/*
Disallow: /control/
Disallow: /finanzas/
Disallow: /perfil/

Sitemap: https://samanito.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")

def llms_txt(request):
    content = """# Samanito - Plataforma SaaS de Gestión Ganadera e Inteligencia Operativa

> Samanito es un software de gestión ganadera multi-tenant diseñado para fincas de producción lechera, engorde y crianza bovina.

## Características Clave para LLMs y Motores Sintéticos
- **Control de Producción Lechera:** Pesaje de ordeño por vaca/lote, curvas de lactancia y alertas de baja producción.
- **Finanzas y Caja Real:** Balance automatizado cruzando ventas de ganado, liquidaciones de leche y gastos recurrentes.
- **Inventario e Insumos:** Deducción automática del stock de medicinas y vacunas en tiempo real.
- **Rotación de Potreros:** Días de ocupación y descanso programados para conservación forrajera.
- **Biometría PWA WebAuthn:** Inicio de sesión instantáneo con huella dactilar/Face ID desde smartphones.

## Estructura de URLs Recomendadas
- /servicios/gestion-ganadera-inteligente
- /servicios/control-produccion-lechera
- /servicios/finanzas-finca-ganadera
- /servicios/rotacion-potreros-forraje
- /servicios/biometria-pwa-ganaderia
"""
    return HttpResponse(content, content_type="text/plain")

def cambiar_finca(request):
    if request.method == 'POST':
        finca_id = request.POST.get('finca_id')
        request.session['finca_activa_id'] = int(finca_id)
        return redirect(request.META.get('HTTP_REFERER', 'control'))
    return redirect('control')

def crear_finca(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        try:
            plan_name = user.suscripcion_saas.plan
            limite = user.suscripcion_saas.plan_obj.limite_fincas if user.suscripcion_saas.plan_obj else 1
        except:
            plan_name = 'TRIAL'
            limite = 1
            
        fincas_count = user.fincas.count()
        
        if fincas_count >= limite:
            messages.error(request, f'Límite de fincas alcanzado para su plan {plan_name}. ¡Contacte a soporte para un Upgrade!')
        else:
            nombre = request.POST.get('nombre')
            f = Finca.objects.create(usuario=user, nombre=nombre)
            request.session['finca_activa_id'] = f.id
            messages.success(request, f'Finca {nombre} creada exitosamente.')
            
    return redirect(request.META.get('HTTP_REFERER', 'control'))

def get_finca_context(request, user):
    fincas_usuario = user.fincas.all()
    finca_activa_id = request.session.get('finca_activa_id')
    
    if not finca_activa_id and fincas_usuario.exists():
        finca_activa_id = fincas_usuario.first().id
        request.session['finca_activa_id'] = finca_activa_id
        
    return finca_activa_id, fincas_usuario

def control(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    
    mostrar_modal_bienvenida = False
    if not finca_activa_id:
        mostrar_modal_bienvenida = True
        fincas_usuario = user.fincas.all()

    config, _ = ConfiguracionUsuario.objects.get_or_create(user=user)
    
    # 1. Total Animales
    total_animales = Animal.objects.filter(finca_id=finca_activa_id).count()
    total_machos = Animal.objects.filter(finca_id=finca_activa_id, sexo='M').count()
    total_hembras = Animal.objects.filter(finca_id=finca_activa_id, sexo='H').count()
    
    # 2. Alertas Destete
    umbral_destete = datetime.date.today() - datetime.timedelta(days=config.meses_destete * 30)
    alertas_destete_count = Animal.objects.filter(finca_id=finca_activa_id, destetado=False, fecha_nacimiento__lte=umbral_destete).count() if config.usar_destete else 0
    
    # 3. Alertas de Inventario (Medicina, Alimentos e Insumos bajo stock)
    articulos_bajo_stock = ArticuloInventario.objects.filter(
        finca_id=finca_activa_id,
        cantidad_actual__lte=F('alerta_minimo')
    )
    count_alertas_inventario = articulos_bajo_stock.count()
    count_medicina_alert = articulos_bajo_stock.filter(categoria='MEDICAMENTO').count()
    count_alimento_alert = articulos_bajo_stock.filter(categoria='ALIMENTO').count()

    # 4. Movimientos Recientes de Insumos
    movimientos_recientes = MovimientoInventario.objects.filter(finca_id=finca_activa_id).order_by('-fecha')[:6]

    # 5. Liquidaciones de Leche Pendientes y Cobradas
    liquidaciones = LiquidacionLeche.objects.filter(finca_id=finca_activa_id)
    liquidaciones_pendientes = liquidaciones.filter(estado_pago='PENDIENTE').order_by('fecha_inicio')[:5]
    monto_pendiente_leche = float(liquidaciones.filter(estado_pago='PENDIENTE').aggregate(total=Sum('monto_total'))['total'] or 0)
    liquidaciones_cobradas_monto = float(liquidaciones.filter(estado_pago='COBRADO').aggregate(total=Sum('monto_total'))['total'] or 0)

    # 6. Balance Financiero Consolidado y Dinero Disponible
    ingresos_animales = float(VentaAnimal.objects.filter(finca_id=finca_activa_id).aggregate(total=Sum('precio_total'))['total'] or 0)
    egresos_gastos = float(GastoFinca.objects.filter(finca_id=finca_activa_id).aggregate(total=Sum('monto'))['total'] or 0)
    egresos_inventario = float(MovimientoInventario.objects.filter(finca_id=finca_activa_id, tipo='ENTRADA').aggregate(total=Sum('costo_total'))['total'] or 0)
    egresos_totales = egresos_gastos + egresos_inventario

    dinero_disponible = (liquidaciones_cobradas_monto + ingresos_animales) - egresos_totales

    # 7. Alertas de Sanidad y Vacunación
    vacunas_pendientes = PlanVacunacion.objects.filter(finca_id=finca_activa_id, estado='PENDIENTE').order_by('fecha_programada')[:5]
    incidentes_activos = IncidenteSanitario.objects.filter(finca_id=finca_activa_id, estado='ACTIVO').order_by('-fecha_incidente')[:5]

    # 8. Últimos Animales Registrados
    ultimos_animales = Animal.objects.filter(finca_id=finca_activa_id).order_by('-id')[:5]
        
    # 9. Rendimiento de Leche (Gráfico y Totales)
    hace_30_dias = datetime.date.today() - datetime.timedelta(days=30)
    dias_leche = []
    valores_leche = []
    
    for i in range(6, -1, -1):
        dia = datetime.date.today() - datetime.timedelta(days=i)
        dias_leche.append(dia.strftime('%d/%m'))
        litros_dia = liquidaciones.filter(fecha_inicio__lte=dia, fecha_fin__gte=dia).aggregate(total=Sum('litros_totales'))['total'] or 0
        valores_leche.append(float(litros_dia))

    prod_semanal = liquidaciones.filter(fecha_inicio__gte=datetime.date.today() - datetime.timedelta(days=7)).aggregate(total=Sum('litros_totales'))['total'] or 0
    vacas_lactancia = Animal.objects.filter(finca_id=finca_activa_id, estado_produccion='LACTANCIA').count()
    vacas_secas = Animal.objects.filter(finca_id=finca_activa_id, estado_produccion='SECA').count()

    context = {
        'total_animales': total_animales,
        'total_machos': total_machos,
        'total_hembras': total_hembras,
        'vacas_lactancia': vacas_lactancia,
        'vacas_secas': vacas_secas,
        'prod_semanal': float(prod_semanal),
        'dias_leche': json.dumps(dias_leche),
        'valores_leche': json.dumps(valores_leche),
        'alertas_destete_count': alertas_destete_count,
        'articulos_bajo_stock': articulos_bajo_stock[:6],
        'count_alertas_inventario': count_alertas_inventario,
        'count_medicina_alert': count_medicina_alert,
        'count_alimento_alert': count_alimento_alert,
        'movimientos_recientes': movimientos_recientes,
        'liquidaciones_pendientes': liquidaciones_pendientes,
        'monto_pendiente_leche': monto_pendiente_leche,
        'dinero_disponible': dinero_disponible,
        'egresos_totales': egresos_totales,
        'vacunas_pendientes': vacunas_pendientes,
        'incidentes_activos': incidentes_activos,
        'ultimos_animales': ultimos_animales,
        'config': config,
        'fincas_usuario': fincas_usuario,
        'mostrar_modal_bienvenida': mostrar_modal_bienvenida,
    }
        
    return render(request, 'control.html', context)

def registro(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')

    if request.method == 'POST':
        animal_id = request.POST.get('animal_id')
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        propietario = request.POST.get('propietario', '')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        sexo = request.POST.get('sexo')
        estado_gestacion = request.POST.get('estado_gestacion', 'N_A')
        estado_produccion = request.POST.get('estado_produccion', 'N_A')
        uso_macho = request.POST.get('uso_macho', 'N_A')
        rebaño_id = request.POST.get('rebaño')
        papa_codigo = request.POST.get('papa')
        mama_codigo = request.POST.get('mama')
        
        try:
            rebaño_obj = Rebaño.objects.get(id=rebaño_id, finca_id=finca_activa_id) if rebaño_id else None
            
            # Gestión de Padres (Si no existen, se crean al vuelo)
            papa = None
            if papa_codigo:
                papa, _ = Animal.objects.get_or_create(
                    finca_id=finca_activa_id,
                    codigo=papa_codigo,
                    defaults={
                        'nombre': f"Padre Externo {papa_codigo}",
                        'sexo': 'M',
                        'uso_macho': 'REPRODUCTOR',
                        'fecha_nacimiento': datetime.date.today() - datetime.timedelta(days=365*4)
                    }
                )
                
            mama = None
            if mama_codigo:
                mama, _ = Animal.objects.get_or_create(
                    finca_id=finca_activa_id,
                    codigo=mama_codigo,
                    defaults={
                        'nombre': f"Madre Externa {mama_codigo}",
                        'sexo': 'H',
                        'fecha_nacimiento': datetime.date.today() - datetime.timedelta(days=365*4)
                    }
                )
            
            if animal_id:
                # Edición
                anim = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
                anim.codigo = codigo
                anim.nombre = nombre
                anim.propietario = propietario
                anim.fecha_nacimiento = fecha_nacimiento
                anim.sexo = sexo
                anim.estado_gestacion = estado_gestacion
                anim.estado_produccion = estado_produccion
                anim.uso_macho = uso_macho
                anim.rebaño = rebaño_obj
                anim.papa = papa
                anim.mama = mama
                anim.save()
                registrar_log(user, finca_activa_id, 'MODIFICACION', 'ANIMALES', f"Actualizó datos del animal: '{nombre}' ({codigo})")
                messages.success(request, f"Animal {nombre} actualizado exitosamente.")
            else:
                # Creación
                Animal.objects.create(
                    finca_id=finca_activa_id,
                    codigo=codigo,
                    nombre=nombre,
                    propietario=propietario,
                    fecha_nacimiento=fecha_nacimiento,
                    sexo=sexo,
                    estado_gestacion=estado_gestacion,
                    estado_produccion=estado_produccion,
                    uso_macho=uso_macho,
                    rebaño=rebaño_obj,
                    papa=papa,
                    mama=mama
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'ANIMALES', f"Registró nuevo animal: '{nombre}' ({codigo})")
                messages.success(request, f"Animal {nombre} registrado exitosamente.")
                
            return redirect('registro')
        except Exception as e:
            messages.error(request, f"Error al registrar animal: {str(e)}")
            
    # Lógica GET y Filtros
    q = request.GET.get('q', '')
    filtro_sexo = request.GET.get('sexo', '')
    filtro_rebano = request.GET.get('rebano', '')
    
    if filtro_rebano:
        try:
            r = Rebaño.objects.get(id=filtro_rebano, finca_id=finca_activa_id)
            animales = r.get_animales()
        except Rebaño.DoesNotExist:
            animales = Animal.objects.filter(finca_id=finca_activa_id)
    else:
        animales = Animal.objects.filter(finca_id=finca_activa_id)
    
    if q:
        animales = animales.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
    if filtro_sexo:
        animales = animales.filter(sexo=filtro_sexo)
        
    propietarios_unicos = Animal.objects.filter(finca_id=finca_activa_id).exclude(propietario__isnull=True).exclude(propietario='').values_list('propietario', flat=True).distinct()
        
    paginator = Paginator(animales, 15)
    page_number = request.GET.get('page')
    animales_paginados = paginator.get_page(page_number)
        
    context = {
        'animales': animales_paginados,
        'rebanos': Rebaño.objects.filter(finca_id=finca_activa_id),
        'q': q,
        'filtro_sexo': filtro_sexo,
        'filtro_rebano': filtro_rebano,
        'fincas_usuario': fincas_usuario,
        'propietarios_unicos': propietarios_unicos,
    }
    return render(request, 'registro.html', context)


def rebano(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'generar_estandares':
            Rebaño.objects.get_or_create(finca_id=finca_activa_id, nombre='Rebaño Horro', defaults={
                'descripcion': 'Vacas Secas (Preñadas o Vacías)',
                'es_dinamico': True, 'filtro_sexo': 'H', 'filtro_estado_produccion': 'SECA'
            })
            Rebaño.objects.get_or_create(finca_id=finca_activa_id, nombre='Rebaño Engorde', defaults={
                'descripcion': 'Machos para sacrificio',
                'es_dinamico': True, 'filtro_sexo': 'M', 'filtro_uso_macho': 'ENGORDE'
            })
            Rebaño.objects.get_or_create(finca_id=finca_activa_id, nombre='Rebaño Mautes', defaults={
                'descripcion': 'Animales de más de 1 año',
                'es_dinamico': True, 'filtro_edad_min_meses': 12
            })
            messages.success(request, "Rebaños estándar generados exitosamente.")
        else:
            # Crear o Editar
            rebano_id = request.POST.get('rebano_id')
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            es_dinamico = request.POST.get('es_dinamico') == 'on'
            filtro_sexo = request.POST.get('filtro_sexo') or None
            
            # Edades
            min_meses = request.POST.get('filtro_edad_min_meses')
            max_meses = request.POST.get('filtro_edad_max_meses')
            min_meses = int(min_meses) if min_meses else None
            max_meses = int(max_meses) if max_meses else None
            
            # Estados
            f_gestacion = request.POST.get('filtro_estado_gestacion') or None
            f_produccion = request.POST.get('filtro_estado_produccion') or None
            f_uso = request.POST.get('filtro_uso_macho') or None
            
            try:
                if rebano_id:
                    # Editar
                    reb = Rebaño.objects.get(id=rebano_id, finca_id=finca_activa_id)
                    reb.nombre = nombre
                    reb.descripcion = descripcion
                    reb.es_dinamico = es_dinamico
                    reb.filtro_sexo = filtro_sexo
                    reb.filtro_edad_min_meses = min_meses
                    reb.filtro_edad_max_meses = max_meses
                    reb.filtro_estado_gestacion = f_gestacion
                    reb.filtro_estado_produccion = f_produccion
                    reb.filtro_uso_macho = f_uso
                    reb.save()
                    messages.success(request, f"Rebaño '{nombre}' actualizado exitosamente.")
                else:
                    # Crear
                    Rebaño.objects.create(
                        finca_id=finca_activa_id,
                        nombre=nombre, 
                        descripcion=descripcion,
                        es_dinamico=es_dinamico,
                        filtro_sexo=filtro_sexo,
                        filtro_edad_min_meses=min_meses,
                        filtro_edad_max_meses=max_meses,
                        filtro_estado_gestacion=f_gestacion,
                        filtro_estado_produccion=f_produccion,
                        filtro_uso_macho=f_uso
                    )
                    messages.success(request, f"Rebaño '{nombre}' creado exitosamente.")
            except Exception as e:
                messages.error(request, f"Error al guardar rebaño: {str(e)}")
                
        return redirect('rebaño')
            
    rebanos = Rebaño.objects.filter(finca_id=finca_activa_id)
    for r in rebanos:
        r.cantidad_animales = r.count_animales()
        
    nombres_basicos = ['Rebaño Horro', 'Rebaño Engorde', 'Rebaño Mautes']
    nombres_existentes = rebanos.values_list('nombre', flat=True)
    mostrar_btn_estandares = not all(n in nombres_existentes for n in nombres_basicos)
        
    context = {
        'rebanos': rebanos,
        'fincas_usuario': fincas_usuario,
        'mostrar_btn_estandares': mostrar_btn_estandares,
    }
    return render(request, 'rebano.html', context)



def crianza(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
    config, _ = ConfiguracionUsuario.objects.get_or_create(user=user)
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'guardar_configuracion':
            meses_destete = request.POST.get('meses_destete')
            meses_mamanto = request.POST.get('meses_mamanto')
            usar_mamanto = request.POST.get('usar_mamanto') == 'on'
            usar_destete = request.POST.get('usar_destete') == 'on'
            
            config.meses_destete = int(meses_destete) if meses_destete else 7
            config.meses_mamanto = int(meses_mamanto) if meses_mamanto else 3
            config.usar_mamanto = usar_mamanto
            config.usar_destete = usar_destete
            config.save()
            
            messages.success(request, "Configuración de reglas de crianza actualizada.")
            
        elif action == 'destetar_animal':
            animal_id = request.POST.get('animal_id')
            nuevo_rebano_id = request.POST.get('rebano_id')
            
            try:
                animal = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
                animal.destetado = True
                
                if nuevo_rebano_id:
                    reb = Rebaño.objects.get(id=nuevo_rebano_id, finca_id=finca_activa_id)
                    animal.rebaño = reb
                    
                animal.save()
                messages.success(request, f"El animal {animal.codigo} ha sido destetado exitosamente.")
            except Exception as e:
                messages.error(request, f"Error al destetar: {str(e)}")
                
        return redirect('crianza')

    # Calcular fechas umbrales
    umbral_destete = datetime.date.today() - datetime.timedelta(days=config.meses_destete * 30)
    umbral_mamanto = datetime.date.today() - datetime.timedelta(days=config.meses_mamanto * 30)
    
    no_destetados = Animal.objects.filter(finca_id=finca_activa_id, destetado=False)
    mamanto = []
    alertas_destete = []
    today = datetime.date.today()
    
    if config.usar_mamanto:
        mamanto = no_destetados.filter(fecha_nacimiento__gt=umbral_mamanto).order_by('-fecha_nacimiento')
        for b in mamanto:
            b.edad_meses = (today - b.fecha_nacimiento).days // 30
            
    if config.usar_destete:
        alertas_destete = no_destetados.filter(fecha_nacimiento__lte=umbral_destete).order_by('fecha_nacimiento')
        for b in alertas_destete:
            b.edad_meses = (today - b.fecha_nacimiento).days // 30

    rebanos = Rebaño.objects.filter(finca_id=finca_activa_id)

    context = {
        'config': config,
        'mamanto': mamanto,
        'alertas_destete': alertas_destete,
        'rebanos': rebanos,
        'fincas_usuario': fincas_usuario,
    }
    
    return render(request, 'crianza.html', context)

def ventas(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'registrar_venta':
            animal_ids = request.POST.getlist('animal_ids')
            motivo = request.POST.get('motivo')
            kilos = request.POST.get('kilos')
            precio = request.POST.get('precio_total')
            comprador = request.POST.get('comprador')
            obs = request.POST.get('observaciones')
            
            if not animal_ids:
                messages.error(request, "Debe seleccionar al menos un animal.")
                return redirect('ventas')
                
            try:
                venta = VentaAnimal.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    motivo=motivo,
                    kilos=kilos if kilos else None,
                    precio_total=precio if precio else None,
                    comprador=comprador,
                    observaciones=obs
                )
                
                for a_id in animal_ids:
                    animal = Animal.objects.get(id=a_id, finca_id=finca_activa_id, estado_vida='VIVO')
                    animal.estado_vida = 'VENDIDO'
                    animal.rebaño = None
                    animal.save()
                    venta.animales.add(animal)
                    
                registrar_log(user, finca_activa_id, 'CREACION', 'VENTAS', f"Registró la venta de {len(animal_ids)} animal(es) por un monto total de ${precio}")
                messages.success(request, f"La venta de {len(animal_ids)} animal(es) ha sido registrada con éxito.")
            except Exception as e:
                messages.error(request, f"Error al registrar la venta: {str(e)}")
                
        return redirect('ventas')
        
    animales_vivos = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO')
    ventas_historico = VentaAnimal.objects.filter(finca_id=finca_activa_id).order_by('-fecha_venta')
    
    total_vendidos = ventas_historico.count()
    total_kilos = sum(v.kilos for v in ventas_historico if v.kilos)
    
    context = {
        'animales_vivos': animales_vivos,
        'ventas': ventas_historico,
        'fincas_usuario': fincas_usuario,
        'total_vendidos': total_vendidos,
        'total_kilos': total_kilos,
    }
    return render(request, 'ventas.html', context)

def descargar_plantilla(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Animales"
    
    headers = ['Codigo', 'Nombre', 'Sexo', 'Fecha_Nacimiento', 'Propietario']
    ws.append(headers)
    
    ejemplo = ['VAC-001', 'Lola', 'H', '2023-05-14', 'Mi Finca']
    ws.append(ejemplo)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_animales.xlsx"'
    wb.save(response)
    return response

def datos_animales(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'importar_excel':
            archivo = request.FILES.get('archivo_excel')
            if not archivo:
                messages.error(request, 'Por favor seleccione un archivo Excel.')
            elif not archivo.name.endswith('.xlsx'):
                messages.error(request, 'El formato del archivo debe ser .xlsx')
            else:
                try:
                    wb = openpyxl.load_workbook(archivo)
                    ws = wb.active
                    
                    headers = [str(cell.value).strip().lower() for cell in ws[1]]
                    
                    if 'codigo' not in headers or 'nombre' not in headers or 'sexo' not in headers or 'fecha_nacimiento' not in headers:
                        messages.error(request, 'El Excel no tiene el formato correcto. Use la plantilla.')
                    else:
                        idx_codigo = headers.index('codigo')
                        idx_nombre = headers.index('nombre')
                        idx_sexo = headers.index('sexo')
                        idx_fecha = headers.index('fecha_nacimiento')
                        idx_prop = headers.index('propietario') if 'propietario' in headers else -1
                        
                        creados = 0
                        omitidos = 0
                        
                        for row in ws.iter_rows(min_row=2, values_only=True):
                            if not row[idx_codigo] or not row[idx_nombre]:
                                continue
                                
                            codigo = str(row[idx_codigo]).strip()
                            nombre = str(row[idx_nombre]).strip()
                            sexo_raw = str(row[idx_sexo]).strip().upper()
                            sexo = 'H' if 'H' in sexo_raw or 'F' in sexo_raw else 'M'
                            
                            fecha = row[idx_fecha]
                            if isinstance(fecha, datetime.datetime):
                                fecha_nac = fecha.date()
                            else:
                                try:
                                    fecha_str = str(fecha).strip()
                                    fecha_nac = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                                except:
                                    fecha_nac = datetime.date.today()
                                    
                            prop = str(row[idx_prop]).strip() if idx_prop >= 0 and row[idx_prop] else None
                            
                            if not Animal.objects.filter(finca_id=finca_activa_id, codigo=codigo).exists():
                                Animal.objects.create(
                                    usuario=user,
                                    finca_id=finca_activa_id,
                                    codigo=codigo,
                                    nombre=nombre,
                                    sexo=sexo,
                                    fecha_nacimiento=fecha_nac,
                                    propietario=prop
                                )
                                creados += 1
                            else:
                                omitidos += 1
                                
                        registrar_log(user, finca_activa_id, 'IMPORTACION', 'ANIMALES', f"Importó animales desde Excel: {creados} creados, {omitidos} omitidos")
                        messages.success(request, f"Importación exitosa. Creados: {creados}. Omitidos (código existente): {omitidos}.")
                except Exception as e:
                    messages.error(request, f"Error al procesar el Excel: {str(e)}")
            
            return redirect('datos_animales')

    total_animales = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO').count()
    context = {
        'fincas_usuario': fincas_usuario,
        'total_animales': total_animales,
    }
    return render(request, 'datos_animales.html', context)


def vacunacion(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'programar_vacuna':
            vacuna = request.POST.get('vacuna')
            fecha_prog = request.POST.get('fecha_programada')
            rebano_id = request.POST.get('rebano_id')
            observaciones = request.POST.get('observaciones')
            articulo_id = request.POST.get('articulo_inventario_id')
            dosis = float(request.POST.get('dosis_por_animal') or 0)
            
            try:
                reb = Rebaño.objects.get(id=rebano_id, finca_id=finca_activa_id) if rebano_id else None
                art_obj = ArticuloInventario.objects.filter(id=articulo_id, finca_id=finca_activa_id).first() if articulo_id else None
                
                PlanVacunacion.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    vacuna=vacuna,
                    fecha_programada=fecha_prog,
                    rebaño=reb,
                    articulo_inventario=art_obj,
                    dosis_por_animal=dosis,
                    observaciones=observaciones
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'SANIDAD', f"Programó vacuna: '{vacuna}' para el {fecha_prog}")
                messages.success(request, f"Plan de vacunación para {vacuna} programado con éxito.")
            except Exception as e:
                messages.error(request, f"Error al programar: {str(e)}")
                
        elif action == 'completar_vacuna':
            vacuna_id = request.POST.get('vacuna_id')
            try:
                plan = PlanVacunacion.objects.get(id=vacuna_id, finca_id=finca_activa_id)
                plan.estado = 'COMPLETADO'
                plan.fecha_aplicacion = datetime.date.today()
                plan.save()

                if plan.articulo_inventario and plan.dosis_por_animal and plan.dosis_por_animal > 0:
                    art = plan.articulo_inventario
                    num_animales = plan.rebaño.animales_fijos.count() if plan.rebaño else Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO').count()
                    total_dosis = float(plan.dosis_por_animal) * num_animales
                    art.cantidad_actual = max(0, float(art.cantidad_actual) - total_dosis)
                    art.save()
                    MovimientoInventario.objects.create(
                        finca_id=finca_activa_id,
                        articulo=art,
                        tipo='SALIDA',
                        cantidad=total_dosis,
                        usuario_registro=user,
                        observaciones=f"Aplicación de vacuna: {plan.vacuna} ({num_animales} animales)"
                    )

                registrar_log(user, finca_activa_id, 'MODIFICACION', 'SANIDAD', f"Marcó como completada la vacunación: '{plan.vacuna}'")
                messages.success(request, f"Vacunación {plan.vacuna} marcada como completada.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                
        return redirect('vacunacion')
        
    pendientes = PlanVacunacion.objects.filter(finca_id=finca_activa_id, estado='PENDIENTE').order_by('fecha_programada')
    completadas = PlanVacunacion.objects.filter(finca_id=finca_activa_id, estado='COMPLETADO').order_by('-fecha_aplicacion')
    rebaños = Rebaño.objects.filter(finca_id=finca_activa_id)
    articulos_vacunas = ArticuloInventario.objects.filter(finca_id=finca_activa_id, categoria='MEDICAMENTO')
    
    context = {
        'fincas_usuario': fincas_usuario,
        'pendientes': pendientes,
        'completadas': completadas,
        'rebaños': rebaños,
        'articulos_vacunas': articulos_vacunas,
    }
    return render(request, 'vacunacion.html', context)


def incidentes(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'registrar_incidente':
            animal_id = request.POST.get('animal_id')
            tipo = request.POST.get('tipo')
            fecha = request.POST.get('fecha_incidente')
            diag = request.POST.get('diagnostico')
            trat = request.POST.get('tratamiento')
            articulo_id = request.POST.get('articulo_inventario_id')
            cant_usada = float(request.POST.get('cantidad_utilizada') or 0)
            
            try:
                animal = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
                articulo_obj = ArticuloInventario.objects.filter(id=articulo_id, finca_id=finca_activa_id).first() if articulo_id else None
                
                IncidenteSanitario.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    animal=animal,
                    fecha_incidente=fecha,
                    tipo=tipo,
                    diagnostico=diag,
                    tratamiento=trat,
                    articulo_inventario=articulo_obj,
                    cantidad_utilizada=cant_usada if articulo_obj else 0
                )
                
                if articulo_obj and cant_usada > 0:
                    articulo_obj.cantidad_actual = max(0, float(articulo_obj.cantidad_actual) - cant_usada)
                    articulo_obj.save()
                    MovimientoInventario.objects.create(
                        finca_id=finca_activa_id,
                        articulo=articulo_obj,
                        tipo='SALIDA',
                        cantidad=cant_usada,
                        usuario_registro=user,
                        observaciones=f"Tratamiento para animal {animal.codigo}: {diag}"
                    )

                registrar_log(user, finca_activa_id, 'CREACION', 'SANIDAD', f"Registró incidente clínico para el animal '{animal.codigo}': {diag}")
                messages.success(request, f"Incidente registrado para el animal {animal.codigo}.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                
        elif action == 'actualizar_estado_incidente':
            incidente_id = request.POST.get('incidente_id')
            nuevo_estado = request.POST.get('nuevo_estado')
            try:
                inc = IncidenteSanitario.objects.get(id=incidente_id, finca_id=finca_activa_id)
                inc.estado = nuevo_estado
                inc.save()
                registrar_log(user, finca_activa_id, 'MODIFICACION', 'SANIDAD', f"Actualizó estado del incidente '{inc.animal.codigo}' a {nuevo_estado}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': True})
                messages.success(request, f"Estado del incidente de {inc.animal.codigo} actualizado.")
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                messages.error(request, f"Error: {str(e)}")
                
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return redirect('incidentes')
        
    atendiendo = IncidenteSanitario.objects.filter(finca_id=finca_activa_id, estado='ATENDIENDO').order_by('-fecha_incidente')
    recuperacion = IncidenteSanitario.objects.filter(finca_id=finca_activa_id, estado='RECUPERACION').order_by('-fecha_incidente')
    recuperado = IncidenteSanitario.objects.filter(finca_id=finca_activa_id, estado='RECUPERADO').order_by('-fecha_incidente')[:50]
    animales_vivos = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO')
    articulos_medicina = ArticuloInventario.objects.filter(finca_id=finca_activa_id, categoria='MEDICAMENTO')
    
    context = {
        'fincas_usuario': fincas_usuario,
        'atendiendo': atendiendo,
        'recuperacion': recuperacion,
        'recuperado': recuperado,
        'animales_vivos': animales_vivos,
        'articulos_medicina': articulos_medicina,
    }
    return render(request, 'incidentes.html', context)


# Endpoints API
def api_buscar_padre(request):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'results': []})
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
    
    q = request.GET.get('q', '')
    if len(q) < 1:
        return JsonResponse({'results': []})
        
    # Machos reproductores
    machos = Animal.objects.filter(finca_id=finca_activa_id, sexo='M', uso_macho='REPRODUCTOR').filter(
        Q(codigo__icontains=q) | Q(nombre__icontains=q)
    )[:10]
    
    results = [{'codigo': m.codigo, 'nombre': m.nombre} for m in machos]
    return JsonResponse({'results': results})

def api_buscar_madre(request):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'results': []})
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')

    q = request.GET.get('q', '')
    if len(q) < 1:
        return JsonResponse({'results': []})
        
    # Hembras de >= 3 años (36 meses) aprox 1095 dias
    tres_anios = datetime.date.today() - datetime.timedelta(days=1095)
    hembras = Animal.objects.filter(finca_id=finca_activa_id, sexo='H', fecha_nacimiento__lte=tres_anios).filter(
        Q(codigo__icontains=q) | Q(nombre__icontains=q)
    )[:10]
    
    results = [{'codigo': h.codigo, 'nombre': h.nombre} for h in hembras]
    return JsonResponse({'results': results})

def api_buscar_vaca_seca(request):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'results': []})
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')

    q = request.GET.get('q', '')
    if len(q) < 1:
        return JsonResponse({'results': []})
        
    # Buscar hembras que NO están en lactancia
    vacas = Animal.objects.filter(finca_id=finca_activa_id, sexo='H', estado_produccion='SECA').filter(
        Q(codigo__icontains=q) | Q(nombre__icontains=q)
    )[:10]
    
    results = [
        {'id': a.id, 'text': f"{a.codigo} - {a.nombre}"}
        for a in vacas
    ]
    return JsonResponse({'results': results})

def api_buscar_animal_vivo(request):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'results': []})
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return JsonResponse({'results': []})
        
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'results': []})
        
    animales = Animal.objects.filter(
        finca_id=finca_activa_id, 
        estado_vida='VIVO'
    ).filter(
        Q(codigo__icontains=q) | Q(nombre__icontains=q)
    )[:15]
    
    results = [
        {'id': a.id, 'text': f"{a.codigo} - {a.nombre}"}
        for a in animales
    ]
    return JsonResponse({'results': results})

def api_reportes(request):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    user = User.objects.get(id=user_id)
    finca_activa_id, _ = get_finca_context(request, user)
    
    if not finca_activa_id:
        return JsonResponse({'error': 'No finca'}, status=400)
        
    sexo = request.GET.get('sexo')
    estado_prod = request.GET.get('estado_produccion')
    estado_gest = request.GET.get('estado_gestacion')
    uso_macho = request.GET.get('uso_macho')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    qs = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO')
    
    if sexo:
        qs = qs.filter(sexo=sexo)
    if estado_prod:
        qs = qs.filter(estado_produccion=estado_prod)
    if estado_gest:
        qs = qs.filter(estado_gestacion=estado_gest)
    if uso_macho:
        qs = qs.filter(uso_macho=uso_macho)
        
    if fecha_desde:
        qs = qs.filter(fecha_nacimiento__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_nacimiento__lte=fecha_hasta)
        
    total = qs.count()
    machos = qs.filter(sexo='M').count()
    hembras = qs.filter(sexo='H').count()
    
    lactancia = qs.filter(estado_produccion='LACTANCIA').count()
    seca = qs.filter(estado_produccion='SECA').count()
    vacia = qs.filter(estado_gestacion='VACIA').count()
    prenada = qs.filter(estado_gestacion='PREÑADA').count()
    
    # Gráficos
    grafico_sexo = [machos, hembras]
    grafico_prod = [lactancia, seca, qs.count() - lactancia - seca]
    
    # Listado limitado para tabla preview
    animales = list(qs.order_by('-id')[:50].values('codigo', 'nombre', 'sexo', 'estado_produccion'))
    
    return JsonResponse({
        'total': total,
        'grafico_sexo': grafico_sexo,
        'grafico_prod': grafico_prod,
        'animales': animales,
        'estadisticas': {
            'lactancia': lactancia,
            'seca': seca,
            'vacia': vacia,
            'prenada': prenada
        }
    })

def exportar_reporte_excel(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, _ = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')
        
    sexo = request.GET.get('sexo')
    estado_prod = request.GET.get('estado_produccion')
    estado_gest = request.GET.get('estado_gestacion')
    uso_macho = request.GET.get('uso_macho')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    qs = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO')
    
    if sexo:
        qs = qs.filter(sexo=sexo)
    if estado_prod:
        qs = qs.filter(estado_produccion=estado_prod)
    if estado_gest:
        qs = qs.filter(estado_gestacion=estado_gest)
    if uso_macho:
        qs = qs.filter(uso_macho=uso_macho)
        
    if fecha_desde:
        qs = qs.filter(fecha_nacimiento__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_nacimiento__lte=fecha_hasta)
            
    # Crear archivo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte Filtrado"
    
    # Encabezados
    headers = ['Codigo', 'Nombre', 'Sexo', 'Fecha Nacimiento', 'Estado Produccion', 'Estado Gestacion', 'Uso (Machos)']
    ws.append(headers)
    
    for a in qs.order_by('codigo'):
        ws.append([
            a.codigo, 
            a.nombre, 
            a.sexo, 
            str(a.fecha_nacimiento) if a.fecha_nacimiento else '', 
            a.estado_produccion, 
            a.estado_gestacion,
            a.uso_macho
        ])
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_animales.xlsx"'
    wb.save(response)
    return response

def finanzas(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
        
    precio_leche_config, _ = PrecioLecheConfig.objects.get_or_create(
        finca_id=finca_activa_id,
        defaults={'precio_por_litro': 0.00}
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'registrar_gasto':
            concepto = request.POST.get('concepto')
            monto = request.POST.get('monto')
            categoria = request.POST.get('categoria')
            tipo = request.POST.get('tipo', 'VARIABLE')
            fecha = request.POST.get('fecha')
            
            try:
                GastoFinca.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    concepto=concepto,
                    monto=monto,
                    categoria=categoria,
                    tipo=tipo,
                    fecha=fecha
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'FINANZAS', f"Registró gasto: '{concepto}' por ${monto} ({tipo})")
                messages.success(request, 'Gasto registrado correctamente')
            except Exception as e:
                messages.error(request, f'Error al registrar gasto: {str(e)}')
                
        elif action == 'configurar_leche':
            precio = request.POST.get('precio_por_litro')
            try:
                precio_leche_config.precio_por_litro = precio
                precio_leche_config.save()
                registrar_log(user, finca_activa_id, 'CONFIGURACION', 'FINANZAS', f"Actualizó el precio de la leche a ${precio} por litro")
                messages.success(request, 'Precio del litro de leche actualizado')
            except Exception as e:
                messages.error(request, f'Error al actualizar precio: {str(e)}')
                
        elif action == 'crear_liquidacion_leche':
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            litros = float(request.POST.get('litros_totales') or 0)
            precio = float(request.POST.get('precio_por_litro') or precio_leche_config.precio_por_litro)
            monto_total = litros * precio
            comprador = request.POST.get('comprador', '')
            estado_pago = request.POST.get('estado_pago', 'PENDIENTE')
            fecha_cobro = datetime.date.today() if estado_pago == 'COBRADO' else None
            obs = request.POST.get('observaciones', '')

            try:
                LiquidacionLeche.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    litros_totales=litros,
                    precio_por_litro=precio,
                    monto_total=monto_total,
                    comprador=comprador,
                    estado_pago=estado_pago,
                    fecha_cobro=fecha_cobro,
                    observaciones=obs
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'FINANZAS', f"Registró periodo de leche ({fecha_inicio} a {fecha_fin}) por ${monto_total} [{estado_pago}]")
                messages.success(request, 'Periodo de liquidación de leche registrado correctamente')
            except Exception as e:
                messages.error(request, f'Error al registrar periodo de leche: {str(e)}')

        elif action == 'cobrar_liquidacion':
            liq_id = request.POST.get('liquidacion_id')
            try:
                liq = LiquidacionLeche.objects.get(id=liq_id, finca_id=finca_activa_id)
                liq.estado_pago = 'COBRADO'
                liq.fecha_cobro = datetime.date.today()
                liq.save()
                registrar_log(user, finca_activa_id, 'EDICION', 'FINANZAS', f"Cobró liquidación de leche #{liq.id} por ${liq.monto_total}")
                messages.success(request, f"Liquidación de leche por ${liq.monto_total} marcada como COBRADA.")
            except Exception as e:
                messages.error(request, f'Error al actualizar cobro: {str(e)}')

        elif action == 'eliminar_liquidacion':
            liq_id = request.POST.get('liquidacion_id')
            try:
                liq = LiquidacionLeche.objects.get(id=liq_id, finca_id=finca_activa_id)
                liq.delete()
                messages.success(request, 'Registro de liquidación eliminado')
            except Exception as e:
                messages.error(request, f'Error al eliminar: {str(e)}')

        elif action == 'eliminar_gasto':
            gasto_id = request.POST.get('gasto_id')
            try:
                gasto = GastoFinca.objects.get(id=gasto_id, finca_id=finca_activa_id)
                concepto_del = gasto.concepto
                monto_del = gasto.monto
                gasto.delete()
                registrar_log(user, finca_activa_id, 'ELIMINACION', 'FINANZAS', f"Eliminó gasto: '{concepto_del}' por ${monto_del}")
                messages.success(request, 'Gasto eliminado')
            except Exception as e:
                messages.error(request, f'Error al eliminar: {str(e)}')
                
        return redirect('finanzas')
        
    # Cálculos Financieros Consolidados
    liquidaciones_leche = LiquidacionLeche.objects.filter(finca_id=finca_activa_id).order_by('-fecha_inicio')
    
    ingresos_leche_cobrados = float(liquidaciones_leche.filter(estado_pago='COBRADO').aggregate(total=Sum('monto_total'))['total'] or 0)
    ingresos_leche_pendientes = float(liquidaciones_leche.filter(estado_pago='PENDIENTE').aggregate(total=Sum('monto_total'))['total'] or 0)
    litros_totales_cobrados = float(liquidaciones_leche.filter(estado_pago='COBRADO').aggregate(total=Sum('litros_totales'))['total'] or 0)
    
    ingresos_animales = float(VentaAnimal.objects.filter(finca_id=finca_activa_id).aggregate(total=Sum('precio_total'))['total'] or 0)
    
    egresos_gastos = float(GastoFinca.objects.filter(finca_id=finca_activa_id).aggregate(total=Sum('monto'))['total'] or 0)
    egresos_inventario = float(MovimientoInventario.objects.filter(finca_id=finca_activa_id, tipo='ENTRADA').aggregate(total=Sum('costo_total'))['total'] or 0)
    egresos_totales = egresos_gastos + egresos_inventario

    ingresos_totales_cobrados = ingresos_leche_cobrados + ingresos_animales
    dinero_disponible = ingresos_totales_cobrados - egresos_totales
    
    gastos = GastoFinca.objects.filter(finca_id=finca_activa_id).order_by('-fecha')
    
    # Datos para gráficos de gastos por categoría
    categorias = ['ALIMENTO', 'VETERINARIA', 'PERSONAL', 'SERVICIOS', 'MANTENIMIENTO', 'OTRO']
    chart_gastos = []
    for c in categorias:
        total_cat = GastoFinca.objects.filter(finca_id=finca_activa_id, categoria=c).aggregate(total=Sum('monto'))['total'] or 0
        chart_gastos.append(float(total_cat))
        
    context = {
        'fincas_usuario': fincas_usuario,
        'precio_leche_config': precio_leche_config,
        'liquidaciones_leche': liquidaciones_leche,
        'ingresos_leche_cobrados': ingresos_leche_cobrados,
        'ingresos_leche_pendientes': ingresos_leche_pendientes,
        'litros_totales_cobrados': litros_totales_cobrados,
        'ingresos_animales': ingresos_animales,
        'ingresos_totales_cobrados': ingresos_totales_cobrados,
        'egresos_gastos': egresos_gastos,
        'egresos_inventario': egresos_inventario,
        'egresos_totales': egresos_totales,
        'dinero_disponible': dinero_disponible,
        'gastos': gastos,
        'chart_gastos': chart_gastos,
    }
    return render(request, 'finanzas.html', context)

def auditoria(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
        
    # Cargar logs de actividad asociados a la finca actual o generales (sin finca)
    logs = LogActividad.objects.filter(finca_id=finca_activa_id).order_by('-fecha_hora')
    
    # Filtros
    modulo_filtro = request.GET.get('modulo')
    accion_filtro = request.GET.get('accion')
    q = request.GET.get('q')
    
    if modulo_filtro:
        logs = logs.filter(modulo=modulo_filtro)
    if accion_filtro:
        logs = logs.filter(accion=accion_filtro)
    if q:
        logs = logs.filter(descripcion__icontains=q)
        
    context = {
        'fincas_usuario': fincas_usuario,
        'logs': logs[:200],  # Mostrar los últimos 200 logs
        'modulo_filtro': modulo_filtro,
        'accion_filtro': accion_filtro,
        'q': q,
    }
    return render(request, 'auditoria.html', context)

def perfil(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')

    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)

    # Obtener suscripción y plan de app2
    suscripcion = None
    limite_fincas = 1  # límite por defecto si no hay plan
    try:
        from app2.models import Suscripcion
        suscripcion, _ = Suscripcion.objects.get_or_create(usuario=user)
        if suscripcion.plan_obj:
            limite_fincas = suscripcion.plan_obj.limite_fincas
        else:
            # Sin plan_obj: Trial = 1 finca, resto tienen más
            plan_limites = {'TRIAL': 1, 'BASICO': 1, 'PLUS': 3, 'PREMIUM': 10, 'VIP': 999}
            limite_fincas = plan_limites.get(suscripcion.plan, 1)
    except Exception:
        pass

    config, _ = ConfiguracionUsuario.objects.get_or_create(user=user)
    todas_las_fincas = Finca.objects.filter(usuario=user)
    fincas_count = todas_las_fincas.count()
    puede_crear_finca = fincas_count < limite_fincas

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'actualizar_datos':
            nombre = request.POST.get('nombre')
            email = request.POST.get('email')

            if User.objects.exclude(id=user.id).filter(nombre=nombre).exists():
                messages.error(request, 'El nombre de usuario ya está en uso')
            elif email and User.objects.exclude(id=user.id).filter(email=email).exists():
                messages.error(request, 'El correo electrónico ya está en uso')
            else:
                user.nombre = nombre
                user.email = email
                user.save()
                registrar_log(user, finca_activa_id, 'MODIFICACION', 'SEGURIDAD', f"Actualizó sus datos básicos de cuenta (Nombre: {nombre})")
                messages.success(request, 'Datos de cuenta actualizados correctamente')

        elif action == 'crear_finca':
            nombre_finca = request.POST.get('nombre_finca', '').strip()
            if not nombre_finca:
                messages.error(request, 'El nombre de la finca no puede estar vacío')
            elif not puede_crear_finca:
                plan_nombre = suscripcion.get_plan_display() if suscripcion else 'Trial'
                messages.error(
                    request,
                    f'Tu plan {plan_nombre} solo permite {limite_fincas} finca(s). '
                    f'Ya tienes {fincas_count}. Contacta a soporte para mejorar tu plan.'
                )
            else:
                nueva_finca = Finca.objects.create(usuario=user, nombre=nombre_finca)
                request.session['finca_activa'] = nueva_finca.id
                registrar_log(user, nueva_finca.id, 'CREACION', 'ANIMALES', f"Creó la finca '{nombre_finca}'")
                messages.success(request, f'Finca "{nombre_finca}" creada exitosamente y establecida como activa')

        elif action == 'cambiar_password':
            current_pw = request.POST.get('current_password')
            new_pw = request.POST.get('new_password')
            confirm_pw = request.POST.get('confirm_password')

            if not check_password(current_pw, user.password) and not (not user.password.startswith('pbkdf2_') and user.password == current_pw):
                messages.error(request, 'La contraseña actual es incorrecta')
            elif new_pw != confirm_pw:
                messages.error(request, 'La nueva contraseña y su confirmación no coinciden')
            elif len(new_pw) < 6:
                messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres')
            else:
                user.password = make_password(new_pw)
                user.save()
                registrar_log(user, finca_activa_id, 'MODIFICACION', 'SEGURIDAD', "Actualizó su contraseña de acceso")
                messages.success(request, 'Contraseña cambiada correctamente')

        elif action == 'guardar_config':
            # Configuración de crianza (existente)
            config.usar_mamanto = 'usar_mamanto' in request.POST
            config.usar_destete = 'usar_destete' in request.POST
            config.meses_mamanto = int(request.POST.get('meses_mamanto', 3))
            config.meses_destete = int(request.POST.get('meses_destete', 7))
            config.save()
            registrar_log(user, finca_activa_id, 'CONFIGURACION', 'SEGURIDAD', "Modificó los parámetros de crianza y destete")
            messages.success(request, 'Configuración de crianza guardada')

        elif action == 'guardar_preferencias':
            config.unidad_peso = request.POST.get('unidad_peso', 'KG')
            config.formato_fecha = request.POST.get('formato_fecha', 'DMY')
            config.moneda_simbolo = request.POST.get('moneda_simbolo', '$') or '$'
            config.mostrar_codigo = 'mostrar_codigo' in request.POST
            try:
                config.animales_por_pag = int(request.POST.get('animales_por_pag', 25))
            except (ValueError, TypeError):
                config.animales_por_pag = 25
            config.tema_preferido = request.POST.get('tema_preferido', 'CLARO')
            config.notif_vencimientos = 'notif_vencimientos' in request.POST
            config.notif_vacunas = 'notif_vacunas' in request.POST
            config.notif_partos = 'notif_partos' in request.POST
            config.save()
            registrar_log(user, finca_activa_id, 'CONFIGURACION', 'SEGURIDAD', "Modificó las preferencias de visualización y notificaciones")
            messages.success(request, 'Preferencias guardadas correctamente')

        return redirect('perfil')

    webauthn_creds = WebAuthnCredential.objects.filter(user=user)
    context = {
        'fincas_usuario': fincas_usuario,
        'todas_las_fincas': todas_las_fincas,
        'user_profile': user,
        'suscripcion': suscripcion,
        'config': config,
        'webauthn_creds': webauthn_creds,
        'puede_crear_finca': puede_crear_finca,
        'limite_fincas_plan': limite_fincas,
        'fincas_count': fincas_count,
    }
    return render(request, 'perfil.html', context)

# --- WEB AUTH N / FINGERPRINT BIOMETRICS ---
def api_webauthn_register_options(request):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    user = User.objects.get(id=user_id)
    challenge = secrets.token_urlsafe(32)
    request.session['webauthn_register_challenge'] = challenge

    options = {
        "challenge": challenge,
        "rp": {
            "name": "Samanito Software",
            "id": request.get_host().split(':')[0]
        },
        "user": {
            "id": str(user.id),
            "name": user.nombre,
            "displayName": user.nombre
        },
        "pubKeyCredParams": [
            {"alg": -7, "type": "public-key"},  # ES256
            {"alg": -257, "type": "public-key"} # RS256
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": "platform",
            "userVerification": "preferred",
            "residentKey": "discouraged"
        },
        "timeout": 60000
    }
    return JsonResponse(options)

def api_webauthn_register_verify(request):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    user = User.objects.get(id=user_id)
    try:
        data = json.loads(request.body)
        credential_id = data.get('id')
        device_name = data.get('device_name', 'Huella Dactilar Mobile')

        if not credential_id:
            return JsonResponse({'error': 'Credencial inválida'}, status=400)

        # Registrar o actualizar la credencial
        WebAuthnCredential.objects.update_or_create(
            credential_id=credential_id,
            defaults={
                'user': user,
                'public_key': data.get('rawId', credential_id),
                'device_name': device_name
            }
        )
        registrar_log(user, None, 'CREACION', 'SEGURIDAD', f"Registró huella/biometría dactilar: {device_name}")
        return JsonResponse({'success': True, 'message': 'Huella registrada con éxito'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def api_webauthn_login_options(request):
    challenge = secrets.token_urlsafe(32)
    request.session['webauthn_login_challenge'] = challenge

    options = {
        "challenge": challenge,
        "timeout": 60000,
        "userVerification": "preferred"
    }
    return JsonResponse(options)

def api_webauthn_login_verify(request):
    try:
        data = json.loads(request.body)
        credential_id = data.get('id')
        
        if not credential_id:
            return JsonResponse({'error': 'Identificador de huella no provisto'}, status=400)
            
        try:
            cred = WebAuthnCredential.objects.get(credential_id=credential_id)
        except WebAuthnCredential.DoesNotExist:
            return JsonResponse({'error': 'Huella dactilar no reconocida en esta finca'}, status=404)
            
        user = cred.user
        if user.bloqueado:
            return JsonResponse({'error': 'Usuario bloqueado'}, status=403)
            
        # Iniciar sesión automáticamente
        request.session['user'] = user.id
        ConfiguracionUsuario.objects.get_or_create(user=user)
        cred.sign_count += 1
        cred.save()
        
        registrar_log(user, None, 'LOGIN', 'SEGURIDAD', f"Inicio de sesión exitoso con Huella Dactilar ({cred.device_name})")
        return JsonResponse({'success': True, 'redirect': '/control/'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def api_webauthn_delete(request, cred_id):
    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    try:
        cred = WebAuthnCredential.objects.get(id=cred_id, user_id=user_id)
        cred.delete()
        messages.success(request, 'Huella dactilar eliminada')
    except WebAuthnCredential.DoesNotExist:
        messages.error(request, 'Huella no encontrada')
    return redirect('perfil')

def engorde(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'crear_corral':
            nombre = request.POST.get('nombre')
            capacidad = request.POST.get('capacidad', 20)
            desc = request.POST.get('descripcion', '')
            try:
                Corral.objects.create(finca_id=finca_activa_id, nombre=nombre, capacidad=capacidad, descripcion=desc)
                registrar_log(user, finca_activa_id, 'CREACION', 'REBAÑOS', f"Creó corral: '{nombre}' con capacidad para {capacidad} animales")
                messages.success(request, 'Corral creado correctamente')
            except Exception as e:
                messages.error(request, f'Error al crear corral: {str(e)}')
                
        elif action == 'registrar_alimentacion':
            corral_id = request.POST.get('corral_id')
            alimento = request.POST.get('tipo_alimento')
            cantidad = request.POST.get('cantidad_kg')
            costo = request.POST.get('costo_total', 0.00)
            fecha = request.POST.get('fecha')
            try:
                corral = Corral.objects.get(id=corral_id, finca_id=finca_activa_id)
                RegistroAlimentacion.objects.create(
                    finca_id=finca_activa_id,
                    corral=corral,
                    fecha=fecha,
                    tipo_alimento=alimento,
                    cantidad_kg=cantidad,
                    costo_total=costo
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'FINANZAS', f"Registró alimentación en corral '{corral.nombre}': {cantidad}kg de {alimento} por ${costo}")
                messages.success(request, 'Alimentación registrada con éxito')
            except Exception as e:
                messages.error(request, f'Error al registrar alimentación: {str(e)}')
                
        elif action == 'registrar_pesaje':
            animal_id = request.POST.get('animal_id')
            peso = request.POST.get('peso_kg')
            fecha = request.POST.get('fecha')
            try:
                animal = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
                PesajeAnimal.objects.create(animal=animal, fecha=fecha, peso_kg=peso)
                registrar_log(user, finca_activa_id, 'CREACION', 'ANIMALES', f"Registró pesaje para el animal {animal.codigo}: {peso}kg")
                messages.success(request, f'Pesaje de {peso}kg registrado para el animal {animal.codigo}')
            except Exception as e:
                messages.error(request, f'Error al registrar pesaje: {str(e)}')
                
        elif action == 'crear_tarea':
            desc = request.POST.get('descripcion')
            cat = request.POST.get('categoria', 'OTRO')
            fecha = request.POST.get('fecha')
            try:
                TareaDiaria.objects.create(finca_id=finca_activa_id, fecha=fecha, descripcion=desc, categoria=cat)
                messages.success(request, 'Tarea diaria programada')
            except Exception as e:
                messages.error(request, f'Error al crear tarea: {str(e)}')
                
        elif action == 'toggle_tarea':
            tarea_id = request.POST.get('tarea_id')
            try:
                tarea = TareaDiaria.objects.get(id=tarea_id, finca_id=finca_activa_id)
                tarea.completada = not tarea.completada
                tarea.save()
                messages.success(request, 'Estado de la tarea actualizado')
            except Exception as e:
                messages.error(request, f'Error al actualizar tarea: {str(e)}')
                
        elif action == 'transferir_animales':
            destino_id = request.POST.get('corral_destino_id')
            animal_ids = request.POST.getlist('animal_ids')
            motivo = request.POST.get('motivo', '')
            try:
                destino = Corral.objects.get(id=destino_id, finca_id=finca_activa_id) if destino_id else None
                for a_id in animal_ids:
                    animal = Animal.objects.get(id=a_id, finca_id=finca_activa_id)
                    origen = animal.corral
                    animal.corral = destino
                    animal.save()
                    HistorialTransferencia.objects.create(
                        animal=animal,
                        corral_origen=origen,
                        corral_destino=destino,
                        motivo=motivo
                    )
                dest_nombre = destino.nombre if destino else 'Ninguno'
                registrar_log(user, finca_activa_id, 'MODIFICACION', 'REBAÑOS', f"Transfirió {len(animal_ids)} animal(es) al corral '{dest_nombre}'")
                messages.success(request, 'Animales transferidos correctamente')
            except Exception as e:
                messages.error(request, f'Error en transferencia: {str(e)}')
                
        return redirect('engorde')
        
    # GET
    corrales_list = Corral.objects.filter(finca_id=finca_activa_id)
    corrales_data = []
    
    total_gdp_finca = 0.0
    con_gdp_finca = 0
    
    for c in corrales_list:
        animales = c.animales.filter(estado_vida='VIVO')
        
        # Calcular GDP (Ganancia Diaria Promedio) del corral
        total_gdp = 0.0
        con_gdp = 0
        for a in animales:
            pesajes = a.pesajes.all().order_by('fecha')
            if pesajes.count() >= 2:
                p_primero = pesajes.first()
                p_ultimo = pesajes.last()
                dias = (p_ultimo.fecha - p_primero.fecha).days
                if dias > 0:
                    gdp = float(p_ultimo.peso_kg - p_primero.peso_kg) / dias
                    total_gdp += gdp
                    con_gdp += 1
                    
        gdp_promedio = total_gdp / con_gdp if con_gdp > 0 else 0.0
        
        total_gdp_finca += total_gdp
        con_gdp_finca += con_gdp
        
        costo_alimento = RegistroAlimentacion.objects.filter(corral=c).aggregate(total=Sum('costo_total'))['total'] or 0
        
        corrales_data.append({
            'corral': c,
            'animales': animales,
            'gdp_promedio': gdp_promedio,
            'costo_alimento': costo_alimento,
            'ocupacion_porcentaje': (animales.count() / c.capacidad * 100) if c.capacidad > 0 else 0,
        })
        
    gdp_promedio_finca = total_gdp_finca / con_gdp_finca if con_gdp_finca > 0 else 0.0
    animales_sin_corral = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO', corral__isnull=True)
    animales_todos = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO')
    
    hoy = datetime.date.today()
    tareas_pendientes = TareaDiaria.objects.filter(finca_id=finca_activa_id, fecha=hoy).order_by('completada')
    
    context = {
        'fincas_usuario': fincas_usuario,
        'corrales': corrales_data,
        'gdp_promedio_finca': gdp_promedio_finca,
        'animales_sin_corral': animales_sin_corral,
        'animales_todos': animales_todos,
        'tareas': tareas_pendientes,
    }
    return render(request, 'engorde.html', context)

import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def manga_manejo(request):
    user_id = request.session.get('user')
    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
            return JsonResponse({'error': 'No autorizado'}, status=401)
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No hay finca activa'}, status=400)
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')

    # AJAX: Buscar animal por RFID o Código
    if request.GET.get('ajax') == 'buscar_animal':
        query = request.GET.get('term', '').strip()
        animal = Animal.objects.filter(
            Q(codigo=query) | Q(caravana_electronica=query) | Q(nombre__icontains=query),
            finca_id=finca_activa_id,
            estado_vida='VIVO'
        ).first()
        if animal:
            return JsonResponse({
                'success': True,
                'id': animal.id,
                'codigo': animal.codigo,
                'nombre': animal.nombre,
                'caravana': animal.caravana_electronica or 'Sin asignar',
                'estado_salud': animal.get_estado_salud_display(),
                'estado_salud_raw': animal.estado_salud,
                'corral': animal.corral.nombre if animal.corral else 'Sin corral',
                'sexo': animal.get_sexo_display(),
                'edad': (datetime.date.today() - animal.fecha_nacimiento).days // 30,
            })
        return JsonResponse({'success': False, 'message': 'Animal no encontrado'})

    # AJAX: Obtener protocolo
    if request.GET.get('ajax') == 'get_protocolo':
        proto_id = request.GET.get('id')
        try:
            proto = ProtocoloTratamiento.objects.get(id=proto_id, finca_id=finca_activa_id)
            return JsonResponse({
                'success': True,
                'diagnostico': proto.diagnostico_asociado,
                'medicamento': proto.medicamento,
                'dosis': proto.dosis,
                'duracion': proto.duracion_dias
            })
        except ProtocoloTratamiento.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Protocolo no encontrado'})

    # POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Procesar sincronización offline desde AJAX
        if action == 'sincronizar_offline' or request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                acciones = data.get('acciones', [])
                sincronizados = 0
                
                for acc in acciones:
                    tipo = acc.get('tipo')
                    fecha_acc = acc.get('fecha', datetime.date.today().strftime('%Y-%m-%d'))
                    
                    if tipo == 'tratamiento':
                        codigo = acc.get('codigo_animal')
                        diag = acc.get('diagnostico')
                        med = acc.get('medicamento')
                        dosis = acc.get('dosis')
                        hosp = acc.get('hospitalizar', False)
                        
                        animal = Animal.objects.filter(codigo=codigo, finca_id=finca_activa_id, estado_vida='VIVO').first()
                        if animal:
                            IncidenteSanitario.objects.create(
                                usuario=user,
                                finca_id=finca_activa_id,
                                animal=animal,
                                fecha_incidente=fecha_acc,
                                tipo='ENFERMEDAD',
                                diagnostico=diag,
                                tratamiento=f"{med} - Dosis: {dosis}",
                                estado='RESUELTO' if not hosp else 'PENDIENTE'
                            )
                            if hosp:
                                corral_hosp = Corral.objects.filter(finca_id=finca_activa_id, es_hospital=True).first()
                                if corral_hosp:
                                    animal.corral = corral_hosp
                                animal.estado_salud = 'HOSPITAL'
                            else:
                                animal.estado_salud = 'TRATAMIENTO'
                            animal.save()
                            sincronizados += 1
                            
                    elif tipo == 'pesaje':
                        codigo = acc.get('codigo_animal')
                        peso = acc.get('peso_kg')
                        animal = Animal.objects.filter(codigo=codigo, finca_id=finca_activa_id, estado_vida='VIVO').first()
                        if animal:
                            PesajeAnimal.objects.create(animal=animal, fecha=fecha_acc, peso_kg=peso)
                            sincronizados += 1
                            
                if sincronizados > 0:
                    registrar_log(user, finca_activa_id, 'IMPORTACION', 'SANIDAD', f"Sincronizó de forma offline {sincronizados} actividades sanitarias/pesajes")
                return JsonResponse({'success': True, 'sincronizados': sincronizados})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        # POST Normal de Formularios
        if action == 'crear_protocolo':
            nombre = request.POST.get('nombre')
            diag = request.POST.get('diagnostico')
            med = request.POST.get('medicamento')
            dosis = request.POST.get('dosis')
            duracion = request.POST.get('duracion_dias', 3)
            try:
                ProtocoloTratamiento.objects.create(
                    finca_id=finca_activa_id,
                    nombre=nombre,
                    diagnostico_asociado=diag,
                    medicamento=med,
                    dosis=dosis,
                    duracion_dias=duracion
                )
                messages.success(request, f"Protocolo '{nombre}' creado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al crear protocolo: {str(e)}")
                
        elif action == 'aplicar_tratamiento':
            animal_id = request.POST.get('animal_id')
            diag = request.POST.get('diagnostico')
            med = request.POST.get('medicamento')
            dosis = request.POST.get('dosis')
            hosp = 'hospitalizar' in request.POST
            
            try:
                animal = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
                IncidenteSanitario.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    animal=animal,
                    fecha_incidente=datetime.date.today(),
                    tipo='ENFERMEDAD',
                    diagnostico=diag,
                    tratamiento=f"{med} - Dosis: {dosis}",
                    estado='PENDIENTE' if hosp else 'RESUELTO'
                )
                
                if hosp:
                    corral_hosp = Corral.objects.filter(finca_id=finca_activa_id, es_hospital=True).first()
                    if corral_hosp:
                        animal.corral = corral_hosp
                    animal.estado_salud = 'HOSPITAL'
                else:
                    animal.estado_salud = 'TRATAMIENTO'
                animal.save()
                
                registrar_log(user, finca_activa_id, 'CREACION', 'SANIDAD', f"Aplicó tratamiento a {animal.codigo}: {diag} ({med})")
                messages.success(request, f"Tratamiento registrado correctamente para {animal.nombre}.")
            except Exception as e:
                messages.error(request, f"Error al aplicar tratamiento: {str(e)}")
                
        elif action == 'alta_medica':
            animal_id = request.POST.get('animal_id')
            nuevo_corral_id = request.POST.get('nuevo_corral_id')
            try:
                animal = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
                animal.estado_salud = 'SANO'
                if nuevo_corral_id:
                    animal.corral = Corral.objects.get(id=nuevo_corral_id, finca_id=finca_activa_id)
                animal.save()
                
                # Marcar incidentes pendientes como resueltos
                IncidenteSanitario.objects.filter(animal=animal, estado='PENDIENTE').update(estado='RESUELTO')
                
                registrar_log(user, finca_activa_id, 'MODIFICACION', 'SANIDAD', f"Dio de alta médica al animal {animal.codigo}")
                messages.success(request, f"Se dio de alta médica al animal {animal.codigo}.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                
        return redirect('manga')

    # GET
    protocolos = ProtocoloTratamiento.objects.filter(finca_id=finca_activa_id)
    hospitalizados = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO', estado_salud='HOSPITAL')
    en_tratamiento = Animal.objects.filter(finca_id=finca_activa_id, estado_vida='VIVO', estado_salud='TRATAMIENTO')
    corrales = Corral.objects.filter(finca_id=finca_activa_id)
    corrales_comunes = corrales.filter(es_hospital=False)
    
    # Comprobar si hay corral hospital, si no hay, crearlo automáticamente
    corral_hospital = corrales.filter(es_hospital=True).first()
    if not corral_hospital:
        corral_hospital = Corral.objects.create(
            finca_id=finca_activa_id,
            nombre="Corral Hospital / Aislamiento",
            capacidad=15,
            es_hospital=True,
            descripcion="Corral destinado al tratamiento y recuperación de animales enfermos."
        )
        
    context = {
        'fincas_usuario': fincas_usuario,
        'protocolos': protocolos,
        'hospitalizados': hospitalizados,
        'en_tratamiento': en_tratamiento,
        'corrales_comunes': corrales_comunes,
        'corral_hospital': corral_hospital,
    }
    return render(request, 'manga.html', context)

def estructura_costos(request):
    user_id = request.session.get('user')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
        
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')

    # Manejo de Formularios POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'crear_gasto_recurrente':
            concepto = request.POST.get('concepto')
            categoria = request.POST.get('categoria')
            monto = request.POST.get('monto')
            frecuencia = request.POST.get('frecuencia')
            observaciones = request.POST.get('observaciones', '')
            fecha_inicio = request.POST.get('fecha_inicio') or datetime.date.today()
            
            try:
                GastoRecurrente.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    concepto=concepto,
                    categoria=categoria,
                    monto=monto,
                    frecuencia=frecuencia,
                    observaciones=observaciones,
                    fecha_inicio=fecha_inicio
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'FINANZAS', f"Registró gasto recurrente '{concepto}' (${monto} {frecuencia})")
                messages.success(request, 'Gasto recurrente registrado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al registrar gasto recurrente: {str(e)}')

        elif action == 'editar_gasto_recurrente':
            gasto_id = request.POST.get('gasto_id')
            try:
                g = GastoRecurrente.objects.get(id=gasto_id, finca_id=finca_activa_id)
                g.concepto = request.POST.get('concepto')
                g.categoria = request.POST.get('categoria')
                g.monto = request.POST.get('monto')
                g.frecuencia = request.POST.get('frecuencia')
                g.observaciones = request.POST.get('observaciones', '')
                if request.POST.get('fecha_inicio'):
                    g.fecha_inicio = request.POST.get('fecha_inicio')
                g.save()
                registrar_log(user, finca_activa_id, 'EDICION', 'FINANZAS', f"Actualizó gasto recurrente '{g.concepto}'")
                messages.success(request, 'Gasto recurrente actualizado')
            except Exception as e:
                messages.error(request, f'Error al editar: {str(e)}')

        elif action == 'toggle_activo':
            gasto_id = request.POST.get('gasto_id')
            try:
                g = GastoRecurrente.objects.get(id=gasto_id, finca_id=finca_activa_id)
                g.activo = not g.activo
                g.save()
                estado_str = "Activado" if g.activo else "Desactivado"
                messages.info(request, f"Gasto '{g.concepto}' {estado_str}")
            except Exception as e:
                messages.error(request, f'Error al cambiar estado: {str(e)}')

        elif action == 'eliminar_gasto_recurrente':
            gasto_id = request.POST.get('gasto_id')
            try:
                g = GastoRecurrente.objects.get(id=gasto_id, finca_id=finca_activa_id)
                concepto_del = g.concepto
                g.delete()
                registrar_log(user, finca_activa_id, 'ELIMINACION', 'FINANZAS', f"Eliminó gasto recurrente '{concepto_del}'")
                messages.success(request, 'Gasto recurrente eliminado')
            except Exception as e:
                messages.error(request, f'Error al eliminar: {str(e)}')

        elif action == 'cargar_a_gastos':
            gasto_id = request.POST.get('gasto_id')
            try:
                g = GastoRecurrente.objects.get(id=gasto_id, finca_id=finca_activa_id)
                GastoFinca.objects.create(
                    usuario=user,
                    finca_id=finca_activa_id,
                    fecha=datetime.date.today(),
                    categoria=g.categoria,
                    concepto=f"[Recurrente] {g.concepto}",
                    monto=g.monto,
                    tipo='FIJO'
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'FINANZAS', f"Asentó en finanzas el gasto recurrente '{g.concepto}' por ${g.monto}")
                messages.success(request, f"Se asentó el gasto '{g.concepto}' en Finanzas de Finca.")
            except Exception as e:
                messages.error(request, f'Error al asentar gasto: {str(e)}')

        return redirect('estructura_costos')

    # Cargar datos para la vista
    gastos_recurrentes = GastoRecurrente.objects.filter(finca_id=finca_activa_id).order_by('-activo', 'categoria')

    # Totales por frecuencia (Solo activos)
    activos = gastos_recurrentes.filter(activo=True)
    total_semanal = float(activos.filter(frecuencia='SEMANAL').aggregate(total=Sum('monto'))['total'] or 0)
    total_mensual = float(activos.filter(frecuencia='MENSUAL').aggregate(total=Sum('monto'))['total'] or 0)
    total_semestral = float(activos.filter(frecuencia='SEMESTRAL').aggregate(total=Sum('monto'))['total'] or 0)
    total_anual = float(activos.filter(frecuencia='ANUAL').aggregate(total=Sum('monto'))['total'] or 0)

    # Equivalencias
    semanal_eq_mensual = total_semanal * 4.333
    mensual_eq_mensual = total_mensual
    semestral_eq_mensual = total_semestral / 6.0
    anual_eq_mensual = total_anual / 12.0

    eq_mensual = semanal_eq_mensual + mensual_eq_mensual + semestral_eq_mensual + anual_eq_mensual
    eq_anual = (total_semanal * 52.0) + (total_mensual * 12.0) + (total_semestral * 2.0) + total_anual

    # Totales por categoría (Equivalente mensual)
    categorias_info = []
    for cat_code, cat_name in GastoFinca.CATEGORIA_CHOICES:
        cat_activos = activos.filter(categoria=cat_code)
        sem = float(cat_activos.filter(frecuencia='SEMANAL').aggregate(total=Sum('monto'))['total'] or 0)
        men = float(cat_activos.filter(frecuencia='MENSUAL').aggregate(total=Sum('monto'))['total'] or 0)
        semest = float(cat_activos.filter(frecuencia='SEMESTRAL').aggregate(total=Sum('monto'))['total'] or 0)
        an = float(cat_activos.filter(frecuencia='ANUAL').aggregate(total=Sum('monto'))['total'] or 0)
        
        cat_eq_mensual = (sem * 4.333) + men + (semest / 6.0) + (an / 12.0)
        if cat_eq_mensual > 0 or cat_activos.exists():
            categorias_info.append({
                'codigo': cat_code,
                'nombre': cat_name,
                'eq_mensual': cat_eq_mensual,
                'count': cat_activos.count()
            })

    context = {
        'fincas_usuario': fincas_usuario,
        'gastos_recurrentes': gastos_recurrentes,
        'total_semanal': total_semanal,
        'total_mensual': total_mensual,
        'total_semestral': total_semestral,
        'total_anual': total_anual,
        'semanal_eq_mensual': semanal_eq_mensual,
        'mensual_eq_mensual': mensual_eq_mensual,
        'semestral_eq_mensual': semestral_eq_mensual,
        'anual_eq_mensual': anual_eq_mensual,
        'eq_mensual': eq_mensual,
        'eq_anual': eq_anual,
        'categorias_info': categorias_info,
        'categoria_choices': GastoFinca.CATEGORIA_CHOICES,
        'frecuencia_choices': GastoRecurrente.FRECUENCIA_CHOICES,
    }
    return render(request, 'estructura_costos.html', context)

def reproduccion(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'registrar_servicio':
            animal_id = request.POST.get('animal_id')
            tipo = request.POST.get('tipo')
            fecha = request.POST.get('fecha')
            toro_o_pajilla = request.POST.get('toro_o_pajilla')
            obs = request.POST.get('observaciones')
            try:
                hembra = Animal.objects.get(id=animal_id)
                # Inbreeding Check Básico
                toro_interno = Animal.objects.filter(finca_id=finca_activa_id, sexo='M', codigo=toro_o_pajilla).first()
                if toro_interno and hembra.padre and hembra.padre == toro_interno:
                    messages.error(request, '¡ALERTA DE CONSANGUINIDAD! El toro seleccionado es el padre de la hembra.')
                    return redirect('reproduccion')
                    
                fecha_obj = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
                fpp = fecha_obj + datetime.timedelta(days=283)
                ServicioReproductivo.objects.create(
                    finca_id=finca_activa_id, hembra=hembra, tipo=tipo, fecha=fecha_obj, toro_o_pajilla=toro_o_pajilla, fecha_probable_parto=fpp, observaciones=obs
                )
                messages.success(request, 'Servicio reproductivo registrado con éxito.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        
        elif action == 'registrar_diagnostico':
            animal_id = request.POST.get('animal_id')
            fecha = request.POST.get('fecha')
            metodo = request.POST.get('metodo')
            resultado = request.POST.get('resultado')
            obs = request.POST.get('observaciones')
            try:
                DiagnosticoGestacion.objects.create(finca_id=finca_activa_id, hembra_id=animal_id, fecha=fecha, metodo=metodo, resultado=resultado, observaciones=obs)
                anim = Animal.objects.get(id=animal_id)
                anim.estado_gestacion = resultado
                anim.save()
                messages.success(request, 'Diagnóstico guardado.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        
        elif action == 'registrar_parto':
            animal_id = request.POST.get('animal_id')
            fecha = request.POST.get('fecha')
            tipo = request.POST.get('tipo')
            facilidad = request.POST.get('facilidad')
            obs = request.POST.get('observaciones')
            try:
                madre = Animal.objects.get(id=animal_id)
                cria_obj = None
                if tipo == 'PARTO':
                    cria_obj = Animal.objects.create(
                        finca_id=finca_activa_id, usuario=user, codigo=f"CRIA-{madre.codigo}-{fecha}", nombre=f"Cria de {madre.nombre}", fecha_nacimiento=fecha, sexo='H', madre_id=madre.id
                    )
                RegistroParto.objects.create(finca_id=finca_activa_id, madre_id=animal_id, fecha=fecha, tipo=tipo, facilidad=facilidad, cria=cria_obj, observaciones=obs)
                madre.estado_gestacion = 'VACIA'
                madre.save()
                messages.success(request, 'Parto/Aborto registrado.')
            except Exception as e:
                messages.error(request, f'Error: {e}')

        return redirect('reproduccion')

    hembras = Animal.objects.filter(finca_id=finca_activa_id, sexo='H')
    machos = Animal.objects.filter(finca_id=finca_activa_id, sexo='M')
    catalogo = CatalogoSemen.objects.filter(finca_id=finca_activa_id)
    servicios = ServicioReproductivo.objects.filter(finca_id=finca_activa_id).order_by('-fecha')
    diagnosticos = DiagnosticoGestacion.objects.filter(finca_id=finca_activa_id).order_by('-fecha')
    partos = RegistroParto.objects.filter(finca_id=finca_activa_id).order_by('-fecha')

    context = {
        'fincas_usuario': fincas_usuario,
        'hembras': hembras,
        'machos': machos,
        'catalogo': catalogo,
        'servicios': servicios[:20],
        'diagnosticos': diagnosticos[:20],
        'partos': partos[:20]
    }
    return render(request, 'reproduccion.html', context)

def potreros(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'crear_potrero':
            nombre = request.POST.get('nombre')
            has = request.POST.get('hectareas')
            tipo_pasto = request.POST.get('tipo_pasto')
            rebano_id = request.POST.get('rebano_id') or None
            try:
                Potrero.objects.create(
                    finca_id=finca_activa_id, 
                    nombre=nombre, 
                    hectareas=has, 
                    tipo_pasto=tipo_pasto,
                    rebaño_id=rebano_id
                )
                messages.success(request, 'Potrero creado.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
                
        elif action == 'rotar_rebano':
            potrero_id = request.POST.get('potrero_id')
            rebano_id = request.POST.get('rebano_id')
            try:
                potrero = Potrero.objects.get(id=potrero_id, finca_id=finca_activa_id)
                if potrero.estado == 'OCUPADO':
                    messages.error(request, 'El potrero ya está ocupado.')
                else:
                    RotacionPotrero.objects.create(finca_id=finca_activa_id, potrero=potrero, rebaño_id=rebano_id, fecha_entrada=datetime.date.today())
                    potrero.estado = 'OCUPADO'
                    potrero.save()
                    messages.success(request, 'Rebaño rotado al potrero.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
                
        elif action == 'retirar_rebano':
            potrero_id = request.POST.get('potrero_id')
            try:
                potrero = Potrero.objects.get(id=potrero_id, finca_id=finca_activa_id)
                rotacion_activa = RotacionPotrero.objects.filter(potrero=potrero, fecha_salida__isnull=True).first()
                if rotacion_activa:
                    rotacion_activa.fecha_salida = datetime.date.today()
                    rotacion_activa.save()
                potrero.estado = 'DESCANSO'
                potrero.save()
                messages.success(request, 'Rebaño retirado del potrero.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
                
        return redirect('potreros')

    potreros = Potrero.objects.filter(finca_id=finca_activa_id)
    rebanos = Rebaño.objects.filter(finca_id=finca_activa_id)
    context = {
        'fincas_usuario': fincas_usuario,
        'potreros': potreros,
        'rebanos': rebanos
    }
    return render(request, 'potreros.html', context)

def inventario(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'crear_articulo':
            nombre = request.POST.get('nombre')
            categoria = request.POST.get('categoria')
            unidad = request.POST.get('unidad_medida')
            alerta = request.POST.get('alerta_minimo')
            try:
                ArticuloInventario.objects.create(finca_id=finca_activa_id, nombre=nombre, categoria=categoria, unidad_medida=unidad, alerta_minimo=alerta)
                messages.success(request, 'Artículo registrado.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        
        elif action == 'registrar_movimiento':
            articulo_id = request.POST.get('articulo_id')
            tipo = request.POST.get('tipo')
            cantidad = float(request.POST.get('cantidad') or 0)
            costo_total = float(request.POST.get('costo_total') or 0)
            obs = request.POST.get('observaciones', '')
            try:
                articulo = ArticuloInventario.objects.get(id=articulo_id, finca_id=finca_activa_id)
                MovimientoInventario.objects.create(
                    finca_id=finca_activa_id,
                    articulo=articulo,
                    tipo=tipo,
                    cantidad=cantidad,
                    costo_total=costo_total if tipo == 'ENTRADA' else 0,
                    usuario_registro=user,
                    observaciones=obs
                )
                if tipo == 'ENTRADA':
                    articulo.cantidad_actual = float(articulo.cantidad_actual) + cantidad
                    if costo_total > 0:
                        cat_gasto = 'VETERINARIA' if articulo.categoria == 'MEDICAMENTO' else ('ALIMENTO' if articulo.categoria == 'ALIMENTO' else 'OTRO')
                        GastoFinca.objects.create(
                            usuario=user,
                            finca_id=finca_activa_id,
                            fecha=datetime.date.today(),
                            categoria=cat_gasto,
                            concepto=f"Compra Inventario: {articulo.nombre} ({cantidad} {articulo.unidad_medida})",
                            monto=costo_total,
                            tipo='VARIABLE'
                        )
                elif tipo == 'SALIDA':
                    articulo.cantidad_actual = max(0, float(articulo.cantidad_actual) - cantidad)
                else:
                    articulo.cantidad_actual = cantidad
                articulo.save()
                messages.success(request, 'Movimiento registrado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error: {e}')

        return redirect('inventario')

    articulos = ArticuloInventario.objects.filter(finca_id=finca_activa_id)
    movimientos = MovimientoInventario.objects.filter(finca_id=finca_activa_id).order_by('-fecha')[:50]
    
    context = {
        'fincas_usuario': fincas_usuario,
        'articulos': articulos,
        'movimientos': movimientos
    }
    return render(request, 'inventario.html', context)

def empleados(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'registrar_empleado':
            nombre = request.POST.get('nombre')
            cargo = request.POST.get('cargo')
            salario = request.POST.get('salario_base')
            fecha = request.POST.get('fecha_contratacion')
            telefono = request.POST.get('telefono')
            Empleado.objects.create(finca_id=finca_activa_id, nombre=nombre, cargo=cargo, salario_base=salario, fecha_contratacion=fecha, telefono=telefono)
            messages.success(request, 'Empleado registrado.')
        elif action == 'pagar_nomina':
            empleado_id = request.POST.get('empleado_id')
            monto = request.POST.get('monto')
            fecha = request.POST.get('fecha')
            concepto = request.POST.get('concepto')
            empleado = Empleado.objects.get(id=empleado_id, finca_id=finca_activa_id)
            PagoNomina.objects.create(finca_id=finca_activa_id, empleado=empleado, fecha=fecha, monto_pagado=monto, concepto=concepto, registrado_por=user)
            # Automaticamente crea un GastoFinca
            GastoFinca.objects.create(finca_id=finca_activa_id, fecha=fecha, concepto=f"Nómina: {empleado.nombre} - {concepto}", categoria='SUELDOS', monto=monto, estado='PAGADO', registrado_por=user)
            messages.success(request, 'Nómina pagada y gasto registrado.')
        return redirect('empleados')
        
    empleados_list = Empleado.objects.filter(finca_id=finca_activa_id)
    pagos = PagoNomina.objects.filter(finca_id=finca_activa_id).order_by('-fecha')[:50]
    context = {
        'fincas_usuario': fincas_usuario,
        'empleados': empleados_list,
        'pagos': pagos
    }
    return render(request, 'empleados.html', context)

def genetica(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'registrar_toro':
            nombre = request.POST.get('nombre_toro')
            raza = request.POST.get('raza')
            codigo = request.POST.get('codigo_pajilla')
            pta = request.POST.get('pta_leche') or 0
            precio = request.POST.get('precio') or 0
            stock = request.POST.get('stock') or 0
            CatalogoSemen.objects.create(finca_id=finca_activa_id, nombre_toro=nombre, raza=raza, codigo_pajilla=codigo, pta_leche=pta, precio=precio, stock=stock)
            messages.success(request, 'Toro agregado al catálogo.')
        elif action == 'actualizar_raza':
            animal_id = request.POST.get('animal_id')
            raza = request.POST.get('composicion_racial')
            anim = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
            anim.composicion_racial = raza
            anim.save()
            messages.success(request, 'Composición racial actualizada.')
        return redirect('genetica')

    catalogo = CatalogoSemen.objects.filter(finca_id=finca_activa_id)
    animales = Animal.objects.filter(finca_id=finca_activa_id)
    context = {
        'fincas_usuario': fincas_usuario,
        'catalogo': catalogo,
        'animales': animales
    }
    return render(request, 'genetica.html', context)

def hoja_vida(request, animal_id):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')

    animal = Animal.objects.get(id=animal_id, finca_id=finca_activa_id)
    
    # Recolectar timeline
    timeline = []
    # 1. Nacimiento
    timeline.append({'fecha': animal.fecha_nacimiento, 'tipo': 'NACIMIENTO', 'desc': 'Nacimiento del animal'})
    # 2. Pesajes
    for p in PesajeAnimal.objects.filter(animal=animal):
        timeline.append({'fecha': p.fecha, 'tipo': 'PESAJE', 'desc': f'Pesaje: {p.peso_kg} kg'})
    # 3. Sanidad
    for i in IncidenteSanitario.objects.filter(animal=animal):
        timeline.append({'fecha': i.fecha_incidente, 'tipo': 'SANIDAD', 'desc': f'{i.get_tipo_display()}: {i.diagnostico}'})
    # 4. Reproduccion (Si es hembra)
    if animal.sexo == 'H':
        for s in ServicioReproductivo.objects.filter(hembra=animal):
            timeline.append({'fecha': s.fecha, 'tipo': 'SERVICIO', 'desc': f'Servicio ({s.get_tipo_display()}) con {s.toro_o_pajilla}'})
        for d in DiagnosticoGestacion.objects.filter(hembra=animal):
            timeline.append({'fecha': d.fecha, 'tipo': 'DIAGNOSTICO', 'desc': f'Diagnóstico: {d.get_resultado_display()}'})
        for p in RegistroParto.objects.filter(madre=animal):
            timeline.append({'fecha': p.fecha, 'tipo': 'PARTO', 'desc': f'Parto/Aborto: {p.get_tipo_display()}'})
            
    # Ordenar por fecha desc
    timeline.sort(key=lambda x: x['fecha'], reverse=True)
    
    context = {
        'fincas_usuario': fincas_usuario,
        'animal': animal,
        'timeline': timeline
    }
    return render(request, 'hoja_vida.html', context)

def ordeno(request):
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        return redirect('control')

    finca_activa = Finca.objects.get(id=finca_activa_id)
    precio_config, _ = PrecioLecheConfig.objects.get_or_create(finca=finca_activa, defaults={'precio_por_litro': 0.50})

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'guardar_ordeno':
            fecha = request.POST.get('fecha') or datetime.date.today()
            turno = request.POST.get('turno', 'MAÑANA')
            rebano_id = request.POST.get('rebano_id') or None
            animal_id = None
            
            # Calcular cantidad de vacas automáticamente
            if rebano_id:
                reb = Rebaño.objects.get(id=rebano_id, finca_id=finca_activa_id)
                vacas = reb.get_animales().filter(sexo='H', estado_produccion='LACTANCIA').count()
            else:
                vacas = Animal.objects.filter(finca_id=finca_activa_id, sexo='H', estado_produccion='LACTANCIA').count()
            
            if vacas == 0:
                vacas = 1
            litros = float(request.POST.get('litros_leche') or 0.0)
            precio = float(request.POST.get('precio_litro') or precio_config.precio_por_litro)
            temp = request.POST.get('temperatura_tanque')
            temp_val = float(temp) if temp else None
            obs = request.POST.get('observaciones', '')

            try:
                RegistroOrdeno.objects.create(
                    finca_id=finca_activa_id,
                    usuario=user,
                    fecha=fecha,
                    turno=turno,
                    rebaño_id=rebano_id,
                    animal_id=animal_id,
                    vacas_ordenadas=vacas,
                    litros_leche=litros,
                    precio_litro=precio,
                    temperatura_tanque=temp_val,
                    observaciones=obs
                )
                registrar_log(user, finca_activa_id, 'CREACION', 'ORDEÑO', f'Registro de ordeño {litros}L')
                messages.success(request, f'Se registraron {litros} L de leche en el ordeño de la {turno.lower()}.')
            except Exception as e:
                messages.error(request, f'Error al guardar ordeño: {e}')

        elif action == 'eliminar_ordeno':
            reg_id = request.POST.get('registro_id')
            try:
                reg = RegistroOrdeno.objects.get(id=reg_id, finca_id=finca_activa_id)
                reg.delete()
                messages.success(request, 'Registro de ordeño eliminado.')
            except Exception as e:
                messages.error(request, f'Error al eliminar: {e}')

        elif action == 'actualizar_precio':
            precio_val = request.POST.get('precio_por_litro')
            if precio_val:
                precio_config.precio_por_litro = float(precio_val)
                precio_config.save()
                messages.success(request, 'Precio base por litro de leche actualizado.')

        return redirect('ordeno')

    # GET
    registros = RegistroOrdeno.objects.filter(finca_id=finca_activa_id).order_by('-fecha', '-id')
    # Filtrar solo animales hembras en lactancia
    animales = Animal.objects.filter(finca_id=finca_activa_id, sexo='H', estado_produccion='LACTANCIA')
    
    # Filtrar solo rebaños que tengan al menos una vaca en lactancia
    rebaños_todos = Rebaño.objects.filter(finca_id=finca_activa_id)
    rebaños = []
    for r in rebaños_todos:
        count = r.get_animales().filter(sexo='H', estado_produccion='LACTANCIA').count()
        if count > 0:
            r.vacas_lactancia_count = count
            rebaños.append(r)

    # KPIs
    today = datetime.date.today()
    registros_hoy = registros.filter(fecha=today)
    litros_hoy = registros_hoy.aggregate(Sum('litros_leche'))['litros_leche__sum'] or 0.0
    vacas_hoy = registros_hoy.aggregate(Sum('vacas_ordenadas'))['vacas_ordenadas__sum'] or 0
    promedio_hoy = round(float(litros_hoy) / float(vacas_hoy), 2) if vacas_hoy > 0 else 0.0

    inicio_mes = today.replace(day=1)
    registros_mes = registros.filter(fecha__gte=inicio_mes)
    litros_mes = registros_mes.aggregate(Sum('litros_leche'))['litros_leche__sum'] or 0.0
    ingreso_mes = sum((r.litros_leche * r.precio_litro) for r in registros_mes)
    ingreso_mes = round(float(ingreso_mes), 2)

    # Chart data (last 14 days)
    fechas_chart = []
    litros_chart = []
    for i in range(13, -1, -1):
        f = today - datetime.timedelta(days=i)
        f_str = f.strftime('%d/%m')
        l_day = registros.filter(fecha=f).aggregate(Sum('litros_leche'))['litros_leche__sum'] or 0.0
        fechas_chart.append(f_str)
        litros_chart.append(float(l_day))

    context = {
        'user': user,
        'fincas_usuario': fincas_usuario,
        'finca_activa_id': finca_activa_id,
        'finca_activa': finca_activa,
        'registros': registros,
        'rebaños': rebaños,
        'animales': animales,
        'precio_config': precio_config,
        'litros_hoy': litros_hoy,
        'vacas_hoy': vacas_hoy,
        'promedio_hoy': promedio_hoy,
        'litros_mes': litros_mes,
        'ingreso_mes': ingreso_mes,
        'fechas_chart_json': json.dumps(fechas_chart),
        'litros_chart_json': json.dumps(litros_chart),
    }
    return render(request, 'ordeno.html', context)


# ──────────────────────────────────────────────
# ASISTENTE IA – VETI (DeepSeek)
# ──────────────────────────────────────────────

def chat(request):
    """Vista principal del chat con Veti."""
    user_id = request.session.get('user')
    if not user_id:
        return redirect('login')

    usuario = get_object_or_404(User, id=user_id)
    finca_activa_id, fincas_usuario = get_finca_context(request, usuario)

    context = {
        'usuario': usuario,
        'fincas_usuario': fincas_usuario,
        'finca_activa_id': finca_activa_id,
    }
    return render(request, 'chat.html', context)


def build_veti_context(usuario, finca):
    """
    Construye un bloque de contexto con datos reales de la finca activa
    para inyectarlo en el prompt de Veti.
    """
    import datetime
    from django.db.models import Sum

    if not finca:
        return """\n\n--- CONTEXTO DEL USUARIO ---
Usuario: {nombre}\nFinca activa: No seleccionada""".format(nombre=usuario.nombre)

    hoy = datetime.date.today()
    hace_7 = hoy - datetime.timedelta(days=7)
    hace_30 = hoy - datetime.timedelta(days=30)

    lineas = []
    lineas.append(f"\n\n=== CONTEXTO EN TIEMPO REAL DE LA FINCA (usa esta información para responder preguntas específicas) ===")
    lineas.append(f"Usuario: {usuario.nombre}")
    lineas.append(f"Finca activa: {finca.nombre}")
    lineas.append(f"Fecha actual: {hoy.strftime('%d/%m/%Y')}")

    # ── Inventario animal ─────────────────────────
    try:
        animales_vivos = Animal.objects.filter(finca=finca, estado_vida='VIVO')
        total = animales_vivos.count()
        hembras = animales_vivos.filter(sexo='H').count()
        machos  = animales_vivos.filter(sexo='M').count()
        lactancia = animales_vivos.filter(estado_produccion='LACTANCIA').count()
        preñadas  = animales_vivos.filter(estado_gestacion='PREÑADA').count()
        en_tratamiento = animales_vivos.filter(estado_salud='TRATAMIENTO').count()
        lineas.append(f"\n[INVENTARIO ANIMAL]")
        lineas.append(f"- Total animales vivos en finca: {total} (Hembras: {hembras}, Machos: {machos})")
        lineas.append(f"- Vacas en lactancia: {lactancia}")
        lineas.append(f"- Vacas preñadas: {preñadas}")
        lineas.append(f"- Animales en tratamiento sanitario: {en_tratamiento}")

        # Últimos registros
        ultimo_animal = Animal.objects.filter(finca=finca).order_by('-id').first()
        ultima_hembra = Animal.objects.filter(finca=finca, sexo='H').order_by('-id').first()
        if ultimo_animal:
            lineas.append(f"- Último animal registrado en general: ID: {ultimo_animal.id} | {ultimo_animal.codigo} – {ultimo_animal.nombre} (Sexo: {'Macho' if ultimo_animal.sexo == 'M' else 'Hembra'}, Nac: {ultimo_animal.fecha_nacimiento})")
        if ultima_hembra:
            lineas.append(f"- Última hembra registrada: ID: {ultima_hembra.id} | {ultima_hembra.codigo} – {ultima_hembra.nombre} (Nac: {ultima_hembra.fecha_nacimiento})")
        
        # Últimos 5 animales registrados
        ultimos_5 = Animal.objects.filter(finca=finca).order_by('-id')[:5]
        if ultimos_5:
            lineas.append("\n[ÚLTIMOS 5 ANIMALES INGRESADOS AL SISTEMA]")
            for a in ultimos_5:
                sexo_str = "Hembra" if a.sexo == "H" else "Macho"
                lineas.append(f"  • ID: {a.id} | {a.codigo} - {a.nombre} | {sexo_str} | Nac: {a.fecha_nacimiento}")
    except Exception:
        pass

    # ── Producción de leche ───────────────────────
    try:
        ordenos_7d = RegistroOrdeno.objects.filter(finca=finca, fecha__gte=hace_7)
        litros_7d = ordenos_7d.aggregate(total=Sum('litros_leche'))['total'] or 0
        ordenos_30d = RegistroOrdeno.objects.filter(finca=finca, fecha__gte=hace_30)
        litros_30d = ordenos_30d.aggregate(total=Sum('litros_leche'))['total'] or 0
        ultimo_ordeno = RegistroOrdeno.objects.filter(finca=finca).order_by('-fecha', '-created_at').first()
        lineas.append(f"\n[PRODUCCIÓN DE LECHE]")
        lineas.append(f"- Producción últimos 7 días: {float(litros_7d):.1f} litros")
        lineas.append(f"- Producción últimos 30 días: {float(litros_30d):.1f} litros")
        if ultimo_ordeno:
            lineas.append(f"- Último ordeño registrado: {ultimo_ordeno.fecha} – {float(ultimo_ordeno.litros_leche):.1f} L ({ultimo_ordeno.get_turno_display()}, {ultimo_ordeno.vacas_ordenadas} vacas)")
    except Exception:
        pass

    # ── Sanidad ───────────────────────────────────
    try:
        incidentes_abiertos = IncidenteSanitario.objects.filter(
            finca=finca, estado__in=['ATENDIENDO', 'RECUPERACION']
        ).select_related('animal').order_by('-fecha_incidente')[:5]
        lineas.append(f"\n[SANIDAD ACTIVA]")
        if incidentes_abiertos:
            for inc in incidentes_abiertos:
                lineas.append(f"  • {inc.animal.codigo} ({inc.animal.nombre}): {inc.diagnostico} – Estado: {inc.get_estado_display()} ({inc.fecha_incidente})")
        else:
            lineas.append("  • Sin incidentes sanitarios activos.")
    except Exception:
        pass

    # ── Vacunas próximas ──────────────────────────
    try:
        vacunas_pendientes = PlanVacunacion.objects.filter(
            finca=finca, estado='PENDIENTE', fecha_programada__gte=hoy
        ).order_by('fecha_programada')[:3]
        lineas.append(f"\n[VACUNAS PENDIENTES]")
        if vacunas_pendientes:
            for v in vacunas_pendientes:
                lineas.append(f"  • {v.vacuna} – Programada: {v.fecha_programada}")
        else:
            lineas.append("  • Sin vacunas pendientes próximas.")
    except Exception:
        pass

    # ── Finanzas recientes ────────────────────────
    try:
        gastos_30d = GastoFinca.objects.filter(finca=finca, fecha__gte=hace_30).aggregate(total=Sum('monto'))['total'] or 0
        liq_reciente = LiquidacionLeche.objects.filter(finca=finca).order_by('-fecha_fin').first()
        lineas.append(f"\n[FINANZAS]")
        lineas.append(f"- Gastos últimos 30 días: ${float(gastos_30d):.2f}")
        if liq_reciente:
            lineas.append(f"- Última liquidación de leche: {liq_reciente.fecha_inicio} a {liq_reciente.fecha_fin} – {float(liq_reciente.litros_totales):.1f} L – ${float(liq_reciente.monto_total):.2f} [{liq_reciente.get_estado_pago_display()}]")
    except Exception:
        pass

    lineas.append("="*60)
    return "\n".join(lineas)


@csrf_exempt
def api_chat(request):
    """Endpoint que recibe un mensaje y retorna la respuesta de DeepSeek."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    user_id = request.session.get('user')
    if not user_id:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    messages_history = body.get('messages', [])
    if not messages_history:
        return JsonResponse({'error': 'Sin mensajes'}, status=400)

    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'API Key no configurada'}, status=500)

    # ── Cargar datos reales de la finca del usuario ──
    try:
        usuario_obj = User.objects.get(id=user_id)
        finca_id = request.session.get('finca_activa_id')
        finca_obj = None
        if finca_id:
            try:
                finca_obj = Finca.objects.get(id=finca_id, usuario=usuario_obj)
            except Finca.DoesNotExist:
                pass
        finca_context = build_veti_context(usuario_obj, finca_obj)
    except Exception:
        finca_context = ""

    # Instrucciones MCP UI (Componentes Visuales)
    mcp_instructions = """
\n\n=== UI COMPONENTS (MCP UI) ===
Puedes devolver componentes visuales usando etiquetas especiales HTML en tu respuesta. El sistema las renderizará automáticamente.

1. Gráficos de barra: Si te preguntan por producciones, comparativas o estadísticas, o si crees que la respuesta se entendería mejor con un gráfico de barras, genera uno.
Formato estricto (NO uses markdown backticks para el chart):
<chart type="bar" labels="Ene,Feb,Mar" data="10,20,30" title="Producción"></chart>

2. Fichas de animal: Si vas a mostrar o listar animales, genera tarjetas visuales para ellos.
Formato estricto:
<animal-card id="ID_NUMERICO" name="NOMBRE" code="CODIGO"></animal-card>
(IMPORTANTE: En el atributo 'id' debes poner SÓLO el número ID interno de la base de datos (por ejemplo id="4"), NO pongas el código alfanumérico ahí. El código va en el atributo 'code'). Si no tienes el ID exacto en tu contexto, DEBES llamar primero a la herramienta listar_animales para obtenerlo; NUNCA inventes o repitas un ID falso.
"""

    # Leer configuración dinámica desde la BD
    try:
        from app2.models import VetiConfig
        veti_cfg = VetiConfig.get_config()
        if not veti_cfg.activo:
            return JsonResponse({'error': 'El asistente Veti no está disponible en este momento.'}, status=503)
        system_prompt = veti_cfg.system_prompt + finca_context + mcp_instructions
        modelo        = veti_cfg.modelo
        temperatura   = veti_cfg.temperatura
        max_tokens    = veti_cfg.max_tokens
    except Exception:
        # Fallback a valores por defecto si la BD falla
        system_prompt = (
            "Eres Veti, un asistente de inteligencia artificial especializado en ganadería bovina. "
            "Trabajas dentro de Samanito, un sistema de gestión ganadera. "
            "Responde siempre en español, de forma clara, profesional y amigable."
        ) + finca_context + mcp_instructions
        modelo      = "deepseek-chat"
        temperatura = 0.7
        max_tokens  = 1024

    # Detectar si hay contenido multimodal (imágenes) en el historial
    # DeepSeek requiere usar deepseek-flash para soporte de visión.
    has_image = False
    for msg in messages_history:
        if isinstance(msg.get('content'), list):
            for part in msg['content']:
                if part.get('type') == 'image_url':
                    has_image = True
                    break
        if has_image:
            break

    if has_image:
        modelo = 'deepseek-flash'

    tools = [
        {
            "type": "function",
            "function": {
                "name": "listar_animales",
                "description": "Obtiene una lista de animales de la finca según filtros. Úsalo cuando el usuario pida listar, buscar, o preguntar por animales (ej. machos más viejos, vacas secas, etc).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sexo": {"type": "string", "enum": ["M", "H"], "description": "Sexo del animal (M o H)"},
                        "estado_produccion": {"type": "string", "description": "Ej: LACTANCIA, SECA, HORRO, DESCARTE"},
                        "order_by": {"type": "string", "enum": ["edad_asc", "edad_desc", "recientes"], "description": "Ordenamiento: edad_asc (jóvenes), edad_desc (viejos), recientes"},
                        "limit": {"type": "integer", "description": "Cantidad máxima a devolver (max 50, por defecto 10)"}
                    }
                }
            }
        }
    ]

    payload = {
        "model": modelo,
        "messages": [{"role": "system", "content": system_prompt}] + messages_history,
        "temperature": temperatura,
        "max_tokens": max_tokens,
        "tools": tools,
    }

    def make_api_call(payload_data):
        data = json.dumps(payload_data).encode('utf-8')
        req = urllib.request.Request(
            'https://api.deepseek.com/chat/completions',
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))

    try:
        result = make_api_call(payload)
        message = result['choices'][0]['message']

        # Verificar si el modelo decidió llamar a una herramienta
        if message.get('tool_calls'):
            payload["messages"].append(message)
            for tool_call in message['tool_calls']:
                if tool_call['function']['name'] == 'listar_animales':
                    try:
                        args = json.loads(tool_call['function']['arguments'])
                    except:
                        args = {}
                    
                    qs = Animal.objects.filter(finca=finca_obj, estado_vida='VIVO') if finca_obj else Animal.objects.none()
                    
                    if args.get('sexo'):
                        qs = qs.filter(sexo=args['sexo'])
                    if args.get('estado_produccion'):
                        qs = qs.filter(estado_produccion__iexact=args['estado_produccion'])
                    
                    order = args.get('order_by')
                    if order == 'edad_asc':
                        qs = qs.order_by('-fecha_nacimiento')
                    elif order == 'edad_desc':
                        qs = qs.order_by('fecha_nacimiento')
                    elif order == 'recientes':
                        qs = qs.order_by('-id')
                    
                    limit = min(args.get('limit', 15), 50)
                    animales = qs[:limit]
                    
                    res_lines = []
                    for a in animales:
                        res_lines.append(f"ID: {a.id} | Código: {a.codigo} | Nombre: {a.nombre} | Nac: {a.fecha_nacimiento} | Sexo: {a.sexo} | Prod: {a.estado_produccion}")
                    
                    res_str = "\n".join(res_lines) if res_lines else "No se encontraron animales con esos filtros en la base de datos."
                    
                    payload["messages"].append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": res_str
                    })
            
            # Segunda llamada con los resultados de la DB
            result = make_api_call(payload)
            reply = result['choices'][0]['message']['content']
        else:
            reply = message['content']

        return JsonResponse({'reply': reply})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        return JsonResponse({'error': f'Error API: {e.code}', 'detail': error_body}, status=502)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
