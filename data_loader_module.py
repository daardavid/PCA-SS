# data_loader_module.py
import pandas as pd
import numpy as np
from functools import reduce 
import traceback
1
def load_excel_file(file_path):
    # PRINT DE DEPURACIÓN INMEDIATO AL ENTRAR A LA FUNCIÓN
    print(f"DEBUG MODULE: Función load_excel_file llamada con ruta: {file_path}")
    print(f"DEBUG MODULE: Tipo de file_path: {type(file_path)}")
    
    try:
        print(f"DEBUG MODULE: Intentando pd.ExcelFile() con: {file_path}")
        # Bloque try-except para la apertura inicial del archivo y obtención de nombres de hojas
        try:
            excel_data = pd.ExcelFile(file_path)
            sheet_names = excel_data.sheet_names
            print(f"\n--- MODULE Cargando hojas del archivo: {file_path} ---")
            print(f"DEBUG MODULE: Hojas encontradas en el archivo: {sheet_names}")
        except Exception as e_open: # Error específico al abrir o leer nombres de hojas
            print(f"MODULE Error al intentar abrir el archivo Excel o leer nombres de hojas '{file_path}': {e_open}")
            print("---------- MODULE TRACEBACK DETALLADO (apertura/nombres hoja) ----------")
            traceback.print_exc()
            print("-------------------------------------------------------------------")
            return None # Retornar None si la apertura inicial falla

        dataframes = {} # Mover la inicialización aquí, después de confirmar que sheet_names existe

        if not sheet_names:
            print("Advertencia MODULE: El archivo Excel no contiene hojas.")
            return {} # Retornar diccionario vacío si no hay hojas

        for sheet_name in sheet_names:
            try:
                print(f"DEBUG MODULE: Intentando parsear la hoja '{sheet_name}'")
                df = excel_data.parse(sheet_name)
                dataframes[sheet_name] = df
                print(f"  MODULE Hoja '{sheet_name}' cargada exitosamente.")
            except Exception as e_parse:
                print(f"  MODULE Error al parsear la hoja '{sheet_name}'.")
                print(f"  MODULE Detalle del error: {e_parse}")
                print("---------- MODULE TRACEBACK DETALLADO (parseo hoja) ----------")
                traceback.print_exc()
                print("---------------------------------------------------------")

        if not dataframes: # Si ninguna hoja se pudo parsear correctamente
            print(f"Advertencia MODULE: No se pudo parsear ninguna hoja de datos válida del archivo (diccionario 'dataframes' está vacío).")
        
        print(f"DEBUG MODULE: Retornando 'dataframes'. Es vacío? {not bool(dataframes)}")
        return dataframes
           
    except FileNotFoundError: # Este except es para pd.ExcelFile(file_path)
        print(f"MODULE Error: Archivo no encontrado en la ruta: {file_path}")
        return None 
           
    except Exception as e_load: # Otro error genérico para pd.ExcelFile(file_path)
        print(f"MODULE Error CRÍTICO (inesperado) al procesar el archivo Excel '{file_path}': {e_load}")
        print("---------- MODULE TRACEBACK DETALLADO (carga general) ----------")
        traceback.print_exc() 
        print("-----------------------------------------------------------")
        return None

