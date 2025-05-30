import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer, SimpleImputer

def manejar_datos_faltantes(df, estrategia='interpolacion', valor_relleno=None, devolver_mascara=False, iteraciones_imputador=10, estimador_imputador=None):
    print(f"\n--- Manejando Datos Faltantes (Estrategia: {estrategia}) ---")
    if df.empty:
        print("  DataFrame de entrada está vacío. No se realiza ninguna acción.")
        if devolver_mascara:
            mascara_vacia = pd.DataFrame(False, index=df.index, columns=df.columns)
            return df.copy(), mascara_vacia
        return df.copy()

    df_copia = df.copy()
    mascara_imputados_original = df_copia.isnull()

    faltantes_antes = mascara_imputados_original.sum().sum()
    if faltantes_antes == 0:
        print("  No se encontraron datos faltantes.")
        if devolver_mascara:
            return df_copia, mascara_imputados_original 
        return df_copia
    
    print(f"  Datos faltantes ANTES del manejo (por columna):\n{df_copia.isnull().sum()[df_copia.isnull().sum() > 0]}")

    columnas_originales = df_copia.columns.tolist()
    indice_original = df_copia.index

    if estrategia == 'eliminar_filas':
        df_copia.dropna(axis=0, how='any', inplace=True)
        print("  Filas con valores NaN eliminadas.")
    
    elif estrategia in ['mean', 'median', 'valor_constante']: # CORREGIDO: incluir 'valor_constante'
        nombre_estrategia_sklearn = estrategia
        if estrategia == 'valor_constante':
            nombre_estrategia_sklearn = 'constant'
            if valor_relleno is None:
                print("  Advertencia: Estrategia 'valor_constante' sin 'valor_relleno'. Se podrían rellenar con NaN o el default del imputador.")
        
        imputador_simple = SimpleImputer(strategy=nombre_estrategia_sklearn, 
                                         fill_value=valor_relleno if estrategia == 'valor_constante' else np.nan, # Usar np.nan si no es constante
                                         keep_empty_features=True) # Mantiene la forma

        df_imputado_np = imputador_simple.fit_transform(df_copia)
        df_copia = pd.DataFrame(df_imputado_np, columns=columnas_originales, index=indice_original)
        # SimpleImputer con keep_empty_features=True y estrategia mean/median rellenará columnas enteramente NaN con NaN si el tipo lo permite,
        # o 0 para numéricos si no. Para que se queden NaN, la columna debe ser de tipo float.
        # Forzar el tipo de las columnas imputadas a float si no lo son para asegurar que NaN se propague.
        for col in df_copia.columns:
            if mascara_imputados_original[col].all(): # Si la columna original era todo NaN
                try: # Intentar asegurar que sea float para mantener NaN
                    df_copia[col] = df_copia[col].astype(float)
                except ValueError: # Si no se puede convertir a float (ej. objetos), dejar como está
                    pass


        print(f"  Valores NaN rellenados con '{estrategia}'.")

    elif estrategia == 'ffill':
        df_copia.ffill(inplace=True)
        df_copia.bfill(inplace=True)
        print("  Valores NaN rellenados con forward fill (y luego backward fill).")
    elif estrategia == 'bfill':
        df_copia.bfill(inplace=True)
        df_copia.ffill(inplace=True)
        print("  Valores NaN rellenados con backward fill (y luego forward fill).")
    elif estrategia == 'interpolacion':
        df_copia.interpolate(method='linear', axis=0, limit_direction='both', inplace=True)
        df_copia.ffill(inplace=True)
        df_copia.bfill(inplace=True)
        print("  Valores NaN rellenados mediante interpolación lineal (y ffill/bfill).")
    
    elif estrategia == 'iterative':
        print(f"  Aplicando IterativeImputer (max_iter={iteraciones_imputador})...")
        
        # IterativeImputer es más robusto si se aplica a columnas que puede manejar.
        # Las columnas enteramente NaN no le dan información.
        columnas_con_algun_valor = df_copia.columns[df_copia.notna().any()].tolist()
        columnas_todo_nan = df_copia.columns[df_copia.isna().all()].tolist()

        if not columnas_con_algun_valor:
            print("  Todas las columnas son completamente NaN. No se puede aplicar IterativeImputer.")
        else:
            df_a_imputar_iter = df_copia[columnas_con_algun_valor].copy() # Trabajar con copia
            
            if estimador_imputador:
                imputer = IterativeImputer(max_iter=iteraciones_imputador, random_state=0, estimator=estimador_imputador)
            else: 
                imputer = IterativeImputer(max_iter=iteraciones_imputador, random_state=0)
            
            df_imputado_np_iter = imputer.fit_transform(df_a_imputar_iter)
            df_imputado_parcial_iter = pd.DataFrame(df_imputado_np_iter, columns=columnas_con_algun_valor, index=indice_original)

            # Reconstruir el DataFrame manteniendo todas las columnas originales
            if columnas_todo_nan:
                df_columnas_nan = df_copia[columnas_todo_nan].copy() # Trabajar con copia
                df_copia = pd.concat([df_imputado_parcial_iter, df_columnas_nan], axis=1)
                df_copia = df_copia[columnas_originales] 
            else:
                df_copia = df_imputado_parcial_iter
                if not df_copia.columns.equals(pd.Index(columnas_originales)): # Reordenar si es necesario
                    df_copia = df_copia.reindex(columns=columnas_originales)


            print("  Valores NaN imputados usando IterativeImputer.")
    else:
        print(f"  Advertencia: Estrategia '{estrategia}' no reconocida. No se manejaron los datos faltantes.")

    faltantes_despues = df_copia.isnull().sum().sum()
    if faltantes_despues > 0:
        print(f"  ADVERTENCIA: Aún quedan {faltantes_despues} datos faltantes después de aplicar la estrategia '{estrategia}'.")
        print(f"  Datos faltantes DESPUÉS del manejo (por columna):\n{df_copia.isnull().sum()[df_copia.isnull().sum() > 0]}")
    else:
        print("  Todos los datos faltantes han sido manejados.")
        
    if devolver_mascara:
        mascara_final_imputados = mascara_imputados_original & (~df_copia.isnull())
        return df_copia, mascara_final_imputados
    else:
        return df_copia
    
