# main.py
import data_loader_module as dl
from pathlib import Path
import pandas as pd
import numpy as np
import os
import preprocessing_module as dl_prep
import visualization_module as dl_viz
import pca_module as pca_mod

# Mostrar todas las filas al imprimir DataFrames
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

# --- DICCIONARIO DE MAPEO PARA NOMBRES DE INDICADORES ---
MAPEO_INDICADORES = {
    # --- NUEVOS INDICADORES (donde el nombre de la hoja es el nombre descriptivo) ---
    'Adjusted savings  education exp': 'Adjusted savings: education expenditure (% of GNI)',
    'Compulsory education, duration': 'Compulsory education, duration (years)',
    'Expenditure on tertiary educati': 'Expenditure on tertiary education (% of government expenditure on education)',
    'GDP growth (annual %)': 'GDP growth (annual %)',
    'GDP per capita growth (annual %': 'GDP per capita growth (annual %)',
    'GDP per capita, PPP (constant 2': 'GDP per capita, PPP (constant 2021 international $)',
    'Gov exp on educa (% of GDP)': 'Government expenditure on education, total (% of GDP)',
    'Gov exp on educa (% of gov exp)': 'Government expenditure on education, total (% of government expenditure)',
    'Poverty headc. ratio at $2.15': 'Poverty headcount ratio at $2.15 a day (2017 PPP) (% of population)',
    'Poverty headc. ratio at $3.65': 'Poverty headcount ratio at $3.65 a day (2017 PPP) (% of population)',
    'Poverty headc. ratio at $6.85': 'Poverty headcount ratio at $6.85 a day (2017 PPP) (% of population)',
    'Poverty headcount ratio at nati': 'Poverty headcount ratio at national poverty lines (% of population)',
    'Poverty headcount ratio at soci': 'Poverty headcount ratio at societal poverty line (% of population)',
    'Prop. of pop pushed below $2.15': 'Proportion of population pushed below the $2.15 ($ 2017 PPP) poverty line by out-of-pocket health care expenditure (%)',
    'Prop. of pop pushed below $3.65': 'Proportion of population pushed below the $3.65 ($ 2017 PPP) poverty line by out-of-pocket health care expenditure (%)',
    'Prop. of pop. spendi more 25%': 'Proportion of population spending more than 25% of household consumption or income on out-of-pocket health care expenditure (%)',
    'Prop. of time on unp. dom. fema': 'Proportion of time spent on unpaid domestic and care work, female (% of 24 hour day)',
    'Prop. of time on unp. dom. male': 'Proportion of time spent on unpaid domestic and care work, male (% of 24 hour day)',
    'Research and development expend': 'Research and development expenditure (% of GDP)',
    'School enroll., tertiary, femal': 'School enrollment, tertiary, female (% gross)',
    'School enroll., tertiary, male': 'School enrollment, tertiary, male (% gross)',
    'Total debt service (% of GNI)': 'Total debt service (% of GNI)',
    # Asegurarse que la CLAVE sea EXACTAMENTE el nombre de la hoja en el EXCEL :).
}

