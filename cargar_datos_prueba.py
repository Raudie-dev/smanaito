"""
Script de carga de datos de prueba para el usuario Juan.
Ejecutar con:
    DJANGO_SETTINGS_MODULE=proyecto.settings python cargar_datos_prueba.py
"""

import os
import sys
import django
import datetime
import json
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from django.utils import timezone
from app1.models import (
    User, Finca, Rebaño, Animal, ConfiguracionUsuario,
    VentaAnimal, PlanVacunacion, IncidenteSanitario,
    LiquidacionLeche, GastoFinca, GastoRecurrente, PrecioLecheConfig,
    LogActividad, Corral, PesajeAnimal, RegistroAlimentacion, TareaDiaria,
    ProtocoloTratamiento, ProtocoloAlimentacion,
    ServicioReproductivo, DiagnosticoGestacion, RegistroParto,
    Potrero, RotacionPotrero,
    ArticuloInventario, MovimientoInventario,
    CatalogoSemen, Empleado, PagoNomina, RegistroOrdeno
)

TODAY = datetime.date.today()

def dias_atras(n):
    return TODAY - datetime.timedelta(days=n)

def meses_atras(n):
    return TODAY - datetime.timedelta(days=n * 30)

# ─────────────────────────────────────────────
print("Buscando usuario Juan...")
# ─────────────────────────────────────────────
usuario = User.objects.get(nombre='Juan')
print(f"   OK Usuario: {usuario.nombre} (ID={usuario.id})")

# ─────────────────────────────────────────────
print("\nCreando Finca...")
# ─────────────────────────────────────────────
finca, _ = Finca.objects.get_or_create(
    usuario=usuario,
    nombre='Finca La Esperanza',
)
print(f"   OK Finca: {finca.nombre} (ID={finca.id})")

ConfiguracionUsuario.objects.get_or_create(
    user=usuario,
    defaults={'usar_mamanto': True, 'usar_destete': True, 'meses_mamanto': 3, 'meses_destete': 7}
)
PrecioLecheConfig.objects.update_or_create(
    finca=finca,
    defaults={'precio_por_litro': 0.45}
)

# ─────────────────────────────────────────────
print("\nCreando Corrales...")
# ─────────────────────────────────────────────
corrales_data = [
    ('Corral de Vacas en Produccion', 60, False),
    ('Corral de Vacas Secas',         30, False),
    ('Corral de Mautes',              50, False),
    ('Corral de Novillas',            40, False),
    ('Corral de Toros',               10, False),
    ('Enfermeria / Hospital',         8,  True),
]
corrales = {}
for nombre, cap, hosp in corrales_data:
    c, _ = Corral.objects.get_or_create(
        finca=finca, nombre=nombre,
        defaults={'capacidad': cap, 'es_hospital': hosp}
    )
    corrales[nombre] = c
print(f"   OK {len(corrales)} corrales creados")

# ─────────────────────────────────────────────
print("\nCreando Rebanos...")
# ─────────────────────────────────────────────
rebano_vacas_prod, _ = Rebaño.objects.get_or_create(
    finca=finca, nombre='Vacas en Produccion',
    defaults={
        'usuario': usuario,
        'descripcion': 'Vacas actualmente en ordeno y lactancia.',
        'es_dinamico': True,
        'filtro_sexo': 'H',
        'filtro_estado_produccion': 'LACTANCIA',
    }
)
rebano_vacas_secas, _ = Rebaño.objects.get_or_create(
    finca=finca, nombre='Vacas Secas / Horras',
    defaults={
        'usuario': usuario,
        'descripcion': 'Vacas en periodo de descanso productivo.',
        'es_dinamico': True,
        'filtro_sexo': 'H',
        'filtro_estado_produccion': 'SECA',
    }
)
rebano_mautes, _ = Rebaño.objects.get_or_create(
    finca=finca, nombre='Mautes',
    defaults={
        'usuario': usuario,
        'descripcion': 'Machos jovenes entre 4 y 18 meses.',
        'es_dinamico': True,
        'filtro_sexo': 'M',
        'filtro_edad_min_meses': 4,
        'filtro_edad_max_meses': 18,
    }
)
rebano_novillas, _ = Rebaño.objects.get_or_create(
    finca=finca, nombre='Novillas',
    defaults={
        'usuario': usuario,
        'descripcion': 'Hembras jovenes de 6 a 30 meses.',
        'es_dinamico': True,
        'filtro_sexo': 'H',
        'filtro_edad_min_meses': 6,
        'filtro_edad_max_meses': 30,
    }
)
rebano_toros, _ = Rebaño.objects.get_or_create(
    finca=finca, nombre='Toros Reproductores',
    defaults={
        'usuario': usuario,
        'descripcion': 'Machos adultos para monta natural.',
        'es_dinamico': True,
        'filtro_sexo': 'M',
        'filtro_edad_min_meses': 24,
        'filtro_uso_macho': 'REPRODUCTOR',
    }
)
print(f"   OK 5 rebanos configurados")

