
import os
import geopandas as gpd
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


from shapely.validation import make_valid
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import fiona

def analizar_shapefile(ruta_shapefile, nombre):
    try:
        gdf = gpd.read_file(ruta_shapefile)
        print(f"\n📊 Análisis de {nombre}:")
        print(f"   - Registros: {len(gdf)}")
        print(f"   - CRS: {gdf.crs}")
        print(f"   - Tipo geometría: {gdf.geometry.geom_type.unique()}")
        print(f"   - Columnas: {list(gdf.columns)}")
        
        # Verificar geometrías válidas
        geometrias_validas = gdf.geometry.is_valid.sum()
        print(f"   - Geometrías válidas: {geometrias_validas}/{len(gdf)}")
        
        # Mostrar algunas columnas importantes si existen
        columnas_relevantes = ['NOMBRE', 'NOMBAREA', 'CATEGORIA', 'NIVEL', 'TIPO', 'ESTADO', 'AREA_HA']
        for col in columnas_relevantes:
            if col in gdf.columns:
                valores_unicos = gdf[col].nunique() if gdf[col].dtype == 'object' else 'numérico'
                print(f"   - {col}: {valores_unicos} valores únicos")
        
        return gdf
    except Exception as e:
        print(f"❌ Error al leer {nombre}: {e}")
        return None

def limpiar_geometrias(gdf, nombre):
    """Limpia y valida geometrías de un GeoDataFrame"""
    print(f"\n🧹 Limpiando geometrías de {nombre}...")
    
    # Crear copia para no modificar el original
    gdf_limpio = gdf.copy()
    
    # 1. Eliminar geometrías nulas o vacías
    geometrias_nulas = gdf_limpio.geometry.isna().sum()
    gdf_limpio = gdf_limpio[~gdf_limpio.geometry.isna()]
    if geometrias_nulas > 0:
        print(f"   ✓ Eliminadas {geometrias_nulas} geometrías nulas")
    
    # 2. Validar y reparar geometrías inválidas
    geometrias_invalidas = (~gdf_limpio.geometry.is_valid).sum()
    if geometrias_invalidas > 0:
        print(f"   🔧 Reparando {geometrias_invalidas} geometrías inválidas...")
        gdf_limpio['geometry'] = gdf_limpio.geometry.apply(
            lambda geom: make_valid(geom) if geom and not geom.is_valid else geom
        )
    
    # 3. Convertir a sistema de coordenadas uniforme (WGS84 UTM 18S)
    if gdf_limpio.crs != 'EPSG:32718':
        print(f"   🗺️ Reproyectando de {gdf_limpio.crs} a EPSG:32718...")
        gdf_limpio = gdf_limpio.to_crs('EPSG:32718')
    
    # 4. Calcular área en hectáreas
    gdf_limpio['area_calculada_ha'] = gdf_limpio.geometry.area / 10000
    
    print(f"   ✅ Registros limpiados: {len(gdf_limpio)}")
    
    return gdf_limpio

