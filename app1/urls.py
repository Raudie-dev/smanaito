from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('cambiar_finca/', views.cambiar_finca, name='cambiar_finca'),
    path('crear_finca/', views.crear_finca, name='crear_finca'),
    path('control/', views.control, name='control'),
    path('registro/', views.registro, name='registro'),
    path('rebaño/', views.rebaño, name='rebaño'),
    path('datos/', views.datos_animales, name='datos_animales'),
    path('datos/exportar/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
    path('datos/plantilla/', views.descargar_plantilla, name='descargar_plantilla'),
    path('ordeño/', views.ordeño, name='ordeño'),
    path('crianza/', views.crianza, name='crianza'),
    path('ventas/', views.ventas, name='ventas'),
    path('sanidad/vacunacion/', views.vacunacion, name='vacunacion'),
    path('sanidad/incidentes/', views.incidentes, name='incidentes'),
    path('finanzas/', views.finanzas, name='finanzas'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('perfil/', views.perfil, name='perfil'),
    path('engorde/', views.engorde, name='engorde'),
    path('manga/', views.manga_manejo, name='manga'),
    path('alimentacion/', views.alimentacion_avanzada, name='alimentacion'),
    
    # Endpoints API
    path('api/buscar_padre/', views.api_buscar_padre, name='api_buscar_padre'),
    path('api/buscar_madre/', views.api_buscar_madre, name='api_buscar_madre'),
    path('api/buscar_vaca_seca/', views.api_buscar_vaca_seca, name='api_buscar_vaca_seca'),
    path('api/buscar_animal_vivo/', views.api_buscar_animal_vivo, name='api_buscar_animal_vivo'),
    path('api/reportes/', views.api_reportes, name='api_reportes'),
]