# ─────────────────────────────────────────────
print("\nCreando Animales...")
# ─────────────────────────────────────────────

toros_data = [
    ('TOR-001', 'Neptuno',  meses_atras(60), 'Brahman Puro',  'REPRODUCTOR'),
    ('TOR-002', 'Galeon',   meses_atras(48), '3/4 Brahman',   'REPRODUCTOR'),
]
toros = []
for codigo, nombre, fnac, raza, uso in toros_data:
    a, _ = Animal.objects.get_or_create(
        finca=finca, codigo=codigo,
        defaults={
            'usuario': usuario, 'nombre': nombre,
            'fecha_nacimiento': fnac, 'composicion_racial': raza,
            'sexo': 'M', 'estado_vida': 'VIVO',
            'estado_gestacion': 'N_A', 'estado_produccion': 'N_A',
            'uso_macho': uso, 'estado_salud': 'SANO', 'destetado': True,
            'corral': corrales['Corral de Toros'],
        }
    )
    toros.append(a)

vacas_prod_data = [
    ('VAC-001', 'Rosalinda',  meses_atras(54), '5/8 Holstein 3/8 Gyr',    'VACIA',   'LACTANCIA'),
    ('VAC-002', 'Mariposa',   meses_atras(60), '3/4 Holstein',            'PREÑADA', 'LACTANCIA'),
    ('VAC-003', 'Esmeralda',  meses_atras(48), '7/8 Holstein',            'VACIA',   'LACTANCIA'),
    ('VAC-004', 'Candelaria', meses_atras(66), 'Holstein Puro',           'PREÑADA', 'LACTANCIA'),
    ('VAC-005', 'Palmera',    meses_atras(42), '5/8 Holstein 3/8 Pardo',  'VACIA',   'LACTANCIA'),
    ('VAC-006', 'Lucero',     meses_atras(36), '3/4 Gyr',                 'VACIA',   'LACTANCIA'),
    ('VAC-007', 'Princesa',   meses_atras(50), '5/8 Holstein',            'PREÑADA', 'LACTANCIA'),
    ('VAC-008', 'Estrella',   meses_atras(72), 'Holstein Puro',           'VACIA',   'LACTANCIA'),
    ('VAC-009', 'Vendaval',   meses_atras(44), '3/4 Brahman 1/4 Holstein','VACIA',   'LACTANCIA'),
    ('VAC-010', 'Florinda',   meses_atras(58), '5/8 Holstein 3/8 Gyr',   'PREÑADA', 'LACTANCIA'),
    ('VAC-011', 'Girasol',    meses_atras(40), '7/8 Holstein',            'VACIA',   'LACTANCIA'),
    ('VAC-012', 'Tormenta',   meses_atras(64), 'Holstein Puro',           'VACIA',   'LACTANCIA'),
]
vacas_prod = []
for codigo, nombre, fnac, raza, gest, prod in vacas_prod_data:
    a, _ = Animal.objects.get_or_create(
        finca=finca, codigo=codigo,
        defaults={
            'usuario': usuario, 'nombre': nombre,
            'fecha_nacimiento': fnac, 'composicion_racial': raza,
            'sexo': 'H', 'estado_vida': 'VIVO',
            'estado_gestacion': gest, 'estado_produccion': prod,
            'uso_macho': 'N_A', 'estado_salud': 'SANO', 'destetado': True,
            'corral': corrales['Corral de Vacas en Produccion'],
        }
    )
    vacas_prod.append(a)

vacas_secas_data = [
    ('SEC-001', 'Caridad',  meses_atras(80), 'Holstein Puro',         'PREÑADA'),
    ('SEC-002', 'Nobleza',  meses_atras(62), '5/8 Holstein 3/8 Gyr', 'PREÑADA'),
    ('SEC-003', 'Volcana',  meses_atras(74), '3/4 Holstein',          'VACIA'),
    ('SEC-004', 'Serenata', meses_atras(55), '7/8 Holstein',          'PREÑADA'),
]
vacas_secas = []
for codigo, nombre, fnac, raza, gest in vacas_secas_data:
    a, _ = Animal.objects.get_or_create(
        finca=finca, codigo=codigo,
        defaults={
            'usuario': usuario, 'nombre': nombre,
            'fecha_nacimiento': fnac, 'composicion_racial': raza,
            'sexo': 'H', 'estado_vida': 'VIVO',
            'estado_gestacion': gest, 'estado_produccion': 'SECA',
            'uso_macho': 'N_A', 'estado_salud': 'SANO', 'destetado': True,
            'corral': corrales['Corral de Vacas Secas'],
        }
    )
    vacas_secas.append(a)

