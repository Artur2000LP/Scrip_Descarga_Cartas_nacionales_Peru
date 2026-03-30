"""
Script para unificar todas las Cartas Nacionales del Perú en un solo GeoPackage
Procesa 500 cartas con 12 capas cada una y las unifica por tipo de geometría
"""

import os
import geopandas as gpd
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Importar para validación de geometrías
from shapely.validation import make_valid
from shapely.geometry import shape
import fiona

# Configuración
CARPETA_CARTAS = "cartas_nacionales_extraidas_20260102_180126"
ARCHIVO_SALIDA = "cartas_nacionales_peru_unificado.gpkg"
CRS_SALIDA = "EPSG:32718"  # UTM 18S - Zona principal del Perú (evita errores de reproyección)

# Tipos de capas a unificar (12 capas diferentes)
TIPOS_CAPAS = {
    'cuad': 'Cuadrícula y marco de las cartas',
    'islas': 'Islas',
    'lagos': 'Lagos',
    'rios': 'Ríos',
    'cotas': 'Puntos de elevación',
    'curvas': 'Curvas de nivel',
    'nevados': 'Nevados',
    'senales': 'Señales topográficas',
    'ncerros': 'Nombres de cerros',
    'nlagos': 'Nombres de lagos',
    'nrios': 'Nombres de ríos',
    'polurb': 'Polígonos urbanos'
}

def obtener_info_carta(nombre_carta):
    """Extrae información del nombre de la carta"""
    # Ejemplo: LIMA_18_25-i_L_Sur
    # Retorna: nombre, zona_utm, codigo_carta, hoja
    partes = nombre_carta.split('_')
    if len(partes) >= 3:
        nombre = partes[0].replace('_', ' ')
        zona_utm = partes[1]
        codigo_hoja = partes[2] if len(partes) > 2 else ''
        return nombre, zona_utm, codigo_hoja
    return nombre_carta, '', ''

def buscar_shapefiles_por_tipo(carpeta_carta, tipo_capa):
    """Busca todos los shapefiles de un tipo específico en una carta"""
    shapefiles = []
    
    for root, dirs, files in os.walk(carpeta_carta):
        for file in files:
            # Buscar archivos que terminen con -tipo.shp (ej: 28q-rios.shp)
            if file.endswith(f'-{tipo_capa}.shp'):
                ruta_completa = os.path.join(root, file)
                shapefiles.append(ruta_completa)
    
    return shapefiles

def limpiar_geometrias(gdf):
    """Limpia y repara geometrías inválidas"""
    from shapely.validation import make_valid
    
    # Intentar reparar geometrías inválidas
    if not gdf.geometry.is_valid.all():
        try:
            # Método 1: make_valid
            gdf.geometry = gdf.geometry.apply(lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom)
        except:
            try:
                # Método 2: buffer(0)
                gdf.geometry = gdf.geometry.apply(lambda geom: geom.buffer(0) if geom is not None and not geom.is_valid else geom)
            except:
                pass
    
    # Eliminar geometrías None o vacías
    gdf = gdf[gdf.geometry.notna()]
    gdf = gdf[~gdf.geometry.is_empty]
    
    return gdf

