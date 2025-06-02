# visualization_module.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np # Para select_dtypes

def graficar_series_de_tiempo(dfs_dict, titulo_general="Visualización de Series de Tiempo"):
    """
    Grafica múltiples DataFrames de series de tiempo en subplots.
    Cada DataFrame en el diccionario se grafica en su propio subplot.
    Se grafican solo las columnas numéricas.

    Args:
        dfs_dict (dict): Un diccionario donde las claves son títulos para los subplots
                         (ej. 'Original sin Imputar', 'Imputado', 'Estandarizado')
                         y los valores son los DataFrames correspondientes.
                         Se espera que los DataFrames tengan un índice tipo tiempo (ej. Años).
        titulo_general (str): Título para toda la figura.
    """
    if not dfs_dict:
        print("No hay DataFrames para graficar.")
        return

    # Filtrar DataFrames vacíos o None
    dfs_validos = {k: v for k, v in dfs_dict.items() if v is not None and not v.empty}
    if not dfs_validos:
        print("Todos los DataFrames proporcionados están vacíos o son None.")
        return

    num_plots = len(dfs_validos)
    if num_plots == 0:
        print("No hay DataFrames válidos para graficar después del filtrado.")
        return

    # Determinar el número de filas y columnas para los subplots
    # Intentar hacer una disposición agradable, por ejemplo, no más de 2 columnas
    cols_subplot = min(num_plots, 2)
    rows_subplot = (num_plots + cols_subplot - 1) // cols_subplot # División entera hacia arriba

    fig, axes = plt.subplots(rows_subplot, cols_subplot, figsize=(15, 5 * rows_subplot), squeeze=False)
    fig.suptitle(titulo_general, fontsize=16)
    
    ax_flat = axes.flatten() # Para iterar fácilmente sobre los ejes

    plot_idx = 0
    for i, (sub_titulo, df) in enumerate(dfs_validos.items()):
        if df is None or df.empty:
            # print(f"Skipping empty or None DataFrame: {sub_titulo}") # Opcional
            # Ocultar el subplot si el df es vacío
            if plot_idx < len(ax_flat):
                ax_flat[plot_idx].set_visible(False)
            plot_idx +=1
            continue

        ax = ax_flat[plot_idx]
        
        # Seleccionar solo columnas numéricas para graficar
        numeric_cols = df.select_dtypes(include=np.number).columns
        
        if numeric_cols.empty:
            ax.text(0.5, 0.5, 'No hay datos numéricos para graficar', ha='center', va='center', transform=ax.transAxes)
            print(f"Advertencia: DataFrame '{sub_titulo}' no tiene columnas numéricas.")
        else:
            for columna in numeric_cols:
                ax.plot(df.index, df[columna], label=columna, marker='o', linestyle='-')
            ax.legend()
            ax.grid(True)
        
        ax.set_title(sub_titulo)
        ax.set_xlabel("Año" if df.index.name == "Año" else "Índice")
        ax.set_ylabel("Valor")
        plot_idx += 1

    # Ocultar ejes no utilizados
    for i in range(plot_idx, len(ax_flat)):
        ax_flat[i].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Ajustar para el suptitle
    plt.show()


if __name__ == '__main__':
    print("--- Ejecutando pruebas para visualization_module.py ---")
    # Crear DataFrames de ejemplo
    años_idx = pd.RangeIndex(start=2000, stop=2010, name="Año")
    df_orig_test = pd.DataFrame({
        'PIB': [100, 102, 101, np.nan, 105, 107, 106, np.nan, 110, 112],
        'Inflacion': [2, 2.1, np.nan, 2.3, 2.4, 2.5, 2.3, 2.2, np.nan, 2.1]
    }, index=años_idx)
    
    df_imputado_test = df_orig_test.copy()
    df_imputado_test['PIB'].fillna(df_imputado_test['PIB'].mean(), inplace=True)
    df_imputado_test['Inflacion'].fillna(df_imputado_test['Inflacion'].mean(), inplace=True)

    df_estandarizado_test = df_imputado_test.copy()
    if not df_estandarizado_test.empty:
        num_cols_est = df_estandarizado_test.select_dtypes(include=np.number).columns
        if not num_cols_est.empty:
            scaler_test = StandardScaler()
            df_estandarizado_test[num_cols_est] = scaler_test.fit_transform(df_estandarizado_test[num_cols_est])

    datos_para_graficar = {
        "Original (con NaNs)": df_orig_test,
        "Imputado (media)": df_imputado_test,
        "Estandarizado": df_estandarizado_test,
        "Vacio": pd.DataFrame() # Para probar el manejo de DFs vacíos
    }
    
    graficar_series_de_tiempo(datos_para_graficar, titulo_general="Evolución de Indicadores de Prueba")