novillas_data = [
    ('NOV-001', 'Amanecer', meses_atras(22), '5/8 Holstein'),
    ('NOV-002', 'Brisa',    meses_atras(18), '7/8 Holstein'),
    ('NOV-003', 'Celeste',  meses_atras(14), '3/4 Gyr'),
    ('NOV-004', 'Diana',    meses_atras(20), 'Holstein Puro'),
    ('NOV-005', 'Eufemia',  meses_atras(16), '5/8 Holstein'),
    ('NOV-006', 'Fantasia', meses_atras(26), '3/4 Holstein'),
]
novillas = []
for codigo, nombre, fnac, raza in novillas_data:
    a, _ = Animal.objects.get_or_create(
        finca=finca, codigo=codigo,
        defaults={
            'usuario': usuario, 'nombre': nombre,
            'fecha_nacimiento': fnac, 'composicion_racial': raza,
            'sexo': 'H', 'estado_vida': 'VIVO',
            'estado_gestacion': 'VACIA', 'estado_produccion': 'N_A',
            'uso_macho': 'N_A', 'estado_salud': 'SANO', 'destetado': True,
            'corral': corrales['Corral de Novillas'],
        }
    )
    novillas.append(a)

mautes_data = [
    ('MAU-001', 'Potro',     meses_atras(10), 'Brahman Puro'),
    ('MAU-002', 'Gladiador', meses_atras(8),  'Brahman Puro'),
    ('MAU-003', 'Valiente',  meses_atras(12), '5/8 Brahman'),
    ('MAU-004', 'Ciclon',    meses_atras(6),  '3/4 Brahman'),
    ('MAU-005', 'Rayo',      meses_atras(14), 'Brahman Puro'),
    ('MAU-006', 'Trueno',    meses_atras(9),  '5/8 Brahman'),
]
mautes = []
for codigo, nombre, fnac, raza in mautes_data:
    a, _ = Animal.objects.get_or_create(
        finca=finca, codigo=codigo,
        defaults={
            'usuario': usuario, 'nombre': nombre,
            'fecha_nacimiento': fnac, 'composicion_racial': raza,
            'sexo': 'M', 'estado_vida': 'VIVO',
            'estado_gestacion': 'N_A', 'estado_produccion': 'N_A',
            'uso_macho': 'ENGORDE', 'estado_salud': 'SANO', 'destetado': True,
            'corral': corrales['Corral de Mautes'],
        }
    )
    mautes.append(a)

crias_data = [
    ('CRI-001', 'Pepito',  dias_atras(45), 'Holstein Cruzado', 'M'),
    ('CRI-002', 'Juanita', dias_atras(30), '5/8 Holstein',     'H'),
    ('CRI-003', 'Bichito', dias_atras(60), 'Brahman Cruzado',  'M'),
    ('CRI-004', 'Lunita',  dias_atras(20), '7/8 Holstein',     'H'),
]
crias = []
for codigo, nombre, fnac, raza, sexo in crias_data:
    a, _ = Animal.objects.get_or_create(
        finca=finca, codigo=codigo,
        defaults={
            'usuario': usuario, 'nombre': nombre,
            'fecha_nacimiento': fnac, 'composicion_racial': raza,
            'sexo': sexo, 'estado_vida': 'VIVO',
            'estado_gestacion': 'N_A', 'estado_produccion': 'N_A',
            'uso_macho': 'N_A', 'estado_salud': 'SANO', 'destetado': False,
        }
    )
    crias.append(a)

vaca_enferma, _ = Animal.objects.get_or_create(
    finca=finca, codigo='VAC-013',
    defaults={
        'usuario': usuario, 'nombre': 'Esperanza',
        'fecha_nacimiento': meses_atras(50),
        'composicion_racial': '5/8 Holstein 3/8 Gyr',
        'sexo': 'H', 'estado_vida': 'VIVO',
        'estado_gestacion': 'VACIA', 'estado_produccion': 'SECA',
        'uso_macho': 'N_A', 'estado_salud': 'TRATAMIENTO', 'destetado': True,
        'corral': corrales['Enfermeria / Hospital'],
    }
)

total_animales = len(toros) + len(vacas_prod) + len(vacas_secas) + len(novillas) + len(mautes) + len(crias) + 1
print(f"   OK {total_animales} animales creados")

# ─────────────────────────────────────────────
print("\nPesajes de engorde y novillas...")
# ─────────────────────────────────────────────
peso_base = {'MAU-001': 120, 'MAU-002': 95, 'MAU-003': 145, 'MAU-004': 70, 'MAU-005': 160, 'MAU-006': 105}
for m in mautes:
    base = peso_base.get(m.codigo, 100)
    for i in range(3, 0, -1):
        PesajeAnimal.objects.get_or_create(
            animal=m, fecha=dias_atras(i * 30),
            defaults={'peso_kg': base - (i * random.randint(12, 18))}
        )
    PesajeAnimal.objects.get_or_create(animal=m, fecha=TODAY, defaults={'peso_kg': base})

for n in novillas:
    PesajeAnimal.objects.get_or_create(animal=n, fecha=dias_atras(60), defaults={'peso_kg': random.randint(200, 290)})
    PesajeAnimal.objects.get_or_create(animal=n, fecha=dias_atras(30), defaults={'peso_kg': random.randint(230, 310)})
    PesajeAnimal.objects.get_or_create(animal=n, fecha=TODAY,          defaults={'peso_kg': random.randint(260, 340)})
