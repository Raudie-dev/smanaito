from app1.models import IncidenteSanitario

# ACTIVO -> ATENDIENDO
activos = IncidenteSanitario.objects.filter(estado='ACTIVO')
act_count = activos.update(estado='ATENDIENDO')
print(f"Convertidos {act_count} incidentes ACTIVO a ATENDIENDO")

# RESUELTO -> RECUPERADO
resueltos = IncidenteSanitario.objects.filter(estado='RESUELTO')
res_count = resueltos.update(estado='RECUPERADO')
print(f"Convertidos {res_count} incidentes RESUELTO a RECUPERADO")