def estandarizar_columnas(gdf, nombre, tipo_area):
    """Estandariza los nombres de columnas y crea campos uniformes"""
    print(f"\n📝 Estandarizando columnas de {nombre}...")
    
    gdf_std = gdf.copy()
    
    # Agregar información del tipo de área
    gdf_std['tipo_dataset'] = tipo_area
    gdf_std['archivo_origen'] = nombre
    
    # Mapeo de posibles nombres de columnas a nombres estándar
    mapeo_columnas = {
        # Nombres comunes para nombre del área
        'NOMBRE': 'nombre_area',
        'NOMBAREA': 'nombre_area', 
        'NAME': 'nombre_area',
        'NOM_AP': 'nombre_area',
        'DENOMINATION': 'nombre_area',
        'nomb_map': 'nombre_area',  # Para areas_delimitadas
        'nombre_map': 'nombre_area',  # Para areas_declaradas
        
        # Categoría o tipo
        'CATEGORIA': 'categoria',
        'CATEGORY': 'categoria',
        'TIPO': 'categoria',
        'TYPE': 'categoria',
        'CAT_AP': 'categoria',
        'clas_map': 'categoria',  # Para areas_delimitadas
        
        # Nivel administrativo
        'NIVEL': 'nivel',
        'LEVEL': 'nivel',
        'NIV_AP': 'nivel',
        
        # Estado
        'ESTADO': 'estado',
        'STATUS': 'estado',
        'EST_AP': 'estado',
        'estado_l': 'estado',  # Para areas_delimitadas
        
        # Área
        'AREA_HA': 'area_original_ha',
        'AREA': 'area_original_ha',
        'SUP_HA': 'area_original_ha',
        
        # Resolución legal
        'resol': 'resolucion_legal',
        'resolucion': 'resolucion_legal',
        'tipo_resol': 'tipo_resolucion',
        'fecha_reso': 'fecha_resolucion',
    }
    
    # Renombrar columnas que existan
    columnas_renombradas = {}
    for col_original, col_nueva in mapeo_columnas.items():
        if col_original in gdf_std.columns:
            columnas_renombradas[col_original] = col_nueva
    
    if columnas_renombradas:
        gdf_std = gdf_std.rename(columns=columnas_renombradas)
        print(f"   ✓ Columnas renombradas: {list(columnas_renombradas.keys())}")
    
    # Crear columnas estándar si no existen
    columnas_estandar = ['nombre_area', 'categoria', 'nivel', 'estado', 'resolucion_legal', 'tipo_resolucion', 'fecha_resolucion']
    for col in columnas_estandar:
        if col not in gdf_std.columns:
            if col in ['nombre_area', 'categoria']:
                gdf_std[col] = f'Sin datos ({tipo_area})'
            else:
                gdf_std[col] = None
    
    # Agregar fecha de procesamiento
    gdf_std['fecha_procesamiento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"   ✅ Columnas estandarizadas: {len(gdf_std.columns)}")
    
    return gdf_std

def filtrar_solo_poligonos(gdf, nombre):
    """Filtra solo las geometrías de tipo polígono"""
    print(f"\n🔺 Filtrando solo polígonos de {nombre}...")
    
    # Obtener tipos de geometría únicos
    tipos_geometria = gdf.geometry.geom_type.unique()
    print(f"   📊 Tipos de geometría encontrados: {tipos_geometria}")
    
    # Filtrar solo polígonos y multipolígonos
    mask_poligonos = gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])
    gdf_poligonos = gdf[mask_poligonos].copy()
    
    print(f"   ✓ Registros originales: {len(gdf)}")
    print(f"   ✓ Polígonos encontrados: {len(gdf_poligonos)}")
    
    # Si no hay polígonos, retornar GeoDataFrame vacío
    if len(gdf_poligonos) == 0:
        print(f"   ⚠️ No se encontraron polígonos en {nombre}")
        return gpd.GeoDataFrame()
    
    return gdf_poligonos.reset_index(drop=True)

def eliminar_duplicados_espaciales(gdf, tolerancia=100):
    """Elimina polígonos duplicados basado en superposición espacial - versión optimizada"""
    print(f"\n🔍 Detectando duplicados espaciales (tolerancia: {tolerancia}m)...")
    
    if len(gdf) == 0:
        print("   ✓ No hay datos para verificar duplicados")
        return gdf
    
    # Crear índice espacial para optimizar búsquedas
    print(f"   📊 Creando índice espacial para {len(gdf)} polígonos...")
    sindex = gdf.sindex
    
    indices_a_eliminar = set()
    procesados = 0
    
    for i, (idx, row) in enumerate(gdf.iterrows()):
        if idx in indices_a_eliminar:
            continue
            
        geometria1 = row.geometry
        if geometria1.is_empty or not geometria1.is_valid:
            continue
        
        # Usar índice espacial para encontrar candidatos cercanos
        possible_matches_index = list(sindex.intersection(geometria1.bounds))
        possible_matches_index = [x for x in possible_matches_index if x != idx and x not in indices_a_eliminar]
        
        for j in possible_matches_index:
            geometria2 = gdf.loc[j, 'geometry']
            
            if geometria2.is_empty or not geometria2.is_valid:
                continue
            
            # Verificar superposición significativa (80% del área menor)
            try:
                interseccion = geometria1.intersection(geometria2)
                area_interseccion = interseccion.area
                area_minima = min(geometria1.area, geometria2.area)
                
                if area_interseccion > area_minima * 0.8:
                    # Es un duplicado, mantener el más grande
                    if geometria1.area >= geometria2.area:
                        indices_a_eliminar.add(j)
                    else:
                        indices_a_eliminar.add(idx)
                        break
            except Exception as e:
                # Si hay error en la comparación, continuar
                continue
        
        procesados += 1
        if procesados % 1000 == 0:
            print(f"   📊 Procesados {procesados}/{len(gdf)} polígonos...")
    
    # Eliminar duplicados
    if indices_a_eliminar:
        gdf_sin_duplicados = gdf.drop(indices_a_eliminar)
        print(f"   ✓ Eliminados {len(indices_a_eliminar)} duplicados espaciales")
    else:
        gdf_sin_duplicados = gdf
        print(f"   ✓ No se encontraron duplicados espaciales")
    
    return gdf_sin_duplicados.reset_index(drop=True)

