import re

# Leer el archivo JavaScript
with open('CartasNacionales_1.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Extraer todos los códigos
codigos = re.findall(r'"codigo"\s*:\s*"([^"]+)"', content)

print(f"Total de códigos encontrados: {len(codigos)}")
print(f"Códigos únicos: {len(set(codigos))}")

# Buscar duplicados
duplicados = {}
for codigo in codigos:
    if codigo in duplicados:
        duplicados[codigo] += 1
    else:
        duplicados[codigo] = 1

duplicados_reales = {k: v for k, v in duplicados.items() if v > 1}

if duplicados_reales:
    print(f"\n¡ENCONTRADOS {len(duplicados_reales)} CÓDIGOS DUPLICADOS!")
    for codigo, count in duplicados_reales.items():
        print(f"  {codigo}: aparece {count} veces")
        # Mostrar contexto
        pattern = rf'"codigo"\s*:\s*"{re.escape(codigo)}".*?"nombre"\s*:\s*"([^"]+)"'
        nombres = re.findall(pattern, content)
        for nombre in nombres:
            print(f"    - {nombre}")
else:
    print("\nNo hay códigos duplicados")

# Contar Features
features = re.findall(r'"type"\s*:\s*"Feature"', content)
print(f"\nTotal de Features: {len(features)}")

# Listar todos los códigos ordenados
print("\n\nTODOS LOS CÓDIGOS (ordenados):")
for i, codigo in enumerate(sorted(set(codigos)), 1):
    print(f"{i}. {codigo}")