def prompt_select_imputation_strategy():
    """
    Permite al usuario seleccionar una estrategia de imputación de datos faltantes.

    Returns:
        tuple: (nombre_estrategia_seleccionada, valor_constante_si_aplica)
               Retorna (None, None) si el usuario no selecciona una opción válida o decide no imputar.
    """
    print("\n--- Selección de Estrategia para Manejar Datos Faltantes ---")
    
    estrategias = {
        1: ('interpolacion', "Interpolación Lineal (bueno para series de tiempo)"),
        2: ('mean', "Rellenar con la Media de la columna"),
        3: ('median', "Rellenar con la Mediana de la columna"),
        4: ('ffill', "Rellenar con el valor anterior (Forward Fill)"),
        5: ('bfill', "Rellenar con el valor siguiente (Backward Fill)"),
        6: ('iterative', "Imputación Iterativa (multivariada, puede ser más lenta)"),
        7: ('valor_constante', "Rellenar con un Valor Constante específico"),
        8: ('eliminar_filas', "Eliminar filas (años) con cualquier dato faltante"),
        9: ('ninguna', "No aplicar ninguna imputación (mantener NaNs)")
    }

    for key, (name, desc) in estrategias.items():
        print(f"  {key}. {name} - {desc}")

    valor_constante_seleccionado = None
    estrategia_seleccionada = None

    while True:
        try:
            choice_str = input("Ingresa el número de la estrategia que deseas usar: ")
            if not choice_str.strip(): # Si el usuario presiona Enter sin nada
                print("No se seleccionó ninguna estrategia. Se mantendrán los NaNs si los hay.")
                return 'ninguna', None # O simplemente None, None si prefieres no hacer nada

            choice = int(choice_str)
            if choice in estrategias:
                estrategia_seleccionada, _ = estrategias[choice]
                
                if estrategia_seleccionada == 'valor_constante':
                    while True:
                        try:
                            val_str = input("Ingresa el valor constante numérico para rellenar los NaNs: ")
                            valor_constante_seleccionado = float(val_str) # Intentar convertir a float
                            break
                        except ValueError:
                            print("Error: Ingresa un valor numérico válido para la constante.")
                elif estrategia_seleccionada == 'ninguna':
                    print("No se aplicará ninguna imputación.")
                    return 'ninguna', None
                    
                print(f"Estrategia seleccionada: '{estrategia_seleccionada}'")
                if valor_constante_seleccionado is not None:
                    print(f"Valor constante a usar: {valor_constante_seleccionado}")
                return estrategia_seleccionada, valor_constante_seleccionado
            else:
                print("Opción inválida. Por favor, elige un número de la lista.")
        except ValueError:
            print("Entrada inválida. Por favor, ingresa solo un número.")

# --- Bloque de prueba para preprocessing_module.py ---
if __name__ == '__main__':
    print("--- Ejecutando pruebas para preprocessing_module.py ---")
    data_ejemplo = {
        'IndicadorA': [1, 2, np.nan, 4, 5, np.nan, 7],
        'IndicadorB': [np.nan, 20, 30, 40, np.nan, 60, 70],
        'IndicadorC': [100, 200, 300, 400, 500, 600, 700], 
        'IndicadorD': [5, np.nan, np.nan, np.nan, 10, 12, 15],
        'IndicadorE': [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan] 
    }
    # Asegurar que todas las columnas sean float para que NaN se maneje consistentemente por SimpleImputer
    df_prueba = pd.DataFrame(data_ejemplo, dtype=float) 
    df_prueba.index = pd.RangeIndex(start=2000, stop=2000 + len(df_prueba), name="Año")


    print("\nDataFrame de Prueba Original:")
    print(df_prueba)
    print(df_prueba.dtypes) # Para ver los tipos

    estrategias_a_probar = ['interpolacion', 'mean', 'median', 'ffill', 'bfill', 'iterative', 'eliminar_filas', ('valor_constante', 0.0)] # Usar 0.0 para valor_constante

    for estrategia_test in estrategias_a_probar:
        valor_constante_test = None
        nombre_param_estrategia = "" 

        if isinstance(estrategia_test, tuple):
            nombre_param_estrategia = estrategia_test[0] 
            valor_constante_test = estrategia_test[1]   
        else:
            nombre_param_estrategia = estrategia_test   
        
        print(f"\n--- Probando estrategia: '{nombre_param_estrategia}' ---")
        df_resultado, mascara = manejar_datos_faltantes(df_prueba.copy(), # Pasar copia para que df_prueba no se altere entre iteraciones
                                                        estrategia=nombre_param_estrategia, 
                                                        devolver_mascara=True, 
                                                        valor_relleno=valor_constante_test)
        print("DataFrame Resultante:")
        print(df_resultado)
        # print("Máscara de Imputados (True donde se imputó):")
        # print(mascara)
        # print(f"Total de valores imputados: {mascara.sum().sum()}")