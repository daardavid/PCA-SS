# visualization_module.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def graficar_series_de_tiempo(dfs_dict, titulo_general="Visualización de Series de Tiempo"):
    """
    Grafica múltiples DataFrames de series de tiempo en subplots apilados verticalmente.
    Cada DataFrame en el diccionario se grafica en su propio subplot.
    Se grafican solo las columnas numéricas.
    La leyenda se mueve fuera del gráfico si hay muchos elementos.

    Args:
        dfs_dict (dict): Un diccionario donde las claves son títulos para los subplots
                         y los valores son los DataFrames correspondientes.
        titulo_general (str): Título para toda la figura.
    """
    if not dfs_dict:
        print("No hay DataFrames para graficar.")
        return

    dfs_validos = {k: v for k, v in dfs_dict.items() if v is not None and not v.empty}
    if not dfs_validos:
        print("Todos los DataFrames proporcionados están vacíos o son None.")
        return

    num_plots = len(dfs_validos)
    if num_plots == 0:
        print("No hay DataFrames válidos para graficar después del filtrado.")
        return

    # --- MODIFICACIÓN PRINCIPAL AQUÍ ---
    # Apilar subplots verticalmente (1 columna)
    cols_subplot = 1
    rows_subplot = num_plots  # Cada subplot en su propia fila

    # Ajustar el tamaño de la figura: más ancha y altura proporcional al número de subplots
    fig_width = 12  # Puedes ajustar esto según tu preferencia
    height_per_subplot = 5  # Altura para cada subplot
    fig, axes = plt.subplots(rows_subplot, cols_subplot, 
                             figsize=(fig_width, height_per_subplot * rows_subplot), 
                             squeeze=False) # squeeze=False asegura que axes siempre sea 2D array
    
    if titulo_general:
        fig.suptitle(titulo_general, fontsize=16, y=0.99) # Ajustar 'y' si es necesario

    ax_flat = axes.flatten()  # Para iterar fácilmente sobre los ejes

    plot_idx = 0
    for i, (sub_titulo, df) in enumerate(dfs_validos.items()):
        ax = ax_flat[plot_idx] # Acceder al subplot actual
        
        if df is None or df.empty: # Esto ya estaba cubierto por dfs_validos, pero doble check
            if plot_idx < len(ax_flat):
                ax_flat[plot_idx].set_visible(False)
            plot_idx +=1
            continue
            
        # Seleccionar solo columnas numéricas para graficar
        numeric_cols = df.select_dtypes(include=np.number).columns
        
        if numeric_cols.empty:
            ax.text(0.5, 0.5, 'No hay datos numéricos para graficar', 
                    ha='center', va='center', transform=ax.transAxes)
            print(f"Advertencia: DataFrame '{sub_titulo}' no tiene columnas numéricas.")
        else:
            for columna in numeric_cols:
                # Usar un tamaño de marcador más pequeño si hay muchas líneas/puntos
                marker_size = 3 if len(numeric_cols) > 10 else 5
                ax.plot(df.index, df[columna], label=columna, marker='o', linestyle='-', markersize=marker_size)
            
            # Mover la leyenda fuera del gráfico si hay muchos indicadores
            if len(numeric_cols) > 8: # Puedes ajustar este umbral (ej. 8 o 10)
                ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize='small')
                # Ajustar el margen derecho del subplot para hacer espacio para la leyenda externa
                # Esto se maneja mejor con fig.tight_layout() o fig.subplots_adjust() después del bucle
            elif len(numeric_cols) > 0 : # Si hay columnas pero no tantas para mover la leyenda
                 ax.legend(fontsize='small')

            ax.grid(True, linestyle=':', alpha=0.7)
        
        ax.set_title(sub_titulo, fontsize=13)
        ax.set_xlabel("Año" if df.index.name == "Año" else str(df.index.name), fontsize=10)
        ax.set_ylabel("Valor", fontsize=10)
        ax.tick_params(axis='x', rotation=45) # Rotar etiquetas del eje X si son largas (años)
        
        plot_idx += 1

    # Ocultar ejes no utilizados si los hubiera (no debería con cols_subplot=1)
    for i in range(plot_idx, len(ax_flat)):
        ax_flat[i].set_visible(False)

    # Ajustar el layout para evitar solapamientos y hacer espacio para suptitle y leyendas externas
    # El parámetro 'right' en subplots_adjust puede necesitar ser menor si las leyendas externas son anchas
    try:
        if any(len(df.select_dtypes(include=np.number).columns) > 8 for df in dfs_validos.values() if df is not None and not df.empty):
            fig.subplots_adjust(right=0.80) # Necesitarás experimentar con este valor
        plt.tight_layout(rect=[0, 0.03, 1, 0.97 if titulo_general else 1])
    except Exception as e_layout:
        print(f"Advertencia al aplicar tight_layout/subplots_adjust: {e_layout}")

    plt.show()

def graficar_cada_df_en_ventana_separada(dfs_dict, titulo_base_ventana="Análisis para"):
    """
    Crea una figura separada de Matplotlib para cada DataFrame en el diccionario.
    """
    if not dfs_dict:
        print("No hay DataFrames para graficar.")
        return

    dfs_validos = {k: v for k, v in dfs_dict.items() if v is not None and not v.empty}
    if not dfs_validos:
        print("Todos los DataFrames proporcionados están vacíos o son None.")
        return

    for key_df, df_actual in dfs_validos.items():
        plt.figure(figsize=(12, 6)) # Nueva figura para cada DF
        ax = plt.gca() # Obtener ejes de la figura actual

        numeric_cols = df_actual.select_dtypes(include=np.number).columns
        
        if numeric_cols.empty:
            ax.text(0.5, 0.5, f'No hay datos numéricos en "{key_df}"', 
                    ha='center', va='center', transform=ax.transAxes)
        else:
            for columna in numeric_cols:
                marker_size = 3 if len(numeric_cols) > 10 else 5
                ax.plot(df_actual.index, df_actual[columna], label=columna, marker='o', linestyle='-', markersize=marker_size)

            if len(numeric_cols) > 8:
                ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize='small')
                plt.subplots_adjust(right=0.80) # Ajuste para leyenda externa
            elif len(numeric_cols) > 0:
                ax.legend(fontsize='small')
            
            ax.grid(True, linestyle=':', alpha=0.7)

        ax.set_title(f"{titulo_base_ventana}: {key_df}", fontsize=14)
        ax.set_xlabel("Año" if df_actual.index.name == "Año" else str(df_actual.index.name), fontsize=10)
        ax.set_ylabel("Valor", fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout(rect=[0,0,1,0.97]) # Ajuste para el título
        if len(numeric_cols) > 8: # Re-aplicar ajuste si la leyenda está fuera
             plt.subplots_adjust(right=0.80, top=0.95)


        plt.show() # Mostrar cada figura individualmente