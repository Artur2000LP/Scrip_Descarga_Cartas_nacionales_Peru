import os
import zipfile
import geopandas as gpd
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime

# Configuración
# Buscar automáticamente la carpeta con más archivos ZIP
carpetas_cartas = [d for d in os.listdir('.') if d.startswith('cartas_nacionales_peru_') and os.path.isdir(d)]
if carpetas_cartas:
    # Encontrar la carpeta con más archivos ZIP
    mejor_carpeta = None
    max_zips = 0
    
    for carpeta in carpetas_cartas:
        num_zips = len([f for f in os.listdir(carpeta) if f.endswith('.zip')])
        if num_zips > max_zips:
            max_zips = num_zips
            mejor_carpeta = carpeta
    
    carpeta_zips = mejor_carpeta
    print(f"Carpeta seleccionada: {carpeta_zips} ({max_zips} archivos ZIP)")
else:
    print("ERROR: No se encontró ninguna carpeta de cartas nacionales")
    print("Asegúrate de ejecutar primero el script descarga_masiva.py")
    exit(1)

carpeta_extraidos = "shapefiles_extraidos"
archivo_geopackage = "cartas_nacionales_peru.gpkg"
nombre_capa = "cartas_nacionales_100k"

print(f"{'='*60}")
print(f"Conversión de Cartas Nacionales a GeoPackage")
print(f"{'='*60}\n")

# Paso 1: Crear carpeta para archivos extraídos
if os.path.exists(carpeta_extraidos):
    print(f"✓ Carpeta {carpeta_extraidos} ya existe, omitiendo extracción...\n")
    # Saltar la extracción
    archivos_zip = []
else:
    os.makedirs(carpeta_extraidos)
    print(f"✓ Carpeta creada: {carpeta_extraidos}\n")
    
    # Paso 2: Extraer todos los archivos ZIP
    print("Paso 1: Extrayendo archivos ZIP...")
    print("-" * 60)

    archivos_zip = [f for f in os.listdir(carpeta_zips) if f.endswith('.zip')]
    total_zips = len(archivos_zip)

    print(f"Encontrados {total_zips} archivos ZIP\n")

    extraidos = 0
    errores_extraccion = []
    for i, archivo_zip in enumerate(archivos_zip, 1):
        ruta_zip = os.path.join(carpeta_zips, archivo_zip)
        
        # Crear subcarpeta para cada carta
        nombre_carta = os.path.splitext(archivo_zip)[0]
        carpeta_destino = os.path.join(carpeta_extraidos, nombre_carta)
        
        try:
            # Intentar extracción normal
            with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                zip_ref.extractall(carpeta_destino)
            
            extraidos += 1
            if i % 50 == 0 or i == total_zips:
                print(f"  Extraídos: {i}/{total_zips} ({(i/total_zips)*100:.1f}%)")
        
        except zipfile.BadZipFile:
            errores_extraccion.append(f"{archivo_zip}: Archivo ZIP corrupto")
        except Exception as e:
            # Intentar extracción manual para archivos con problemas de rutas
            try:
                with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        # Normalizar la ruta
                        member_path = member.replace('\\', '/')
                        target_path = os.path.join(carpeta_destino, member_path)
                        
                        # Crear directorio si no existe
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # Extraer archivo
                        if not member.endswith('/'):
                            with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                                target.write(source.read())
                
                extraidos += 1
                if i % 50 == 0 or i == total_zips:
                    print(f"  Extraídos: {i}/{total_zips} ({(i/total_zips)*100:.1f}%)")
            except Exception as e2:
                errores_extraccion.append(f"{archivo_zip}: {str(e2)[:100]}")

    print(f"\n✓ {extraidos} archivos extraídos exitosamente")
    if errores_extraccion:
        print(f"⚠ {len(errores_extraccion)} errores de extracción")
        if len(errores_extraccion) <= 5:
            for error in errores_extraccion:
                print(f"  - {error}")
    print()

# Paso 3: Encontrar todos los shapefiles
print("Paso 2: Buscando archivos shapefile...")
print("-" * 60)

shapefiles = []
for root, dirs, files in os.walk(carpeta_extraidos):
    for file in files:
        if file.endswith('.shp'):
            ruta_completa = os.path.join(root, file)
            shapefiles.append(ruta_completa)