def generar_reporte_unificacion(gdfs_originales, gdf_unificado, archivo_reporte):
    """Genera un reporte detallado de la unificación"""
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        f.write("# REPORTE DE UNIFICACIÓN - ÁREAS PROTEGIDAS DEL PERÚ\n")
        f.write(f"Fecha de procesamiento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## DATOS ORIGINALES\n")
        for nombre, gdf in gdfs_originales.items():
            if gdf is not None:
                f.write(f"### {nombre}\n")
                f.write(f"- Registros: {len(gdf)}\n")
                f.write(f"- CRS original: {gdf.crs}\n")
                f.write(f"- Área total (ha): {gdf.geometry.area.sum()/10000:,.2f}\n")
                if 'categoria' in gdf.columns:
                    f.write("- Categorías:\n")
                    for cat, count in gdf['categoria'].value_counts().head(10).items():
                        f.write(f"  - {cat}: {count}\n")
                f.write("\n")
        
        f.write("## RESULTADO UNIFICADO\n")
        f.write(f"- Total de registros: {len(gdf_unificado)}\n")
        f.write(f"- CRS final: {gdf_unificado.crs}\n")
        f.write(f"- Área total (ha): {gdf_unificado['area_calculada_ha'].sum():,.2f}\n")
        
        f.write("\n### Distribución por tipo de dataset:\n")
        for tipo, count in gdf_unificado['tipo_dataset'].value_counts().items():
            f.write(f"- {tipo}: {count} registros\n")
        
        f.write("\n### Distribución por categoría:\n")
        for cat, count in gdf_unificado['categoria'].value_counts().head(15).items():
            f.write(f"- {cat}: {count} registros\n")
        
        f.write("\n## ESTADÍSTICAS DE ÁREA\n")
        stats = gdf_unificado['area_calculada_ha'].describe()
        f.write(f"- Área mínima: {stats['min']:,.2f} ha\n")
        f.write(f"- Área máxima: {stats['max']:,.2f} ha\n")
        f.write(f"- Área promedio: {stats['mean']:,.2f} ha\n")
        f.write(f"- Área mediana: {stats['50%']:,.2f} ha\n")

