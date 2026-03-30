# 🗺️ Script Descarga Cartas Nacionales Perú

> **Herramientas para descargar, analizar y unificar las Cartas Nacionales del IGN-Perú**

## 📋 Descripción

Conjunto de scripts en Python para automatizar la descarga masiva, análisis y procesamiento de las Cartas Nacionales del Instituto Geográfico Nacional del Perú (IGN), incluyendo la unificación de áreas protegidas.

## 🚀 Características

- **📥 Descarga masiva** de cartas en formato PDF y JPG
- **🔍 Análisis automático** de cartas existentes y faltantes  
- **🗂️ Unificación** de áreas protegidas del Perú
- **📊 Conversión** a formato GeoPackage
- **🌐 Visualización web** con mapas interactivos
- **📈 Reportes** automatizados de progreso

## 🛠️ Scripts Principales

| Script | Función |
|--------|---------|
| `descarga_masiva.py` | Descarga masiva de cartas nacionales |
| `descargar_cartas_pdf_jpg.py` | Descarga específica PDF/JPG |
| `analizar_cartas.py` | Análisis de cartas descargadas |
| `buscar_faltantes.py` | Identifica cartas faltantes |
| `unificar_cartas_nacionales.py` | Unifica cartas por zona |
| `unificar_areas_protegidas_peru.py` | Procesa áreas protegidas |
| `convertir_a_geopackage.py` | Conversión a formato GIS |
| `extraer_cartas.py` | Extracción de datos específicos |

## 📦 Instalación

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/scrip_descargaCartasNACIONALES.git
cd scrip_descargaCartasNACIONALES

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Uso Rápido

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Descarga masiva
python descarga_masiva.py

# Analizar cartas descargadas
python analizar_cartas.py

# Generar reporte de faltantes
python buscar_faltantes.py
```

## 📊 Visualización

- **`pagina_cartas.html`**: Visualizador web de cartas
- **`debug_mapa.html`**: Mapa de debug interactivo
- **`pagina_completa.html`**: Vista completa del proyecto

## 📁 Estructura del Proyecto

```
├── 📜 Scripts Python principales
├── 🌐 Páginas HTML de visualización  
├── 📊 Archivos JS de datos
├── 📋 Reportes e informes (.md)
├── 📂 data_del_peru/
│   └── Lista_Ubigeos_INEI.csv
└── 📄 Archivos de configuración
```

## 🗃️ Datos

- **Lista de Ubigeos INEI**: Códigos oficiales del INEI
- **Cartas Nacionales**: Mapas topográficos 1:100,000
- **Áreas Protegidas**: SERNANP y otras entidades

## 📄 Reportes

- `INFORME_31_DICIEMBRE_2025.md`: Informe de avance anual
- `reporte_unificacion_areas_protegidas.md`: Reporte técnico

## ⚡ Características Técnicas

- **Python 3.8+** requerido
- **Descarga paralela** para mayor velocidad
- **Manejo de errores** robusto
- **Reinicio automático** en caso de fallos
- **Logs detallados** de progreso

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📜 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🎯 Estado del Proyecto

![Status](https://img.shields.io/badge/Status-Activo-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Maintainability](https://img.shields.io/badge/Maintainability-A-brightgreen)

---

### 📞 Contacto

**Desarrollador**: Tu Nombre  
**Email**: tu-email@ejemplo.com  
**GitHub**: [@tu-usuario](https://github.com/tu-usuario)

---

⭐ **¡Dale una estrella al proyecto si te resultó útil!** ⭐