# --- CONFIGURACIÓN ---
FILE_PATH = Path(r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\INDICADORES WDI_V2.xlsx")
OUTPUT_DIR = Path(r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\Excels guardados")


if __name__ == "__main__":
    print("Herramienta de Análisis de Datos y PCA v1.1.0") # MODIFICADO: Versión incrementada, lo estoy subiendo a Github
    print("---------------------------------------------")

    # Crear el directorio de salida si no existe
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e_dir:
        print(f"ADVERTENCIA: No se pudo crear el directorio de salida: {OUTPUT_DIR}")
        print(f"           Error: {e_dir}")
        print("           Los archivos Excel se guardarán en el directorio actual del script si procede.")
        OUTPUT_DIR = Path(".")

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
        print("   No hay datos originales para transformar.")
    else:
        for nombre_indicador, df_original_indicador in data_for_analysis_original.items():
            df_transf = dl.transformar_df_indicador_v1(df_original_indicador,
                                                       col_paises_nombre_original='Unnamed: 0',
                                                       nuevo_nombre_indice_paises='Pais')
            if df_transf is not None and not df_transf.empty:
                data_transformada_indicadores[nombre_indicador] = df_transf
            else:
                print(f"   Advertencia en main: No se pudo transformar el indicador '{nombre_indicador}'.")
    
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
            print(f"   Advertencia: El DataFrame resultó vacío después de la estrategia de imputación '{nombre_estrategia_elegida}'.")
    
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
    df_estandarizado = pd.DataFrame() 
    scaler_utilizado = None

    if not df_imputado.empty:
        if df_imputado.isnull().sum().sum() > 0:
            print("\nADVERTENCIA: Aún existen NaNs en el DataFrame después de la imputación.")
            print("La estandarización podría fallar o producir resultados inesperados.")
            if input("¿Desea eliminar las filas con NaNs restantes antes de estandarizar? (s/n): ").strip().lower() == 's':
                df_imputado_sin_nans_para_scaler = df_imputado.dropna(axis=0, how='any')
                if df_imputado_sin_nans_para_scaler.empty:
                    print("   Después de eliminar filas con NaNs, el DataFrame está vacío. No se puede estandarizar.")
                else:
                    df_estandarizado, scaler_utilizado = dl_prep.estandarizar_datos(df_imputado_sin_nans_para_scaler, devolver_scaler=True)
            else:
                print("   No se aplicará estandarización debido a NaNs restantes.")
        else: 
            df_estandarizado, scaler_utilizado = dl_prep.estandarizar_datos(df_imputado, devolver_scaler=True)

        if not df_estandarizado.empty:
            print(f"\n--- DataFrame Consolidado para {country_to_analyze} (ESTANDARIZADO) ---")
            print(df_estandarizado.head())
            # df_estandarizado.info() # Ya se muestra info después, opcional aquí
            if scaler_utilizado:
                print(f"   Scaler mean: {scaler_utilizado.mean_}, Scaler var: {scaler_utilizado.var_}")
        else:
            print("\nNo se generó un DataFrame estandarizado.")
    
    # ----- NUEVO: 8. ANÁLISIS DE COMPONENTES PRINCIPALES (PCA) -----
    print("\n\n--- 8. Iniciando Análisis de Componentes Principales (PCA) ---")
    pca_model_final = None
    df_componentes_principales = pd.DataFrame()
    df_cargas = pd.DataFrame()
    df_varianza_explicada_pca = pd.DataFrame() # Para guardar en Excel

    if not df_estandarizado.empty and df_estandarizado.isnull().sum().sum() == 0:
        # a. Realizar PCA inicial (con todos los componentes para ver la varianza)
        print("   Realizando PCA inicial para análisis de varianza...")
        pca_model_inicial, _ = pca_mod.realizar_pca(df_estandarizado, n_components=None)

        if pca_model_inicial:
            # b. Obtener y mostrar varianza explicada
            evr, cum_evr = pca_mod.obtener_varianza_explicada(pca_model_inicial)
            if evr is not None and cum_evr is not None:
                print("\n   Varianza Explicada por Componente Principal (PCA Inicial):")
                df_varianza_explicada_pca = pd.DataFrame({
                    'Componente': [f'PC{i+1}' for i in range(len(evr))],
                    'Varianza Explicada': evr,
                    'Varianza Acumulada': cum_evr
                }).set_index('Componente')
                print(df_varianza_explicada_pca)

                # c. Graficar Scree Plot
                if input("\n   ¿Deseas ver el Scree Plot para ayudar a seleccionar el número de componentes? (s/n): ").strip().lower() == 's':
                    pca_mod.graficar_scree_plot(evr)

                # d. Seleccionar el número de componentes a retener
                sugg_90 = np.where(cum_evr >= 0.90)[0]
                sugg_95 = np.where(cum_evr >= 0.95)[0]
                n_sugg_90 = sugg_90[0] + 1 if len(sugg_90) > 0 else None
                n_sugg_95 = sugg_95[0] + 1 if len(sugg_95) > 0 else None
                
                n_comp_seleccionados = pca_mod.prompt_seleccionar_n_componentes(
                    pca_model_inicial.n_components_,
                    suggested_n_comp_90=n_sugg_90,
                    suggested_n_comp_95=n_sugg_95
                )

                if n_comp_seleccionados > 0:
                     # e. Realizar PCA final con el número de componentes seleccionados
                    print(f"\n   Realizando PCA final con {n_comp_seleccionados} componentes seleccionados...")
                    pca_model_final, df_componentes_principales = pca_mod.realizar_pca(df_estandarizado, n_components=n_comp_seleccionados)

                    if df_componentes_principales is not None and not df_componentes_principales.empty:
                        print(f"\n   --- Componentes Principales para {country_to_analyze} (Top {n_comp_seleccionados}) ---")
                        print(df_componentes_principales.head())
                        df_componentes_principales.info()

                        # f. Obtener y mostrar las cargas de los componentes
                        # Los nombres de las columnas de df_estandarizado son los indicadores originales
                        nombres_indicadores_pca = df_estandarizado.columns.tolist()
                        nombres_mapeados_para_cargas = [MAPEO_INDICADORES.get(code, code) for code in nombres_indicadores_pca]
                        
                        df_cargas_temp = pca_mod.obtener_cargas_pca(pca_model_final, nombres_indicadores_pca)
                        if df_cargas_temp is not None:
                            df_cargas = df_cargas_temp.copy()
                            # Renombrar índice de df_cargas para mejor legibilidad en la salida
                            df_cargas.index = nombres_mapeados_para_cargas
                            print("\n   --- Cargas de los Componentes Principales ---")
                            print(df_cargas)
                        else:
                            print("   No se pudieron obtener las cargas del PCA.")
                    else:
                        print("   No se pudieron calcular los componentes principales con el número seleccionado.")
                else:
                    print("   No se seleccionó un número válido de componentes para el PCA final. Se omite.")
            else:
                print("   No se pudo obtener la varianza explicada del PCA inicial.")
        else:
            print("   No se pudo inicializar el modelo PCA inicial.")
    elif df_estandarizado.empty:
        print("\n   El DataFrame estandarizado está vacío. No se puede realizar PCA.")
    else: # Contiene NaNs
        print("\n   El DataFrame estandarizado contiene NaNs. No se puede realizar PCA.")

    # ----- MODIFICADO: 9. VISUALIZACIÓN DE DATOS EN DIFERENTES ETAPAS -----
    print("\n\n--- 9. Visualizando Datos ---")
    if input("¿Deseas graficar las series de tiempo (Original, Imputado, Estandarizado, Componentes PCA)? (s/n): ").strip().lower() == 's':
        
        df_orig_graf = df_consolidado_original.rename(columns=MAPEO_INDICADORES)
        df_imp_graf = df_imputado.rename(columns=MAPEO_INDICADORES)
        
        dfs_a_graficar = {
            f"Original Consolidado ({country_to_analyze})": df_orig_graf,
            f"Imputado ({country_to_analyze}, Estr: {nombre_estrategia_elegida if nombre_estrategia_elegida else 'N/A'})": df_imp_graf
        }
        
        if not df_estandarizado.empty:
            df_est_graf = df_estandarizado.rename(columns=MAPEO_INDICADORES) # Renombrar aquí por si acaso
            dfs_a_graficar[f"Estandarizado ({country_to_analyze})"] = df_est_graf
        else:
            print("   (No se graficará el DataFrame estandarizado porque está vacío o no se generó).")
            
        # NUEVO: Añadir componentes principales a la visualización si existen
        if not df_componentes_principales.empty:
            # Los componentes ya tienen nombres 'PC1', 'PC2', etc. No necesitan mapeo.
            dfs_a_graficar[f"Componentes Principales ({country_to_analyze})"] = df_componentes_principales
        else:
            print("   (No se graficarán los Componentes Principales porque no se generaron o están vacíos).")
            
        if dfs_a_graficar:
           # dl_viz.graficar_series_de_tiempo(dfs_a_graficar,
            #                                 titulo_general=f"Evolución de Indicadores y Componentes para {country_to_analyze}")
            dl_viz.graficar_cada_df_en_ventana_separada(dfs_a_graficar, titulo_base_ventana=f"Evolución para {country_to_analyze}")
        else:
            print("   No hay DataFrames válidos para graficar.")


    # ----- MODIFICADO: 10. GUARDAR RESULTADOS EN EXCEL -----
    print("\n\n--- 10. Guardando Resultados en Excel ---")
    if input("¿Deseas guardar los resultados en un archivo Excel? (s/n): ").strip().lower() == 's':
        try:
            excel_filename = f"Reporte_Procesado_PCA_{country_to_analyze}_{nombre_estrategia_elegida if nombre_estrategia_elegida else 'SinImputar'}.xlsx"
            full_excel_path = OUTPUT_DIR / excel_filename
            
            saved_sheets_list = []

            with pd.ExcelWriter(full_excel_path) as writer:
                if not df_consolidado_original.empty:
                    df_consolidado_original.to_excel(writer, sheet_name='1_Original', index=True)
                    saved_sheets_list.append('1_Original')
                if not df_imputado.empty:
                    df_imputado.to_excel(writer, sheet_name='2_Imputado', index=True)
                    saved_sheets_list.append('2_Imputado')
                if not mascara_imputados.empty:
                    mascara_imputados.to_excel(writer, sheet_name='3_Mascara_Imputacion', index=True)
                    saved_sheets_list.append('3_Mascara_Imputacion')
                if not df_estandarizado.empty:
                    df_estandarizado.to_excel(writer, sheet_name='4_Estandarizado', index=True)
                    saved_sheets_list.append('4_Estandarizado')
                
                # NUEVO: Guardar resultados del PCA
                if not df_varianza_explicada_pca.empty: # Guardar la tabla de varianza explicada
                    df_varianza_explicada_pca.to_excel(writer, sheet_name='5_PCA_Varianza_Expl', index=True)
                    saved_sheets_list.append('5_PCA_Varianza_Expl')
                if not df_componentes_principales.empty:
                    df_componentes_principales.to_excel(writer, sheet_name='6_PCA_Componentes', index=True)
                    saved_sheets_list.append('6_PCA_Componentes')
                if not df_cargas.empty:
                    df_cargas.to_excel(writer, sheet_name='7_PCA_Cargas', index=True) # df_cargas ya tiene índice mapeado
                    saved_sheets_list.append('7_PCA_Cargas')

            if saved_sheets_list:
                print(f"\nArchivo Excel con múltiples hojas guardado exitosamente en: {full_excel_path}")
                print(f"El archivo contiene las siguientes hojas: {', '.join(saved_sheets_list)}.")
            else:
                print("\nNo se generaron datos para guardar en el archivo Excel.")

        except PermissionError:
            print(f"   Error de Permiso: No se pudo guardar el archivo en {full_excel_path}.")
            print("   Asegúrate de que el archivo no esté abierto y que tengas permisos de escritura en la carpeta.")
        except Exception as e_excel:
            print(f"   Error al intentar guardar el archivo Excel: {e_excel}")

    print("\n---------------------------------------------")
    print("Fin de la ejecución de la Herramienta de Análisis.")