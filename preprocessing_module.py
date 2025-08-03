# preprocessing_module.py
import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer, SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler

def manejar_datos_faltantes(df, estrategia='interpolacion', valor_relleno=None, 
                            devolver_mascara=False, iteraciones_imputador=10, 
                            estimador_imputador=None, metodo_interpolacion='linear', 
                            orden_interpolacion=3, knn_vecinos=5, **kwargs):
    if df.empty:
        if devolver_mascara:
            mascara_vacia = pd.DataFrame(False, index=df.index, columns=df.columns)
            return df.copy(), mascara_vacia
        return df.copy()

    df_copia = df.copy()
    mascara_imputados_original = df_copia.isnull()
    faltantes_antes = mascara_imputados_original.sum().sum()

    if faltantes_antes == 0:
        if devolver_mascara:
            return df_copia, pd.DataFrame(False, index=df.index, columns=df.columns)
        return df_copia
    
    # print(f"  Datos faltantes ANTES (por columna):\n{df_copia.isnull().sum()[df_copia.isnull().sum() > 0]}")

    columnas_originales = df_copia.columns.tolist()
    indice_original = df_copia.index
    
    numeric_cols_original = df_copia.select_dtypes(include=np.number).columns.tolist()
    # categorical_cols_original = df_copia.select_dtypes(exclude=np.number).columns.tolist() # No se usa activamente aún

    df_procesado = False # Bandera para saber si se aplicó alguna estrategia

    if estrategia == 'eliminar_filas':
        df_copia.dropna(axis=0, how='any', inplace=True)
        # print("  Filas con valores NaN eliminadas.")
        df_procesado = True
    
    elif estrategia in ['mean', 'median', 'most_frequent', 'valor_constante']:
        nombre_estrategia_sklearn = estrategia
        fill_val_const = np.nan 

        if estrategia == 'valor_constante':
            nombre_estrategia_sklearn = 'constant'
            if valor_relleno is None:
                valor_relleno = 0.0 
                print(f"  Advertencia: Estrategia 'valor_constante' sin 'valor_relleno'. Se usará {valor_relleno} por defecto.")
            fill_val_const = valor_relleno
        
        # Columnas que tienen algunos NaNs pero no son completamente NaN
        cols_con_nan_parcial = df_copia.columns[df_copia.isnull().any() & df_copia.notna().any()].tolist()
        # Columnas que son completamente NaN
        cols_todo_nan = df_copia.columns[df_copia.isna().all()].tolist()
        # Columnas sin ningún NaN
        cols_sin_nan = df_copia.columns[df_copia.notna().all()].tolist()

        df_imputado_final_simple = df_copia.copy() # Empezar con una copia

        if cols_con_nan_parcial:
            # Para 'mean' y 'median', solo aplicar a numéricas dentro de cols_con_nan_parcial
            if estrategia in ['mean', 'median']:
                cols_a_imputar_simple = [col for col in cols_con_nan_parcial if col in numeric_cols_original]
            else: # 'most_frequent', 'constant' pueden aplicar a todas las cols_con_nan_parcial
                cols_a_imputar_simple = cols_con_nan_parcial
            
            if cols_a_imputar_simple:
                df_parte_a_imputar = df_copia[cols_a_imputar_simple]
                imputador_simple = SimpleImputer(strategy=nombre_estrategia_sklearn, 
                                                 fill_value=fill_val_const if estrategia == 'valor_constante' else None)
                
                df_imputado_np = imputador_simple.fit_transform(df_parte_a_imputar)
                df_imputado_parcial = pd.DataFrame(df_imputado_np, columns=cols_a_imputar_simple, index=indice_original)
                
                # Actualizar df_imputado_final_simple
                for col in cols_a_imputar_simple:
                    df_imputado_final_simple[col] = df_imputado_parcial[col]
            else:
                pass

        # Las columnas en cols_todo_nan y cols_sin_nan ya están correctas en df_imputado_final_simple
        # (o se quedan como NaN o ya estaban completas)
        df_copia = df_imputado_final_simple[columnas_originales] # Asegurar orden
        # print(f"  Valores NaN rellenados con '{estrategia}'.")
        df_procesado = True

    elif estrategia == 'ffill':
        # ... (código ffill como estaba) ...
        limit_val = kwargs.get('ffill_limit')
        df_copia.ffill(inplace=True, limit=limit_val)
        df_copia.bfill(inplace=True, limit=kwargs.get('bfill_limit_after_ffill'))
        # print(f"  Valores NaN rellenados con forward fill (limit={limit_val}).")
        df_procesado = True
    elif estrategia == 'bfill':
        # ... (código bfill como estaba) ...
        limit_val = kwargs.get('bfill_limit')
        df_copia.bfill(inplace=True, limit=limit_val)
        df_copia.ffill(inplace=True, limit=kwargs.get('ffill_limit_after_bfill'))
        # print(f"  Valores NaN rellenados con backward fill (limit={limit_val}).")
        df_procesado = True
    elif estrategia == 'interpolacion':
        # ... (código interpolacion como estaba, asegurando que solo aplica a numeric_cols_original) ...
        if not numeric_cols_original:
            pass
        else:
            df_copia[numeric_cols_original] = df_copia[numeric_cols_original].interpolate(
                method=metodo_interpolacion, axis=0, limit_direction='both', 
                order=orden_interpolacion if metodo_interpolacion in ['polynomial', 'spline'] else None
            )
            df_copia[numeric_cols_original] = df_copia[numeric_cols_original].ffill()
            df_copia[numeric_cols_original] = df_copia[numeric_cols_original].bfill()
            # print(f"  Valores NaN en columnas numéricas rellenados mediante interpolación '{metodo_interpolacion}'.")
        df_procesado = True
    
    elif estrategia in ['iterative', 'knn']:
        # ... (código para iterative y knn como estaba, asegurando que solo aplica a 
        #      columnas numéricas que no son completamente NaN, y luego reconstruye) ...
        cols_num_imputables_adv = [col for col in numeric_cols_original if df_copia[col].notna().any()]
        
        if not cols_num_imputables_adv:
            pass
        else:
            df_parte_num_imputable_adv = df_copia[cols_num_imputables_adv].copy()
            
            if estrategia == 'iterative':
                pass
                imputer_adv = IterativeImputer(max_iter=iteraciones_imputador, random_state=0, estimator=estimador_imputador)
            else: # knn
                pass
                imputer_adv = KNNImputer(n_neighbors=knn_vecinos)
            
            df_imputado_np_adv = imputer_adv.fit_transform(df_parte_num_imputable_adv)
            df_imputado_parcial_adv = pd.DataFrame(df_imputado_np_adv, columns=cols_num_imputables_adv, index=indice_original)
            
            # Actualizar df_copia solo con las columnas numéricas imputadas
            for col in cols_num_imputables_adv:
                df_copia[col] = df_imputado_parcial_adv[col]
            # print(f"  Valores NaN en columnas numéricas imputados usando '{estrategia}'.")
        df_procesado = True
    
    if not df_procesado:
        pass

    # Mensajes de advertencia eliminados para limpieza
        
    if devolver_mascara:
        mascara_final_imputados = mascara_imputados_original & (~df_copia.isnull())
        return df_copia, mascara_final_imputados
    else:
        return df_copia