print("   OK Pesajes registrados")

# ─────────────────────────────────────────────
print("\nInventario...")
# ─────────────────────────────────────────────
inventario_data = [
    ('Ivermectina 1%',        'MEDICAMENTO', 'LT',    8.5,  2.0),
    ('Oxitetraciclina LA',    'MEDICAMENTO', 'LT',    4.0,  1.0),
    ('Vitaminas ADE',         'MEDICAMENTO', 'LT',    6.0,  2.0),
    ('Meloxicam 5%',          'MEDICAMENTO', 'LT',    2.5,  0.5),
    ('Vacuna Aftosa',         'MEDICAMENTO', 'DOSIS', 120,  20),
    ('Vacuna Brucelosis',     'MEDICAMENTO', 'DOSIS', 60,   10),
    ('Vacuna Botulismo',      'MEDICAMENTO', 'DOSIS', 80,   15),
    ('Melaza',                'ALIMENTO',    'KG',    500,  50),
    ('Urea Pecuaria',         'ALIMENTO',    'KG',    200,  30),
    ('Sal Mineralizada',      'ALIMENTO',    'KG',    300,  40),
    ('Concentrado Inicio',    'ALIMENTO',    'KG',    400,  50),
    ('Concentrado Lactante',  'ALIMENTO',    'KG',    350,  50),
    ('Jeringa 10ml',          'HERRAMIENTA', 'UNIDAD',50,   10),
    ('Agujas 18G',            'HERRAMIENTA', 'UNIDAD',200,  20),
    ('Caravanas Amarillas',   'HERRAMIENTA', 'UNIDAD',100,  10),
]
articulos = {}
for nombre, cat, unidad, stock, alerta in inventario_data:
    art, _ = ArticuloInventario.objects.get_or_create(
        finca=finca, nombre=nombre,
        defaults={'categoria': cat, 'unidad_medida': unidad, 'cantidad_actual': stock, 'alerta_minimo': alerta}
    )
    MovimientoInventario.objects.get_or_create(
        finca=finca, articulo=art, tipo='ENTRADA', cantidad=stock,
        defaults={'costo_total': stock * random.uniform(1, 5), 'observaciones': 'Stock inicial'}
    )
    articulos[nombre] = art
print(f"   OK {len(articulos)} articulos de inventario")

# ─────────────────────────────────────────────
print("\nPotreros...")
# ─────────────────────────────────────────────
potreros_data = [
    ('Potrero 1 - El Mata Palo', 12.5, 'Brachiaria brizantha',  'OCUPADO'),
    ('Potrero 2 - La Palma',     8.0,  'Brachiaria humidícola', 'DESCANSO'),
    ('Potrero 3 - El Jobo',      15.0, 'Pasto Guinea',          'DESCANSO'),
    ('Potrero 4 - La Laja',      10.0, 'Pasto Bermuda',         'OCUPADO'),
    ('Potrero 5 - El Cerro',     20.0, 'Brachiaria brizantha',  'DESCANSO'),
    ('Potrero 6 - La Quebrada',  7.5,  'Pasto Estrella',        'MANTENIMIENTO'),
]
potreros = []
for nombre, ha, pasto, estado in potreros_data:
    p, _ = Potrero.objects.get_or_create(
        finca=finca, nombre=nombre,
        defaults={'hectareas': ha, 'tipo_pasto': pasto, 'estado': estado}
    )
    potreros.append(p)

potreros[0].rebaño = rebano_vacas_prod; potreros[0].save()
potreros[3].rebaño = rebano_mautes;     potreros[3].save()

for p in potreros[:4]:
    RotacionPotrero.objects.get_or_create(
        finca=finca, potrero=p, rebaño=rebano_vacas_prod, fecha_entrada=dias_atras(60),
        defaults={'fecha_salida': dias_atras(45), 'observaciones': 'Rotacion normal'}
    )
print(f"   OK {len(potreros)} potreros creados")

# ─────────────────────────────────────────────
print("\nSanidad...")
# ─────────────────────────────────────────────
vacunaciones_data = [
    ('Vacuna Aftosa',               dias_atras(90),                            dias_atras(88),  'COMPLETADO', None),
    ('Vacuna Brucelosis',           dias_atras(120),                           dias_atras(119), 'COMPLETADO', rebano_novillas),
    ('Vacuna Botulismo',            dias_atras(60),                            dias_atras(58),  'COMPLETADO', None),
    ('Vacuna Aftosa - Proxima',     TODAY + datetime.timedelta(days=90),       None,            'PENDIENTE',  None),
    ('Desparasitacion Ivermectina', dias_atras(30),                            dias_atras(29),  'COMPLETADO', None),
    ('Desparasitacion - Proxima',   TODAY + datetime.timedelta(days=60),       None,            'PENDIENTE',  None),
]
for vacuna, fecha_prog, fecha_aplic, estado, rebano in vacunaciones_data:
    PlanVacunacion.objects.get_or_create(
        finca=finca, vacuna=vacuna, fecha_programada=fecha_prog,
        defaults={
            'usuario': usuario, 'fecha_aplicacion': fecha_aplic,
            'rebaño': rebano, 'estado': estado,
            'dosis_por_animal': 2.0, 'observaciones': 'Programa sanitario anual',
        }
    )