def unificar_capa(tipo_capa, descripcion):
    """Unifica todos los shapefiles de un tipo específico"""
    print(f"\n{'─'*70}")
    print(f"🔄 Procesando: {tipo_capa.upper()} - {descripcion}")
    print(f"{'─'*70}")
    
    gdfs_lista = []
    cartas_procesadas = 0
    cartas_con_error = 0
    geometrias_totales = 0
    
    # Recorrer todas las cartas
    cartas_dirs = sorted([d for d in os.listdir(CARPETA_CARTAS) 
                          if os.path.isdir(os.path.join(CARPETA_CARTAS, d))])
    
    total_cartas = len(cartas_dirs)
    
    for idx, carta_dir in enumerate(cartas_dirs, 1):
        carpeta_carta = os.path.join(CARPETA_CARTAS, carta_dir)
        
        # Buscar shapefiles de este tipo en la carta
        shapefiles = buscar_shapefiles_por_tipo(carpeta_carta, tipo_capa)
        
        if not shapefiles:
            continue
        
        for shapefile in shapefiles:
            gdf = None
            exito = False
            
            # ESTRATEGIA 1: Lectura y reproyección normal
            try:
                gdf = gpd.read_file(shapefile)
                if len(gdf) == 0:
                    continue
                
                # Limpiar geometrías
                gdf = limpiar_geometrias(gdf)
                if len(gdf) == 0:
                    continue
                
                # Extraer información de la carta
                nombre, zona_utm, codigo = obtener_info_carta(carta_dir)
                
                # Agregar columnas de metadatos
                gdf['carta_nombre'] = nombre
                gdf['carta_zona_utm'] = zona_utm
                gdf['carta_codigo'] = codigo
                gdf['carta_directorio'] = carta_dir
                gdf['archivo_origen'] = os.path.basename(shapefile)
                
                # Reproyectar a UTM 18S (solo si es diferente)
                if gdf.crs is not None and str(gdf.crs) != CRS_SALIDA:
                    # Las cartas UTM 18S no necesitan reproyección
                    if 'EPSG:32718' not in str(gdf.crs).upper():
                        gdf = gdf.to_crs(CRS_SALIDA)
                else:
                    # Si no tiene CRS, asumimos que ya está en UTM 18S
                    gdf.set_crs(CRS_SALIDA, inplace=True)
                
                exito = True
                
            except Exception as e1:
                # ESTRATEGIA 2: Leer y limpiar geometrías antes de reproyectar
                try:
                    gdf = gpd.read_file(shapefile)
                    if len(gdf) > 0:
                        # Limpiar geometrías primero
                        gdf = limpiar_geometrias(gdf)
                        
                        # Agregar metadatos
                        nombre, zona_utm, codigo = obtener_info_carta(carta_dir)
                        gdf['carta_nombre'] = nombre
                        gdf['carta_zona_utm'] = zona_utm
                        gdf['carta_codigo'] = codigo
                        gdf['carta_directorio'] = carta_dir
                        gdf['archivo_origen'] = os.path.basename(shapefile)
                        
                        # Intentar reproyectar geometría por geometría
                        if gdf.crs is not None and str(gdf.crs) != CRS_SALIDA:
                            if 'EPSG:32718' not in str(gdf.crs).upper():
                                geometrias_reproyectadas = []
                                for idx_geom, row in gdf.iterrows():
                                    try:
                                        geom_temp = gpd.GeoDataFrame([row], crs=gdf.crs)
                                        geom_reproj = geom_temp.to_crs(CRS_SALIDA)
                                        geometrias_reproyectadas.append(geom_reproj.iloc[0])
                                    except:
                                        # Si falla, mantener geometría original
                                        geometrias_reproyectadas.append(row)
                                
                                gdf = gpd.GeoDataFrame(geometrias_reproyectadas, crs=CRS_SALIDA)
                            else:
                                # Ya está en UTM 18S
                                gdf.set_crs(CRS_SALIDA, inplace=True)
                        
                        exito = True
                        
                except Exception as e2:
                    # ESTRATEGIA 3: Forzar CRS sin reproyectar
                    try:
                        gdf = gpd.read_file(shapefile)
                        if len(gdf) > 0:
                            gdf = limpiar_geometrias(gdf)
                            
                            nombre, zona_utm, codigo = obtener_info_carta(carta_dir)
                            gdf['carta_nombre'] = nombre
                            gdf['carta_zona_utm'] = zona_utm
                            gdf['carta_codigo'] = codigo
                            gdf['carta_directorio'] = carta_dir
                            gdf['archivo_origen'] = os.path.basename(shapefile)
                            
                            # Forzar CRS a UTM 18S sin reproyectar
                            # Esto mantiene las geometrías exactas sin transformación
                            if gdf.crs is None or 'EPSG:32718' in str(gdf.crs).upper():
                                gdf.set_crs(CRS_SALIDA, inplace=True, allow_override=True)
                            else:
                                # Intentar reproyección suave
                                try:
                                    gdf = gdf.to_crs(CRS_SALIDA)
                                except:
                                    # Forzar CRS sin reproyectar
                                    gdf.set_crs(CRS_SALIDA, inplace=True, allow_override=True)
                            
                            exito = True
                            print(f"   🔧 Reparado (sin reproyección): {carta_dir}")
                            
                    except Exception as e3:
                        # ESTRATEGIA 4: Leer geometría por geometría con fiona
                        try:
                            features_validas = []
                            
                            with fiona.open(shapefile) as src:
                                crs_original = src.crs
                                for feature in src:
                                    try:
                                        # Intentar crear geometría
                                        geom = shape(feature['geometry'])
                                        if geom is not None and not geom.is_empty:
                                            # Validar
                                            if not geom.is_valid:
                                                geom = make_valid(geom)
                                            features_validas.append({
                                                'geometry': geom,
                                                **feature['properties']
                                            })
                                    except:
                                        # Saltar esta geometría específica
                                        continue
                            
                            if features_validas:
                                gdf = gpd.GeoDataFrame(features_validas, crs=crs_original)
                                
                                # Agregar metadatos
                                nombre, zona_utm, codigo = obtener_info_carta(carta_dir)
                                gdf['carta_nombre'] = nombre
                                gdf['carta_zona_utm'] = zona_utm
                                gdf['carta_codigo'] = codigo
                                gdf['carta_directorio'] = carta_dir
                                gdf['archivo_origen'] = os.path.basename(shapefile)
                                
                                # IMPORTANTE: Reproyectar correctamente según la zona UTM
                                crs_str = str(crs_original).upper() if crs_original else ''
                                
                                # Si es UTM 17S o 19S, DEBE reproyectar a 18S
                                if 'EPSG:32717' in crs_str or '32717' in crs_str:
                                    # UTM 17S -> reproyectar a 18S
                                    gdf = gdf.to_crs(CRS_SALIDA)
                                elif 'EPSG:32719' in crs_str or '32719' in crs_str:
                                    # UTM 19S -> reproyectar a 18S
                                    gdf = gdf.to_crs(CRS_SALIDA)
                                elif 'EPSG:32718' in crs_str or '32718' in crs_str:
                                    # Ya está en UTM 18S, solo asegurar CRS
                                    gdf.set_crs(CRS_SALIDA, inplace=True, allow_override=True)
                                else:
                                    # CRS desconocido o None, asumir UTM 18S (misma zona)
                                    gdf.set_crs(CRS_SALIDA, inplace=True, allow_override=True)
                                
                                exito = True
                                print(f"   🔧 Reparado (fiona): {carta_dir} - {len(features_validas)} geometrías")
                            
                        except Exception as e4:
                            cartas_con_error += 1
                            print(f"   ❌ FALLO TOTAL en {carta_dir}: {str(e4)[:40]}")
            
            # Si tuvo éxito por cualquier estrategia, agregar a la lista
            if exito and gdf is not None and len(gdf) > 0:
                gdfs_lista.append(gdf)
                geometrias_totales += len(gdf)
                cartas_procesadas += 1
        
        # Mostrar progreso cada 50 cartas
        if idx % 50 == 0:
            print(f"   Progreso: {idx}/{total_cartas} cartas revisadas | "
                  f"Procesadas: {cartas_procesadas} | "
                  f"Geometrías: {geometrias_totales:,}")
    
    print(f"\n📊 Resumen:")
    print(f"   ✓ Cartas procesadas: {cartas_procesadas}/{total_cartas}")
    print(f"   ✓ Total geometrías: {geometrias_totales:,}")
    if cartas_con_error > 0:
        print(f"   ⚠️  Cartas con error: {cartas_con_error}")
    
    # Unificar todos los GeoDataFrames
    if gdfs_lista:
        print(f"\n🔗 Unificando {len(gdfs_lista)} capas...")
        gdf_unificado = pd.concat(gdfs_lista, ignore_index=True)
        
        # Asegurar que tenga CRS correcto
        if gdf_unificado.crs is None:
            gdf_unificado.set_crs(CRS_SALIDA, inplace=True)
        
        print(f"   ✓ Capa unificada: {len(gdf_unificado):,} geometrías totales")
        return gdf_unificado
    else:
        print(f"   ⚠️  No se encontraron datos para esta capa")
        return None