print(f"✓ Encontrados {len(shapefiles)} archivos shapefile\n")

if len(shapefiles) == 0:
    print("⚠ No se encontraron archivos shapefile.")
    print("Verifica que los archivos ZIP contengan shapefiles.")
    exit(1)

# Paso 4: Combinar todos los shapefiles en un GeoPackage
print("Paso 3: Convirtiendo a GeoPackage...")
print("-" * 60)
print("Esto puede tomar varios minutos...\n")

# Definir CRS común para todo el Perú
# Usamos WGS 84 (EPSG:4326) como CRS común porque abarca todo el territorio
crs_comun = "EPSG:4326"
print(f"CRS común seleccionado: WGS 84 (EPSG:4326)\n")

# Eliminar GeoPackage anterior si existe
if os.path.exists(archivo_geopackage):
    os.remove(archivo_geopackage)
    print(f"✓ GeoPackage anterior eliminado\n")

procesados = 0
errores = 0
gdfs = []

for i, shp in enumerate(shapefiles, 1):
    try:
        # Leer shapefile
        gdf = gpd.read_file(shp)
        
        # Reproyectar a CRS común
        if gdf.crs != crs_comun:
            gdf = gdf.to_crs(crs_comun)
        
        # Agregar columna con el nombre de la carta
        nombre_carta = os.path.basename(os.path.dirname(shp))
        gdf['carta_nacional'] = nombre_carta
        
        gdfs.append(gdf)
        procesados += 1
        
        if i % 50 == 0 or i == len(shapefiles):
            print(f"  Procesados: {i}/{len(shapefiles)} ({(i/len(shapefiles))*100:.1f}%)")
    
    except Exception as e:
        errores += 1
        if errores <= 5:  # Mostrar solo los primeros 5 errores
            print(f"  ✗ Error en {os.path.basename(shp)}: {e}")

print(f"\n✓ {procesados} shapefiles leídos correctamente")
if errores > 0:
    print(f"⚠ {errores} errores encontrados\n")

# Combinar todos los GeoDataFrames
print("\nPaso 4: Fusionando datos...")
print("-" * 60)

try:
    # Concatenar todos los GeoDataFrames
    gdf_completo = gpd.GeoDataFrame(
        pd.concat(gdfs, ignore_index=True),
        crs=gdfs[0].crs if gdfs else None
    )
    
    print(f"✓ Total de geometrías: {len(gdf_completo)}")
    print(f"✓ Sistema de coordenadas: {gdf_completo.crs}\n")
    
    # Guardar en GeoPackage
    print("Paso 5: Guardando GeoPackage...")
    print("-" * 60)
    
    gdf_completo.to_file(archivo_geopackage, layer=nombre_capa, driver="GPKG")
    
    # Obtener tamaño del archivo
    tamaño_mb = os.path.getsize(archivo_geopackage) / (1024 * 1024)
    
    print(f"\n{'='*60}")
    print(f"✓ ¡CONVERSIÓN COMPLETADA!")
    print(f"{'='*60}")
    print(f"\nArchivo creado: {archivo_geopackage}")
    print(f"Tamaño: {tamaño_mb:.2f} MB")
    print(f"Capa: {nombre_capa}")
    print(f"Total de geometrías: {len(gdf_completo)}")
    print(f"\nPuedes abrir el archivo en QGIS, ArcGIS o cualquier software GIS")
    
    # Preguntar si desea eliminar archivos extraídos
    print(f"\n{'='*60}")
    print("¿Desea eliminar la carpeta de archivos extraídos?")
    print(f"Carpeta: {carpeta_extraidos} ({len(shapefiles)} archivos)")
    respuesta = input("Escribe 'si' para eliminar o Enter para conservar: ").lower().strip()
    
    if respuesta == 'si':
        shutil.rmtree(carpeta_extraidos)
        print(f"✓ Carpeta {carpeta_extraidos} eliminada")
    else:
        print(f"✓ Carpeta {carpeta_extraidos} conservada")

except Exception as e:
    print(f"\n✗ Error al crear GeoPackage: {e}")
    import traceback
    traceback.print_exc()
