# main.py

import data_loader_module as dl
from pathlib import Path
import pandas as pd # Necesario para la carga de prueba directa
import os # Necesario para la verificación de archivo
import preprocessing_module as dl_prep

# --- CONFIGURACIÓN ---
# Define la ruta a tu archivo Excel.
# Opción 1: Ruta absoluta
FILE_PATH = Path(r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\SOCIOECONOMICOS_V2.xlsx")

# Opción 2: Ruta relativa (si SOCIOECONOMICOS_V2.xlsx está en la misma carpeta que main.py)
# SCRIPT_DIR = Path(__file__).resolve().parent
# FILE_PATH = SCRIPT_DIR / "SOCIOECONOMICOS_V2.xlsx"


if __name__ == "__main__":
    print("Herramienta de Análisis de Datos y PCA v0.7") # Incrementa la versión
    print("---------------------------------------------")

    # 1. Cargar todas las hojas
    all_sheets_data = dl.load_excel_file(FILE_PATH) 
    if not all_sheets_data: 
        print("\nNo se pudieron cargar datos del archivo Excel. Terminando.")
        exit() 

    # 2. Seleccionar hojas (indicadores)
    available_sheet_names_list = list(all_sheets_data.keys())
    selected_sheet_names = dl.prompt_select_sheets(available_sheet_names_list)
    if not selected_sheet_names:
        print("\nNo se seleccionaron hojas (indicadores). Terminando.")
        exit() 
    
    data_for_analysis_original = {name: all_sheets_data[name] for name in selected_sheet_names if name in all_sheets_data}
    
    # 3. Transformar los DataFrames seleccionados
    data_transformada_indicadores = {}
    print("\n--- Transformando Indicadores Seleccionados ---")
    if not data_for_analysis_original:
        print("  No hay datos originales para transformar.") # Esta condición puede que nunca se cumpla si selected_sheet_names no está vacío
    else:
        for nombre_indicador, df_original_indicador in data_for_analysis_original.items():
            # print(f"Transformando indicador: {nombre_indicador}...") # Ya se imprime dentro de la función
            df_transf = dl.transformar_df_indicador_v1(df_original_indicador, 
                                                       col_paises_nombre_original='Unnamed: 0', 
                                                       nuevo_nombre_indice_paises='Pais') 
            if df_transf is not None and not df_transf.empty:
                data_transformada_indicadores[nombre_indicador] = df_transf
                # print(f"  Indicador '{nombre_indicador}' transformado exitosamente.") # Ya se imprime dentro
            else:
                print(f"  Advertencia en main: No se pudo transformar el indicador '{nombre_indicador}'.")
       
    if not data_transformada_indicadores:
        print("\nNo se pudo transformar ningún indicador. Terminando.")
        exit()

    # 4. Permitir al usuario seleccionar UN país
    country_to_analyze = dl.prompt_select_country(data_transformada_indicadores) 
    if not country_to_analyze:
        print("\nNo se seleccionó un país para el análisis. Terminando.")
        exit()
    
    # 5. Consolidar los datos de los indicadores transformados para el país elegido
    df_consolidado_final_pais = dl.consolidate_data_for_country(
                                    data_transformada_indicadores, 
                                    country_to_analyze, 
                                    selected_sheet_names # Pasamos la lista original de nombres de hojas seleccionadas
                                                         # para asegurar el orden de las columnas y los nombres correctos.
                                )
                                                                                                                    
    if df_consolidado_final_pais.empty:
        print(f"\nNo se pudieron consolidar los datos para {country_to_analyze}. Terminando el programa.")
        exit()

    print(f"\n--- Datos Consolidados Finales para {country_to_analyze} (listos para ACP) ---")
    print(df_consolidado_final_pais.head())
    print("\nInformación del DataFrame consolidado final:")
    df_consolidado_final_pais.info()

  # 6. MANEJO DE DATOS FALTANTES - Permitir al usuario elegir la estrategia
    estrategia_elegida, valor_constante = dl_prep.prompt_select_imputation_strategy()

    df_imputado = df_consolidado_final_pais.copy() # Empezar con una copia
    mascara_imputados = pd.DataFrame() # Inicializar

    if estrategia_elegida and estrategia_elegida != 'ninguna':
        print(f"\nAplicando manejo de datos faltantes con estrategia: '{estrategia_elegida}'...")
        df_imputado, mascara_imputados = dl_prep.manejar_datos_faltantes(
                                            df_consolidado_final_pais, 
                                            estrategia=estrategia_elegida, 
                                            valor_relleno=valor_constante, # Se pasa el valor si la estrategia es 'valor_constante'
                                            devolver_mascara=True
                                            )
        if df_imputado.empty and not df_consolidado_final_pais.empty :
            print(f"  Advertencia: El DataFrame resultó vacío después de la estrategia de imputación '{estrategia_elegida}'.")
    elif estrategia_elegida == 'ninguna':
        print("\nSe omitió el paso de imputación de datos faltantes.")
        mascara_imputados = pd.DataFrame(False, index=df_imputado.index, columns=df_imputado.columns) # Sin imputaciones
    else: # Si prompt_select_imputation_strategy devolvió None, None
        print("\nNo se seleccionó una estrategia de imputación válida. Se omitió el paso.")
        mascara_imputados = pd.DataFrame(False, index=df_imputado.index, columns=df_imputado.columns)


    print(f"\n--- Datos Consolidados para {country_to_analyze} (DESPUÉS de intentar manejar faltantes) ---")
    print(df_imputado.head())
    print("\nInformación del DataFrame después de imputación:")
    df_imputado.info()
    print(f"Total de NaNs DESPUÉS de imputación: {df_imputado.isnull().sum().sum()}")

    if not mascara_imputados.empty:
        print(f"Total de valores imputados durante el proceso: {mascara_imputados.sum().sum()}")
    else:
        print("No se generó máscara de imputación (o no se aplicó imputación).")

    print("\n---------------------------------------------")
    print("Fin de la ejecución actual de main.py (después de intentar transformación).")