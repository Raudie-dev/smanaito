import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Samanito_soft.settings')
django.setup()

from app1.models import User, Finca, Animal, Rebaño, RegistroOrdeno

for user in User.objects.all():
    # Crear Finca Principal
    finca, created = Finca.objects.get_or_create(
        usuario=user,
        nombre=f"Finca Principal de {user.nombre}"
    )
    
    # Asignar a todos los modelos
    Animal.objects.filter(usuario=user, finca__isnull=True).update(finca=finca)
    Rebaño.objects.filter(usuario=user, finca__isnull=True).update(finca=finca)
    RegistroOrdeno.objects.filter(usuario=user, finca__isnull=True).update(finca=finca)

print("Migración a Multi-Finca completada exitosamente.")