def prompt_select_sheets(available_sheet_names):
    """
    Permite al usuario seleccionar hojas (indicadores) de una lista.
    Ahora incluye la opción de escribir 'TODOS' para seleccionar todas las hojas.

    Args:
        available_sheet_names (list): Lista de nombres de hojas disponibles.

    Returns:
        list: Lista de nombres de hojas seleccionadas. Vacía si no se selecciona ninguna.
    """
    if not available_sheet_names:
        print("No hay hojas disponibles para seleccionar.")
        return []

    print("\n--- Hojas (Indicadores) Disponibles para Selección ---")
    for i, sheet_name in enumerate(available_sheet_names):
        print(f"  {i+1}. {sheet_name}")

    selected_names_final = []
    while True:
        # Mensaje del prompt para el usuario
        prompt_message = (
            "Ingresa los números de las hojas/indicadores que quieres usar, separados por comas (ej. 1,3),\n"
            "escribe 'TODOS' para seleccionar todas, o deja vacío para no seleccionar ninguna: "
        )
        selection_str = input(prompt_message)

        # Comprobar si el usuario escribió 'TODOS' (insensible a mayúsculas/minúsculas)
        if selection_str.strip().lower() == 'todos':
            print("\n--- Todas las Hojas/Indicadores Seleccionados ---")
            # No es necesario imprimir todos aquí, main.py ya lo hace con los seleccionados.
            # Pero si quieres una confirmación inmediata:
            # for name in available_sheet_names:
            #     print(f"  - {name}")
            return available_sheet_names  # Devuelve la lista completa de nombres de hojas

        # Comprobar si la entrada está vacía
        if not selection_str.strip():
            print("No se seleccionó ninguna hoja.")
            return []

        try:
            selected_indices = [int(idx.strip()) - 1 for idx in selection_str.split(',')]
            temp_selected_names = []
            valid_selection_made = False
            for i in selected_indices:
                if 0 <= i < len(available_sheet_names):
                    temp_selected_names.append(available_sheet_names[i])
                    valid_selection_made = True
                else:
                    print(f"Advertencia: El número {i+1} está fuera de rango y será ignorado.")

            if not valid_selection_made and temp_selected_names: # Si solo hubo inválidos pero se intentó algo
                 print("Todos los números ingresados estaban fuera de rango. Intenta de nuevo.")
                 continue


            # Eliminar duplicados manteniendo el orden de la primera aparición
            seen = set()
            selected_names_final = [x for x in temp_selected_names if not (x in seen or seen.add(x))]

            if selected_names_final:
                return selected_names_final
            else:
                print("No se seleccionó ninguna hoja válida con los números ingresados. Intenta de nuevo.")
        
        except ValueError:
            # Mensaje de error actualizado
            print("Error: Entrada inválida. Ingresa solo números separados por comas (ej. 1,3), la palabra 'TODOS', o deja vacío. Intenta de nuevo.")

def transformar_df_indicador_v1(df_original, col_paises_nombre_original='Unnamed: 0', nuevo_nombre_indice_paises='Pais'):
    print(f"\n--- Transformando DataFrame (Estructura V1) ---")
    if df_original is None or df_original.empty:
        print("  DataFrame original está vacío. No se puede transformar.")
        return None
    try:
        df = df_original.copy()
        if col_paises_nombre_original not in df.columns:
            print(f"  Error: La columna de países '{col_paises_nombre_original}' no se encuentra en el DataFrame.")
            print(f"  Columnas disponibles: {df.columns.tolist()}")
            return None
        df.set_index(col_paises_nombre_original, inplace=True)
        df.index.name = nuevo_nombre_indice_paises
        print(f"  Índice establecido a '{df.index.name}'. Columnas actuales (años): {df.columns.tolist()}")
        print("  Transponiendo DataFrame...")
        df_transformado = df.transpose()
        df_transformado.index.name = 'Año'
        df_transformado.index = pd.to_numeric(df_transformado.index, errors='coerce')
        original_rows = len(df_transformado)
        df_transformado.dropna(axis=0, how='all', subset=None, inplace=True)
        df_transformado = df_transformado[df_transformado.index.notna()]
        if len(df_transformado) < original_rows:
            print(f"  Se eliminaron {original_rows - len(df_transformado)} filas con Años no válidos o completamente vacías.")
        if df_transformado.empty:
            print("  DataFrame vacío después de eliminar Años no válidos.")
            return None
        try:
            df_transformado.index = df_transformado.index.astype(int)
        except ValueError:
            print("  Advertencia: El índice de Años no pudo ser convertido a entero.")
        print("  Convirtiendo valores de datos a numérico...")
        for col_pais in df_transformado.columns:
            df_transformado[col_pais] = pd.to_numeric(df_transformado[col_pais], errors='coerce')
        df_transformado.dropna(axis=1, how='all', inplace=True)
        print("  Transformación V1 completada.")
        return df_transformado
    except Exception as e:
        print(f"  Error durante la transformación del DataFrame (V1): {e}")
        traceback.print_exc() 
        return None
    
