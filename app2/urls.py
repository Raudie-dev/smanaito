from django.urls import path
from . import views

urlpatterns = [
    path('login_admin/', views.login_admin, name='login_admin'),
    path('control_admin/', views.control_admin, name='control_admin'),
    path('toggle_bloqueo/<int:user_id>/', views.toggle_bloqueo, name='toggle_bloqueo'),
    path('editar_suscripcion/', views.editar_suscripcion, name='editar_suscripcion'),

]