incidentes_data = [
    (vacas_prod[2], dias_atras(45), 'ENFERMEDAD', 'Mastitis Clinica',       'Antibiotico intramamario 3 dias', 'RESUELTO'),
    (vaca_enferma,  dias_atras(5),  'ENFERMEDAD', 'Neumonia',               'Oxitetraciclina LA 1ml/10kg',    'ACTIVO'),
    (mautes[1],     dias_atras(20), 'LESION',     'Herida por alambre',     'Curacion diaria + antibiotico',  'RESUELTO'),
    (vacas_prod[7], dias_atras(10), 'ENFERMEDAD', 'Hipocalcemia post-parto','Calcio intravenoso IV',           'RESUELTO'),
]
for animal, fecha, tipo, diag, trat, estado in incidentes_data:
    IncidenteSanitario.objects.get_or_create(
        finca=finca, animal=animal, fecha_incidente=fecha,
        defaults={'usuario': usuario, 'tipo': tipo, 'diagnostico': diag, 'tratamiento': trat, 'estado': estado}
    )
print("   OK Sanidad creada")

# ─────────────────────────────────────────────
print("\nReproduccion...")
# ─────────────────────────────────────────────
servicios_data = [
    (vacas_prod[1],  dias_atras(210), 'MONTA', 'Neptuno (TOR-001)'),
    (vacas_prod[3],  dias_atras(195), 'MONTA', 'Galeon (TOR-002)'),
    (vacas_prod[6],  dias_atras(180), 'IA',    'Pajilla HOL-2023-A'),
    (vacas_prod[9],  dias_atras(170), 'MONTA', 'Neptuno (TOR-001)'),
    (vacas_secas[0], dias_atras(150), 'MONTA', 'Galeon (TOR-002)'),
    (vacas_secas[1], dias_atras(140), 'IA',    'Pajilla HOL-2024-B'),
    (vacas_secas[3], dias_atras(160), 'MONTA', 'Neptuno (TOR-001)'),
]
for hembra, fecha, tipo, toro in servicios_data:
    ServicioReproductivo.objects.get_or_create(
        finca=finca, hembra=hembra, fecha=fecha,
        defaults={'tipo': tipo, 'toro_o_pajilla': toro,
                  'fecha_probable_parto': fecha - datetime.timedelta(days=280-fecha.toordinal() % 10)}
    )
    DiagnosticoGestacion.objects.get_or_create(
        finca=finca, hembra=hembra, fecha=fecha + datetime.timedelta(days=45),
        defaults={'metodo': 'ECOGRAFIA', 'resultado': 'PREÑADA', 'observaciones': 'Confirmado por ecografia'}
    )

partos_data = [
    (vacas_prod[0], dias_atras(300), crias[0]),
    (vacas_prod[2], dias_atras(250), crias[1]),
    (vacas_prod[4], dias_atras(270), crias[2]),
    (vacas_prod[7], dias_atras(10),  crias[3]),
]
for madre, fecha, cria in partos_data:
    RegistroParto.objects.get_or_create(
        finca=finca, madre=madre, fecha=fecha,
        defaults={'tipo': 'PARTO', 'facilidad': 'NORMAL', 'cria': cria, 'observaciones': 'Parto normal'}
    )
print("   OK Reproduccion creada")

# ─────────────────────────────────────────────
print("\nFinanzas: Liquidaciones de Leche...")
# ─────────────────────────────────────────────
for mes_atras in range(5, 0, -1):
    for q in [1, 2]:
        if q == 1:
            fi = meses_atras(mes_atras)
            ff = fi + datetime.timedelta(days=14)
        else:
            fi = meses_atras(mes_atras) + datetime.timedelta(days=15)
            ff = meses_atras(mes_atras - 1) - datetime.timedelta(days=1)
        litros = round(random.uniform(2800, 3800), 2)
        precio = round(random.uniform(0.42, 0.48), 2)
        LiquidacionLeche.objects.get_or_create(
            finca=finca, fecha_inicio=fi, fecha_fin=ff,
            defaults={
                'usuario': usuario, 'litros_totales': litros,
                'precio_por_litro': precio, 'monto_total': round(litros * precio, 2),
                'comprador': 'Lacteos del Llano C.A.',
                'estado_pago': 'COBRADO',
                'fecha_cobro': ff + datetime.timedelta(days=5),
                'observaciones': f'Quincena {"1era" if q == 1 else "2da"}',
            }
        )

