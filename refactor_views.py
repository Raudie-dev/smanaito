import re

file_path = '/home/juan/Documentos/Proyectos/Samanito_soft/app1/views.py'
with open(file_path, 'r') as f:
    content = f.read()

# Patrón para inyectar finca_activa
finca_context = """    finca_activa_id, fincas_usuario = get_finca_context(request, user)
    if not finca_activa_id:
        messages.error(request, 'Debe crear una finca primero')
        return redirect('control')"""

# Modificando la vista registro
def patch_view(view_name, content, add_context=True):
    pattern = r'(def ' + view_name + r'\(request\):.*?user = User\.objects\.get\(id=user_id\))'
    if add_context:
        replacement = r'\1\n' + finca_context
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Dentro de la vista, reemplazar las consultas a BD
    # Nota: No podemos usar regex globales sobre todo el archivo sin cuidado.
    return content

content = patch_view('registro', content)
content = patch_view('rebaño', content)
content = patch_view('ordeño', content)
content = patch_view('crianza', content)
content = patch_view('api_buscar_padre', content)
content = patch_view('api_buscar_madre', content)
content = patch_view('api_buscar_vaca_seca', content)

# Reemplazos globales (cuidado con no afectar control ni el signup)
# Solo después de def registro, rebaño, etc.
# Sustituir `usuario=user` por `finca_id=finca_activa_id` en todo el documento,
# pero OJO que en app2 y otros lugares no se debe romper. En app1.views casi todo es válido.
# Para evitar romper el signup y login:
parts = content.split('def registro(request):')
if len(parts) == 2:
    p1 = parts[0]
    p2 = 'def registro(request):' + parts[1]
    
    # En p2, reemplazamos 'usuario=user' por 'finca_id=finca_activa_id'
    p2 = p2.replace('usuario=user', 'finca_id=finca_activa_id')
    # Añadimos fincas_usuario al context
    p2 = re.sub(r'(context\s*=\s*{.*?)}', r'\1    \'fincas_usuario\': fincas_usuario,\n    }', p2, flags=re.DOTALL)
    content = p1 + p2

with open(file_path, 'w') as f:
    f.write(content)
print("Vistas refactorizadas con éxito.")
