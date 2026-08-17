from django.db import models

class User(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128)
    bloqueado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

class Finca(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fincas')
    nombre = models.CharField(max_length=150)
    
    def __str__(self):
        return self.nombre

class Rebaño(models.Model):
    SEXO_CHOICES = [
        ('M', 'Solo Machos'),
        ('H', 'Solo Hembras'),
    ]
    GESTACION_CHOICES = [
        ('VACIA', 'Vacía'),
        ('PREÑADA', 'Preñada'),
    ]
    PRODUCCION_CHOICES = [
        ('LACTANCIA', 'En Lactancia'),
        ('SECA', 'Seca / Horra'),
    ]
    USO_CHOICES = [
        ('REPRODUCTOR', 'Reproductor'),
        ('ENGORDE', 'Engorde'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    # Configuraciones Smart (Dinámicas)
    es_dinamico = models.BooleanField(default=False)
    filtro_sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, null=True, blank=True)
    filtro_edad_min_meses = models.IntegerField(null=True, blank=True, help_text="Edad mínima en meses")
    filtro_edad_max_meses = models.IntegerField(null=True, blank=True, help_text="Edad máxima en meses")
    
    filtro_estado_gestacion = models.CharField(max_length=20, choices=GESTACION_CHOICES, null=True, blank=True)
    filtro_estado_produccion = models.CharField(max_length=20, choices=PRODUCCION_CHOICES, null=True, blank=True)
    filtro_uso_macho = models.CharField(max_length=20, choices=USO_CHOICES, null=True, blank=True)
    
    def __str__(self):
        return self.nombre

    def get_animales(self):
        from .models import Animal
        import datetime
        from django.db.models import Q
        
        if not self.es_dinamico:
            return self.animales_fijos.filter(estado_vida='VIVO')
            
        qs = Animal.objects.filter(finca=self.finca, estado_vida='VIVO')
        
        if self.filtro_sexo:
            qs = qs.filter(sexo=self.filtro_sexo)
            
        today = datetime.date.today()
        if self.filtro_edad_min_meses:
            max_birth_date = today - datetime.timedelta(days=self.filtro_edad_min_meses * 30)
            qs = qs.filter(fecha_nacimiento__lte=max_birth_date)
            
        if self.filtro_edad_max_meses:
            min_birth_date = today - datetime.timedelta(days=self.filtro_edad_max_meses * 30)
            qs = qs.filter(fecha_nacimiento__gte=min_birth_date)
            
        if self.filtro_estado_gestacion:
            qs = qs.filter(estado_gestacion=self.filtro_estado_gestacion)
            
        if self.filtro_estado_produccion:
            qs = qs.filter(estado_produccion=self.filtro_estado_produccion)
            
        if self.filtro_uso_macho:
            qs = qs.filter(uso_macho=self.filtro_uso_macho)
            
        return qs
        
    def count_animales(self):
        return self.get_animales().count()

class Animal(models.Model):
    SEXO_CHOICES = [
        ('M', 'Macho'),
        ('H', 'Hembra'),
    ]
    GESTACION_CHOICES = [
        ('VACIA', 'Vacía'),
        ('PREÑADA', 'Preñada'),
        ('N_A', 'No Aplica'),
    ]
    PRODUCCION_CHOICES = [
        ('LACTANCIA', 'En Lactancia'),
        ('SECA', 'Seca / Horra'),
        ('N_A', 'No Aplica'),
    ]
    USO_CHOICES = [
        ('REPRODUCTOR', 'Reproductor'),
        ('ENGORDE', 'Engorde'),
        ('N_A', 'No Aplica'),
    ]
    ESTADO_VIDA_CHOICES = [
        ('VIVO', 'En Finca'),
        ('VENDIDO', 'Vendido'),
        ('FALLECIDO', 'Fallecido'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, null=True, blank=True)
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100)
    propietario = models.CharField(max_length=150, null=True, blank=True, help_text="Propietario del animal")
    fecha_nacimiento = models.DateField()
    # Si pertenece a un rebaño fijo:
    rebaño = models.ForeignKey(Rebaño, on_delete=models.SET_NULL, null=True, blank=True, related_name='animales_fijos')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    
    # Estados Independientes
    estado_vida = models.CharField(max_length=20, choices=ESTADO_VIDA_CHOICES, default='VIVO')
    estado_gestacion = models.CharField(max_length=20, choices=GESTACION_CHOICES, default='N_A')
    estado_produccion = models.CharField(max_length=20, choices=PRODUCCION_CHOICES, default='N_A')
    uso_macho = models.CharField(max_length=20, choices=USO_CHOICES, default='N_A')
    destetado = models.BooleanField(default=False, help_text="Indica si el animal ya fue destetado")
    
    papa = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='hijos_padre')
    mama = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='hijos_madre')

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class RegistroOrdeno(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField(auto_now_add=True)
    hora_finalizacion = models.TimeField()
    rebaño = models.ForeignKey(Rebaño, on_delete=models.CASCADE, related_name='registros_ordeno')
    cantidad_litros = models.DecimalField(max_digits=8, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.rebaño.nombre} - {self.fecha} - {self.cantidad_litros}L"

class ConfiguracionUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuracion')
    usar_mamanto = models.BooleanField(default=True)
    usar_destete = models.BooleanField(default=True)
    meses_mamanto = models.IntegerField(default=3)
    meses_destete = models.IntegerField(default=7)

    def __str__(self):
        return f"Config de {self.user.nombre}"

class VentaAnimal(models.Model):
    MOTIVO_CHOICES = [
        ('CRIA', 'Para Cría / Vida'),
        ('SACRIFICIO', 'Para Sacrificio (Kilos)'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE)
    animales = models.ManyToManyField(Animal, related_name='ventas_info')
    fecha_venta = models.DateField(auto_now_add=True)
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    kilos = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    precio_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    comprador = models.CharField(max_length=150, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Venta - {self.motivo} ({self.fecha_venta})"

class PlanVacunacion(models.Model):
    ESTADO_VACUNA_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE)
    vacuna = models.CharField(max_length=150)
    fecha_programada = models.DateField()
    fecha_aplicacion = models.DateField(null=True, blank=True)
    # Si rebaño es null, se asume que es para toda la población
    rebaño = models.ForeignKey(Rebaño, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_VACUNA_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.vacuna} - {self.fecha_programada}"

class IncidenteSanitario(models.Model):
    ESTADO_INCIDENTE_CHOICES = [
        ('ACTIVO', 'Activo / En Tratamiento'),
        ('RESUELTO', 'Resuelto / Curado'),
    ]
    TIPO_INCIDENTE_CHOICES = [
        ('ENFERMEDAD', 'Enfermedad'),
        ('LESION', 'Lesión / Herida'),
        ('PARTO', 'Complicación de Parto'),
        ('OTRO', 'Otro'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='incidentes')
    fecha_incidente = models.DateField()
    tipo = models.CharField(max_length=50, choices=TIPO_INCIDENTE_CHOICES)
    diagnostico = models.CharField(max_length=200)
    tratamiento = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_INCIDENTE_CHOICES, default='ACTIVO')
    
    def __str__(self):
        return f"{self.animal.codigo} - {self.diagnostico}"

class GastoFinca(models.Model):
    CATEGORIA_CHOICES = [
        ('ALIMENTO', 'Alimento / Suplementos'),
        ('VETERINARIA', 'Medicina / Veterinaria'),
        ('PERSONAL', 'Sueldos / Personal'),
        ('SERVICIOS', 'Servicios Públicos (Luz, Agua)'),
        ('MANTENIMIENTO', 'Mantenimiento / Infraestructura'),
        ('OTRO', 'Otros Gastos'),
    ]
    TIPO_CHOICES = [
        ('FIJO', 'Gasto Fijo'),
        ('VARIABLE', 'Gasto Variable'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE)
    fecha = models.DateField()
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    concepto = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='VARIABLE')
    
    def __str__(self):
        return f"{self.concepto} - {self.monto}"

class PrecioLecheConfig(models.Model):
    finca = models.OneToOneField(Finca, on_delete=models.CASCADE, related_name='precio_leche_config')
    precio_por_litro = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Precio Leche Finca {self.finca.nombre}: {self.precio_por_litro}"

class LogActividad(models.Model):
    ACCION_CHOICES = [
        ('CREACION', 'Creación / Registro'),
        ('MODIFICACION', 'Modificación / Actualización'),
        ('ELIMINACION', 'Eliminación'),
        ('LOGIN', 'Inicio de Sesión'),
        ('IMPORTACION', 'Importación Masiva'),
        ('CONFIGURACION', 'Cambio de Configuración'),
    ]
    
    MODULO_CHOICES = [
        ('ANIMALES', 'Animales'),
        ('REBAÑOS', 'Rebaños'),
        ('ORDEÑO', 'Control de Ordeño'),
        ('SANIDAD', 'Sanidad'),
        ('VENTAS', 'Ventas'),
        ('FINANZAS', 'Finanzas'),
        ('SEGURIDAD', 'Seguridad / Acceso'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=50, choices=ACCION_CHOICES)
    modulo = models.CharField(max_length=50, choices=MODULO_CHOICES)
    descripcion = models.TextField()
    
    def __str__(self):
        return f"{self.fecha_hora.strftime('%d/%m/%Y %H:%M')} | {self.usuario.nombre} | {self.modulo} - {self.accion}"