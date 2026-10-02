from django.urls import path
from . import views

urlpatterns = [
    path('login_admin/', views.login_admin, name='login_admin'),
    path('logout_admin/', views.logout_admin, name='logout_admin'),
    path('control_admin/', views.control_admin, name='control_admin'),
    path('clientes/', views.admin_clientes, name='admin_clientes'),
    path('finanzas/', views.admin_finanzas, name='admin_finanzas'),
    path('planes/', views.admin_planes, name='admin_planes'),
    path('logs/', views.admin_logs, name='admin_logs'),
    path('toggle_bloqueo/<int:user_id>/', views.toggle_bloqueo, name='toggle_bloqueo'),
    path('editar_suscripcion/', views.editar_suscripcion, name='editar_suscripcion'),
    path('guardar_plan_saas/', views.guardar_plan_saas, name='guardar_plan_saas'),
    path('eliminar_plan_saas/<int:plan_id>/', views.eliminar_plan_saas, name='eliminar_plan_saas'),
    path('registrar_pago_saas/', views.registrar_pago_saas, name='registrar_pago_saas'),
    path('conciliacion/', views.admin_conciliacion, name='admin_conciliacion'),
    path('procesar_conciliacion/', views.procesar_conciliacion, name='procesar_conciliacion'),
    path('metodos_pago/', views.admin_metodos_pago, name='admin_metodos_pago'),
    path('guardar_metodo_pago/', views.guardar_metodo_pago, name='guardar_metodo_pago'),

    # Veti IA
    path('veti/', views.admin_veti, name='admin_veti'),
    path('veti/guardar/', views.guardar_veti_config, name='guardar_veti_config'),
]