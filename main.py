# main.py

import data_loader_module as dl
from pathlib import Path
import pandas as pd # Necesario para la carga de prueba directa
import os # Necesario para la verificación de archivo

# --- CONFIGURACIÓN ---
# Define la ruta a tu archivo Excel.
# Opción 1: Ruta absoluta
FILE_PATH = Path(r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\SOCIOECONOMICOS_V1.xlsx")

# Opción 2: Ruta relativa (si SOCIOECONOMICOS_V1.xlsx está en la misma carpeta que main.py)
# SCRIPT_DIR = Path(__file__).resolve().parent
# FILE_PATH = SCRIPT_DIR / "SOCIOECONOMICOS_V1.xlsx"


if __name__ == "__main__":
    print("Herramienta de Análisis de Datos y PCA v0.4") # Versión actualizada
    print("---------------------------------------------")

    # --- VERIFICACIÓN PREVIA DE ARCHIVO EN MAIN.PY (Útil para depuración inicial) ---
    print(f"DEBUG MAIN: La ruta del archivo es: {FILE_PATH}")
    print(f"DEBUG MAIN: ¿El archivo existe en esta ruta? {os.path.exists(FILE_PATH)}")
    print(f"DEBUG MAIN: ¿Es un archivo? {os.path.isfile(FILE_PATH)}")

    if not os.path.exists(FILE_PATH) or not os.path.isfile(FILE_PATH):
        print("Error CRÍTICO en MAIN: El archivo especificado no existe o no es un archivo. Verifica FILE_PATH.")
        exit()
    
    # --- INTENTO DE CARGA DE PRUEBA DIRECTA EN MAIN.PY (Útil para depuración inicial) ---
    print("DEBUG MAIN: Intentando una carga de prueba muy básica del archivo Excel...")
    try:
        test_excel_file = pd.ExcelFile(FILE_PATH)
        test_sheet_names = test_excel_file.sheet_names
        print(f"DEBUG MAIN: Carga de prueba directa exitosa. Hojas encontradas: {test_sheet_names}")
        if not test_sheet_names:
            print("DEBUG MAIN: Carga de prueba directa exitosa, PERO el archivo no tiene hojas.")
    except Exception as e_test_load:
        print(f"Error CRÍTICO en MAIN durante la carga de prueba directa: {e_test_load}")
        import traceback
        traceback.print_exc()
        print("Terminando debido a error en carga de prueba directa.")
        exit()
    
    print("DEBUG MAIN: Pasando a llamar a dl.load_excel_file...")
    # --- FIN DE VERIFICACIÓN PREVIA Y CARGA DE PRUEBA ---

    # 1. Cargar todas las hojas del archivo Excel usando el módulo
    all_sheets_data = dl.load_excel_file(FILE_PATH) 

    if not all_sheets_data: 
        print("\nNo se pudieron cargar datos del archivo Excel (llamada a dl.load_excel_file falló). Terminando el programa.")
        exit() 

    # 2. Permitir al usuario seleccionar las hojas (indicadores)
    available_sheet_names_list = list(all_sheets_data.keys())
    selected_sheet_names = dl.prompt_select_sheets(available_sheet_names_list)

    if not selected_sheet_names:
        print("\nNo se seleccionaron hojas (indicadores) para el análisis. Terminando el programa.")
        exit() 
    
    # Filtrar para obtener solo los DataFrames de las hojas seleccionadas
    data_for_analysis_original = {}
    for name in selected_sheet_names:
        if name in all_sheets_data: 
            data_for_analysis_original[name] = all_sheets_data[name]
    
    print("\n--- DataFrames de Indicadores Seleccionados (ANTES de transformar) ---")
    if not data_for_analysis_original:
        print("  ADVERTENCIA: El diccionario de datos originales para análisis está vacío.")
    else:
        for sheet_name, df_content in data_for_analysis_original.items():
            print(f"\nIndicador (Hoja): {sheet_name}")
            if df_content is not None and not df_content.empty:
                print(df_content.head())
            else:
                print("  (DataFrame es None o está vacío)")
    
    # 3. Transformar los DataFrames seleccionados
    data_transformada_indicadores = {}
    print("\n--- Transformando Indicadores Seleccionados ---")
    if not data_for_analysis_original:
        print("  No hay datos para transformar.")
    else:
        for nombre_indicador, df_original_indicador in data_for_analysis_original.items():
            print(f"Transformando indicador: {nombre_indicador}...")
            
            # Asegúrate de que 'Unnamed: 0' sea el nombre correcto de tu columna de países
            # en el formato de tu Excel V1, o ajústalo.
            df_transf = dl.transformar_df_indicador_v1(df_original_indicador, 
                                                       col_paises_nombre_original='Unnamed: 0', 
                                                       nuevo_nombre_indice_paises='Pais') 
            
            if df_transf is not None and not df_transf.empty:
                data_transformada_indicadores[nombre_indicador] = df_transf
                print(f"  Indicador '{nombre_indicador}' transformado exitosamente.")
                print("  Primeras filas del DataFrame transformado:")
                print(df_transf.head())
            else:
                print(f"  Advertencia: No se pudo transformar el indicador '{nombre_indicador}' o resultó vacío.")
       
    if not data_transformada_indicadores:
        print("\nNo se pudo transformar ningún indicador seleccionado o todos resultaron vacíos. Terminando el programa.")
        exit()

    print("\n--- DataFrames de Indicadores TRANSFORMADOS (primeras filas) ---")
    # Este bloque es para verificar el resultado de la transformación
    for sheet_name, df_content in data_transformada_indicadores.items():
        print(f"\nIndicador Transformado (Hoja Original): {sheet_name}")
        if df_content is not None and not df_content.empty:
            print(df_content.head())
            print(f"  Índice: {df_content.index.name} (Tipo: {df_content.index.dtype})")
            print(f"  Columnas (Países): {df_content.columns.tolist()[:5]}...") # Muestra solo las primeras 5 para no saturar
        else:
            print("  (DataFrame transformado es None o está vacío)")

    # 4. PRÓXIMO PASO: Permitir al usuario seleccionar UN país de los disponibles en los DFs transformados
    # country_to_analyze = dl.prompt_select_country(data_transformada_indicadores) 

    # if not country_to_analyze:
    #     print("\nNo se seleccionó un país para el análisis. Terminando el programa.")
    #     exit()
    
    # print(f"\nPaís seleccionado para análisis final: {country_to_analyze}")

    # 5. PRÓXIMO PASO: Consolidar los datos de los indicadores transformados para el país elegido
    # df_consolidado_final_pais = dl.consolidate_data_for_country(data_transformada_indicadores, country_to_analyze, selected_sheet_names)
                                                                                                                    
    # if df_consolidado_final_pais.empty:
    #     print(f"No se pudieron consolidar los datos para {country_to_analyze}. Terminando el programa.")
    #     exit()

    # print(f"\n--- Datos Consolidados Finales para {country_to_analyze} (listos para ACP) ---")
    # print(df_consolidado_final_pais.head())
    # df_consolidado_final_pais.info()

    print("\n---------------------------------------------")
    print("Fin de la ejecución actual de main.py (después de intentar transformación).")