from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('llms.txt', views.llms_txt, name='llms_txt'),
    path('login/', views.login, name='login'),
    path('test-email/', views.test_email_view, name='test_email'),
    path('signup/', views.signup, name='signup'),
    path('cambiar_finca/', views.cambiar_finca, name='cambiar_finca'),
    path('crear_finca/', views.crear_finca, name='crear_finca'),
    path('control/', views.control, name='control'),
    path('registro/', views.registro, name='registro'),
    path('rebano/', views.rebano, name='rebaño'),
    path('datos/', views.datos_animales, name='datos_animales'),
    path('datos/exportar/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
    path('datos/plantilla/', views.descargar_plantilla, name='descargar_plantilla'),
    path('crianza/', views.crianza, name='crianza'),
    path('ventas/', views.ventas, name='ventas'),
    path('sanidad/vacunacion/', views.vacunacion, name='vacunacion'),
    path('sanidad/incidentes/', views.incidentes, name='incidentes'),
    path('finanzas/', views.finanzas, name='finanzas'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('perfil/', views.perfil, name='perfil'),
    path('engorde/', views.engorde, name='engorde'),
    path('manga/', views.manga_manejo, name='manga'),
    path('estructura-costos/', views.estructura_costos, name='estructura_costos'),
    path('reproduccion/', views.reproduccion, name='reproduccion'),
    path('ordeno/', views.ordeno, name='ordeno'),
    path('potreros/', views.potreros, name='potreros'),
    path('inventario/', views.inventario, name='inventario'),
    path('empleados/', views.empleados, name='empleados'),
    path('genetica/', views.genetica, name='genetica'),
    path('hoja_vida/<int:animal_id>/', views.hoja_vida, name='hoja_vida'),
    
    # Endpoints API
    path('api/buscar_padre/', views.api_buscar_padre, name='api_buscar_padre'),
    path('api/buscar_madre/', views.api_buscar_madre, name='api_buscar_madre'),
    path('api/buscar_vaca_seca/', views.api_buscar_vaca_seca, name='api_buscar_vaca_seca'),
    path('api/buscar_animal_vivo/', views.api_buscar_animal_vivo, name='api_buscar_animal_vivo'),
    path('api/reportes/', views.api_reportes, name='api_reportes'),

    # WebAuthn Biometría (Huella Digital)
    path('api/webauthn/register/options/', views.api_webauthn_register_options, name='webauthn_register_options'),
    path('api/webauthn/register/verify/', views.api_webauthn_register_verify, name='webauthn_register_verify'),
    path('api/webauthn/login/options/', views.api_webauthn_login_options, name='webauthn_login_options'),
    path('api/webauthn/login/verify/', views.api_webauthn_login_verify, name='webauthn_login_verify'),
    path('api/webauthn/delete/<int:cred_id>/', views.api_webauthn_delete, name='webauthn_delete'),

    # Asistente IA – Veti
    path('asistente/', views.chat, name='chat'),
    path('api/chat/', views.api_chat, name='api_chat'),
]