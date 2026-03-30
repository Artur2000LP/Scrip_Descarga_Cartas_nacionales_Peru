import requests
import os
import re
import time
from datetime import datetime

# Carpeta de destino con fecha y hora
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_folder = f"cartas_nacionales_peru_{timestamp}"

print(f"{'='*80}")
print(f"DESCARGA MASIVA DE CARTAS NACIONALES DEL PERÚ - ESCALA 1:100,000")
print(f"{'='*80}")
print(f"\nCarpeta de destino: {output_folder}\n")

if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"✓ Carpeta creada: {os.path.abspath(output_folder)}\n")

def extraer_enlaces_descarga():
    """Extrae todos los enlaces de descarga organizados por zona"""
    print("Obteniendo enlaces desde el mapa interactivo...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url_datos = "https://geogpsperu.github.io/100kshp.github.com/data/CartasNacionales_1.js"
        
        print(f"Descargando: {url_datos}")
        response = requests.get(url_datos, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Guardar archivo de datos
        with open('CartasNacionales_1.js', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        contenido = response.text
        enlaces_dict = {}
        
        # Buscar bloques de properties en el GeoJSON
        properties_pattern = r'"properties"\s*:\s*\{[^}]+\}'
        properties_blocks = re.findall(properties_pattern, contenido)
        
        print(f"Procesando {len(properties_blocks)} cartas...\n")
        
        for block in properties_blocks:
            nombre_match = re.search(r'"nombre"\s*:\s*"([^"]+)"', block)
            codigo_match = re.search(r'"codigo"\s*:\s*"([^"]+)"', block)
            googledriv_match = re.search(r'"googledriv"\s*:\s*"([^"]+)"', block)
            zona_match = re.search(r'"ZonaUTM_"\s*:\s*"([^"]+)"', block)
            
            if googledriv_match and nombre_match and codigo_match:
                url = googledriv_match.group(1).replace('\\/', '/')
                nombre = nombre_match.group(1)
                codigo = codigo_match.group(1)
                zona = zona_match.group(1) if zona_match else "Sin_zona"
                
                # Evitar duplicados usando el código como clave
                if codigo not in enlaces_dict:
                    enlaces_dict[codigo] = {
                        'nombre': nombre,
                        'url': url,
                        'zona': zona,
                        'codigo': codigo
                    }
        
        # Estadísticas por zona
        zonas_count = {}
        for datos in enlaces_dict.values():
            zona = datos['zona']
            zonas_count[zona] = zonas_count.get(zona, 0) + 1
        
        print(f"{'='*80}")
        print(f"RESUMEN DE CARTAS ENCONTRADAS:")
        print(f"{'='*80}")
        print(f"Total oficial esperado: 501 cartas")
        print(f"Total disponibles en archivo: {len(enlaces_dict)} cartas")
        
        if len(enlaces_dict) < 501:
            print(f"\n⚠️  ADVERTENCIA: Faltan {501 - len(enlaces_dict)} cartas en el archivo oficial")
        
        print(f"\nDistribución por Zona UTM:")
        for zona in sorted(zonas_count.keys()):
            print(f"  • Zona {zona}: {zonas_count[zona]} cartas")
        print(f"{'='*80}\n")
        
        return list(enlaces_dict.values())
        
    except Exception as e:
        print(f"❌ Error al extraer enlaces: {e}")
        import traceback
        traceback.print_exc()
        return []

def convertir_url_gdrive(url):
    """Convierte URL de Google Drive a formato de descarga directa"""
    if 'drive.google.com/open?id=' in url:
        file_id = url.split('id=')[1].split('&')[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    elif '/file/d/' in url:
        file_id = url.split('/file/d/')[1].split('/')[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

def descargar_archivo(carta, carpeta_zona):
    """Descarga un archivo de carta nacional"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = convertir_url_gdrive(carta['url'])
        nombre_archivo = f"{carta['codigo']}_{carta['nombre']}.zip"
        
        # Crear carpeta de zona si no existe
        os.makedirs(carpeta_zona, exist_ok=True)
        
        path_completo = os.path.join(carpeta_zona, nombre_archivo)
        
        # Verificar si ya existe
        if os.path.exists(path_completo):
            size_mb = os.path.getsize(path_completo) / (1024*1024)
            print(f"  ⏭️  Ya existe: {nombre_archivo} ({size_mb:.1f} MB)")
            return True
        
        # Descargar
        response = requests.get(url, headers=headers, stream=True, timeout=120, allow_redirects=True)
        
        if response.status_code == 200:
            # Obtener tamaño del archivo
            total_size = int(response.headers.get('content-length', 0))
            
            with open(path_completo, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            size_mb = os.path.getsize(path_completo) / (1024*1024)
            print(f"  ✓ Descargado: {nombre_archivo} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"  ❌ Error HTTP {response.status_code}: {nombre_archivo}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {carta['codigo']} - {str(e)[:50]}")
        return False

def descargar_cartas():
    """Descarga todas las cartas organizadas por zonas"""
    enlaces = extraer_enlaces_descarga()
    
    if not enlaces:
        print("No se encontraron enlaces para descargar")
        return
    
    print(f"Iniciando descarga de {len(enlaces)} cartas...\n")
    
    # Organizar por zonas
    cartas_por_zona = {}
    for carta in enlaces:
        zona = carta['zona']
        if zona not in cartas_por_zona:
            cartas_por_zona[zona] = []
        cartas_por_zona[zona].append(carta)
    
    # Descargar por zona
    exitosos_total = 0
    fallidos_total = 0
    cartas_fallidas = []
    
    for zona in sorted(cartas_por_zona.keys()):
        cartas_zona = cartas_por_zona[zona]
        carpeta_zona = os.path.join(output_folder, f"Zona_{zona}")
        
        print(f"\n{'='*80}")
        print(f"ZONA {zona} - {len(cartas_zona)} cartas")
        print(f"{'='*80}")
        
        exitosos_zona = 0
        fallidos_zona = 0
        
        for i, carta in enumerate(cartas_zona, 1):
            print(f"[{i}/{len(cartas_zona)}] {carta['codigo']} - {carta['nombre'][:40]}...")
            
            if descargar_archivo(carta, carpeta_zona):
                exitosos_zona += 1
                exitosos_total += 1
            else:
                fallidos_zona += 1
                fallidos_total += 1
                cartas_fallidas.append({
                    'codigo': carta['codigo'],
                    'nombre': carta['nombre'],
                    'zona': zona,
                    'url': carta['url']
                })
            
            time.sleep(0.5)  # Pausa para no saturar el servidor
        
        print(f"\nZona {zona} completada: ✓ {exitosos_zona} exitosas, ✗ {fallidos_zona} fallidas")
    
    # Resumen final
    print(f"\n{'='*80}")
    print(f"DESCARGA COMPLETADA")
    print(f"{'='*80}")
    print(f"✓ Exitosas: {exitosos_total}/{len(enlaces)}")
    print(f"✗ Fallidas: {fallidos_total}/{len(enlaces)}")
    print(f"\nArchivos guardados en: {os.path.abspath(output_folder)}")
    
    # Mostrar cartas fallidas
    if cartas_fallidas:
        print(f"\n{'='*80}")
        print(f"CARTAS FALLIDAS ({len(cartas_fallidas)}):")
        print(f"{'='*80}")
        for carta in cartas_fallidas:
            print(f"  • {carta['codigo']} - {carta['nombre']} [Zona {carta['zona']}]")
        
        # Guardar lista de fallidas
        with open('cartas_fallidas.txt', 'w', encoding='utf-8') as f:
            for carta in cartas_fallidas:
                f.write(f"{carta['codigo']}\t{carta['nombre']}\t{carta['zona']}\t{carta['url']}\n")
        print(f"\nLista guardada en: cartas_fallidas.txt")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    try:
        descargar_cartas()
    except KeyboardInterrupt:
        print("\n\n⚠️  Descarga interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
