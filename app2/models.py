from django.db import models

class User_admin(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    bloqueado = models.BooleanField(default=False)
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.nombre

class Suscripcion(models.Model):
    PLAN_CHOICES = [
        ('TRIAL', 'Prueba (Trial)'),
        ('BASICO', 'Básico'),
        ('PLUS', 'Plus'),
        ('PREMIUM', 'Premium'),
        ('VIP', 'VIP'),
    ]
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('VENCIDA', 'Vencida'),
        ('SUSPENDIDA', 'Suspendida'),
    ]
    
    usuario = models.OneToOneField('app1.User', on_delete=models.CASCADE, related_name='suscripcion_saas')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='TRIAL')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVA')
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Suscripción de {self.usuario.nombre} - {self.plan}"