def prompt_select_country(data_transformada_indicadores):
    """
    Permite al usuario seleccionar un país de los disponibles en los DataFrames transformados.

    Args:
        data_transformada_indicadores (dict): Diccionario donde las claves son nombres de indicadores
                                              y los valores son DataFrames con Años como índice
                                              y Países como columnas.
    Returns:
        str: El nombre del país seleccionado, o None si no se selecciona ninguno o hay error.
    """
    if not data_transformada_indicadores:
        print("No hay datos transformados disponibles para seleccionar un país.")
        return None

    # Tomar el primer DataFrame del diccionario para obtener la lista de países (columnas)
    # Asumimos que todos los DataFrames transformados tienen una estructura de columnas similar (países)
    primer_nombre_indicador = next(iter(data_transformada_indicadores))
    df_referencia_paises = data_transformada_indicadores[primer_nombre_indicador]

    if df_referencia_paises is None or df_referencia_paises.empty:
        print(f"El DataFrame de referencia ('{primer_nombre_indicador}') para listar países está vacío o no existe.")
        return None

    paises_disponibles = df_referencia_paises.columns.tolist()

    if not paises_disponibles:
        print("No se encontraron países (columnas) en el DataFrame de referencia.")
        return None

    print("\n--- Países Disponibles para Selección ---")
    for i, pais_nombre in enumerate(paises_disponibles):
        print(f"  {i+1}. {pais_nombre}")

    pais_seleccionado_final = None
    while True: # Bucle hasta obtener una selección válida o vacía
        selection_str = input("Ingresa el número del país que quieres analizar, o deja vacío para no seleccionar: ")
        
        if not selection_str.strip():
            print("No se seleccionó ningún país.")
            return None

        try:
            selected_index = int(selection_str.strip()) - 1
            
            if 0 <= selected_index < len(paises_disponibles):
                pais_seleccionado_final = paises_disponibles[selected_index]
                print(f"\n--- País Seleccionado para Análisis ---")
                print(f"  - {pais_seleccionado_final}")
                return pais_seleccionado_final
            else:
                print(f"Advertencia: El número {selected_index + 1} está fuera de rango. Intenta de nuevo.")
        
        except ValueError:
            print("Error: Entrada inválida. Ingresa solo un número. Intenta de nuevo.")

