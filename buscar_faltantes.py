import re

# Leer el archivo JavaScript
with open('CartasNacionales_1.js', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Extraer todos los códigos
codigos = re.findall(r'"codigo"\s*:\s*"([^"]+)"', contenido)
codigos_set = set(codigos)

print(f"Total códigos encontrados: {len(codigos_set)}\n")

# Analizar qué cartas faltan en secuencias continuas
# Las cartas siguen formato NN-letra (01-l, 01-m, 01-n, etc.)
fila_cartas = {}
for codigo in codigos:
    num, letra = codigo.split('-')
    num = int(num)
    if num not in fila_cartas:
        fila_cartas[num] = []
    fila_cartas[num].append(letra)

# Alfabeto de cartas (orden estándar)
alfabeto = 'abcdefghijklmnñopqrstuvwxyz'

print("ANÁLISIS POR FILA (buscando huecos en secuencias continuas):")
print("=" * 80)

for fila in sorted(fila_cartas.keys()):
    letras = sorted(fila_cartas[fila], key=lambda x: alfabeto.index(x))
    print(f"\nFila {fila:02d}: {len(letras)} cartas")
    print(f"  Letras: {', '.join(letras)}")
    
    # Buscar huecos en la secuencia
    indices = [alfabeto.index(l) for l in letras]
    if len(indices) > 1:
        huecos = []
        for i in range(len(indices) - 1):
            if indices[i+1] - indices[i] > 1:
                # Hay un hueco
                for idx in range(indices[i] + 1, indices[i+1]):
                    letra_faltante = alfabeto[idx]
                    huecos.append(letra_faltante)
        
        if huecos:
            print(f"  ⚠️  HUECOS: {', '.join([f'{fila:02d}-{h}' for h in huecos])}")

print("\n" + "=" * 80)
print("ESTADÍSTICAS:")
print(f"Filas con cartas: {len(fila_cartas)}")
print(f"Total de cartas: {sum(len(v) for v in fila_cartas.values())}")

# Buscar filas faltantes
todas_filas = set(range(1, 38))  # 37 es la última fila
filas_presentes = set(fila_cartas.keys())
filas_faltantes = todas_filas - filas_presentes

if filas_faltantes:
    print(f"\n⚠️  FILAS COMPLETAMENTE FALTANTES: {sorted(filas_faltantes)}")
