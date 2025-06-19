# PCA-SS

Herramienta en Python para el Análisis de Componentes Principales (PCA) sobre indicadores socioeconómicos.
Permite cargar datos desde archivos Excel, consolidarlos y generar visualizaciones de los resultados.

## Requisitos
- Python 3
- Pandas, NumPy, Matplotlib y scikit-learn

## Ejecución básica

El script principal es `main.py`. Por defecto utiliza rutas definidas en el código para el archivo Excel de entrada y los directorios de salida, pero puedes sobreescribirlas mediante argumentos en la línea de comandos:

```bash
python main.py --excel RUTA_EXCEL [RUTA_EXCEL2 ...] \
               --excel-output-dir DIRECTORIO_EXCEl \
               --plot-output-dir DIRECTORIO_PLOTS
```

**Argumentos**
- `--excel`: uno o varios archivos Excel con los indicadores.
- `--excel-output-dir`: carpeta donde se guardarán copias de Excel y datos transformados.
- `--plot-output-dir`: carpeta en la que se almacenarán las figuras generadas.

Si no se proporcionan argumentos, `main.py` usará las rutas por defecto especificadas en el código. Durante la ejecución se mostrará un menú interactivo para seleccionar indicadores y países antes de realizar el PCA.