def consolidate_data_for_country(data_transformada_indicadores, country_to_analyze, selected_sheet_names):
    """
    Consolida los datos de múltiples indicadores para un país específico en un solo DataFrame.

    Args:
        data_transformada_indicadores (dict): Diccionario donde las claves son nombres de indicadores
                                              y los valores son DataFrames con Años como índice
                                              y Países como columnas.
        country_to_analyze (str): El nombre del país seleccionado.
        selected_sheet_names (list): Lista de los nombres de las hojas/indicadores seleccionados,
                                     para mantener el orden de las columnas y los nombres.
    Returns:
        pd.DataFrame: Un DataFrame con Años como índice y los indicadores seleccionados como columnas
                      para el país especificado. Devuelve un DataFrame vacío si hay error.
    """
    if not data_transformada_indicadores:
        print("No hay datos transformados de indicadores para consolidar.")
        return pd.DataFrame()
    if not country_to_analyze:
        print("No se especificó un país para la consolidación.")
        return pd.DataFrame()
    if not selected_sheet_names:
        print("No se especificaron nombres de hojas/indicadores para la consolidación.")
        return pd.DataFrame()

    print(f"\n--- Consolidando datos para el país: {country_to_analyze} ---")
    
    lista_series_del_pais = []

    for nombre_indicador in selected_sheet_names:
        if nombre_indicador in data_transformada_indicadores:
            df_indicador_actual = data_transformada_indicadores[nombre_indicador]
            
            if df_indicador_actual is None or df_indicador_actual.empty:
                print(f"  Advertencia: El DataFrame transformado para el indicador '{nombre_indicador}' está vacío o es None. Se omitirá.")
                continue # Saltar al siguiente indicador

            if country_to_analyze in df_indicador_actual.columns:
                # Seleccionar la serie de datos para el país
                serie_pais_indicador = df_indicador_actual[country_to_analyze].copy()
                # Renombrar la Serie para que su nombre sea el del indicador (nombre de la hoja)
                # Esto será el nombre de la columna en el DataFrame final
                serie_pais_indicador.name = nombre_indicador 
                lista_series_del_pais.append(serie_pais_indicador)
                print(f"  Datos del indicador '{nombre_indicador}' para '{country_to_analyze}' añadidos.")
            else:
                print(f"  Advertencia: El país '{country_to_analyze}' no se encontró como columna en el indicador transformado '{nombre_indicador}'. Se omitirá.")
        else:
            print(f"  Advertencia: El indicador '{nombre_indicador}' no se encontró en los datos transformados. Se omitirá.")

    if not lista_series_del_pais:
        print(f"No se pudieron obtener datos para ningún indicador para el país '{country_to_analyze}'.")
        return pd.DataFrame()

    # Concatenar todas las Series en un solo DataFrame.
    # Cada Serie se convertirá en una columna. El índice (Año) se alineará automáticamente.
    try:
        df_consolidado_final = pd.concat(lista_series_del_pais, axis=1)
        print(f"\n--- Datos Consolidados para {country_to_analyze} (listos para ACP) ---")
        # print(df_consolidado_final.head()) # main.py se encargará de imprimir el head
        # df_consolidado_final.info()
        return df_consolidado_final
    except Exception as e_concat:
        print(f"Error al concatenar las series de datos para el país '{country_to_analyze}': {e_concat}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    
# En data_loader_module.py (o adaptado para main.py)
def preparar_datos_corte_transversal(all_sheets_data, selected_indicators_codes, selected_countries_names, target_year, col_paises_nombre_original='Unnamed: 0'):
    """
    [CORREGIDA v2] Prepara un DataFrame para un análisis de corte transversal para un año específico.
    Maneja la configuración del índice de forma más robusta para evitar errores.
    """
    print(f"\n--- Preparando datos de corte transversal para el año: {target_year} ---")

    target_year_str = str(target_year)
    target_year_int = int(target_year)

    list_of_series_for_year = []

    for indicator_code in selected_indicators_codes:
        if indicator_code not in all_sheets_data:
            print(f"Advertencia: Indicador '{indicator_code}' no encontrado. Se omitirá.")
            continue
        
        df_indicator = all_sheets_data[indicator_code].copy()

        # --- LÓGICA DE ÍNDICE CORREGIDA Y ROBUSTA ---
        # 1. Comprobar si la columna de países está en las columnas del DataFrame.
        if col_paises_nombre_original in df_indicator.columns:
            # Si está, establecerla como el índice.
            # Prevenir errores por nombres de países duplicados, mantener solo el primero.
            if df_indicator[col_paises_nombre_original].duplicated().any():
                df_indicator = df_indicator.drop_duplicates(subset=[col_paises_nombre_original], keep='first')
            df_indicator.set_index(col_paises_nombre_original, inplace=True)
        
        # 2. Si no estaba en las columnas, verificar si el índice actual NO es ya el correcto.
        elif df_indicator.index.name != col_paises_nombre_original:
            # Si no está en las columnas y el índice actual tampoco es el correcto,
            # significa que no podemos identificar los países en esta hoja. La omitimos.
            print(f"Advertencia: No se encontró la columna de países '{col_paises_nombre_original}' en el indicador '{indicator_code}'. Se omitirá.")
            continue
        # Si el código llega aquí, significa que el índice del DataFrame es correcto.
        # --- FIN DE LA LÓGICA DE ÍNDICE CORREGIDA ---

        # Buscar la columna del año (como número, texto o float)
        year_col_to_use = None
        if target_year_int in df_indicator.columns:
            year_col_to_use = target_year_int
        elif target_year_str in df_indicator.columns:
            year_col_to_use = target_year_str
        elif float(target_year_int) in df_indicator.columns:
            year_col_to_use = float(target_year_int)

        if year_col_to_use is None:
            print(f"Advertencia: Año '{target_year}' no encontrado en indicador '{indicator_code}'. Se generarán NaNs para este indicador.")
            nan_series = pd.Series(index=selected_countries_names, name=indicator_code, dtype=float)
            list_of_series_for_year.append(nan_series)
            continue
            
        # Extraer los datos para los países seleccionados usando .reindex()
        series_from_sheet = df_indicator[year_col_to_use]
        indicator_series_for_year = series_from_sheet.reindex(selected_countries_names)
        indicator_series_for_year.name = indicator_code
        list_of_series_for_year.append(indicator_series_for_year)

    if not list_of_series_for_year:
        print(f"No se pudieron extraer datos para ningún indicador para el año {target_year}.")
        return pd.DataFrame(index=selected_countries_names)

    # Concatenar y dar formato final
    df_cross_section = pd.concat(list_of_series_for_year, axis=1)
    df_cross_section = df_cross_section.reindex(selected_countries_names)

    print(f"DataFrame para el año {target_year} (primeras filas):")
    print(df_cross_section.head())
    return df_cross_section

def preparar_datos_panel_longitudinal(all_sheets_data, selected_indicators_codes, selected_countries_codes, col_paises_nombre_original='Unnamed: 0'):
    """
    [CORREGIDA v2] Prepara un DataFrame en formato de panel (longitudinal).
    Maneja la configuración del índice de forma robusta para evitar errores.
    """
    print("\n--- Preparando datos en formato de panel longitudinal ---")
    
    panel_data_list = []
    
    for indicator_code in selected_indicators_codes:
        if indicator_code not in all_sheets_data:
            print(f"Advertencia: Indicador '{indicator_code}' no encontrado. Se omitirá.")
            continue
        
        df_indicator = all_sheets_data[indicator_code].copy()
        
        # --- LÓGICA CORREGIDA PARA MANEJAR EL ÍNDICE ---
        # Primero, verificamos si la columna de países ('Unnamed: 0') ya es el índice.
        if df_indicator.index.name == col_paises_nombre_original:
            # Si lo es, lo convertimos de nuevo en una columna para poder usar 'melt' después.
            df_indicator.reset_index(inplace=True)

        # Ahora, verificamos si la columna de países existe.
        # Si no existe en este punto, la hoja tiene un formato incorrecto y la omitimos.
        if col_paises_nombre_original not in df_indicator.columns:
            print(f"Advertencia: No se encontró la columna de países '{col_paises_nombre_original}' en el indicador '{indicator_code}'. Se omitirá.")
            continue
        # --- FIN DE LA LÓGICA CORREGIDA ---
            
        # Filtrar solo por los países seleccionados
        df_indicator = df_indicator[df_indicator[col_paises_nombre_original].isin(selected_countries_codes)]
        if df_indicator.empty:
            # Esta advertencia es útil si un indicador no tiene datos para NINGUNO de los países seleccionados
            # print(f"Advertencia: Ninguno de los países seleccionados se encontró en el indicador '{indicator_code}'.")
            continue

        # Usar pd.melt para convertir de formato ancho a largo
        try:
            df_melted = df_indicator.melt(
                id_vars=[col_paises_nombre_original],
                var_name='Año',
                value_name=indicator_code
            )
            panel_data_list.append(df_melted)
        except Exception as e_melt:
            print(f"Error al transformar el indicador '{indicator_code}': {e_melt}")

    if not panel_data_list:
        print("No se pudo procesar ningún indicador en formato de panel.")
        return pd.DataFrame()

    # Unir todos los DataFrames de indicadores en uno solo
    if len(panel_data_list) == 1:
        df_panel_final = panel_data_list[0]
    else:
        df_panel_final = reduce(lambda left, right: pd.merge(left, right, on=[col_paises_nombre_original, 'Año'], how='outer'), panel_data_list)
    
    # Limpiar y ordenar
    df_panel_final.rename(columns={col_paises_nombre_original: 'País'}, inplace=True)
    df_panel_final['Año'] = pd.to_numeric(df_panel_final['Año'], errors='coerce')
    df_panel_final.dropna(subset=['Año'], inplace=True)
    df_panel_final['Año'] = df_panel_final['Año'].astype(int)
    df_panel_final.sort_values(by=['País', 'Año'], inplace=True)
    df_panel_final.set_index(['País', 'Año'], inplace=True)
    
    print("Datos de panel construidos (primeras filas):")
    print(df_panel_final.head())
    
    return df_panel_final

# --- Bloque de prueba ---
if __name__ == '__main__':
    print("--- Ejecutando pruebas para data_loader_module.py ---")
    test_file_path_v1 = r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\INDICADORES WDI_V8_vf.xlsm"
    
    # Llama directamente a las funciones definidas arriba en el módulo
    all_data_v1 = load_excel_file(test_file_path_v1)

    if all_data_v1 and 'DT.TDS.DECT.GN.ZS' in all_data_v1: # Asegúrate que esta hoja exista para probar
        df_para_transformar_v1 = all_data_v1['DT.TDS.DECT.GN.ZS']
        print("\nDataFrame original V1 de DT.TDS.DECT.GN.ZS (primeras filas):")
        print(df_para_transformar_v1.head())
        
        df_transformado_v1 = transformar_df_indicador_v1(df_para_transformar_v1, 
                                                        col_paises_nombre_original='Unnamed: 0', # VERIFICA este nombre
                                                        nuevo_nombre_indice_paises='Pais')

        if df_transformado_v1 is not None:
            print("\n--- DataFrame REAL V1 Transformado (DT.TDS.DECT.GN.ZS) ---")
            print(df_transformado_v1.head())
            print(f"Índice: {df_transformado_v1.index.name}, Tipo: {df_transformado_v1.index.dtype}")
            print(f"Columnas (Países): {df_transformado_v1.columns.tolist()}")
            print(f"Forma del DataFrame transformado: {df_transformado_v1.shape}")
        else:
            print("Fallo la transformación del DataFrame V1 real.")
    elif not all_data_v1:
        print("No se cargaron datos para la prueba de transformación.")
    else:
        print(f"La hoja 'DT.TDS.DECT.GN.ZS' no se encontró en los datos cargados para la prueba de transformación.")