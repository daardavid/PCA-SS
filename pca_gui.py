import os
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, simpledialog, colorchooser
import data_loader_module as dl
import preprocessing_module as dl_prep
import visualization_module as dl_viz
import pca_module as pca_mod
from constants import MAPEO_INDICADORES, CODE_TO_NAME
from pca_panel3d_logic import PCAPanel3DLogic
from project_save_config import ProjectConfig
import platform
import subprocess


PROJECTS_DIR = r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\Proyectos save"



class PCAApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PCA Socioeconómicos - GUI")
        self.geometry("600x400")

        # --- Inicializa la configuración del proyecto ---
        self.project_config = ProjectConfig()   # Aquí vive todo el estado

        # ====== Menú de Proyecto y Editar ======
        menu_bar = tk.Menu(self)

        # --- Proyecto ---
        mnu_project = tk.Menu(menu_bar, tearoff=0)
        mnu_project.add_command(label="Nuevo proyecto",  command=self.new_project)
        mnu_project.add_command(label="Abrir proyecto…", command=self.load_project)
        mnu_project.add_command(label="Guardar proyecto", command=self.save_project)
        menu_bar.add_cascade(label="Proyecto", menu=mnu_project)

        # --- Editar ---
        mnu_edit = tk.Menu(menu_bar, tearoff=0)
        mnu_edit.add_command(label="Editar título…",         command=self.edit_title_dialog)
        mnu_edit.add_command(label="Editar título leyenda…", command=self.edit_legend_dialog) 
        mnu_edit.add_separator()
        mnu_edit.add_command(label="Asignar colores…",       command=self.edit_colors_dialog)
        mnu_edit.add_command(label="Modificar unidades…",    command=self.edit_units_dialog)  
        mnu_edit.add_command(label="Editar fuente…",         command=self.edit_footer_dialog) 
        menu_bar.add_cascade(label="Editar", menu=mnu_edit)

        self.config(menu=menu_bar)
        # =============================

        # Menú principal
        tk.Label(self, text="¿Qué tipo de análisis deseas realizar?", font=("Arial", 15)).pack(pady=20)
        tk.Button(self, text="Serie de Tiempo (1 unidad)", width=35, height=2, command=self.start_series_analysis).pack(pady=8)
        tk.Button(self, text="Corte Transversal (Biplot 2D)", width=35, height=2, command=self.start_cross_section_analysis).pack(pady=8)
        tk.Button(self, text="Trayectorias Panel (PCA 3D)", width=35, height=2, command=self.start_panel_analysis).pack(pady=8)
        self.btn_run_project = tk.Button(
            self,
            text="Ejecutar proyecto",
            width=35,
            height=2,
            state=tk.DISABLED,
            command=self.run_project_from_cfg
        )
        self.btn_run_project.pack(pady=8)
        self.status = tk.Label(self, text="Status: Waiting...", fg="blue")
        self.status.pack(pady=10)

        self.lbl_project = tk.Label(self, text="Proyecto: Ninguno", fg="gray")
        self.lbl_project.pack(pady=2)



    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)

    def new_project(self):
        nombre = simpledialog.askstring("Nuevo Proyecto", "¿Cómo se va a llamar tu proyecto?")
        if nombre:
            self.project_config = ProjectConfig()  # Reinicia la configuración
            self.project_config.project_name = nombre.strip()
            self.status.config(text=f"Proyecto nuevo: {nombre.strip()}")
            self.sync_gui_from_cfg()  
        else:
            self.status.config(text="Creación de proyecto cancelada.")
    
    def save_project(self):
        project_name = self.project_config.project_name or "mi_proyecto"
        save_path = os.path.join(PROJECTS_DIR, f"{project_name}.json")
        self.project_config.save_to_file(save_path)
        messagebox.showinfo("Guardado", f"Proyecto guardado en:\n{save_path}")
        self.sync_gui_from_cfg() 

    def load_project(self):
        initial_dir = PROJECTS_DIR
        file_path = filedialog.askopenfilename(
            title="Selecciona proyecto",
            initialdir=initial_dir,
            filetypes=[("Archivos de Proyecto JSON", "*.json")]
        )
        if file_path:
            self.project_config = ProjectConfig.load_from_file(file_path)
            self.sync_gui_from_cfg() 

    def open_projects_folder(self):
        folder = PROJECTS_DIR
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.call(["open", folder])
        else:
            subprocess.call(["xdg-open", folder])

    def populate_from_project_config(self):
        pass  # Ya no es necesario, todo vive en self.project_config

    def sync_gui_from_cfg(self):
        """Refresca etiquetas y habilita el botón 'Ejecutar proyecto'."""
        cfg = self.project_config
        # etiqueta de proyecto
        self.lbl_project.config(
            text=f"Proyecto: {cfg.project_name or 'Sin nombre'}"
        )
        # resumen rápido debajo del título
        resumen = []
        if cfg.data_file:
            resumen.append("archivo OK")
        if cfg.selected_indicators:
            resumen.append(f"{len(cfg.selected_indicators)} indicadores")
        if cfg.selected_units:
            resumen.append(f"{len(cfg.selected_units)} unidades")
        if cfg.selected_years:
            resumen.append(f"{len(cfg.selected_years)} años")
        if cfg.footer_note:
            resumen.append("leyenda OK")
        self.status.config(text=" • ".join(resumen) if resumen else "Status: Waiting…")
        # ¿Ya hay todo lo mínimo para correr?  (indicadores, unidades, años)
        ready = all([
            cfg.data_file,
            cfg.selected_indicators,
            cfg.selected_units,
            cfg.selected_years
        ])
        self.btn_run_project.config(state=tk.NORMAL if ready else tk.DISABLED)

    # --- FLUJO 1: Serie de tiempo ---
    def start_series_analysis(self):
        self.status.config(text="Flujo: Serie de tiempo (1 unidad)")
        self.series_wizard()

    def series_wizard(self):
        self.step_select_file(lambda:
            self.step_select_indicators(lambda:
                self.step_select_units(lambda:
                    self.run_series_analysis()
                , allow_multiple=False)  # Solo una unidad
            , multi=True)  
        )

    def run_series_analysis(self):
        from pca_logic import PCAAnalysisLogic
        cfg = self.project_config
        # 1. Selección de estrategia de imputación
        estrategia, params = self.gui_select_imputation_strategy()
        # 2. Ejecutar la lógica de análisis (sin GUI)
        results = PCAAnalysisLogic.run_series_analysis_logic(cfg, imputation_strategy=estrategia, imputation_params=params)

        if "error" in results:
            messagebox.showerror("Error", results["error"])
            return
        if "warning" in results:
            messagebox.showwarning("Advertencia", results["warning"])
            return

        df_consolidado = results["df_consolidado"]
        df_imputado = results["df_imputado"]
        mascara_imputados = results["mascara_imputados"]
        df_estandarizado = results["df_estandarizado"]
        scaler = results["scaler"]
        df_covarianza = results["df_covarianza"]
        pca_sugerencias = results["pca_sugerencias"]
        selected_unit = cfg.selected_units[0]

        # Mensaje de éxito
        ncols = df_consolidado.shape[1]
        messagebox.showinfo(
            "Indicadores seleccionados",
            f"Se consolidaron {ncols} indicadores para el país '{selected_unit}'."
        )

        # Selección de número de componentes desde GUI
        if pca_sugerencias["evr"] is not None:
            n_componentes_usuario = self.gui_select_n_components(
                max_components=len(pca_sugerencias["evr"]),
                suggested_n_90=pca_sugerencias["n_sugg_90"],
                suggested_n_95=pca_sugerencias["n_sugg_95"]
            )
            from pca_logic import PCAAnalysisLogic
            pca_model_final, df_componentes = PCAAnalysisLogic.run_pca_final(df_estandarizado, n_componentes_usuario)
        else:
            pca_model_final, df_componentes = None, None

        # Visualización
        dfs_a_graficar = {
            f"Original Consolidado ({selected_unit})": df_consolidado.rename(columns=MAPEO_INDICADORES),
            f"Imputado ({selected_unit})": df_imputado.rename(columns=MAPEO_INDICADORES),
            f"Estandarizado ({selected_unit})": df_estandarizado.rename(columns=MAPEO_INDICADORES)
        }
        if df_componentes is not None:
            dfs_a_graficar[f"Componentes PCA ({selected_unit})"] = df_componentes
        dl_viz.graficar_cada_df_en_ventana_separada(dfs_a_graficar, titulo_base_ventana=f"Evolución para {selected_unit}")

        # Exportar a Excel
        if messagebox.askyesno("¿Exportar a Excel?", "¿Deseas guardar los resultados en un archivo Excel?"):
            filename = filedialog.asksaveasfilename(
                title="Guardar Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if filename:
                with pd.ExcelWriter(filename) as writer:
                    df_consolidado.rename(columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Original", index=True)
                    df_imputado.rename(columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Imputado", index=True)
                    df_estandarizado.rename(columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Estandarizado", index=True)
                    # Matriz de covarianza
                    df_covarianza.rename(index=MAPEO_INDICADORES, columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Matriz_Covarianza", index=True)
                    # Máscara de imputación (opcional)
                    if not mascara_imputados.empty:
                        mascara_imputados.to_excel(writer, sheet_name="Mascara_NaNs", index=True)
                    # Componentes principales
                    if df_componentes is not None:
                        df_componentes.to_excel(writer, sheet_name="ComponentesPCA", index=True)
                    if pca_sugerencias["df_varianza_explicada"] is not None:
                        pca_sugerencias["df_varianza_explicada"].to_excel(writer, sheet_name="PCA_VarianzaExp", index=True)
                    # Parámetros del scaler
                    pd.DataFrame({
                        "media": scaler.mean_,
                        "desv_std": scaler.scale_
                    }, index=df_estandarizado.columns).to_excel(writer, sheet_name="Scaler_Params")
                messagebox.showinfo("Listo", f"Archivo guardado en:\n{filename}")
        try:
            self.status.config(text="Análisis de serie de tiempo completado.")
        except tk.TclError:
            pass


    def start_cross_section_analysis(self):
        try:
            self.status.config(text="Flujo: Corte transversal (biplot 2D)")
            self.cross_section_wizard()  # ← Asegúrate de tener este método también
        except tk.TclError:
            pass

    def cross_section_wizard(self):
        self.step_select_file(lambda:
            self.step_select_indicators(lambda:
                self.step_select_units(lambda:
                    self.step_select_year(lambda:
                        self.run_cross_section_analysis()
                    )
                )
            )
        )

    def run_cross_section_analysis(self):
        from pca_cross_logic import PCAAnalysisLogic
        cfg = self.project_config
        selected_years = [int(y) for y in cfg.selected_years]
        for year_to_analyze in selected_years:
            # Preguntar si hay datos faltantes y si desea imputar
            estrategia, params = None, None
            # Ejecutar lógica de análisis (sin GUI)
            # Primero, obtener si hay NaNs para preguntar
            temp_results = PCAAnalysisLogic.run_cross_section_analysis_logic(cfg, year_to_analyze)
            if "warning" in temp_results and "faltantes" in temp_results["warning"]:
                respuesta = messagebox.askyesno(
                    f"Imputar año {year_to_analyze}",
                    f"Se encontraron datos faltantes para el año {year_to_analyze}.\n¿Quieres imputar los valores faltantes?"
                )
                if respuesta:
                    estrategia, params = self.gui_select_imputation_strategy()
            # Ejecutar lógica final con o sin imputación
            results = PCAAnalysisLogic.run_cross_section_analysis_logic(cfg, year_to_analyze, imputation_strategy=estrategia, imputation_params=params)
            if "warning" in results:
                messagebox.showwarning("Atención", results["warning"])
                continue
            df_year_cross_section = results["df_year_cross_section"]
            df_year_processed = results["df_year_processed"]
            df_year_estandarizado = results["df_year_estandarizado"]
            scaler = results["scaler"]
            df_cov_cs = results["df_cov_cs"]
            pca_model_cs = results["pca_model_cs"]
            df_pc_scores_cs = results["df_pc_scores_cs"]
            df_varianza_explicada_cs = results["df_varianza_explicada_cs"]
            evr_cs = results["evr_cs"]
            cum_evr_cs = results["cum_evr_cs"]

            # Mensaje de varianza explicada
            if len(evr_cs) >= 2:
                msg = (
                    f"Para el año {year_to_analyze}, los 2 primeros componentes explican:\n"
                    f"PC1: {evr_cs[0]:.2%}\n"
                    f"PC2: {evr_cs[1]:.2%}\n"
                    f"Total: {cum_evr_cs[1]:.2%} de la varianza"
                )
            elif len(evr_cs) == 1:
                msg = (
                    f"Solo se pudo calcular un componente principal para el año {year_to_analyze}.\n"
                    f"PC1 explica: {evr_cs[0]:.2%} de la varianza"
                )
            else:
                msg = "No se pudo calcular componentes principales para este año."
            messagebox.showinfo("Varianza explicada por los 2 componentes", msg)

            # Visualización (biplot)
            try:
                custom_colors = self.project_config.color_groups or {}
                unit_order = df_year_estandarizado.index.tolist()
                grupos_individuos = [
                    unit if unit in custom_colors else "Otros"
                    for unit in unit_order
                ]
                mapa_de_colores = {"Otros": "#808080"}
                mapa_de_colores.update(custom_colors)
                dl_viz.graficar_biplot_corte_transversal(
                    pca_model=pca_model_cs,
                    df_pc_scores=df_pc_scores_cs,
                    nombres_indicadores_originales=df_year_estandarizado.columns.tolist(),
                    nombres_indicadores_etiquetas=[MAPEO_INDICADORES.get(code, code) for code in df_year_estandarizado.columns.tolist()],
                    nombres_individuos_etiquetas=unit_order,
                    grupos_individuos=grupos_individuos,
                    mapa_de_colores=mapa_de_colores,
                    titulo=self.project_config.custom_titles.get("biplot", f"Biplot {year_to_analyze}"),
                    legend_title=self.project_config.custom_titles.get("legend", "Grupos de Países"),
                    ruta_guardado=None,
                    footer_note=self.project_config.custom_titles.get("footer", "")
                )
            except Exception as e:
                messagebox.showwarning("Error Biplot", f"No se pudo generar el biplot: {e}")

            # Exportar a Excel
            if messagebox.askyesno("¿Exportar?", f"¿Quieres guardar los resultados para el año {year_to_analyze}?"):
                filename = filedialog.asksaveasfilename(
                    title=f"Guardar resultados {year_to_analyze}",
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx *.xls")]
                )
                if filename:
                    with pd.ExcelWriter(filename) as writer:
                        df_year_cross_section.rename(columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Original", index=True)
                        df_year_processed.rename(columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Procesado", index=True)
                        df_year_estandarizado.rename(columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Estandarizado", index=True)
                        df_cov_cs.rename(index=MAPEO_INDICADORES, columns=MAPEO_INDICADORES).to_excel(writer, sheet_name="Matriz_Covarianza", index=True)
                        if df_pc_scores_cs is not None:
                            df_pc_scores_cs.to_excel(writer, sheet_name="ComponentesPCA", index=True)
                        if df_varianza_explicada_cs is not None:
                            df_varianza_explicada_cs.to_excel(writer, sheet_name="PCA_VarianzaExp", index=True)
                    messagebox.showinfo("Listo", f"Archivo guardado:\n{filename}")
        try:
            self.status.config(text="Análisis de corte transversal completado.")
        except tk.TclError:
            pass

    # --- FLUJO 3: Panel 3D ---
    def start_panel_analysis(self):
        try:
            self.status.config(text="Flujo: Trayectorias panel (PCA 3D)")
            self.panel_wizard()
        except tk.TclError:
            pass

    def panel_wizard(self):
        self.step_select_file(lambda:
            self.step_select_indicators(lambda:
                self.step_select_units(lambda:
                    self.step_select_year(lambda:
                        self.run_panel_analysis()
                    )
                )
            )
        )

    def run_panel_analysis(self):
        try:
            self.status.config(text=f"Panel 3D para años {self.project_config.selected_years} y unidades: {self.project_config.selected_units}")
            # Obtener datos y parámetros
            if not self.project_config.data_file or not self.project_config.selected_indicators or not self.project_config.selected_units:
                messagebox.showerror("Error", "Faltan datos para el análisis 3D. Selecciona archivo, indicadores y países.")
                return
            # Cargar todas las hojas
            all_sheets_data = dl.load_excel_file(self.project_config.data_file)
            if not all_sheets_data:
                messagebox.showerror("Error", "No se pudieron cargar los datos del archivo seleccionado.")
                return
            # Ejecutar lógica 3D
            results = PCAPanel3DLogic.run_panel3d_analysis_logic(
                all_sheets_data,
                list(all_sheets_data.keys()),
                self.project_config.selected_indicators,
                self.project_config.selected_units
            )
            if 'error' in results:
                messagebox.showerror("Error", results['error'])
                return
            # Visualizar
            try:
                dl_viz.graficar_trayectorias_3d(
                    results['df_pc_scores_panel'],
                    results['pca_model_panel'],
                    results['country_groups'],
                    results['group_colors'],
                    titulo="Trayectorias de Países en el Espacio PCA (Panel 3D)"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error al graficar el análisis 3D: {e}")
        except tk.TclError:
            pass
        

    # ========== REUTILIZABLES ==========

    def step_select_file(self, callback):
        file = filedialog.askopenfilename(
            title="Selecciona el archivo Excel",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file:
            self.project_config.data_file = file
            import data_loader_module as dl
            all_sheets_data = dl.load_excel_file(file)
            if all_sheets_data:
                self.sheet_names = list(all_sheets_data.keys())
                callback()
                self.sync_gui_from_cfg()  # ← nuevo
            else:
                self.sheet_names = []
                messagebox.showerror("Error", "No se pudo cargar el archivo seleccionado.")
                self.sync_gui_from_cfg()  # ← nuevo

    def step_select_indicators(self, callback, multi=True):
        """Abre una ventana para seleccionar uno o varios indicadores/hojas del Excel."""
        import tkinter as tk
        from tkinter import messagebox, Toplevel

        if not self.sheet_names:
            messagebox.showerror("Error", "Primero selecciona un archivo.")
            return

        win = Toplevel(self)
        win.title("Selecciona indicadores")
        win.geometry("420x480")

        # Instrucción clara
        n_disp = len(self.sheet_names)
        label_text = f"Selecciona {'uno o más' if multi else 'un'} indicador{'es' if multi else ''} para el análisis ({n_disp} disponibles):"
        lbl = tk.Label(win, text=label_text, wraplength=400)
        lbl.pack(pady=10)

        # Configura el Listbox según el modo múltiple o único
        listbox = tk.Listbox(
            win,
            selectmode=tk.MULTIPLE if multi else tk.SINGLE,
            width=50,
            height=min(20, n_disp)
        )
        for ind in self.sheet_names:
            listbox.insert(tk.END, ind)
        listbox.pack(pady=5)

        # Botones para seleccionar/desmarcar todo (solo para múltiple)
        button_frame = tk.Frame(win)
        button_frame.pack(pady=10)

        if multi:
            btn_selall = tk.Button(
                button_frame, text="Seleccionar todo", command=lambda: listbox.select_set(0, tk.END),
                bg="lightgreen", fg="black", width=15
            )
            btn_selall.grid(row=0, column=0, padx=5)

            btn_unselall = tk.Button(
                button_frame, text="Quitar selección", command=lambda: listbox.select_clear(0, tk.END),
                bg="lightcoral", fg="black", width=15
            )
            btn_unselall.grid(row=0, column=1, padx=5)

        # Botón OK
        def confirm_selection():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showerror("Error", "Selecciona al menos un indicador.")
                return
            self.project_config.selected_indicators = [self.sheet_names[i] for i in selected_indices]
            win.destroy()
            callback()
            self.sync_gui_from_cfg()  # ← nuevo

        btn_ok = tk.Button(
            button_frame, text="OK", command=confirm_selection, bg="lightblue", fg="black", width=15
        )
        if multi:
            btn_ok.grid(row=0, column=2, padx=5)
        else:
            btn_ok.grid(row=0, column=0, padx=5)

        # Permite cerrar con ESC
        win.bind("<Escape>", lambda event: win.destroy())
        win.grab_set()
        win.focus_set()

    def step_select_units(self, callback, allow_multiple=True):
        if not self.project_config.data_file or not self.project_config.selected_indicators:
            messagebox.showerror("Error", "Primero selecciona archivo e indicadores.")
            return

        excel_data = pd.read_excel(
            self.project_config.data_file,
            sheet_name=self.project_config.selected_indicators[0]
        )
        if 'Unnamed: 0' not in excel_data.columns:
            messagebox.showerror("Error", "No se encontró la columna 'Unnamed: 0' en la hoja seleccionada.")
            return
        all_units = sorted(excel_data['Unnamed: 0'].dropna().unique())
        display_names = [f"{CODE_TO_NAME.get(unit, str(unit))} ({unit})" for unit in all_units]

        win = Toplevel(self)
        win.title("Selecciona unidades")
        win.geometry("400x430")
        lbl = tk.Label(win, text="Selecciona unidades para el análisis:")
        lbl.pack(pady=10)
        listbox = tk.Listbox(win, selectmode=tk.MULTIPLE if allow_multiple else tk.SINGLE, width=50, height=20)
        for name in display_names:
            listbox.insert(tk.END, name)
        listbox.pack()
        button_frame = tk.Frame(win)
        button_frame.pack(pady=10)

        def select_all():
            listbox.select_set(0, tk.END)
        def unselect_all():
            listbox.select_clear(0, tk.END)
        def confirm_selection():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showerror("Error", "Selecciona al menos una unidad.")
                return
            self.project_config.selected_units = [all_units[i] for i in selected_indices]
            win.destroy()
            callback()
            self.sync_gui_from_cfg()  # ← nuevo

        tk.Button(button_frame, text="Select All", command=select_all, bg="lightgreen", fg="black").grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Unselect All", command=unselect_all, bg="lightcoral", fg="black").grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="OK", command=confirm_selection, bg="lightblue", fg="black").grid(row=0, column=2, padx=5)

    def step_select_year(self, callback=None, multi=True):
        df = pd.read_excel(
            self.project_config.data_file,
            sheet_name=self.project_config.selected_indicators[0]
        )
        year_columns = [col for col in df.columns if col != 'Unnamed: 0' and str(col).isdigit()]
        year_columns = sorted(year_columns, key=lambda x: int(x))  # ordena por año

        win = Toplevel(self)
        win.title("Select Year(s)")
        win.geometry("300x400")
        tk.Label(win, text="Select year(s) for analysis:").pack(pady=10)
        listbox = tk.Listbox(win, selectmode=tk.MULTIPLE if multi else tk.SINGLE, height=20)
        for year in year_columns:
            listbox.insert(tk.END, year)
        listbox.pack()

        def select_all():
            listbox.select_set(0, tk.END)
        def unselect_all():
            listbox.select_clear(0, tk.END)
        def confirm():
            idxs = listbox.curselection()
            if not idxs:
                messagebox.showerror("Error", "Selecciona al menos un año.")
                return
            self.project_config.selected_years = [year_columns[i] for i in idxs]
            win.destroy()
            self.status.config(text=f"Selected years: {self.project_config.selected_years}")
            if callback:
                callback()
            self.sync_gui_from_cfg()  # ← nuevo

        button_frame = tk.Frame(win)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Select All", command=select_all, bg="lightgreen").grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Unselect All", command=unselect_all, bg="lightcoral").grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="OK", command=confirm, bg="lightblue").grid(row=0, column=2, padx=5)

    def gui_select_imputation_strategy(self):
        estrategia = None
        params = {}

        STRATEGIAS = [
            ("interpolacion", "Interpolación (lineal por defecto, o especificar método)"),
            ("mean", "Rellenar con la Media"),
            ("median", "Rellenar con la Mediana"),
            ("most_frequent", "Rellenar con el Valor Más Frecuente (moda)"),
            ("ffill", "Rellenar con valor anterior (Forward Fill)"),
            ("bfill", "Rellenar con valor siguiente (Backward Fill)"),
            ("iterative", "Imputación Iterativa (multivariada)"),
            ("knn", "Imputación KNN (basada en vecinos)"),
            ("valor_constante", "Rellenar con un Valor Constante específico"),
            ("eliminar_filas", "Eliminar filas con datos faltantes"),
            ("ninguna", "No aplicar ninguna imputación (mantener NaNs)"),
        ]

        # Ventana emergente
        win = Toplevel(self)
        win.title("Selecciona Estrategia de Imputación")
        win.geometry("480x420")
        tk.Label(win, text="Selecciona cómo quieres imputar los datos faltantes:", font=("Arial", 11, "bold")).pack(pady=10)

        estrategia_var = tk.StringVar(value="interpolacion")
        for key, txt in STRATEGIAS:
            tk.Radiobutton(win, text=txt, variable=estrategia_var, value=key, anchor="w", justify="left").pack(fill="x", padx=25)

        # Para parámetro extra (valor constante)
        valor_entry = tk.Entry(win)
        def on_radio_change(*a):
            if estrategia_var.get() == "valor_constante":
                valor_entry.pack(pady=8)
                valor_entry.delete(0, tk.END)
                valor_entry.insert(0, "0")
            else:
                valor_entry.pack_forget()

        estrategia_var.trace_add('write', on_radio_change)

        def on_ok():
            nonlocal estrategia, params
            estrategia = estrategia_var.get()
            if estrategia == "valor_constante":
                try:
                    params["valor_constante"] = float(valor_entry.get())
                except Exception:
                    params["valor_constante"] = valor_entry.get()
            win.destroy()

        tk.Button(win, text="OK", command=on_ok, bg="lightblue").pack(pady=14)
        win.transient(self)
        win.grab_set()
        self.wait_window(win)
        return estrategia, params

    def gui_select_n_components(self, max_components, suggested_n_90=None, suggested_n_95=None):
        """
        Abre un diálogo para que el usuario seleccione el número de componentes principales a retener.
        """
        selected_n = [max_components]  # Usamos lista para tener referencia mutable en closure

        win = Toplevel(self)
        win.title("Seleccionar número de componentes principales")
        win.geometry("420x250")
        mensaje = f"Ingrese cuántos componentes principales deseas retener (1-{max_components}).\n"
        if suggested_n_90:
            mensaje += f"Sugerencia: {suggested_n_90} componentes ≈ 80% varianza.\n"
        if suggested_n_95:
            mensaje += f"Sugerencia: {suggested_n_95} componentes ≈ 90% varianza.\n"
        mensaje += f"Deja vacío para usar todos ({max_components})."

        tk.Label(win, text=mensaje, justify="left", wraplength=400).pack(pady=16)

        entry = tk.Entry(win)
        entry.pack(pady=6)
        entry.focus_set()

        def on_ok():
            value = entry.get().strip()
            if not value:
                selected_n[0] = max_components
            else:
                try:
                    n = int(value)
                    if 1 <= n <= max_components:
                        selected_n[0] = n
                    else:
                        messagebox.showerror("Error", f"El número debe estar entre 1 y {max_components}.")
                        return
                except Exception:
                    messagebox.showerror("Error", "Debes ingresar un número entero válido.")
                    return
            win.destroy()

        tk.Button(win, text="OK", command=on_ok, bg="lightblue", width=12).pack(pady=16)
        win.grab_set()
        self.wait_window(win)
        return selected_n[0]

    def run_project_from_cfg(self):
        cfg = self.project_config
        # regla simple: si una unidad y varios años → serie; si varias unidades y un año → corte transversal
        if len(cfg.selected_units) == 1 and len(cfg.selected_years) > 1:
            self.run_series_analysis()
        elif len(cfg.selected_units) > 1 and len(cfg.selected_years) == 1:
            self.run_cross_section_analysis()
        else:
            messagebox.showinfo(
                "Selector de flujo",
                "No se detecta un flujo claro; abre el menú y elige manualmente."
            )

    def edit_title_dialog(self):
        cfg = self.project_config
        new_title = simpledialog.askstring(
            "Título del gráfico",
            "Escribe el nuevo título:",
            initialvalue=cfg.custom_titles.get("biplot", "")
        )
        if new_title is not None:
            cfg.custom_titles["biplot"] = new_title.strip()
            self.status.config(text="Título actualizado.")
            self.sync_gui_from_cfg()

    def edit_legend_dialog(self):
        cfg = self.project_config
        new_txt = simpledialog.askstring(
            "Título de la leyenda",
            "Escribe cómo quieres que aparezca el encabezado de la leyenda:",
            initialvalue=cfg.custom_titles.get("legend", "")
        )
        if new_txt is not None:
            cfg.custom_titles["legend"] = new_txt.strip()
            self.status.config(text="Título de leyenda actualizado.")
            self.sync_gui_from_cfg()

    def edit_colors_dialog(self):
        cfg = self.project_config
        win = Toplevel(self); win.title("Asignar colores")
        win.geometry("360x420"); win.resizable(False, False)
        tk.Label(win, text="Elige individuos / unidades:").pack(pady=(12,2))
        lst = tk.Listbox(win, selectmode=tk.EXTENDED, height=14, width=34)
        for name in sorted(cfg.selected_units):
            lst.insert(tk.END, name)
        lst.pack()
        preview = tk.Label(win, width=4, relief="groove", bg="gray")
        preview.pack(pady=6)
        def refresh_preview(*_):
            sels = lst.curselection()
            if sels:
                unit = lst.get(sels[0])
                preview.config(bg=cfg.color_groups.get(unit, "gray"))
        lst.bind("<<ListboxSelect>>", refresh_preview)
        def set_color():
            rgb, hex_ = colorchooser.askcolor()
            if not hex_:
                return
            for i in lst.curselection():
                cfg.color_groups[lst.get(i)] = hex_
            refresh_preview()
        def unset_color():
            for i in lst.curselection():
                cfg.color_groups.pop(lst.get(i), None)
            refresh_preview()
        frm_btn = tk.Frame(win); frm_btn.pack(pady=4)
        tk.Button(frm_btn, text="Elegir color",  width=12, command=set_color).grid(row=0, column=0, padx=4)
        tk.Button(frm_btn, text="Quitar color",  width=12, command=unset_color).grid(row=0, column=1, padx=4)
        def accept():
            self.sync_gui_from_cfg()
            win.destroy()
        tk.Button(win, text="Aceptar", width=12, bg="#b7e0ee", command=accept).pack(pady=(12,8))
        win.grab_set(); win.focus_set()

    def edit_units_dialog(self):
        """
        Permite borrar o agregar unidades en caliente.
        • Muestra dos list-box:
          -  «Disponibles»  (todas las que existen en el Excel)
          -  «Seleccionadas» (las que ya están en cfg.selected_units)
        • Botones  >>  y  <<  para mover.
        """
        cfg      = self.project_config
        if not cfg.data_file or not cfg.selected_indicators:
            messagebox.showwarning("Primero elige archivo/indicadores")
            return
        all_units = sorted(
            pd.read_excel(
                cfg.data_file,
                sheet_name=cfg.selected_indicators[0]
            )['Unnamed: 0'].dropna().unique()
        )
        win = Toplevel(self); win.title("Modificar unidades"); win.resizable(False, False)
        tk.Label(win, text="Disponibles").grid(row=0, column=0, padx=8, pady=6)
        tk.Label(win, text="Seleccionadas").grid(row=0, column=2, padx=8, pady=6)
        lst_all  = tk.Listbox(win, height=18, selectmode=tk.EXTENDED, exportselection=False)
        lst_sel  = tk.Listbox(win, height=18, selectmode=tk.EXTENDED, exportselection=False)
        for u in all_units:         lst_all.insert(tk.END, u)
        for u in cfg.selected_units: lst_sel.insert(tk.END, u)
        lst_all.grid(row=1, column=0, padx=8)
        lst_sel.grid(row=1, column=2, padx=8)
        frm_btn = tk.Frame(win); frm_btn.grid(row=1, column=1, padx=4)
        def to_sel():
            for i in lst_all.curselection():
                unit = lst_all.get(i)
                if unit not in lst_sel.get(0, tk.END):
                    lst_sel.insert(tk.END, unit)
        def to_all():
            sel_items = [lst_sel.get(i) for i in lst_sel.curselection()]
            for item in sel_items:
                idx = lst_sel.get(0, tk.END).index(item)
                lst_sel.delete(idx)
                cfg.color_groups.pop(item, None)
        tk.Button(frm_btn, text=">>", command=to_sel).pack(pady=10)
        tk.Button(frm_btn, text="<<", command=to_all).pack(pady=10)
        def accept():
            cfg.selected_units = list(lst_sel.get(0, tk.END))
            self.sync_gui_from_cfg()
            win.destroy()
        tk.Button(win, text="Aceptar", width=12, command=accept).grid(row=2, column=0, columnspan=3, pady=12)
        win.grab_set(); win.focus_set()

    def edit_footer_dialog(self):
        cfg = self.project_config
        new_note = simpledialog.askstring(
            "Leyenda / Fuente",
            "Texto que aparecerá debajo del gráfico:",
            initialvalue=cfg.custom_titles.get("footer", "")
        )
        if new_note is not None:
            cfg.custom_titles["footer"] = new_note.strip()
            self.status.config(text="Fuente/leyenda actualizada.")
            self.sync_gui_from_cfg()

# ------------- FIN CLASE --------------

if __name__ == "__main__":
    app = PCAApp()
    app.mainloop()