LiquidacionLeche.objects.get_or_create(
    finca=finca,
    fecha_inicio=TODAY - datetime.timedelta(days=10),
    fecha_fin=TODAY,
    defaults={
        'usuario': usuario, 'litros_totales': 1400.0,
        'precio_por_litro': 0.45, 'monto_total': 630.0,
        'comprador': 'Lacteos del Llano C.A.',
        'estado_pago': 'PENDIENTE',
        'observaciones': 'Quincena en curso'
    }
)
print("   OK Liquidaciones creadas (6 meses historico)")

# ─────────────────────────────────────────────
print("\nGastos...")
# ─────────────────────────────────────────────
gastos_data = [
    (5,   'PERSONAL',      'Quincena obreros Sep 2da',         650.0,  'FIJO'),
    (20,  'PERSONAL',      'Quincena obreros Sep 1ra',         650.0,  'FIJO'),
    (5,   'ALIMENTO',      'Concentrado 1 ton',                420.0,  'VARIABLE'),
    (10,  'VETERINARIA',   'Oxitetraciclina LA 2lt',           95.0,   'VARIABLE'),
    (12,  'VETERINARIA',   'Vitaminas ADE 1lt',                38.0,   'VARIABLE'),
    (18,  'MANTENIMIENTO', 'Reparacion cerca potrero 3',       120.0,  'VARIABLE'),
    (25,  'SERVICIOS',     'Electricidad Agosto',              85.0,   'FIJO'),
    (35,  'PERSONAL',      'Quincena obreros Ago 2da',         650.0,  'FIJO'),
    (40,  'ALIMENTO',      'Sal mineralizada 200kg',           180.0,  'VARIABLE'),
    (45,  'MANTENIMIENTO', 'Pintura corrales',                 240.0,  'VARIABLE'),
    (50,  'PERSONAL',      'Quincena obreros Ago 1ra',         650.0,  'FIJO'),
    (55,  'VETERINARIA',   'Servicio veterinario mensual',     200.0,  'FIJO'),
    (60,  'ALIMENTO',      'Urea pecuaria 100kg',              90.0,   'VARIABLE'),
    (65,  'SERVICIOS',     'Electricidad Julio',               78.0,   'FIJO'),
    (70,  'VETERINARIA',   'Vacuna Aftosa 100 dosis',          340.0,  'VARIABLE'),
    (80,  'PERSONAL',      'Quincena obreros Jul 2da',         650.0,  'FIJO'),
    (90,  'MANTENIMIENTO', 'Alambre y postes',                 380.0,  'VARIABLE'),
    (95,  'PERSONAL',      'Quincena obreros Jul 1ra',         650.0,  'FIJO'),
    (100, 'ALIMENTO',      'Melaza 500kg',                     200.0,  'VARIABLE'),
    (105, 'SERVICIOS',     'Electricidad Junio',               92.0,   'FIJO'),
    (2,   'VETERINARIA',   'Oxitocina + antibioticos parto',   55.0,   'VARIABLE'),
]
for dias, cat, concepto, monto, tipo in gastos_data:
    GastoFinca.objects.get_or_create(
        finca=finca, fecha=dias_atras(dias), concepto=concepto,
        defaults={'usuario': usuario, 'categoria': cat, 'monto': monto, 'tipo': tipo}
    )

gastos_rec_data = [
    ('Nomina de Obreros (2 personas)',  'PERSONAL',      1300.0, 'MENSUAL'),
    ('Servicio Veterinario Mensual',    'VETERINARIA',   200.0,  'MENSUAL'),
    ('Electricidad Finca',              'SERVICIOS',     85.0,   'MENSUAL'),
    ('Alimento Concentrado',            'ALIMENTO',      420.0,  'MENSUAL'),
    ('Mantenimiento General',           'MANTENIMIENTO', 150.0,  'MENSUAL'),
    ('Desparasitacion General',         'VETERINARIA',   180.0,  'SEMESTRAL'),
    ('Vacunacion Aftosa',               'VETERINARIA',   340.0,  'SEMESTRAL'),
]
for concepto, cat, monto, freq in gastos_rec_data:
    GastoRecurrente.objects.get_or_create(
        finca=finca, concepto=concepto,
        defaults={'usuario': usuario, 'categoria': cat, 'monto': monto, 'frecuencia': freq, 'activo': True}
    )
print("   OK Gastos e ingresos creados")

# ─────────────────────────────────────────────
print("\nVenta historica...")
# ─────────────────────────────────────────────
animal_vendido, _ = Animal.objects.get_or_create(
    finca=finca, codigo='MAU-VEND-01',
    defaults={
        'usuario': usuario, 'nombre': 'Colosio',
        'fecha_nacimiento': meses_atras(20),
        'composicion_racial': '3/4 Brahman',
        'sexo': 'M', 'estado_vida': 'VENDIDO',
        'estado_gestacion': 'N_A', 'estado_produccion': 'N_A',
        'uso_macho': 'ENGORDE', 'estado_salud': 'SANO', 'destetado': True,
    }
)
if not animal_vendido.ventas_info.exists():
    venta = VentaAnimal.objects.create(
        usuario=usuario, finca=finca, motivo='SACRIFICIO',
        kilos=380.0, precio_total=760.0,
        comprador='Frigorifico Los Llanos',
        observaciones='380kg en pie, buen estado'
    )
    venta.animales.add(animal_vendido)
    venta.fecha_venta = dias_atras(45)
    venta.save()
