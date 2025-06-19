# visualization_module.py
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches #para la leyenda de los colores
import pandas as pd
import numpy as np
from adjustText import adjust_text
from pathlib import Path

def maximizar_plot():
    """Intenta maximizar la ventana del plot de Matplotlib para diferentes 'backends'."""
    try:
        # Esta función busca el manejador de la figura actual y llama al método
        # de maximización correspondiente al sistema operativo y backend gráfico.
        fig_manager = plt.get_current_fig_manager()
        if hasattr(fig_manager, 'window'):
            if hasattr(fig_manager.window, 'showMaximized'):
                fig_manager.window.showMaximized() # Para backend Qt
            elif hasattr(fig_manager.window, 'state'):
                fig_manager.window.state('zoomed') # Para backend Tk
        # Puedes añadir más condiciones para otros backends si es necesario (ej. WXAgg)
    except Exception as e:
        print(f"Advertencia: No se pudo maximizar la ventana del plot automáticamente: {e}")
        print("El tamaño del gráfico se controlará con el parámetro 'figsize'.")

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

def graficar_biplot_corte_transversal(
    # --- Datos Esenciales ---
    pca_model,
    df_pc_scores,
    nombres_indicadores_originales,

    # --- Etiquetas y Colores ---
    nombres_indicadores_etiquetas,
    nombres_individuos_etiquetas,
    grupos_individuos=None,
    mapa_de_colores=None,

    # --- Parámetros de Configuración del Gráfico ---
    titulo="Biplot PCA",
    pc_x=0,
    pc_y=1,
    figsize=(18, 14),
    arrow_scale=0.8,
    fontsize_paises=10,
    fontsize_indicadores=11,

    # --- Parámetro para Guardar (¡Este es el importante!) ---
    ruta_guardado=None
):
    """
    [OPTIMIZADA] Crea un biplot maximizado, flexible y legible para un análisis de PCA de corte transversal.
    """
    # --- 1. Verificaciones Iniciales ---
    if pca_model is None or df_pc_scores.empty:
        print("Modelo PCA o scores no disponibles para generar biplot.")
        return
    if pca_model.n_features_in_ != len(nombres_indicadores_originales):
        print("Error: El número de indicadores no coincide con el modelo PCA.")
        return

    # --- 2. Preparación de Coordenadas ---
    scores = df_pc_scores.iloc[:, [pc_x, pc_y]].values
    xs = scores[:, 0]
    ys = scores[:, 1]
    loadings = pca_model.components_[[pc_x, pc_y], :].T
    max_score_range = np.max([np.abs(xs), np.abs(ys)])
    max_loading_val = np.abs(loadings).max()
    if max_loading_val == 0: max_loading_val = 1
    scalefactor = max_score_range / max_loading_val * arrow_scale
    loadings_scaled = loadings * scalefactor

    # --- 3. Creación del Gráfico ---
    fig, ax = plt.subplots(figsize=figsize)
    colores_individuos = 'gray'
    if grupos_individuos and mapa_de_colores:
        colores_individuos = [mapa_de_colores.get(grupo, 'gray') for grupo in grupos_individuos]
    ax.scatter(xs, ys, s=60, alpha=0.7, c=colores_individuos, zorder=3)

    variable_texts = []
    for i, name in enumerate(nombres_indicadores_etiquetas):
        x_loading, y_loading = loadings_scaled[i, 0], loadings_scaled[i, 1]
        ax.arrow(0, 0, x_loading, y_loading, color='red', alpha=0.8, head_width=0.08, zorder=4)
        text_obj = ax.text(x_loading * 1.15, y_loading * 1.15, name, color='maroon',
                           ha='center', va='center', fontsize=fontsize_indicadores, zorder=5)
        variable_texts.append(text_obj)

    # --- 4. Ajuste de Etiquetas y Leyenda ---
    textos_paises = [ax.text(xs[i], ys[i], name, fontsize=fontsize_paises) for i, name in enumerate(nombres_individuos_etiquetas)]
    adjust_text(textos_paises, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5, alpha=0.6))
    adjust_text(variable_texts)

    if grupos_individuos and mapa_de_colores:
        unique_groups_in_plot = sorted(list(set(grupos_individuos)))
        legend_patches = [mpatches.Patch(color=mapa_de_colores.get(group, 'gray'), label=group) for group in unique_groups_in_plot]
        ax.legend(handles=legend_patches, title="Grupos de Países", loc='upper left', bbox_to_anchor=(1.02, 1))

    # --- 5. Formato Final del Gráfico ---
    pc_x_label = df_pc_scores.columns[pc_x]
    pc_y_label = df_pc_scores.columns[pc_y]
    var_pc_x = pca_model.explained_variance_ratio_[pc_x] * 100
    var_pc_y = pca_model.explained_variance_ratio_[pc_y] * 100
    ax.set_xlabel(f"{pc_x_label} ({var_pc_x:.2f}% varianza explicada)", fontsize=12)
    ax.set_ylabel(f"{pc_y_label} ({var_pc_y:.2f}% varianza explicada)", fontsize=12)
    ax.set_title(titulo, fontsize=15)
    ax.grid(True, linestyle=':', alpha=0.7, zorder=0)
    ax.axhline(0, color='dimgray', linewidth=1.5, linestyle='-', zorder=1)
    ax.axvline(0, color='dimgray', linewidth=1.5, linestyle='-', zorder=1)
    fig.tight_layout(rect=[0, 0, 0.88, 0.96])

        # --- AÑADIR TEXTO DE LA "FUENTE" de elaboración ---
    fig.text(0.03, 0.0007, "Fuente: Elaboración propia con datos de WDI.", 
             ha='left', va='bottom', fontsize=8, color='gray')

    # --- 6. Guardar y Mostrar ---
    # Guardar el gráfico ANTES de mostrarlo
    if ruta_guardado:
        try:
            # Aseguramos que el directorio de guardado exista
            Path(ruta_guardado).parent.mkdir(parents=True, exist_ok=True)
            # Guardamos la figura
            fig.savefig(ruta_guardado, format='svg', bbox_inches='tight', pad_inches=0.1)
            print(f"\nGráfico SVG guardado exitosamente en: {ruta_guardado}")
        except Exception as e:
            print(f"Error al guardar el gráfico en {ruta_guardado}: {e}")

    # Mostrar el gráfico maximizado
    maximizar_plot()
    plt.show()