def estandarizar_datos(df, devolver_scaler=False):
    """
    Estandariza las columnas numéricas de un DataFrame (media 0, desviación estándar 1).

    Args:
        df (pd.DataFrame): DataFrame de entrada (Años como índice, Indicadores como columnas).
                           Se espera que las columnas a estandarizar sean numéricas.
        devolver_scaler (bool): Si True, devuelve también el objeto scaler ajustado.

    Returns:
        pd.DataFrame: DataFrame con las columnas numéricas estandarizadas.
        (Opcional) sklearn.preprocessing.StandardScaler: El objeto scaler ajustado.
    """
    if df.empty:
        if devolver_scaler:
            return df.copy(), None
        return df.copy()

    df_copia = df.copy()
    
    # Seleccionar solo columnas numéricas para estandarizar
    numeric_cols = df_copia.select_dtypes(include=np.number).columns.tolist()
    
    if not numeric_cols:
        print("  No se encontraron columnas numéricas para estandarizar.")
        if devolver_scaler:
            return df_copia, None
        return df_copia

    # print(f"  Columnas numéricas a estandarizar: {numeric_cols}")
    
    scaler = StandardScaler()
    
    # Aplicar el scaler SOLO a las columnas numéricas
    df_copia[numeric_cols] = scaler.fit_transform(df_copia[numeric_cols])
    
    # print("  Datos estandarizados exitosamente.")
    
    if devolver_scaler:
        return df_copia, scaler
    else:
        return df_copia