print("   OK Venta registrada")

# ─────────────────────────────────────────────
print("\nEmpleados y Nomina...")
# ─────────────────────────────────────────────
empleados_data = [
    ('Carlos Medina',   'MAYORAL',     850.0, dias_atras(730), '0414-7654321'),
    ('Pedro Gonzalez',  'OBRERO',      450.0, dias_atras(365), '0416-1234567'),
    ('Luis Torrealba',  'OBRERO',      450.0, dias_atras(180), '0412-9876543'),
    ('Dr. Hector Ruiz', 'VETERINARIO', 200.0, dias_atras(900), '0424-5551234'),
]
empleados = []
for nombre, cargo, salario, fecha_cont, tel in empleados_data:
    emp, _ = Empleado.objects.get_or_create(
        finca=finca, nombre=nombre,
        defaults={'cargo': cargo, 'salario_base': salario, 'fecha_contratacion': fecha_cont, 'telefono': tel}
    )
    empleados.append(emp)

for emp in empleados[:3]:
    for m in range(1, 4):
        PagoNomina.objects.get_or_create(
            finca=finca, empleado=emp, fecha=meses_atras(m),
            defaults={
                'monto_pagado': emp.salario_base / 2,
                'concepto': f'Quincena mes-{m}',
                'registrado_por': usuario,
            }
        )
print(f"   OK {len(empleados)} empleados y nomina creados")

# ─────────────────────────────────────────────
print("\nCatalogo de Semen...")
# ─────────────────────────────────────────────
semen_data = [
    ('Excellence ET',    'Holstein', 'HOL-2023-A', 2850.00, 18.50, 8),
    ('Goldwyn Renegade', 'Holstein', 'HOL-2022-R', 2100.00, 14.00, 12),
    ('Altaspring',       'Holstein', 'HOL-2024-S', 3200.00, 22.00, 5),
    ('Brahman Elite 7',  'Brahman',  'BRA-2023-7', 1200.00,  8.00, 15),
    ('Guzerat Master',   'Guzerat',  'GUZ-2022-M',  900.00,  6.00, 20),
]
for nombre, raza, codigo_p, pta, precio, stock in semen_data:
    CatalogoSemen.objects.get_or_create(
        finca=finca, codigo_pajilla=codigo_p,
        defaults={'nombre_toro': nombre, 'raza': raza, 'pta_leche': pta, 'precio': precio, 'stock': stock}
    )
print("   OK Catalogo de semen creado")

# ─────────────────────────────────────────────
print("\nProtocolos...")
# ─────────────────────────────────────────────
protocolos_trat = [
    ('Protocolo Mastitis',        'Mastitis Clinica',       'Amoxicilina + Cloxacilina intramamario', '1 jeringa/cuarto 2x/dia', 5),
    ('Protocolo Neumonia',        'Neumonia Bacteriana',    'Oxitetraciclina LA 300mg/ml',            '1ml/10kg IM',             3),
    ('Protocolo Garrapata',       'Infestacion Garrapatas', 'Ivermectina 1%',                         '1ml/50kg SC',             1),
    ('Protocolo Hipocalcemia',    'Hipocalcemia',           'Gluconato de Calcio 23%',                '500ml IV lento',          1),
    ('Protocolo Diarrea Ternero', 'Diarrea Neonatal',       'Suero oral + Florfenicol',               '2.5ml/10kg IM',           3),
]
for nombre, diag, med, dosis, dur in protocolos_trat:
    ProtocoloTratamiento.objects.get_or_create(
        finca=finca, nombre=nombre,
        defaults={'diagnostico_asociado': diag, 'medicamento': med, 'dosis': dosis, 'duracion_dias': dur}
    )

ingredientes = [
    {'nombre': 'Maiz Molido',  'porcentaje': 45, 'costo_por_kg': 0.28},
    {'nombre': 'Sorgo',        'porcentaje': 25, 'costo_por_kg': 0.22},
    {'nombre': 'Torta de Soya','porcentaje': 15, 'costo_por_kg': 0.55},
    {'nombre': 'Melaza',       'porcentaje': 10, 'costo_por_kg': 0.18},
    {'nombre': 'Urea Pecuaria','porcentaje':  3, 'costo_por_kg': 0.65},
    {'nombre': 'Sal Mineral',  'porcentaje':  2, 'costo_por_kg': 0.80},
]
ProtocoloAlimentacion.objects.get_or_create(
    finca=finca, nombre='Racion Mautes - Engorde Intensivo',
    defaults={
        'ingredientes_json': json.dumps(ingredientes),
        'racion_base_kg': 6.00,
        'dias_transicion': 14,
        'incremento_porcentaje': 10.00,
    }
)
print("   OK Protocolos creados")