def main():
    """Función principal"""
    print("🇵🇪 UNIFICACIÓN DE ÁREAS PROTEGIDAS DEL PERÚ")
    print("=" * 60)
    
    # Configuración
    carpeta_datos = "poligonsdeAreasProtegidasPeru"
    archivo_salida = "areas_protegidas_peru_unificado.gpkg"
    archivo_reporte = "reporte_unificacion_areas_protegidas.md"
    crs_objetivo = "EPSG:32718"  # UTM 18S
    
    # Archivos de entrada
    archivos_entrada = {
        "areas_declaradas": os.path.join(carpeta_datos, "declarados.shp"),
        "areas_delimitadas": os.path.join(carpeta_datos, "delimitados.shp"),
        "pqn_cam_sigda": os.path.join(carpeta_datos, "PQN_CAM_SIGDA.shp")
    }
    
    # Verificar que la carpeta existe
    if not os.path.exists(carpeta_datos):
        print(f"❌ Error: La carpeta {carpeta_datos} no existe")
        return
    
    # Paso 1: Cargar y analizar archivos
    print("\n📂 PASO 1: CARGANDO Y ANALIZANDO ARCHIVOS")
    print("-" * 60)
    
    gdfs_originales = {}
    for nombre, ruta in archivos_entrada.items():
        if os.path.exists(ruta):
            gdf = analizar_shapefile(ruta, nombre)
            gdfs_originales[nombre] = gdf
        else:
            print(f"⚠️ Archivo no encontrado: {ruta}")
            gdfs_originales[nombre] = None
    
    # Paso 2: Limpiar geometrías
    print("\n🧹 PASO 2: LIMPIANDO GEOMETRÍAS")
    print("-" * 60)
    
    gdfs_limpios = {}
    for nombre, gdf in gdfs_originales.items():
        if gdf is not None:
            gdf_limpio = limpiar_geometrias(gdf, nombre)
            # Filtrar solo polígonos después de limpiar
            gdf_poligonos = filtrar_solo_poligonos(gdf_limpio, nombre)
            if len(gdf_poligonos) > 0:
                gdfs_limpios[nombre] = gdf_poligonos
            else:
                print(f"   ⚠️ {nombre} no contiene polígonos, se excluye del análisis")
    
    # Paso 3: Estandarizar columnas
    print("\n📝 PASO 3: ESTANDARIZANDO COLUMNAS")
    print("-" * 60)
    
    gdfs_estandarizados = {}
    tipos_area = {
        "areas_declaradas": "Áreas Declaradas",
        "areas_delimitadas": "Áreas Delimitadas", 
        "pqn_cam_sigda": "PQN CAM SIGDA"
    }
    
    for nombre, gdf in gdfs_limpios.items():
        gdf_std = estandarizar_columnas(gdf, nombre, tipos_area[nombre])
        gdfs_estandarizados[nombre] = gdf_std
    
    # Paso 4: Unificar datasets
    print("\n🔗 PASO 4: UNIFICANDO DATASETS")
    print("-" * 60)
    
    # Concatenar todos los GeoDataFrames
    gdfs_para_unir = [gdf for gdf in gdfs_estandarizados.values() if gdf is not None]
    
    if not gdfs_para_unir:
        print("❌ No hay datos para unificar")
        return
    
    print(f"   📊 Uniendo {len(gdfs_para_unir)} datasets...")
    gdf_unificado = pd.concat(gdfs_para_unir, ignore_index=True)
    
    # Paso 5: Eliminar duplicados espaciales
    print("\n🔍 PASO 5: ELIMINANDO DUPLICADOS ESPACIALES")
    print("-" * 60)
    
    gdf_final = eliminar_duplicados_espaciales(gdf_unificado, tolerancia=50)
    
    # Paso 6: Guardar resultado
    print("\n💾 PASO 6: GUARDANDO RESULTADO")
    print("-" * 60)
    
    # Guardar SOLO como GeoPackage (archivo único)
    print(f"   📁 Guardando como GeoPackage (archivo único): {archivo_salida}")
    gdf_final.to_file(archivo_salida, driver="GPKG", layer="areas_protegidas_peru")
    print(f"   ✅ Archivo único generado exitosamente")
    
    # Eliminar archivos shapefile si existen (para dejar solo el archivo único)
    archivos_shp = [
        archivo_salida.replace('.gpkg', '.shp'),
        archivo_salida.replace('.gpkg', '.dbf'),
        archivo_salida.replace('.gpkg', '.prj'),
        archivo_salida.replace('.gpkg', '.cpg'),
        archivo_salida.replace('.gpkg', '.shx')
    ]
    
    for archivo_shp in archivos_shp:
        if os.path.exists(archivo_shp):
            os.remove(archivo_shp)
            print(f"   🗑️ Eliminado: {os.path.basename(archivo_shp)}")
    
    # Paso 7: Generar reporte
    print("\n📊 PASO 7: GENERANDO REPORTE")
    print("-" * 60)
    
    generar_reporte_unificacion(gdfs_originales, gdf_final, archivo_reporte)
    
    # Resumen final
    print("\n✅ UNIFICACIÓN COMPLETADA")
    print("=" * 60)
    print(f"📊 Total de áreas protegidas unificadas: {len(gdf_final)}")
    print(f"🗺️ Sistema de coordenadas: {gdf_final.crs}")
    print(f"📐 Área total: {gdf_final['area_calculada_ha'].sum():,.2f} hectáreas")
    print(f"📁 Archivo de salida: {archivo_salida}")
    print(f"📄 Reporte detallado: {archivo_reporte}")
    
    # Mostrar top 10 áreas más grandes
    print(f"\n🏔️ TOP 10 ÁREAS PROTEGIDAS MÁS GRANDES:")
    top_areas = gdf_final.nlargest(10, 'area_calculada_ha')[['nombre_area', 'categoria', 'area_calculada_ha']]
    for i, (_, row) in enumerate(top_areas.iterrows(), 1):
        print(f"{i:2d}. {row['nombre_area']} ({row['categoria']}) - {row['area_calculada_ha']:,.0f} ha")

if __name__ == "__main__":
    main()