def graficar_trayectorias_3d(df_pc_scores, pca_model, grupos_paises, mapa_de_colores, titulo="Trayectorias de Países en el Espacio PCA"):
    """
    Crea un gráfico 3D que muestra las trayectorias de los países a través del tiempo
    en el espacio de los 3 primeros componentes principales.
    """
    if df_pc_scores.shape[1] < 3:
        print("Error: Se necesitan al menos 3 componentes principales para un gráfico 3D.")
        return

    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(projection='3d')

    paises_unicos = df_pc_scores.index.get_level_values('País').unique()

    for pais_code in paises_unicos:
        datos_pais = df_pc_scores.loc[pais_code]
        if datos_pais.empty: continue
            
        grupo = grupos_paises.get(pais_code, 'Otros')
        color = mapa_de_colores.get(grupo, 'gray')
        
        ax.plot(datos_pais['PC1'], datos_pais['PC2'], datos_pais['PC3'], 
                color=color, alpha=0.6, label=f'_line_{pais_code}')
        
        ax.scatter(datos_pais['PC1'].iloc[0], datos_pais['PC2'].iloc[0], datos_pais['PC3'].iloc[0], 
                   color=color, marker='o', s=40, label=f'_start_{pais_code}')
        ax.scatter(datos_pais['PC1'].iloc[-1], datos_pais['PC2'].iloc[-1], datos_pais['PC3'].iloc[-1], 
                   color=color, marker='^', s=100, label=f'_end_{pais_code}')
        # Añadir etiqueta solo al punto final para no saturar el gráfico
        ax.text(datos_pais['PC1'].iloc[-1], datos_pais['PC2'].iloc[-1], datos_pais['PC3'].iloc[-1], 
                f' {pais_code}', color='black', fontsize=9)

    legend_patches = [mpatches.Patch(color=color, label=grupo) for grupo, color in mapa_de_colores.items()]
    ax.legend(handles=legend_patches, title="Grupos de Países", loc='center left', bbox_to_anchor=(1.05, 0.5))

    var_pc1 = pca_model.explained_variance_ratio_[0] * 100
    var_pc2 = pca_model.explained_variance_ratio_[1] * 100
    var_pc3 = pca_model.explained_variance_ratio_[2] * 100
    ax.set_xlabel(f"\nPC1 ({var_pc1:.2f}%)", fontsize=10)
    ax.set_ylabel(f"\nPC2 ({var_pc2:.2f}%)", fontsize=10)
    ax.set_zlabel(f"\nPC3 ({var_pc3:.2f}%)", fontsize=10)
    
    ax.set_title(titulo, fontsize=16)
    fig.tight_layout()
    maximizar_plot()
    plt.show()