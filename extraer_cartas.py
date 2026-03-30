import os
import zipfile
from pathlib import Path
from datetime import datetime
import time
import subprocess
import shutil

def extraer_zip_manteniendo_nombre(ruta_zip, carpeta_destino, max_intentos=3):
    """
    Extrae un archivo ZIP manteniendo el nombre del archivo ZIP como nombre de carpeta
    Reintenta hasta max_intentos veces si falla, usando métodos alternativos
    """
    nombre_archivo = os.path.basename(ruta_zip)
    nombre_sin_ext = nombre_archivo.replace('.zip', '')
    ruta_destino = os.path.join(carpeta_destino, nombre_sin_ext)
    
    # Si la carpeta ya existe, mostrar mensaje y saltar
    if os.path.exists(ruta_destino):
        print(f"  ⏭️  Ya existe: {nombre_sin_ext}")
        return True
    
    # Reintentar hasta max_intentos veces
    for intento in range(1, max_intentos + 1):
        try:
            # Crear carpeta
            os.makedirs(ruta_destino, exist_ok=True)
            
            # Método 1: zipfile de Python (intentos 1-2)
            if intento <= 2:
                with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                    zip_ref.extractall(ruta_destino)
                
                print(f"  ✓ Extraído: {nombre_sin_ext}")
                return True
            
            # Método 2: PowerShell Expand-Archive (intento 3)
            else:
                print(f"  ⚠️  Intentando con método alternativo (PowerShell)...")
                ruta_zip_abs = os.path.abspath(ruta_zip)
                ruta_destino_abs = os.path.abspath(ruta_destino)
                
                cmd = f'powershell -Command "Expand-Archive -Path \'{ruta_zip_abs}\' -DestinationPath \'{ruta_destino_abs}\' -Force"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"  ✓ Extraído: {nombre_sin_ext} (método alternativo)")
                    return True
                else:
                    raise Exception(f"PowerShell falló: {result.stderr[:50]}")
            
        except zipfile.BadZipFile as e:
            if intento < max_intentos:
                print(f"  ⚠️  Intento {intento}/{max_intentos} falló, reintentando...")
                time.sleep(0.5)
            else:
                print(f"  ✗ Error: {nombre_archivo} no se pudo extraer después de {max_intentos} intentos")
                if os.path.exists(ruta_destino):
                    shutil.rmtree(ruta_destino)
                return False
                
        except Exception as e:
            if intento < max_intentos:
                print(f"  ⚠️  Intento {intento}/{max_intentos} falló: {str(e)[:50]}, reintentando...")
                time.sleep(0.5)
            else:
                print(f"  ✗ Error al extraer {nombre_archivo}: {str(e)[:80]}")
                if os.path.exists(ruta_destino):
                    shutil.rmtree(ruta_destino)
                return False
    
    return False

def extraer_todas_las_cartas(carpeta_origen=None, carpeta_destino=None):
    """
    Extrae todas las cartas ZIP encontradas manteniendo los nombres originales
    """
    # Generar nombre de carpeta con timestamp si no se especifica
    if carpeta_destino is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        carpeta_destino = f"cartas_nacionales_extraidas_{timestamp}"
    
    # Si no se especifica carpeta origen, buscar carpetas de descargas
    if carpeta_origen is None:
        carpetas = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('cartas_nacionales_peru_')]
        
        if carpetas:
            carpetas.sort(reverse=True)
            carpeta_origen = carpetas[0]
            print(f"📁 Usando carpeta: {carpeta_origen}\n")
        else:
            carpeta_origen = '.'
            print("📁 Buscando archivos ZIP en el directorio actual...\n")
    
    # Crear carpeta destino
    os.makedirs(carpeta_destino, exist_ok=True)
    
    # Buscar todos los archivos ZIP
    archivos_zip = []
    for root, dirs, files in os.walk(carpeta_origen):
        for file in files:
            if file.endswith('.zip'):
                archivos_zip.append(os.path.join(root, file))
    
    if not archivos_zip:
        print(f"⚠️  No se encontraron archivos ZIP en {carpeta_origen}")
        return
    
    # Ordenar archivos
    archivos_zip.sort()
    
    print(f"{'='*80}")
    print(f"EXTRACCIÓN DE CARTAS NACIONALES")
    print(f"{'='*80}")
    print(f"📂 Carpeta origen: {os.path.abspath(carpeta_origen)}")
    print(f"📁 Carpeta destino: {os.path.abspath(carpeta_destino)}")
    print(f"Archivos ZIP encontrados: {len(archivos_zip)}")
    print(f"{'='*80}\n")
    
    exitosos = 0
    fallidos = 0
    archivos_fallidos = []
    
    for i, ruta_zip in enumerate(archivos_zip, 1):
        nombre_archivo = os.path.basename(ruta_zip)
        print(f"[{i}/{len(archivos_zip)}] {nombre_archivo}")
        
        if extraer_zip_manteniendo_nombre(ruta_zip, carpeta_destino):
            exitosos += 1
        else:
            fallidos += 1
            archivos_fallidos.append({
                'archivo': os.path.basename(ruta_zip),
                'ruta': ruta_zip
            })
    
    print(f"\n{'='*80}")
    print(f"EXTRACCIÓN COMPLETADA")
    print(f"{'='*80}")
    print(f"✓ Exitosas: {exitosos}/{len(archivos_zip)}")
    print(f"✗ Fallidas: {fallidos}/{len(archivos_zip)}")
    
    # Mostrar archivos fallidos
    if archivos_fallidos:
        print(f"\n{'='*80}")
        print(f"⚠️  ARCHIVOS QUE FALLARON ({len(archivos_fallidos)}):")
        print(f"{'='*80}")
        for item in archivos_fallidos:
            print(f"  ✗ {item['archivo']}")
        
        # Guardar lista de fallidos
        with open('archivos_zip_fallidos.txt', 'w', encoding='utf-8') as f:
            f.write(f"Archivos ZIP que fallaron en la extracción\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            for item in archivos_fallidos:
                f.write(f"{item['archivo']}\n")
                f.write(f"Ruta completa: {item['ruta']}\n\n")
        
        print(f"\n💾 Lista guardada en: archivos_zip_fallidos.txt")
        print(f"   Estos archivos necesitan ser re-descargados")
    
    print(f"\nCartas extraídas en: {os.path.abspath(carpeta_destino)}")
    print(f"\n💡 IMPORTANTE: El nombre de cada carpeta mantiene el nombre original del ZIP")
    print(f"   Ejemplo: 12-o_NUEVA ESPERANZA.zip → 12-o_NUEVA ESPERANZA/")
    print(f"{'='*80}")

if __name__ == "__main__":
    import sys
    
    try:
        if len(sys.argv) > 1:
            carpeta_origen = sys.argv[1]
            carpeta_destino = sys.argv[2] if len(sys.argv) > 2 else None
            extraer_todas_las_cartas(carpeta_origen, carpeta_destino)
        else:
            extraer_todas_las_cartas()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Extracción interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
