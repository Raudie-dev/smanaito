from django.db import models

class User_admin(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    bloqueado = models.BooleanField(default=False)
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.nombre

class PlanSaaS(models.Model):
    codigo = models.CharField(max_length=50, unique=True, help_text="Ej: BASICO, PLUS, PREMIUM")
    nombre = models.CharField(max_length=150)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    badge = models.CharField(max_length=50, default="Popular")
    descripcion = models.TextField(blank=True, null=True)
    limite_fincas = models.IntegerField(default=1)
    limite_animales = models.IntegerField(default=100)
    caracteristicas_list = models.TextField(help_text="Separadas por salto de línea", blank=True, null=True)
    destacado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Módulos permitidos
    mod_ordeno = models.BooleanField(default=True, verbose_name="Módulo de Ordeño")
    mod_reproduccion = models.BooleanField(default=True, verbose_name="Módulo de Reproducción")
    mod_genetica = models.BooleanField(default=True, verbose_name="Módulo de Genética")
    mod_engorde = models.BooleanField(default=True, verbose_name="Módulo de Engorde")
    mod_crianza = models.BooleanField(default=True, verbose_name="Módulo de Crianza")
    mod_potreros = models.BooleanField(default=True, verbose_name="Módulo de Potreros")
    mod_vacunacion = models.BooleanField(default=True, verbose_name="Módulo de Vacunación")
    mod_incidentes = models.BooleanField(default=True, verbose_name="Módulo de Incidentes")
    mod_empleados = models.BooleanField(default=True, verbose_name="Módulo de Empleados")
    mod_inventario = models.BooleanField(default=True, verbose_name="Módulo de Inventario")
    mod_finanzas = models.BooleanField(default=True, verbose_name="Módulo de Finanzas")
    mod_estructura_costos = models.BooleanField(default=True, verbose_name="Módulo de Estructura de Costos")
    mod_auditoria = models.BooleanField(default=True, verbose_name="Módulo de Auditoría")

    def __str__(self):
        return f"{self.nombre} (${self.precio_mensual}/mes)"

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
    plan_obj = models.ForeignKey(PlanSaaS, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVA')
    monto_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Suscripción de {self.usuario.nombre} - {self.plan}"

class PagoSuscripcion(models.Model):
    ESTADO_PAGO = [
        ('AL_DIA', 'Al Día'),
        ('PENDIENTE', 'Pendiente / Debe'),
        ('RECHAZADO', 'Rechazado'),
    ]
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()
    periodo_correspondiente = models.CharField(max_length=50, help_text="Ej: Septiembre 2026")
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO, default='AL_DIA')
    comprobante = models.CharField(max_length=100, blank=True, null=True)
    registrado_por = models.ForeignKey(User_admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.suscripcion.usuario.nombre} - ${self.monto} ({self.estado})"

class LogSistemaAdmin(models.Model):
    admin_user = models.ForeignKey(User_admin, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=[('SISTEMA', 'Sistema'), ('FINANZAS', 'Finanzas'), ('CLIENTES', 'Clientes'), ('PLANES', 'Planes')])
    descripcion = models.TextField()
    ip = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.tipo}] {self.descripcion}"


# ── Configuración global de Veti IA ──────────────────────
VETI_DEFAULT_PROMPT = (
    "Eres Veti, un asistente de inteligencia artificial especializado en ganadería bovina. "
    "Trabajas dentro de Samanito, un sistema de gestión ganadera. "
    "Puedes ayudar con temas de manejo animal, reproducción, sanidad, nutrición, "
    "registros zootécnicos, finanzas de finca, ordeño, engorde y todo lo relacionado "
    "con la producción bovina. Responde siempre en español, de forma clara, profesional "
    "y amigable. Si el usuario hace preguntas no relacionadas con ganadería, puedes "
    "responderlas brevemente pero recuérdale tu especialidad."
)

class VetiConfig(models.Model):
    """Singleton: configuración global del asistente Veti."""
    system_prompt = models.TextField(
        verbose_name="Prompt del sistema",
        default=VETI_DEFAULT_PROMPT,
        help_text="Instrucciones base que definen el comportamiento de Veti."
    )
    modelo = models.CharField(
        max_length=60,
        default="deepseek-chat",
        verbose_name="Modelo DeepSeek",
        help_text="Nombre del modelo a usar (ej: deepseek-chat, deepseek-reasoner)."
    )
    temperatura = models.FloatField(
        default=0.7,
        verbose_name="Temperatura (0.0 – 2.0)",
        help_text="Controla la creatividad. 0 = preciso, 2 = muy creativo."
    )
    max_tokens = models.IntegerField(
        default=1024,
        verbose_name="Máx. tokens de respuesta",
        help_text="Límite de longitud de cada respuesta."
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Veti habilitado",
        help_text="Si está desactivado, el asistente no estará disponible para los usuarios."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración Veti"

    def __str__(self):
        return f"VetiConfig (modelo={self.modelo}, temp={self.temperatura})"

    @classmethod
    def get_config(cls):
        """Devuelve la config singleton, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
