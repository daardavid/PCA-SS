# main.py
import data_loader_module as dl
from pathlib import Path
import pandas as pd # Necesario para la carga de prueba directa
import os # Necesario para la verificación de archivo
import preprocessing_module as dl_prep
import visualization_module as dl_viz

# Mostrar todas las filas al imprimir DataFrames (útil para tu depuración actual)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000) 

# --- DICCIONARIO DE MAPEO PARA NOMBRES DE INDICADORES ---
MAPEO_INDICADORES = {
    'SI.POV.LMIC': '% población de pobreza (3,20 USD día) (PPP)',
    'DT.TDS.DECT.GN.ZS': 'Servicio total de la deuda (% del GNI)', 
    'NY.GDP.PCAP.PP.KD': 'PIB per cápita, (PPP) (constant 2011 international $)',
    'NY.GDP.MKTP.KD.ZG': 'Crecimiento PIB (% anual)'
}

# --- CONFIGURACIÓN ---
# Define la ruta a tu archivo Excel.
# Opción 1: Ruta absoluta
FILE_PATH = Path(r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\SOCIOECONOMICOS_V2.xlsx")

# Opción 2: Ruta relativa (si SOCIOECONOMICOS_V2.xlsx está en la misma carpeta que main.py)
# SCRIPT_DIR = Path(__file__).resolve().parent
# FILE_PATH = SCRIPT_DIR / "SOCIOECONOMICOS_V2.xlsx"

# --- DIRECTORIO DE SALIDA PARA LOS EXCEL ---
OUTPUT_DIR = Path(r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\Excels guardados")


if __name__ == "__main__":
    print("Herramienta de Análisis de Datos y PCA v0.9.2") # Incrementa la versión
    print("---------------------------------------------")

    # Crear el directorio de salida si no existe
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e_dir:
        print(f"ADVERTENCIA: No se pudo crear el directorio de salida: {OUTPUT_DIR}")
        print(f"           Error: {e_dir}")
        print("           Los archivos Excel se guardarán en el directorio actual del script si procede.")
        OUTPUT_DIR = Path(".") # Guardar en el directorio actual como fallback

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
    if not data_for_analysis_original:
        print("  No hay datos originales para transformar.")
    else:
        for nombre_indicador, df_original_indicador in data_for_analysis_original.items():
            df_transf = dl.transformar_df_indicador_v1(df_original_indicador, 
                                                       col_paises_nombre_original='Unnamed: 0', 
                                                       nuevo_nombre_indice_paises='Pais') 
            if df_transf is not None and not df_transf.empty:
                data_transformada_indicadores[nombre_indicador] = df_transf
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
    
    # 5. Consolidar los datos para el país elegido
    df_consolidado_original = dl.consolidate_data_for_country(
                                    data_transformada_indicadores, 
                                    country_to_analyze, 
                                    selected_sheet_names
                                )
                                                                                                                    
    if df_consolidado_original.empty:
        print(f"\nNo se pudieron consolidar los datos para {country_to_analyze}. Terminando el programa.")
        exit()

    print(f"\n--- Datos Consolidados para {country_to_analyze} (ANTES de manejar faltantes) ---")
    print(df_consolidado_original.head()) 
    print("\nInformación del DataFrame consolidado (ANTES de manejar faltantes):")
    df_consolidado_original.info()
    print(f"Total de NaNs ANTES de imputación: {df_consolidado_original.isnull().sum().sum()}")

    # 6. MANEJO DE DATOS FALTANTES
    nombre_estrategia_elegida, params_para_imputacion = dl_prep.prompt_select_imputation_strategy()

    df_imputado = df_consolidado_original.copy() 
    mascara_imputados = pd.DataFrame(False, index=df_imputado.index, columns=df_imputado.columns)

    if nombre_estrategia_elegida and nombre_estrategia_elegida != 'ninguna':
        df_imputado, mascara_imputados = dl_prep.manejar_datos_faltantes(
                                            df_consolidado_original, 
                                            estrategia=nombre_estrategia_elegida,
                                            devolver_mascara=True,
                                            **params_para_imputacion 
                                        )
        if df_imputado.empty and not df_consolidado_original.empty :
            print(f"  Advertencia: El DataFrame resultó vacío después de la estrategia de imputación '{nombre_estrategia_elegida}'.")
    
    elif nombre_estrategia_elegida == 'ninguna':
        print("\nSe omitió el paso de imputación de datos faltantes.")
    else: 
        print("\nNo se seleccionó una estrategia de imputación válida. Se omitió el paso de imputación.")

    print(f"\n--- Datos Consolidados para {country_to_analyze} (DESPUÉS de intentar manejar faltantes) ---")
    print(df_imputado.head()) 
    print("\nInformación del DataFrame después de imputación:")
    df_imputado.info()
    print(f"Total de NaNs DESPUÉS de imputación: {df_imputado.isnull().sum().sum()}")

    if not mascara_imputados.empty:
        print(f"Total de valores imputados durante el proceso: {mascara_imputados.sum().sum()}")
    else:
        print("No se generó máscara de imputación (o no se aplicó imputación).")

    # 7. ESTANDARIZACIÓN DE DATOS
    # Solo estandarizar si tenemos datos después de la imputación
    df_estandarizado = pd.DataFrame() # Inicializar
    scaler_utilizado = None

    if not df_imputado.empty:
        # Verificar si aún hay NaNs después de la imputación elegida.
        # StandardScaler no maneja NaNs.
        if df_imputado.isnull().sum().sum() > 0:
            print("\nADVERTENCIA: Aún existen NaNs en el DataFrame después de la imputación.")
            print("La estandarización podría fallar o producir resultados inesperados.")
            print("Considere una estrategia de imputación que elimine todos los NaNs o 'eliminar_filas'.")
            # Opción: Preguntar al usuario si desea continuar o elegir otra imputación, o eliminar filas.
            if input("¿Desea eliminar las filas con NaNs restantes antes de estandarizar? (s/n): ").strip().lower() == 's':
                df_imputado_sin_nans_para_scaler = df_imputado.dropna(axis=0, how='any')
                if df_imputado_sin_nans_para_scaler.empty:
                    print("  Después de eliminar filas con NaNs, el DataFrame está vacío. No se puede estandarizar.")
                else:
                    df_estandarizado, scaler_utilizado = dl_prep.estandarizar_datos(df_imputado_sin_nans_para_scaler, devolver_scaler=True)
            else:
                print("  No se aplicará estandarización debido a NaNs restantes.")
        else: # No hay NaNs, se puede estandarizar directamente
            df_estandarizado, scaler_utilizado = dl_prep.estandarizar_datos(df_imputado, devolver_scaler=True)

        if not df_estandarizado.empty:
            print(f"\n--- DataFrame Consolidado para {country_to_analyze} (ESTANDARIZADO) ---")
            print(df_estandarizado.head())
            df_estandarizado.info()
            if scaler_utilizado:
                print(f"  Scaler mean: {scaler_utilizado.mean_}, Scaler var: {scaler_utilizado.var_}")
        else:
            print("\nNo se generó un DataFrame estandarizado.")

    # 8. VISUALIZACIÓN DE DATOS EN DIFERENTES ETAPAS
    print("\n--- Visualizando Datos ---")
    if input("¿Deseas graficar las series de tiempo de los datos (Original, Imputado, Estandarizado)? (s/n): ").strip().lower() == 's':
        
        # Renombrar columnas ANTES de pasarlas a la función de graficado
        df_orig_graf = df_consolidado_original.rename(columns=MAPEO_INDICADORES)
        df_imp_graf = df_imputado.rename(columns=MAPEO_INDICADORES)
        
        dfs_a_graficar = {
            f"Original Consolidado ({country_to_analyze})": df_orig_graf,
            f"Imputado ({country_to_analyze}, Estr: {nombre_estrategia_elegida if nombre_estrategia_elegida else 'N/A'})": df_imp_graf
        }
        
        if not df_estandarizado.empty:
            # df_estandarizado ya tiene los nombres de columna correctos si df_imputado los tenía
            # (porque estandarizar_datos preserva los nombres de columna)
            # PERO, si estandarizar_datos fue llamado con df_consolidado_original (que tenía códigos),
            # entonces df_estandarizado tendría códigos.
            # Para ser seguros, renombramos aquí también si df_estandarizado se basó en un df con códigos.
            # Asumiendo que df_estandarizado tiene las mismas columnas (o un subconjunto) que df_imputado:
            df_est_graf = df_estandarizado.rename(columns=MAPEO_INDICADORES)
            dfs_a_graficar[f"Estandarizado ({country_to_analyze})"] = df_est_graf
        else:
            print("  (No se graficará el DataFrame estandarizado porque está vacío o no se generó).")
            
        if dfs_a_graficar:
            # No es necesario modificar dl_viz.graficar_series_de_tiempo
            # si ya itera sobre las columnas del DataFrame para las leyendas.
            dl_viz.graficar_series_de_tiempo(dfs_a_graficar, 
                                             titulo_general=f"Evolución de Indicadores para {country_to_analyze}")
        else:
            print("  No hay DataFrames válidos para graficar.")


    # 9. OPCIÓN DE GUARDAR EN UN ÚNICO ARCHIVO EXCEL CON MÚLTIPLES HOJAS
    if input("\n¿Deseas guardar los resultados en un archivo Excel? (s/n): ").strip().lower() == 's':
        try:
            # Nombre base para el archivo Excel
            # Actualizamos el nombre para reflejar que puede incluir datos estandarizados
            excel_filename = f"Reporte_Procesado_{country_to_analyze}_{nombre_estrategia_elegida if nombre_estrategia_elegida else 'SinImputar'}.xlsx"
            full_excel_path = OUTPUT_DIR / excel_filename
            
            with pd.ExcelWriter(full_excel_path) as writer: 
                df_consolidado_original.to_excel(writer, sheet_name='1_Datos_Originales', index=True)
                df_imputado.to_excel(writer, sheet_name='2_Datos_Imputados', index=True)
                
                if not mascara_imputados.empty:
                    mascara_imputados.to_excel(writer, sheet_name='3_Mascara_Imputacion', index=True)
                else:
                    pd.DataFrame([{'mensaje': 'No se generó máscara de imputación.'}]).to_excel(writer, sheet_name='3_Mascara_Imputacion', index=False)

                # Añadir la hoja con los datos estandarizados
                if 'df_estandarizado' in locals() and not df_estandarizado.empty: # Verifica si df_estandarizado existe y no está vacío
                    df_estandarizado.to_excel(writer, sheet_name='4_Datos_Imput_Estandarizados', index=True)
                    sheet_names_saved = "'1_Datos_Originales', '2_Datos_Imputados', '3_Mascara_Imputacion', '4_Datos_Imput_Estandarizados'"
                else:
                    pd.DataFrame([{'mensaje': 'No se generaron datos estandarizados o estaban vacíos.'}]).to_excel(writer, sheet_name='4_Datos_Imput_Estandarizados', index=False)
                    sheet_names_saved = "'1_Datos_Originales', '2_Datos_Imputados', '3_Mascara_Imputacion' (Estandarización no disponible)"


            print(f"\nArchivo Excel con múltiples hojas guardado exitosamente en: {full_excel_path}")
            print(f"El archivo contiene las siguientes hojas: {sheet_names_saved}.")

        except PermissionError:
            print(f"  Error de Permiso: No se pudo guardar el archivo en {full_excel_path}.")
            print("  Asegúrate de que el archivo no esté abierto y que tengas permisos de escritura en la carpeta.")
        except Exception as e_excel:
            print(f"  Error al intentar guardar el archivo Excel: {e_excel}")
            print("  Asegúrate de tener instalada una librería para manejar Excel, como 'openpyxl': pip install openpyxl")

    # ... (el resto de tus prints finales)
    print("\n---------------------------------------------")
    print("Fin de la ejecución actual de main.py.")