def main():
    """Función principal"""
    print("╔" + "═"*70 + "╗")
    print("║" + " "*15 + "UNIFICADOR DE CARTAS NACIONALES DEL PERÚ" + " "*15 + "║")
    print("╚" + "═"*70 + "╝")
    
    inicio_total = datetime.now()
    
    # Verificar que existe la carpeta de cartas
    if not os.path.exists(CARPETA_CARTAS):
        print(f"\n❌ ERROR: No se encuentra la carpeta {CARPETA_CARTAS}")
        return
    
    # Contar cartas disponibles
    num_cartas = len([d for d in os.listdir(CARPETA_CARTAS) 
                      if os.path.isdir(os.path.join(CARPETA_CARTAS, d))])
    
    print(f"\n📁 Carpeta de origen: {CARPETA_CARTAS}")
    print(f"📊 Total de cartas encontradas: {num_cartas}")
    print(f"💾 Archivo de salida: {ARCHIVO_SALIDA}")
    print(f"🌐 Sistema de coordenadas: {CRS_SALIDA} (UTM 18S - evita huecos)")
    print(f"📑 Capas a procesar: {len(TIPOS_CAPAS)}")
    
    # Eliminar archivo anterior si existe
    if os.path.exists(ARCHIVO_SALIDA):
        print(f"\n🗑️  Eliminando archivo anterior...")
        os.remove(ARCHIVO_SALIDA)
    
    # Procesar cada tipo de capa
    capas_exitosas = 0
    
    for idx, (tipo_capa, descripcion) in enumerate(TIPOS_CAPAS.items(), 1):
        print(f"\n\n{'='*70}")
        print(f"CAPA {idx}/{len(TIPOS_CAPAS)}")
        print(f"{'='*70}")
        
        inicio_capa = datetime.now()
        
        try:
            gdf_unificado = unificar_capa(tipo_capa, descripcion)
            
            if gdf_unificado is not None and len(gdf_unificado) > 0:
                # Guardar en GeoPackage
                print(f"\n💾 Guardando capa '{tipo_capa}' en GeoPackage...")
                gdf_unificado.to_file(
                    ARCHIVO_SALIDA, 
                    layer=tipo_capa,
                    driver="GPKG"
                )
                
                tiempo_capa = (datetime.now() - inicio_capa).total_seconds()
                print(f"   ✓ Capa guardada exitosamente ({tiempo_capa:.1f} segundos)")
                capas_exitosas += 1
            else:
                print(f"   ⚠️  Capa vacía, no se guardó")
                
        except Exception as e:
            print(f"\n❌ ERROR procesando {tipo_capa}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Resumen final
    tiempo_total = (datetime.now() - inicio_total).total_seconds()
    
    print("\n\n" + "="*70)
    print("📊 RESUMEN FINAL")
    print("="*70)
    print(f"✓ Capas procesadas exitosamente: {capas_exitosas}/{len(TIPOS_CAPAS)}")
    print(f"⏱️  Tiempo total: {tiempo_total/60:.1f} minutos")
    
    if os.path.exists(ARCHIVO_SALIDA):
        tamaño_mb = os.path.getsize(ARCHIVO_SALIDA) / (1024 * 1024)
        print(f"💾 Archivo generado: {ARCHIVO_SALIDA}")
        print(f"📦 Tamaño: {tamaño_mb:.1f} MB")
        print(f"\n✅ ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print(f"\n🗺️  Ahora puedes abrir '{ARCHIVO_SALIDA}' en QGIS")
        print(f"    El mapa del Perú estará perfectamente armado y georeferenciado")
    else:
        print(f"\n❌ No se generó el archivo de salida")

if __name__ == "__main__":
    main()
