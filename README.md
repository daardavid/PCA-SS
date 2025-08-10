# PCA-SS: Análisis de Componentes Principales para Datos Socioeconómicos

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg)

Una aplicación completa para realizar análisis PCA (Análisis de Componentes Principales) sobre datos socioeconómicos con interfaz gráfica intuitiva.

## 🎯 Características Principales

- **Interfaz Gráfica Intuitiva**: GUI moderna construida con Tkinter
- **Múltiples Tipos de Análisis**: 
  - Serie de tiempo (análisis longitudinal)
  - Corte transversal (comparación entre países)
  - Panel 3D (trayectorias temporales)
- **Gestión Robusta de Datos Faltantes**: 10+ estrategias de imputación
- **Visualizaciones Profesionales**: Gráficos interactivos y exportables
- **Sistema de Proyectos**: Guarda y carga configuraciones completas
- **Soporte Multiidioma**: Español e Inglés
- **Exportación de Resultados**: Formatos Excel y SVG

## 🚀 Instalación Rápida

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clona o descarga el proyecto**:
```bash
git clone https://github.com/daardavid/PCA-SS.git
cd PCA-SS
```

2. **Instala las dependencias**:
```bash
pip install -r requirements.txt
```

3. **Verifica la instalación**:
```bash
python check_dependencies.py
```

4. **Ejecuta la aplicación**:
```bash
python pca_gui.py
```

## 📋 Dependencias

### Dependencias Críticas
- `pandas>=1.5.0` - Análisis y manipulación de datos
- `numpy>=1.21.0` - Computación numérica
- `scikit-learn>=1.1.0` - Algoritmos de machine learning
- `matplotlib>=3.5.0` - Visualización de datos
- `openpyxl>=3.0.9` - Manejo de archivos Excel

### Dependencias Opcionales
- `adjustText>=0.7.3` - Mejora automática de etiquetas en gráficos

## 🎮 Guía de Uso

### 1. Crear un Nuevo Proyecto
1. Ejecuta `python pca_gui.py`
2. Ve a **Proyecto → Nuevo proyecto**
3. Asigna un nombre descriptivo

### 2. Cargar Datos
- Usa archivos Excel (.xlsx, .xls)
- Formato esperado: Primera columna con códigos de países, columnas siguientes con años
- Cada hoja representa un indicador socioeconómico

### 3. Configurar Análisis

#### Serie de Tiempo (1 país, múltiples años)
```
Proyecto → Serie de Tiempo → Seleccionar:
- Archivo de datos
- Indicadores (múltiples)
- País (uno)
- Años (múltiples)
```

#### Corte Transversal (múltiples países, años específicos)
```
Proyecto → Corte Transversal → Seleccionar:
- Archivo de datos  
- Indicadores (múltiples)
- Países (múltiples)
- Años (uno o varios)
```

#### Panel 3D (múltiples países y años)
```
Proyecto → Panel 3D → Seleccionar:
- Archivo de datos
- Indicadores (múltiples)
- Países (múltiples)  
- Años (múltiples)
```

### 4. Ejecutar Análisis
- Haz clic en **Ejecutar** junto al tipo de análisis configurado
- La aplicación manejará automáticamente datos faltantes
- Se generarán visualizaciones interactivas

## 📊 Tipos de Visualización

### Biplots 2D
- Visualiza relaciones entre países e indicadores
- Vectores muestran dirección e intensidad de indicadores
- Puntos representan países coloreados por grupos

### Gráficos 3D
- Trayectorias de países a través del tiempo
- Primeros 3 componentes principales
- Animación interactiva

### Series de Tiempo
- Evolución temporal de indicadores
- Datos originales, imputados y estandarizados
- Múltiples subplots organizados

## 🔧 Gestión de Datos Faltantes

La aplicación incluye estrategias avanzadas de imputación:

- **Interpolación**: Lineal, polinomial, spline
- **Estadísticas**: Media, mediana, moda
- **Propagación**: Forward fill, backward fill
- **Métodos Avanzados**: Imputación iterativa, KNN
- **Personalizado**: Valores constantes, eliminación de filas

## 🎨 Personalización

### Colores y Grupos
- Asigna colores personalizados a grupos de países
- Edita títulos, leyendas y pies de página
- Configura unidades y etiquetas

### Configuración Global
- Tema claro/oscuro
- Idioma (español/inglés)
- Fuentes y tamaños personalizados

## 📁 Estructura del Proyecto

```
PCA-SS/
├── pca_gui.py              # Interfaz gráfica principal
├── data_loader_module.py   # Carga y transformación de datos
├── preprocessing_module.py # Limpieza e imputación
├── pca_module.py          # Algoritmos PCA
├── visualization_module.py # Generación de gráficos
├── constants.py           # Constantes y mapeos
├── dependency_manager.py  # Gestión de dependencias
├── check_dependencies.py  # Verificador de instalación
├── project_save_config.py # Configuración de proyectos
├── i18n_es.py            # Traducciones español
├── i18n_en.py            # Traducciones inglés
├── requirements.txt       # Dependencias del proyecto
└── README.md             # Esta documentación
```

## 🧪 Testing

Para ejecutar las pruebas (próximamente):
```bash
pytest tests/
```

Para verificar el estilo de código:
```bash
black --check .
flake8 .
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

**David Armando Abreu Rosique**
- Email: davidabreu1110@gmail.com
- GitHub: [@daardavid](https://github.com/daardavid)
- Ko-fi: [Invítame un café ☕](https://ko-fi.com/daardavid)

## 🙏 Agradecimientos

- Instituto de Investigaciones Económicas de la UNAM
- Equipo de desarrollo de scikit-learn
- Comunidad de matplotlib y pandas

## 📚 Referencias

- [Documentación de scikit-learn PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)
- [Análisis de Componentes Principales - Wikipedia](https://es.wikipedia.org/wiki/An%C3%A1lisis_de_componentes_principales)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

**¿Te gusta el proyecto?** ⭐ ¡Dale una estrella en GitHub!

**¿Necesitas ayuda?** 📧 Contacta al autor o abre un issue.