def prompt_select_imputation_strategy():
    """
    Permite al usuario seleccionar una estrategia de imputación de datos faltantes
    y los parámetros relevantes.

    Returns:
        tuple: (nombre_estrategia_seleccionada, kwargs_para_imputacion)
               kwargs_para_imputacion es un diccionario con parámetros como
               'valor_relleno', 'metodo_interpolacion', 'knn_vecinos', etc.
               Retorna (None, None) si el usuario no selecciona una opción válida o decide no imputar.
    """
    print("\n--- Selección de Estrategia para Manejar Datos Faltantes ---")
    
    # Actualizamos la lista de estrategias
    estrategias = {
        1: ('interpolacion', "Interpolación (lineal por defecto, o especificar método)"),
        2: ('mean', "Rellenar con la Media de la columna (solo numéricas)"),
        3: ('median', "Rellenar con la Mediana de la columna (solo numéricas)"),
        4: ('most_frequent', "Rellenar con el Valor Más Frecuente (moda)"),
        5: ('ffill', "Rellenar con el valor anterior (Forward Fill)"),
        6: ('bfill', "Rellenar con el valor siguiente (Backward Fill)"),
        7: ('iterative', "Imputación Iterativa (multivariada, solo numéricas)"),
        8: ('knn', "Imputación KNN (basada en vecinos, solo numéricas)"),
        9: ('valor_constante', "Rellenar con un Valor Constante específico"),
        10: ('eliminar_filas', "Eliminar filas (años) con cualquier dato faltante"),
        11: ('ninguna', "No aplicar ninguna imputación (mantener NaNs)")
    }

    for key, (name, desc) in estrategias.items():
        print(f"  {key}. {name} - {desc}")

    params_imputacion = {} # Para guardar parámetros adicionales
    estrategia_seleccionada_nombre = None

    while True:
        try:
            choice_str = input("Ingresa el número de la estrategia que deseas usar: ")
            if not choice_str.strip():
                print("No se seleccionó ninguna estrategia. Se mantendrán los NaNs si los hay.")
                return 'ninguna', {} 

            choice = int(choice_str)
            if choice in estrategias:
                estrategia_seleccionada_nombre, _ = estrategias[choice]

                if estrategia_seleccionada_nombre == 'valor_constante':
                    while True:
                        try:
                            val_str = input("Ingresa el valor constante para rellenar los NaNs (puede ser numérico o texto): ")
                            # Intentar convertir a float si es posible, si no, dejar como string
                            try:
                                params_imputacion['valor_relleno'] = float(val_str)
                            except ValueError:
                                params_imputacion['valor_relleno'] = val_str # Guardar como string
                            break 
                        except ValueError: # Este except es por si float() falla de forma inesperada, aunque ya está cubierto.
                             print("Error al procesar el valor constante.") # improbable llegar aquí
                
                elif estrategia_seleccionada_nombre == 'interpolacion':
                    print("Métodos de interpolación disponibles: linear, time, index, values, nearest, zero, ")
                    print("slinear, quadratic, cubic, barycentric, krogh, polynomial, spline, piecewise_polynomial, pchip, akima, cubicspline.")
                    met_int = input("Ingresa el método de interpolación (ej. 'linear', 'polynomial', 'spline') [default: linear]: ").strip()
                    if met_int:
                        params_imputacion['metodo_interpolacion'] = met_int
                        if met_int in ['polynomial', 'spline']:
                            while True:
                                try:
                                    orden_str = input(f"Ingresa el orden para interpolación '{met_int}' (ej. 2, 3) [default: 3]: ").strip()
                                    if not orden_str: # Usar default si está vacío
                                        params_imputacion['orden_interpolacion'] = 3
                                        break
                                    params_imputacion['orden_interpolacion'] = int(orden_str)
                                    break
                                except ValueError:
                                    print("Error: Ingresa un número entero válido para el orden.")
                    # Si met_int está vacío, se usará el default de la función `manejar_datos_faltantes`

                elif estrategia_seleccionada_nombre == 'knn':
                    while True:
                        try:
                            vecinos_str = input("Ingresa el número de vecinos para KNNImputer (ej. 5) [default: 5]: ").strip()
                            if not vecinos_str: # Usar default si está vacío
                                params_imputacion['knn_vecinos'] = 5
                                break
                            params_imputacion['knn_vecinos'] = int(vecinos_str)
                            if params_imputacion['knn_vecinos'] < 1:
                                print("El número de vecinos debe ser al menos 1.")
                                continue
                            break
                        except ValueError:
                            print("Error: Ingresa un número entero válido para los vecinos.")
                
                elif estrategia_seleccionada_nombre == 'iterative':
                     while True:
                        try:
                            iter_str = input(f"Ingresa el número máximo de iteraciones para IterativeImputer (ej. 10) [default: 10]: ").strip()
                            if not iter_str: # Usar default si está vacío
                                params_imputacion['iteraciones_imputador'] = 10
                                break
                            params_imputacion['iteraciones_imputador'] = int(iter_str)
                            if params_imputacion['iteraciones_imputador'] < 1:
                                print("El número de iteraciones debe ser al menos 1.")
                                continue
                            break
                        except ValueError:
                            print("Error: Ingresa un número entero válido para las iteraciones.")
                
                elif estrategia_seleccionada_nombre == 'ffill' or estrategia_seleccionada_nombre == 'bfill':
                    while True:
                        try:
                            limit_str = input(f"Ingresa el límite de NaNs consecutivos a rellenar con {estrategia_seleccionada_nombre} (opcional, deja vacío para no limitar): ").strip()
                            if not limit_str:
                                params_imputacion[f'{estrategia_seleccionada_nombre}_limit'] = None # Se pasará como None
                                break
                            limit_val = int(limit_str)
                            if limit_val < 1:
                                print("El límite debe ser al menos 1 si se especifica.")
                                continue
                            # El nombre del kwarg en la función manejar_datos_faltantes es ffill_limit o bfill_limit
                            params_imputacion[f'{estrategia_seleccionada_nombre}_limit'] = limit_val
                            break
                        except ValueError:
                            print("Error: Ingresa un número entero válido para el límite.")


                elif estrategia_seleccionada_nombre == 'ninguna':
                    print("No se aplicará ninguna imputación.")
                    return 'ninguna', {} # Devuelve estrategia 'ninguna' y diccionario de parámetros vacío
                    
                print(f"\nEstrategia seleccionada: '{estrategia_seleccionada_nombre}'")
                print(f"Parámetros para la imputación: {params_imputacion}")
                return estrategia_seleccionada_nombre, params_imputacion # Devuelve la estrategia y el dict de parámetros
            else:
                print("Opción inválida. Por favor, elige un número de la lista.")
        except ValueError:
            print("Entrada inválida. Por favor, ingresa solo un número.")