# ─────────────────────────────────────────────
print("\nTareas Diarias...")
# ─────────────────────────────────────────────
tareas_data = [
    (TODAY,                             empleados[0], 'Verificar bebederos en todos los corrales',          'LIMPIEZA',     False),
    (TODAY,                             empleados[1], 'Suministrar concentrado Corral de Mautes (60kg)',    'ALIMENTACION', False),
    (TODAY,                             empleados[2], 'Aplicar 2da dosis oxitetraciclina a VAC-013',        'SANIDAD',      False),
    (TODAY,                             empleados[1], 'Ordeno matutino y registro en planilla',             'OTRO',         True),
    (dias_atras(1),                     empleados[0], 'Revision de cercas Potrero 1 y 4',                  'LIMPIEZA',     True),
    (dias_atras(1),                     empleados[2], 'Curacion de herida MAU-002 Gladiador',              'SANIDAD',      True),
    (TODAY + datetime.timedelta(days=1),empleados[0], 'Rotacion vacas a Potrero 2',                        'OTRO',         False),
    (TODAY + datetime.timedelta(days=3),empleados[1], 'Desparasitacion general novillas',                  'SANIDAD',      False),
]
for fecha, emp, desc, cat, completada in tareas_data:
    TareaDiaria.objects.get_or_create(
        finca=finca, fecha=fecha, descripcion=desc,
        defaults={'asignado_a': emp, 'categoria': cat, 'completada': completada}
    )
print("   OK Tareas diarias creadas")

# ─────────────────────────────────────────────
print("\n" + "="*56)
print("RESUMEN FINAL")
print("="*56)
total_vivos = Animal.objects.filter(finca=finca, estado_vida='VIVO').count()
hembras     = Animal.objects.filter(finca=finca, estado_vida='VIVO', sexo='H').count()
machos      = Animal.objects.filter(finca=finca, estado_vida='VIVO', sexo='M').count()
en_prod     = Animal.objects.filter(finca=finca, estado_vida='VIVO', estado_produccion='LACTANCIA').count()
preniadas   = Animal.objects.filter(finca=finca, estado_vida='VIVO', estado_gestacion='PREÑADA').count()
print(f"Usuario:               Juan")
print(f"Finca:                 Finca La Esperanza")
print(f"Total animales vivos:  {total_vivos}")
print(f"  Hembras:             {hembras}")
print(f"  Machos:              {machos}")
print(f"  Vacas en produccion: {en_prod}")
print(f"  Preñadas:            {preniadas}")
print(f"Corrales:              6")
print(f"Potreros:              6")
print(f"Rebanos:               5")
print()
print("\nCreando Registros de Ordeño...")
for i in range(29, -1, -1):
    fecha_ord = dias_atras(i)
    litros_m = random.randint(180, 240) + random.choice([0.0, 0.5])
    RegistroOrdeno.objects.get_or_create(
        finca=finca,
        fecha=fecha_ord,
        turno='MAÑANA',
        defaults={
            'usuario': usuario,
            'rebaño': rebano_vacas_prod,
            'vacas_ordenadas': 18,
            'litros_leche': litros_m,
            'precio_litro': 0.45,
            'temperatura_tanque': 4.0,
            'observaciones': 'Ordeño matutino sin novedades.'
        }
    )
    litros_t = random.randint(120, 160) + random.choice([0.0, 0.5])
    RegistroOrdeno.objects.get_or_create(
        finca=finca,
        fecha=fecha_ord,
        turno='TARDE',
        defaults={
            'usuario': usuario,
            'rebaño': rebano_vacas_prod,
            'vacas_ordenadas': 18,
            'litros_leche': litros_t,
            'precio_litro': 0.45,
            'temperatura_tanque': 4.2,
            'observaciones': 'Ordeño vespertino.'
        }
    )

print("Modulos con datos:")
print("  OK Registro de animales (35+ cabezas)")
print("  OK Rebanos dinamicos (5 rebanos con filtros)")
print("  OK Control de Ordeño (30 días de ordeño diario)")
print("  OK Pesajes y engorde (mautes y novillas)")
print("  OK Reproduccion (servicios, diagnosticos, partos)")
print("  OK Sanidad (vacunaciones e incidentes)")
print("  OK Finanzas (leche 6 meses, gastos, ventas)")
print("  OK Inventario (medicamentos, alimentos, equipos)")
print("  OK Potreros y rotaciones")
print("  OK Empleados y nomina (4 empleados)")
print("  OK Genetica / Catalogo semen (5 toros)")
print("  OK Protocolos sanitarios y de alimentacion")
print("  OK Tareas diarias (hoy, ayer y proximos dias)")
print("="*56)
print("CARGA COMPLETADA EXITOSAMENTE")
