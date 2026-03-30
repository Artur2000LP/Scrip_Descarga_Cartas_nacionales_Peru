import requests
import os
import re
import time
from datetime import datetime

# Carpeta de destino con fecha y hora
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_folder = f"cartas_nacionales_pdf_jpg_{timestamp}"

print(f"{'='*80}")
print(f"DESCARGA DE CARTAS NACIONALES DEL PERÚ - PDF Y JPG (ALTA RESOLUCIÓN)")
print(f"{'='*80}")
print(f"\nCarpeta de destino: {output_folder}\n")

if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"✓ Carpeta creada: {os.path.abspath(output_folder)}\n")

def extraer_enlaces_descarga():
    """Extrae todos los enlaces de PDF y JPG organizados por zona"""
    print("Obteniendo enlaces desde el mapa interactivo...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # URLs de los dos archivos de datos (PDF y JPG)
        url_pdf = "https://geogpsperu.github.io/cartaspdfjpg.github.com/data/CartasNacionalesPDF_1.js"
        
        print(f"Descargando datos de cartas PDF y JPG...")
        response = requests.get(url_pdf, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Guardar archivo de datos para referencia
        with open('CartasNacionalesPDF_JPG_data.js', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        contenido = response.text
        cartas_dict = {}
        
        # Buscar bloques de properties en el GeoJSON
        properties_pattern = r'"properties"\s*:\s*\{[^}]+\}'
        properties_blocks = re.findall(properties_pattern, contenido)
        
        print(f"Procesando {len(properties_blocks)} cartas...\n")
        
        for block in properties_blocks:
            nombre_match = re.search(r'"nombre"\s*:\s*"([^"]+)"', block)
            codigo_match = re.search(r'"cod_nac"\s*:\s*"([^"]+)"', block)
            pdf_match = re.search(r'"pdf"\s*:\s*"([^"]+)"', block)
            jpg_match = re.search(r'"jpg"\s*:\s*"([^"]+)"', block)
            zona_match = re.search(r'"zonal"\s*:\s*"([^"]+)"', block)
            cuadricula_match = re.search(r'"cuadricula"\s*:\s*"([^"]+)"', block)
            hemisferio_match = re.search(r'"Hemisferio"\s*:\s*"([^"]+)"', block)
            
            if codigo_match and nombre_match:
                url_pdf = pdf_match.group(1).replace('\\/', '/') if pdf_match else None
                url_jpg = jpg_match.group(1).replace('\\/', '/') if jpg_match else None
                nombre = nombre_match.group(1)
                codigo = codigo_match.group(1)
                zona = zona_match.group(1) if zona_match else "Sin_zona"
                cuadricula = cuadricula_match.group(1) if cuadricula_match else "L"
                hemisferio = hemisferio_match.group(1) if hemisferio_match else "Sur"
                
                # Evitar duplicados usando el código como clave
                if codigo not in cartas_dict:
                    cartas_dict[codigo] = {
                        'nombre': nombre,
                        'url_pdf': url_pdf,
                        'url_jpg': url_jpg,
                        'zona': zona,
                        'codigo': codigo,
                        'cuadricula': cuadricula,
                        'hemisferio': hemisferio
                    }
        
        # Estadísticas por zona
        zonas_count = {}
        for datos in cartas_dict.values():
            zona = datos['zona']
            zonas_count[zona] = zonas_count.get(zona, 0) + 1
        
        print(f"{'='*80}")
        print(f"RESUMEN DE CARTAS ENCONTRADAS:")
        print(f"{'='*80}")
        print(f"Total de cartas disponibles: {len(cartas_dict)} cartas")
        print(f"Archivos por carta: PDF (Alta Resolución) + JPG")
        print(f"Total de archivos a descargar: {len(cartas_dict) * 2}")
        
        print(f"\nDistribución por Zona UTM:")
        for zona in sorted(zonas_count.keys()):
            print(f"  • Zona {zona}{cartas_dict[list(cartas_dict.keys())[0]]['hemisferio']}: {zonas_count[zona]} cartas")
        print(f"{'='*80}\n")
        
        return list(cartas_dict.values())
        
    except Exception as e:
        print(f"❌ Error al extraer enlaces: {e}")
        import traceback
        traceback.print_exc()
        return []

def convertir_url_gdrive(url):
    """Convierte URL de Google Drive a formato de descarga directa"""
    if not url:
        return None
        
    if 'drive.google.com/open?id=' in url:
        file_id = url.split('id=')[1].split('&')[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    elif 'drive.google.com/file/d/' in url:
        file_id = url.split('/d/')[1].split('/')[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    else:
        return url

def descargar_archivo(url, ruta_destino, nombre_carta, tipo_archivo):
    """Descarga un archivo desde Google Drive con reintentos"""
    if not url:
        print(f"  ⚠️  URL no disponible para {tipo_archivo}")
        return False
        
    max_intentos = 3
    for intento in range(1, max_intentos + 1):
        try:
            url_descarga = convertir_url_gdrive(url)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            session = requests.Session()
            response = session.get(url_descarga, headers=headers, stream=True, timeout=60)
            
            # Verificar si Google Drive requiere confirmación
            if 'virus scan warning' in response.text.lower() or 'download_warning' in response.text:
                # Obtener token de confirmación
                for key, value in response.cookies.items():
                    if key.startswith('download_warning'):
                        url_descarga = f"{url_descarga}&confirm={value}"
                        response = session.get(url_descarga, headers=headers, stream=True, timeout=60)
                        break
            
            response.raise_for_status()
            
            # Descargar archivo
            tamaño_total = int(response.headers.get('content-length', 0))
            
            with open(ruta_destino, 'wb') as archivo:
                if tamaño_total > 0:
                    descargado = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            archivo.write(chunk)
                            descargado += len(chunk)
                else:
                    archivo.write(response.content)
            
            # Verificar si el archivo descargado es válido (no es página de error HTML)
            if os.path.getsize(ruta_destino) < 1024:  # Si es menor a 1KB probablemente es error
                with open(ruta_destino, 'rb') as f:
                    contenido = f.read()
                    if b'<!DOCTYPE html' in contenido or b'<html' in contenido:
                        os.remove(ruta_destino)
                        raise Exception("El archivo descargado es una página HTML (error)")
            
            tamaño_mb = os.path.getsize(ruta_destino) / (1024 * 1024)
            print(f"  ✓ {tipo_archivo}: {tamaño_mb:.2f} MB descargados")
            return True
            
        except Exception as e:
            print(f"  ❌ Error intento {intento}/{max_intentos} ({tipo_archivo}): {e}")
            if os.path.exists(ruta_destino):
                os.remove(ruta_destino)
            if intento < max_intentos:
                time.sleep(2 * intento)  # Espera progresiva
    
    return False

def descargar_cartas(cartas):
    """Descarga todas las cartas PDF y JPG organizadas por zona"""
    if not cartas:
        print("No hay cartas para descargar")
        return
    
    estadisticas = {
        'total': len(cartas) * 2,  # Cada carta tiene PDF y JPG
        'exitosas_pdf': 0,
        'exitosas_jpg': 0,
        'fallidas_pdf': 0,
        'fallidas_jpg': 0,
        'por_zona': {}
    }
    
    print(f"\n{'='*80}")
    print(f"INICIANDO DESCARGA DE {len(cartas)} CARTAS (PDF + JPG)")
    print(f"{'='*80}\n")
    
    # Agrupar por zona para organizar carpetas
    cartas_por_zona = {}
    for carta in cartas:
        zona = carta['zona']
        if zona not in cartas_por_zona:
            cartas_por_zona[zona] = []
        cartas_por_zona[zona].append(carta)
    
    for zona in sorted(cartas_por_zona.keys()):
        cartas_zona = cartas_por_zona[zona]
        hemisferio = cartas_zona[0]['hemisferio']
        
        print(f"\n{'─'*80}")
        print(f"ZONA {zona}{hemisferio} - {len(cartas_zona)} cartas")
        print(f"{'─'*80}\n")
        
        # Crear carpeta de zona
        carpeta_zona = os.path.join(output_folder, f"Zona_{zona}{hemisferio}")
        if not os.path.exists(carpeta_zona):
            os.makedirs(carpeta_zona)
        
        estadisticas['por_zona'][zona] = {
            'total_cartas': len(cartas_zona),
            'exitosas_pdf': 0,
            'exitosas_jpg': 0,
            'fallidas_pdf': 0,
            'fallidas_jpg': 0
        }
        
        for i, carta in enumerate(cartas_zona, 1):
            nombre = carta['nombre']
            codigo = carta['codigo']
            cuadricula = carta['cuadricula']
            
            # Nombre de carpeta: NOMBRE_ZONA_CODIGO_CUADRICULA_Hemisferio
            nombre_carpeta = f"{nombre}_{zona}_{codigo}_{cuadricula}_{hemisferio}".replace(" ", "_")
            carpeta_carta = os.path.join(carpeta_zona, nombre_carpeta)
            
            if not os.path.exists(carpeta_carta):
                os.makedirs(carpeta_carta)
            
            print(f"[{i}/{len(cartas_zona)}] {nombre} ({codigo}) - Zona {zona}{cuadricula}:")
            
            # Descargar PDF
            nombre_pdf = f"{codigo}_{nombre}_{zona}_{cuadricula}_{hemisferio}.pdf".replace(" ", "_")
            ruta_pdf = os.path.join(carpeta_carta, nombre_pdf)
            
            if descargar_archivo(carta['url_pdf'], ruta_pdf, nombre, "PDF"):
                estadisticas['exitosas_pdf'] += 1
                estadisticas['por_zona'][zona]['exitosas_pdf'] += 1
            else:
                estadisticas['fallidas_pdf'] += 1
                estadisticas['por_zona'][zona]['fallidas_pdf'] += 1
            
            # Descargar JPG
            nombre_jpg = f"{codigo}_{nombre}_{zona}_{cuadricula}_{hemisferio}.jpg".replace(" ", "_")
            ruta_jpg = os.path.join(carpeta_carta, nombre_jpg)
            
            if descargar_archivo(carta['url_jpg'], ruta_jpg, nombre, "JPG"):
                estadisticas['exitosas_jpg'] += 1
                estadisticas['por_zona'][zona]['exitosas_jpg'] += 1
            else:
                estadisticas['fallidas_jpg'] += 1
                estadisticas['por_zona'][zona]['fallidas_jpg'] += 1
            
            time.sleep(0.5)  # Pausa entre descargas para no saturar
    
    # Resumen final
    print(f"\n{'='*80}")
    print(f"RESUMEN DE DESCARGAS")
    print(f"{'='*80}\n")
    
    total_exitosas = estadisticas['exitosas_pdf'] + estadisticas['exitosas_jpg']
    total_fallidas = estadisticas['fallidas_pdf'] + estadisticas['fallidas_jpg']
    
    print(f"Archivos PDF:")
    print(f"  ✓ Exitosas: {estadisticas['exitosas_pdf']}/{len(cartas)}")
    print(f"  ❌ Fallidas: {estadisticas['fallidas_pdf']}/{len(cartas)}")
    
    print(f"\nArchivos JPG:")
    print(f"  ✓ Exitosas: {estadisticas['exitosas_jpg']}/{len(cartas)}")
    print(f"  ❌ Fallidas: {estadisticas['fallidas_jpg']}/{len(cartas)}")
    
    print(f"\nTOTAL:")
    print(f"  ✓ Exitosas: {total_exitosas}/{estadisticas['total']} archivos")
    print(f"  ❌ Fallidas: {total_fallidas}/{estadisticas['total']} archivos")
    
    print(f"\nDesglose por zona:")
    for zona in sorted(estadisticas['por_zona'].keys()):
        z = estadisticas['por_zona'][zona]
        print(f"  Zona {zona}:")
        print(f"    PDF: {z['exitosas_pdf']}/{z['total_cartas']} | JPG: {z['exitosas_jpg']}/{z['total_cartas']}")
    
    print(f"\n{'='*80}")
    print(f"Archivos guardados en: {os.path.abspath(output_folder)}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    inicio = time.time()
    
    # Extraer enlaces
    cartas = extraer_enlaces_descarga()
    
    if cartas:
        # Descargar archivos
        descargar_cartas(cartas)
        
        fin = time.time()
        tiempo_total = fin - inicio
        horas = int(tiempo_total // 3600)
        minutos = int((tiempo_total % 3600) // 60)
        segundos = int(tiempo_total % 60)
        
        print(f"\n⏱️  Tiempo total: {horas:02d}:{minutos:02d}:{segundos:02d}")
        print(f"✅ Proceso completado\n")
    else:
        print(f"\n❌ No se pudieron extraer las cartas\n")
