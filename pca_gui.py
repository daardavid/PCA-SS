import os
import json
import logging
from logging.handlers import RotatingFileHandler
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
import sys
import webbrowser
import functools


# === i18n infrastructure ===

# --- Inicialización robusta del idioma ---
def get_saved_lang():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings = json.load(f)
            return settings.get("lang", "es")
    except Exception:
        return "es"

_LANG = get_saved_lang()
_TRANSLATIONS = None
def set_language(lang):
    global _LANG, _TRANSLATIONS
    _LANG = lang
    if lang == "en":
        from i18n_en import TRANSLATIONS as T
    else:
        from i18n_es import TRANSLATIONS as T
    _TRANSLATIONS = T
set_language(_LANG)

def tr(key):
    if _TRANSLATIONS is None:
        set_language(_LANG)
    return _TRANSLATIONS.get(key, key)


# === Configuración de rutas y logging ===
PROJECTS_DIR = r"C:\Users\messi\OneDrive\Escritorio\escuela\Servicio Social\Python\PCA\Proyectos save"
LOG_PATH = os.path.join(os.path.dirname(__file__), "pca_gui.log")
logger = logging.getLogger("pca_gui")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(LOG_PATH, maxBytes=200_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# === Decorador para callbacks seguros ===
def safe_gui_callback(func):
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}")
            tk = args[0] if args else None
            from tkinter import messagebox
            msg = str(e)
            if hasattr(e, 'args') and e.args and isinstance(e.args[0], str):
                msg = e.args[0]
            messagebox.showerror(tr("error"), f"{tr('unexpected_error') if 'unexpected_error' in _TRANSLATIONS else 'Unexpected error'}:\n{msg}")
    return wrapper

# === Definición de la clase principal de la app ===

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

class PCAApp(tk.Tk):
    """Aplicación PCA Socioeconómicos GUI principal."""
    def __init__(self):
        super().__init__()
        self.title("PCA Socioeconómicos - GUI")
        self._setup_config()
        self._setup_ui()
        self._bind_events()

    @safe_gui_callback
    def start_cross_section_analysis(self):
        """Inicia el flujo de análisis de corte transversal (varias unidades, un año o varios años)."""
        try:
            self._last_analysis_type = 'cross_section_config'
            self.status.config(text="Flujo: Corte transversal (varias unidades, años)")
            self.cross_section_wizard()
        except tk.TclError:
            pass

    def cross_section_wizard(self):
        self.step_select_file(lambda:
            self.step_select_indicators(lambda:
                self.step_select_units(lambda:
                    self.step_select_year(lambda:
                        self.run_cross_section_analysis()
                    , multi=True)
                , allow_multiple=True)
            , multi=True)
        )
    @safe_gui_callback
    def run_series_analysis(self):
        """Ejecuta el análisis de serie de tiempo para la unidad y años seleccionados."""
        from pca_logic import PCAAnalysisLogic
        cfg = self.project_config.series_config
        estrategia, params = None, None
        # Ejecuta la lógica real
        results = PCAAnalysisLogic.run_series_analysis_logic(cfg, imputation_strategy=estrategia, imputation_params=params)
        if "warning" in results:
            messagebox.showwarning("Atención", results["warning"])
            return
        if "error" in results:
            messagebox.showerror("Error", results["error"])
            return

        # Graficar resultados de serie de tiempo
        dfs_dict = {
            "Consolidado": results.get("df_consolidado"),
            "Imputado": results.get("df_imputado"),
            "Estandarizado": results.get("df_estandarizado")
        }
        dl_viz.graficar_series_de_tiempo(dfs_dict, titulo_general="Serie de Tiempo - Análisis PCA")

        # Preguntar si desea exportar los resultados
        if messagebox.askyesno(tr("export_title") if "export_title" in _TRANSLATIONS else "¿Exportar?", tr("export_msg") if "export_msg" in _TRANSLATIONS else "¿Quieres guardar los resultados del análisis de serie de tiempo?"):
            filename = filedialog.asksaveasfilename(
                title=tr("save_results_title") if "save_results_title" in _TRANSLATIONS else "Guardar resultados serie de tiempo",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if filename:
                import pandas as pd
                with pd.ExcelWriter(filename) as writer:
                    if results.get("df_consolidado") is not None:
                        results["df_consolidado"].to_excel(writer, sheet_name="Consolidado", index=True)
                    if results.get("df_imputado") is not None:
                        results["df_imputado"].to_excel(writer, sheet_name="Imputado", index=True)
                    if results.get("df_estandarizado") is not None:
                        results["df_estandarizado"].to_excel(writer, sheet_name="Estandarizado", index=True)
                    if results.get("df_covarianza") is not None:
                        results["df_covarianza"].to_excel(writer, sheet_name="Matriz_Covarianza", index=True)
                    if results.get("pca_sugerencias") and results["pca_sugerencias"].get("df_varianza_explicada") is not None:
                        results["pca_sugerencias"]["df_varianza_explicada"].to_excel(writer, sheet_name="PCA_VarianzaExp", index=True)
                messagebox.showinfo(tr("done") if "done" in _TRANSLATIONS else "Listo", tr("file_saved").format(filename=filename) if "file_saved" in _TRANSLATIONS else f"Archivo guardado:\n{filename}")

        messagebox.showinfo("Info", "Análisis de serie de tiempo completado correctamente.")
    def start_series_analysis(self):
        """Inicia el flujo de análisis de serie de tiempo (1 unidad, varios años)."""
        try:
            self.status.config(text="Flujo: Serie de tiempo (1 unidad)")
            self.series_wizard()
        except tk.TclError:
            pass

    def series_wizard(self):
        self.step_select_file(lambda:
            self.step_select_indicators(lambda:
                self.step_select_units(lambda:
                    self.run_series_analysis()
                , allow_multiple=False)  # Solo una unidad
            , multi=True)
        )
    def show_settings_window(self):
        import matplotlib.pyplot as plt
        win = Toplevel(self)
        win.title("Configuración")
        win.geometry("370x400")
        win.resizable(False, False)
        # Tema
        tk.Label(win, text="Tema:", font=("Arial", 11)).pack(pady=(18, 2))
        theme_var = tk.StringVar(value=self.theme)
        frm_theme = tk.Frame(win)
        frm_theme.pack()
        tk.Radiobutton(frm_theme, text="Claro", variable=theme_var, value="light").pack(side="left", padx=8)
        tk.Radiobutton(frm_theme, text="Oscuro", variable=theme_var, value="dark").pack(side="left", padx=8)

        # Idioma
        tk.Label(win, text="Idioma / Language:", font=("Arial", 11)).pack(pady=(18, 2))
        lang_var = tk.StringVar(value=getattr(self, "lang", "es"))
        frm_lang = tk.Frame(win)
        frm_lang.pack()
        tk.Radiobutton(frm_lang, text="Español", variable=lang_var, value="es").pack(side="left", padx=8)
        tk.Radiobutton(frm_lang, text="English", variable=lang_var, value="en").pack(side="left", padx=8)

        # Tamaño de ventana
        tk.Label(win, text="Tamaño de ventana (ej: 800x600):", font=("Arial", 11)).pack(pady=(18, 2))
        size_var = tk.StringVar(value=self.geometry())
        entry_size = tk.Entry(win, textvariable=size_var, width=16)
        entry_size.pack()

        # Fuente
        tk.Label(win, text="Fuente principal:", font=("Arial", 11)).pack(pady=(18, 2))
        font_var = tk.StringVar(value=getattr(self, "custom_font", "Arial"))
        entry_font = tk.Entry(win, textvariable=font_var, width=16)
        entry_font.pack()

        # Tamaño de fuente
        tk.Label(win, text="Tamaño de fuente:", font=("Arial", 11)).pack(pady=(18, 2))
        fontsize_var = tk.StringVar(value=str(getattr(self, "custom_fontsize", 12)))
        entry_fontsize = tk.Entry(win, textvariable=fontsize_var, width=6)
        entry_fontsize.pack()

        # Guardar y cerrar
        def save_and_close():
            self.theme = theme_var.get()
            self.custom_font = font_var.get()
            try:
                self.custom_fontsize = int(fontsize_var.get())
            except Exception:
                self.custom_fontsize = 12
            try:
                self.geometry(size_var.get())
            except Exception:
                pass
            new_lang = lang_var.get()
            lang_changed = (getattr(self, 'lang', 'es') != new_lang)
            self.lang = new_lang
            self.save_settings()
            self.apply_theme()
            self.apply_font_settings()
            self.apply_matplotlib_style()
            if lang_changed:
                self.change_language(self.lang)
            self.sync_gui_from_cfg()
            win.destroy()
        tk.Button(win, text="Guardar", command=save_and_close, bg="#b7e0ee", width=12).pack(pady=18)
        win.grab_set(); win.focus_set()

    def apply_matplotlib_style(self):
        import matplotlib.pyplot as plt
        if getattr(self, "theme", "light") == "dark":
            plt.style.use('dark_background')
        else:
            plt.style.use('default')

    def apply_theme(self):
        # Aplica tema claro/oscuro a la ventana principal y widgets básicos
        bg_light = "#f5f5f5"; fg_light = "#222"; btn_light = "#e0e0e0"
        bg_dark = "#23272e"; fg_dark = "#f5f5f5"; btn_dark = "#444"
        if getattr(self, "theme", "light") == "dark":
            bg, fg, btn = bg_dark, fg_dark, btn_dark
        else:
            bg, fg, btn = bg_light, fg_light, btn_light
        self.configure(bg=bg)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label) or isinstance(widget, tk.Button):
                widget.configure(bg=bg, fg=fg)
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=bg)
        # Menú
        self.menu_bar.configure(bg=bg, fg=fg)

    def apply_font_settings(self):
        # Aplica fuente y tamaño a los widgets principales
        font = getattr(self, "custom_font", "Arial")
        fontsize = getattr(self, "custom_fontsize", 12)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label) or isinstance(widget, tk.Button):
                widget.configure(font=(font, fontsize))

    def load_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"last_dir": "", "theme": "light"}

    def save_settings(self):
        settings = {
            "last_dir": getattr(self, "last_dir", ""),
            "theme": getattr(self, "theme", "light"),
            "window_size": self.geometry(),
            "custom_font": getattr(self, "custom_font", "Arial"),
            "custom_fontsize": getattr(self, "custom_fontsize", 12),
            "lang": getattr(self, "lang", "es")
        }
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"No se pudo guardar settings.json: {e}")

    def apply_settings(self, settings):
        # Tamaño de ventana
        if "window_size" in settings:
            try:
                self.geometry(settings["window_size"])
            except Exception:
                pass
        self.theme = settings.get("theme", "light")
        self.last_dir = settings.get("last_dir", "")
        self.custom_font = settings.get("custom_font", "Arial")
        self.custom_fontsize = settings.get("custom_fontsize", 12)
        self.lang = settings.get("lang", "es")
        self.apply_matplotlib_style()

    def _setup_config(self):
        """Carga la configuración inicial y crea directorios necesarios."""
        settings = self.load_settings()
        self.apply_settings(settings)
        self.project_config = ProjectConfig()
        if not os.path.exists(PROJECTS_DIR):
            os.makedirs(PROJECTS_DIR)

    def _bind_events(self):
        """Enlaza eventos de la aplicación (por ejemplo cerrar ventana)."""
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_ui(self):
        """Crea la barra de menús y widgets principales de la aplicación."""
        # Barra de menús y comandos
        menu_bar = tk.Menu(self)

        # --- Configuración (ícono de engranaje) ---
        mnu_settings = tk.Menu(menu_bar, tearoff=0)
        mnu_settings.add_command(label="Preferencias... ⚙️", command=self.show_settings_window)
        settings_index = menu_bar.index("end") + 1 if menu_bar.index("end") is not None else 0
        menu_bar.add_cascade(label=tr("settings_menu") if "settings_menu" in _TRANSLATIONS else "Configuración", menu=mnu_settings)

        # --- Proyecto ---
        mnu_project = tk.Menu(menu_bar, tearoff=0)
        mnu_project.add_command(label=tr("new_project"),  command=self.new_project)
        mnu_project.add_command(label=tr("open_project"), command=self.load_project)
        mnu_project.add_command(label=tr("save_project"), command=self.save_project)
        project_index = menu_bar.index("end") + 1 if menu_bar.index("end") is not None else 1
        menu_bar.add_cascade(label=tr("project"), menu=mnu_project)

        # --- Editar ---
        mnu_edit = tk.Menu(menu_bar, tearoff=0)
        # Submenú Serie de Tiempo
        mnu_edit_series = tk.Menu(mnu_edit, tearoff=0)
        mnu_edit_series.add_command(label="Editar título...", command=lambda: self.edit_title_dialog('series_config'))
        mnu_edit_series.add_command(label="Editar leyenda...", command=lambda: self.edit_legend_dialog('series_config'))
        mnu_edit_series.add_command(label="Asignar colores...", command=lambda: self.edit_colors_dialog('series_config'))
        mnu_edit_series.add_command(label="Modificar unidades", command=lambda: self.edit_units_dialog('series_config'))
        mnu_edit_series.add_command(label="Editar pie de página...", command=lambda: self.edit_footer_dialog('series_config'))
        mnu_edit.add_cascade(label=tr("series_menu") if "series_menu" in _TRANSLATIONS else "Serie de Tiempo", menu=mnu_edit_series)

        # Submenú Biplot 2D
        mnu_edit_biplot = tk.Menu(mnu_edit, tearoff=0)
        mnu_edit_biplot.add_command(label="Editar título...", command=lambda: self.edit_title_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label="Editar leyenda...", command=lambda: self.edit_legend_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label="Asignar colores...", command=lambda: self.edit_colors_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label="Modificar unidades", command=lambda: self.edit_units_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label="Editar pie de página...", command=lambda: self.edit_footer_dialog('cross_section_config'))
        mnu_edit.add_cascade(label=tr("biplot_menu") if "biplot_menu" in _TRANSLATIONS else "Biplot 2D", menu=mnu_edit_biplot)

        # Submenú PCA 3D
        mnu_edit_panel = tk.Menu(mnu_edit, tearoff=0)
        mnu_edit_panel.add_command(label="Editar título...", command=lambda: self.edit_title_dialog('panel_config'))
        mnu_edit_panel.add_command(label="Editar leyenda...", command=lambda: self.edit_legend_dialog('panel_config'))
        mnu_edit_panel.add_command(label="Asignar colores...", command=lambda: self.edit_colors_dialog('panel_config'))
        mnu_edit_panel.add_command(label="Modificar unidades", command=lambda: self.edit_units_dialog('panel_config'))
        mnu_edit_panel.add_command(label="Editar pie de página...", command=lambda: self.edit_footer_dialog('panel_config'))
        mnu_edit.add_cascade(label=tr("panel_menu") if "panel_menu" in _TRANSLATIONS else "PCA 3D", menu=mnu_edit_panel)

        edit_index = menu_bar.index("end") + 1 if menu_bar.index("end") is not None else 2
        menu_bar.add_cascade(label=tr("edit_menu") if "edit_menu" in _TRANSLATIONS else "Editar", menu=mnu_edit)

        # --- Ayuda ---
        mnu_help = tk.Menu(menu_bar, tearoff=0)
        mnu_help.add_command(label=tr("manual_menu") if "manual_menu" in _TRANSLATIONS else "Manual", command=self.show_manual_window)
        mnu_help.add_command(label=tr("about_menu") if "about_menu" in _TRANSLATIONS else "Acerca de nosotros", command=self.show_about_window)
        help_index = menu_bar.index("end") + 1 if menu_bar.index("end") is not None else 3
        menu_bar.add_cascade(label=tr("help_menu") if "help_menu" in _TRANSLATIONS else "Ayuda", menu=mnu_help)

        self.config(menu=menu_bar)
        # Guarda referencias necesarias
        self.menu_bar = menu_bar
        self.mnu_project = mnu_project
        self.mnu_edit = mnu_edit
        self.mnu_help = mnu_help
        self.mnu_settings = mnu_settings
        self.mnu_edit_series = mnu_edit_series
        self.mnu_edit_biplot = mnu_edit_biplot
        self.mnu_edit_panel = mnu_edit_panel
        # ...otros atributos de menú y widget según sea necesario...

        # =============================
        # Menú principal (textos serán reemplazados por tr() en el siguiente paso)
        self.lbl_analysis_type = tk.Label(self, text=tr("select_analysis_type"), font=("Arial", 15))
        self.lbl_analysis_type.pack(pady=20)
        # --- Serie de Tiempo ---
        frm_series = tk.Frame(self)
        frm_series.pack(pady=4)
        self.btn_series = tk.Button(frm_series, text=tr("series_analysis"), width=28, height=2, command=self.start_series_analysis)
        self.btn_series.pack(side="left", padx=2)
        self.btn_run_series = tk.Button(frm_series, text="Ejecutar", width=10, height=2, state=tk.DISABLED, command=self.run_series_analysis)
        self.btn_run_series.pack(side="left", padx=2)
        # --- Corte Transversal ---
        frm_cross = tk.Frame(self)
        frm_cross.pack(pady=4)
        self.btn_cross = tk.Button(frm_cross, text=tr("cross_section_analysis"), width=28, height=2, command=self.start_cross_section_analysis)
        self.btn_cross.pack(side="left", padx=2)
        self.btn_run_cross = tk.Button(frm_cross, text="Ejecutar", width=10, height=2, state=tk.DISABLED, command=self.run_cross_section_analysis)
        self.btn_run_cross.pack(side="left", padx=2)
        # --- Panel 3D ---
        frm_panel = tk.Frame(self)
        frm_panel.pack(pady=4)
        self.btn_panel = tk.Button(frm_panel, text=tr("panel_analysis"), width=28, height=2, command=self.start_panel_analysis)
        self.btn_panel.pack(side="left", padx=2)
        self.btn_run_panel = tk.Button(frm_panel, text="Ejecutar", width=10, height=2, state=tk.DISABLED, command=self.run_panel_analysis)
        self.btn_run_panel.pack(side="left", padx=2)
        self.status = tk.Label(self, text=tr("status_waiting"), fg="blue")
        self.status.pack(pady=10)

        self.lbl_project = tk.Label(self, text=f"{tr('project')}: Ninguno", fg="gray")
        self.lbl_project.pack(pady=2)

        self.apply_theme()
        self.apply_font_settings()
        self.apply_matplotlib_style()
        self.change_language(self.lang)


        # Menú Donar
        import webbrowser
        mnu_donate = tk.Menu(menu_bar, tearoff=0)
        mnu_donate.add_command(
            label="☕ Invítame un café",
            command=lambda: webbrowser.open("https://ko-fi.com/daardavid")
        )
        def show_bank_transfer():
            win = Toplevel(self)
            win.title("Transferencia bancaria (Solo México)")
            win.geometry("420x220")
            msg = (
                "Gracias por tu apoyo.\n\n"
                "Banco: HSBC\n"
                "CLABE: 021180065956536300\n"
                "A nombre de: David Abreu Rosique\n\n"
                "Puedes copiar estos datos para transferir desde tu app bancaria.\n"
            )
            lbl = tk.Label(win, text=msg, font=("Arial", 12), justify="left")
            lbl.pack(padx=18, pady=18)
            def copy_clabe():
                win.clipboard_clear()
                win.clipboard_append("021180065956536300")
                lbl.config(text=msg+"\n¡CLABE copiada al portapapeles!")
            btn_copy = tk.Button(win, text="Copiar CLABE", command=copy_clabe, bg="#988bfd", font=("Arial", 11, "bold"))
            btn_copy.pack(pady=6)
            btn_close = tk.Button(win, text="Cerrar", command=win.destroy)
            btn_close.pack(pady=4)
            win.grab_set(); win.focus_set()
        mnu_donate.add_command(
            label="Transferencia bancaria (Solo México)",
            command=show_bank_transfer
        )
        menu_bar.add_cascade(label="Donar", menu=mnu_donate)


    def on_close(self):
        self.save_settings()
        self.destroy()

    def show_about_window(self):
        import webbrowser
        about_text = (
            "# Acerca de nosotros\n\n"
            "Este programa fue desarrollado por David Armando Abreu Rosique.\n\n"
            "Historia: Esta aplicación nació como parte de un proyecto de análisis de datos socioeconómicos, con el objetivo de facilitar el uso de PCA para usuarios no expertos.\n\n"
            "Agradezco a todo el equipo del Instituto de Investigaciones Económicas de la UNAM.\n\n"
            "Contacto: davidabreu1110@gmail.com.\n\n"
            "¿Te gusta el programa? Puedes apoyarme invitándome un café en Ko-fi.\n"
        )
        win = Toplevel(self)
        win.title("Acerca de nosotros")
        win.geometry("600x400")
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True)
        txt = tk.Text(frame, wrap="word", font=("Arial", 12))
        txt.insert("1.0", about_text)
        txt.config(state="disabled")
        txt.pack(side="top", fill="both", expand=True)
        scroll = tk.Scrollbar(frame, command=txt.yview)
        txt.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        btn_kofi = tk.Button(frame, text="Visitar Ko-fi", bg="#ffdd57", font=("Arial", 11, "bold"), command=lambda: webbrowser.open("https://ko-fi.com/daardavid"))
        btn_kofi.pack(side="bottom", pady=10)

    def show_manual_window(self):
        manual_text = (
            "# Manual de la aplicación\n\n"
            "Esta aplicación permite realizar análisis PCA sobre datos socioeconómicos.\n\n"
            "- **Nuevo Proyecto**: Crea un nuevo proyecto.\n"
            "- **Abrir Proyecto**: Carga un proyecto guardado.\n"
            "- **Guardar Proyecto**: Guarda el estado actual.\n\n"
            "Puedes seleccionar indicadores, unidades y años, y ejecutar análisis de serie de tiempo, corte transversal o panel.\n\n"
            "**Ejemplo de uso:**\n\n1. Crea un nuevo proyecto.\n2. Selecciona el archivo de datos.\n3. Elige los indicadores, unidades y años.\n4. Ejecuta el análisis.\n\nPara más detalles, consulta el manual completo."
        )
        win = Toplevel(self)
        win.title("Manual")
        win.geometry("600x500")
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True)
        txt = tk.Text(frame, wrap="word", font=("Arial", 12))
        txt.insert("1.0", manual_text)
        txt.config(state="disabled")
        txt.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(frame, command=txt.yview)
        txt.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

    # El resto de los métodos de la clase PCAApp deben ir aquí
    # ...

    def build_menu_bar(self):
        # Reconstruye la barra de menús y actualiza referencias
        import webbrowser
        menu_bar = tk.Menu(self)

        # --- Configuración (ícono de engranaje) ---
        mnu_settings = tk.Menu(menu_bar, tearoff=0)
        mnu_settings.add_command(label=tr("settings_menu") if "settings_menu" in _TRANSLATIONS else "Preferencias... ⚙️", command=self.show_settings_window)
        menu_bar.add_cascade(label=tr("settings_menu") if "settings_menu" in _TRANSLATIONS else "Configuración", menu=mnu_settings)

        # --- Proyecto ---
        mnu_project = tk.Menu(menu_bar, tearoff=0)
        mnu_project.add_command(label=tr("new_project"),  command=self.new_project)
        mnu_project.add_command(label=tr("open_project"), command=self.load_project)
        mnu_project.add_command(label=tr("save_project"), command=self.save_project)
        menu_bar.add_cascade(label=tr("project"), menu=mnu_project)

        # --- Editar ---
        mnu_edit = tk.Menu(menu_bar, tearoff=0)
        # Submenú Serie de Tiempo
        mnu_edit_series = tk.Menu(mnu_edit, tearoff=0)
        mnu_edit_series.add_command(label=tr("edit_title"), command=lambda: self.edit_title_dialog('series_config'))
        mnu_edit_series.add_command(label=tr("edit_legend"), command=lambda: self.edit_legend_dialog('series_config'))
        mnu_edit_series.add_command(label=tr("assign_colors"), command=lambda: self.edit_colors_dialog('series_config'))
        mnu_edit_series.add_command(label=tr("edit_units"), command=lambda: self.edit_units_dialog('series_config'))
        mnu_edit_series.add_command(label=tr("edit_footer"), command=lambda: self.edit_footer_dialog('series_config'))
        mnu_edit.add_cascade(label=tr("series_menu") if "series_menu" in _TRANSLATIONS else "Serie de Tiempo", menu=mnu_edit_series)

        # Submenú Biplot 2D
        mnu_edit_biplot = tk.Menu(mnu_edit, tearoff=0)
        mnu_edit_biplot.add_command(label=tr("edit_title"), command=lambda: self.edit_title_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label=tr("edit_legend"), command=lambda: self.edit_legend_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label=tr("assign_colors"), command=lambda: self.edit_colors_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label=tr("edit_units"), command=lambda: self.edit_units_dialog('cross_section_config'))
        mnu_edit_biplot.add_command(label=tr("edit_footer"), command=lambda: self.edit_footer_dialog('cross_section_config'))
        mnu_edit.add_cascade(label=tr("biplot_menu") if "biplot_menu" in _TRANSLATIONS else "Biplot 2D", menu=mnu_edit_biplot)

        # Submenú PCA 3D
        mnu_edit_panel = tk.Menu(mnu_edit, tearoff=0)
        mnu_edit_panel.add_command(label=tr("edit_title"), command=lambda: self.edit_title_dialog('panel_config'))
        mnu_edit_panel.add_command(label=tr("edit_legend"), command=lambda: self.edit_legend_dialog('panel_config'))
        mnu_edit_panel.add_command(label=tr("assign_colors"), command=lambda: self.edit_colors_dialog('panel_config'))
        mnu_edit_panel.add_command(label=tr("edit_units"), command=lambda: self.edit_units_dialog('panel_config'))
        mnu_edit_panel.add_command(label=tr("edit_footer"), command=lambda: self.edit_footer_dialog('panel_config'))
        mnu_edit.add_cascade(label=tr("panel_menu") if "panel_menu" in _TRANSLATIONS else "PCA 3D", menu=mnu_edit_panel)

        menu_bar.add_cascade(label=tr("edit_menu") if "edit_menu" in _TRANSLATIONS else "Editar", menu=mnu_edit)

        # --- Ayuda ---
        mnu_help = tk.Menu(menu_bar, tearoff=0)
        mnu_help.add_command(label=tr("manual_menu") if "manual_menu" in _TRANSLATIONS else "Manual", command=self.show_manual_window)
        mnu_help.add_command(label=tr("about_menu") if "about_menu" in _TRANSLATIONS else "Acerca de nosotros", command=self.show_about_window)
        menu_bar.add_cascade(label=tr("help_menu") if "help_menu" in _TRANSLATIONS else "Ayuda", menu=mnu_help)

        # --- Donar ---
        mnu_donate = tk.Menu(menu_bar, tearoff=0)
        mnu_donate.add_command(
            label=tr("donate_menu") if "donate_menu" in _TRANSLATIONS else "☕ Invítame un café",
            command=lambda: webbrowser.open("https://ko-fi.com/daardavid")
        )
        def show_bank_transfer():
            win = Toplevel(self)
            win.title("Transferencia bancaria (Solo México)")
            win.geometry("420x220")
            msg = (
                "Gracias por tu apoyo.\n\n"
                "Banco: HSBC\n"
                "CLABE: 021180065956536300\n"
                "A nombre de: David Abreu Rosique\n\n"
                "Puedes copiar estos datos para transferir desde tu app bancaria.\n"
            )
            lbl = tk.Label(win, text=msg, font=("Arial", 12), justify="left")
            lbl.pack(padx=18, pady=18)
            def copy_clabe():
                win.clipboard_clear()
                win.clipboard_append("021180065956536300")
                lbl.config(text=msg+"\n¡CLABE copiada al portapapeles!")
            btn_copy = tk.Button(win, text="Copiar CLABE", command=copy_clabe, bg="#988bfd", font=("Arial", 11, "bold"))
            btn_copy.pack(pady=6)
            btn_close = tk.Button(win, text="Cerrar", command=win.destroy)
            btn_close.pack(pady=4)
            win.grab_set(); win.focus_set()
        mnu_donate.add_command(
            label=tr("donate_bank") if "donate_bank" in _TRANSLATIONS else "Transferencia bancaria (Solo México)",
            command=show_bank_transfer
        )
        menu_bar.add_cascade(label=tr("donate_menu") if "donate_menu" in _TRANSLATIONS else "Donar", menu=mnu_donate)

        # Actualiza referencias
        self.menu_bar = menu_bar
        self.mnu_project = mnu_project
        self.mnu_edit = mnu_edit
        self.mnu_help = mnu_help
        self.mnu_settings = mnu_settings
        self.mnu_edit_series = mnu_edit_series
        self.mnu_edit_biplot = mnu_edit_biplot
        self.mnu_edit_panel = mnu_edit_panel
        self.mnu_donate = mnu_donate
        self.menu_indices = {
            "settings": 0,
            "project": 1,
            "edit": 2,
            "help": 3,
            "donate": 4
        }
        self.config(menu=menu_bar)

    def change_language(self, lang):
        if lang == getattr(self, "lang", "es"):
            return  # No hay cambio
        answer = messagebox.askyesno(
            "Reiniciar aplicación",
            "Para aplicar el cambio de idioma, la aplicación debe reiniciarse. ¿Deseas continuar?\n\nTo apply the language change, the app must restart. Continue?"
        )
        if answer:
            self.lang = lang
            self.save_settings()
            python = sys.executable
            import os
            os.execl(python, python, *sys.argv)
        # Si no, no hace nada



    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)

    @safe_gui_callback
    def new_project(self):
        while True:
            nombre = simpledialog.askstring(tr("new_project"), tr("ask_project_name") if "ask_project_name" in _TRANSLATIONS else "¿Cómo se va a llamar tu proyecto?")
            if nombre is None:
                self.status.config(text=tr("cancelled_project_creation") if "cancelled_project_creation" in _TRANSLATIONS else "Creación de proyecto cancelada.")
                return
            nombre = nombre.strip()
            if not nombre:
                messagebox.showwarning(tr("warning"), tr("empty_project_name") if "empty_project_name" in _TRANSLATIONS else "El nombre no puede estar vacío.")
                continue
            if any(c in nombre for c in r'<>:"/\\|?*'):
                messagebox.showwarning(tr("warning"), tr("invalid_project_name") if "invalid_project_name" in _TRANSLATIONS else "El nombre contiene caracteres no permitidos.")
                continue
            break
        self.project_config = ProjectConfig()  # Reinicia la configuración
        self.project_config.project_name = nombre
        self.status.config(text=f"{tr('new_project')}: {nombre}")
        self.sync_gui_from_cfg()
    
    @safe_gui_callback
    def save_project(self):
        project_name = self.project_config.project_name or "mi_proyecto"
        save_path = os.path.join(PROJECTS_DIR, f"{project_name}.json")
        self.project_config.save_to_file(save_path)
        messagebox.showinfo(tr("info"), f"{tr('project')} {tr('save_project').lower()}\n{save_path}")
        self.sync_gui_from_cfg()

    @safe_gui_callback
    def load_project(self):
        initial_dir = getattr(self, "last_dir", PROJECTS_DIR) or PROJECTS_DIR
        file_path = filedialog.askopenfilename(
            title=tr("open_project"),
            initialdir=initial_dir,
            filetypes=[(tr("project") + " JSON", "*.json")]
        )
        if file_path:
            self.last_dir = os.path.dirname(file_path)
            self.project_config = ProjectConfig.load_from_file(file_path)
            self.sync_gui_from_cfg()

    @safe_gui_callback
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
        """Refresca etiquetas y habilita el botón 'Ejecutar' según la configuración."""
        cfg = self.project_config
        self.lbl_project.config(
            text=f"{tr('project')}: {cfg.project_name or tr('unnamed_project') if 'unnamed_project' in _TRANSLATIONS else 'Sin nombre'}"
        )
        # Habilita o deshabilita los botones 'Ejecutar' según la configuración de cada análisis
        # Serie de tiempo
        series_cfg = getattr(cfg, 'series_config', {})
        ready_series = bool(series_cfg.get('data_file')) and bool(series_cfg.get('selected_indicators')) and bool(series_cfg.get('selected_units')) and bool(series_cfg.get('selected_years'))
        self.btn_run_series.config(state=tk.NORMAL if ready_series else tk.DISABLED)
        # Corte transversal
        cross_cfg = getattr(cfg, 'cross_section_config', {})
        ready_cross = bool(cross_cfg.get('data_file')) and bool(cross_cfg.get('selected_indicators')) and bool(cross_cfg.get('selected_units')) and bool(cross_cfg.get('selected_years'))
        self.btn_run_cross.config(state=tk.NORMAL if ready_cross else tk.DISABLED)
        # Panel 3D
        panel_cfg = getattr(cfg, 'panel_config', {})
        ready_panel = bool(panel_cfg.get('data_file')) and bool(panel_cfg.get('selected_indicators')) and bool(panel_cfg.get('selected_units')) and bool(panel_cfg.get('selected_years'))
        self.btn_run_panel.config(state=tk.NORMAL if ready_panel else tk.DISABLED)
    @safe_gui_callback
    def run_cross_section_analysis(self):
        from pca_cross_logic import PCAAnalysisLogic
        cfg = self.project_config.cross_section_config
        selected_years = [int(y) for y in cfg["selected_years"]]
        for year_to_analyze in selected_years:
            estrategia, params = None, None
            temp_results = PCAAnalysisLogic.run_cross_section_analysis_logic(cfg, year_to_analyze)
            if "warning" in temp_results and "faltantes" in temp_results["warning"]:
                respuesta = messagebox.askyesno(
                    f"Imputar año {year_to_analyze}",
                    f"Se encontraron datos faltantes para el año {year_to_analyze}.\n¿Quieres imputar los valores faltantes?"
                )
                if respuesta:
                    estrategia, params = self.gui_select_imputation_strategy()
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

            if len(evr_cs) >= 2:
                msg = tr("explained_variance_2").format(
                    year=year_to_analyze,
                    pc1=evr_cs[0],
                    pc2=evr_cs[1],
                    total=cum_evr_cs[1]
                ) if "explained_variance_2" in _TRANSLATIONS else (
                    f"Para el año {year_to_analyze}, los 2 primeros componentes explican:\n"
                    f"PC1: {evr_cs[0]:.2%}\n"
                    f"PC2: {evr_cs[1]:.2%}\n"
                    f"Total: {cum_evr_cs[1]:.2%} de la varianza"
                )
                title = tr("explained_variance_title") if "explained_variance_title" in _TRANSLATIONS else "Varianza explicada por los 2 componentes"
            elif len(evr_cs) == 1:
                msg = tr("explained_variance_1").format(
                    year=year_to_analyze,
                    pc1=evr_cs[0]
                ) if "explained_variance_1" in _TRANSLATIONS else (
                    f"Solo se pudo calcular un componente principal para el año {year_to_analyze}.\n"
                    f"PC1 explica: {evr_cs[0]:.2%} de la varianza"
                )
                title = tr("explained_variance_title") if "explained_variance_title" in _TRANSLATIONS else "Varianza explicada por los 2 componentes"
            else:
                msg = tr("explained_variance_none") if "explained_variance_none" in _TRANSLATIONS else "No se pudo calcular componentes principales para este año."
                title = tr("explained_variance_title") if "explained_variance_title" in _TRANSLATIONS else "Varianza explicada por los 2 componentes"
            messagebox.showinfo(title, msg)

            try:
                custom_colors = cfg.get("color_groups", {}) or {}
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
                    titulo=cfg.get("custom_titles", {}).get("biplot", f"Biplot {year_to_analyze}"),
                    legend_title=cfg.get("custom_titles", {}).get("legend", "Grupos de Países"),
                    ruta_guardado=None,
                    footer_note=cfg.get("custom_titles", {}).get("footer", "")
                )
            except Exception as e:
                messagebox.showwarning("Error Biplot", f"No se pudo generar el biplot: {e}")

            export_title = tr("export_title") if "export_title" in _TRANSLATIONS else "¿Exportar?"
            export_msg = tr("export_msg").format(year=year_to_analyze) if "export_msg" in _TRANSLATIONS else f"¿Quieres guardar los resultados para el año {year_to_analyze}?"
            if messagebox.askyesno(export_title, export_msg):
                filename = filedialog.asksaveasfilename(
                    title=tr("save_results_title").format(year=year_to_analyze) if "save_results_title" in _TRANSLATIONS else f"Guardar resultados {year_to_analyze}",
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
                    messagebox.showinfo(tr("done") if "done" in _TRANSLATIONS else "Listo", tr("file_saved").format(filename=filename) if "file_saved" in _TRANSLATIONS else f"Archivo guardado:\n{filename}")
        try:
            self.status.config(text="Análisis de corte transversal completado.")
        except tk.TclError:
            pass

    # --- FLUJO 3: Panel 3D ---
    @safe_gui_callback
    def start_panel_analysis(self):
        try:
            self._last_analysis_type = 'panel_config'
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

    @safe_gui_callback
    def run_panel_analysis(self):
        try:
            cfg = self.project_config.panel_config
            self.status.config(text=f"Panel 3D para años {cfg.get('selected_years', [])} y unidades: {cfg.get('selected_units', [])}")
            if not cfg.get('data_file') or not cfg.get('selected_indicators') or not cfg.get('selected_units'):
                messagebox.showerror("Error", "Faltan datos para el análisis 3D. Selecciona archivo, indicadores y países.")
                return
            all_sheets_data = dl.load_excel_file(cfg['data_file'])
            if not all_sheets_data:
                messagebox.showerror("Error", "No se pudieron cargar los datos del archivo seleccionado.")
                return
            results = PCAPanel3DLogic.run_panel3d_analysis_logic(
                all_sheets_data,
                list(all_sheets_data.keys()),
                cfg['selected_indicators'],
                cfg['selected_units']
            )
            if 'error' in results:
                messagebox.showerror("Error", results['error'])
                return
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

            # Opción de exportar resultados
            if messagebox.askyesno(tr("export_title") if "export_title" in _TRANSLATIONS else "¿Exportar?", tr("export_msg") if "export_msg" in _TRANSLATIONS else "¿Quieres guardar los resultados del análisis Panel 3D?"):
                filename = filedialog.asksaveasfilename(
                    title=tr("save_results_title") if "save_results_title" in _TRANSLATIONS else "Guardar resultados Panel 3D",
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx *.xls")]
                )
                if filename:
                    import pandas as pd
                    with pd.ExcelWriter(filename) as writer:
                        if results.get("df_pc_scores_panel") is not None:
                            results["df_pc_scores_panel"].to_excel(writer, sheet_name="PC_Scores_Panel", index=True)
                        if results.get("country_groups") is not None:
                            pd.DataFrame(results["country_groups"]).to_excel(writer, sheet_name="Country_Groups")
                        if results.get("group_colors") is not None:
                            pd.DataFrame(list(results["group_colors"].items()), columns=["Group", "Color"]).to_excel(writer, sheet_name="Group_Colors", index=False)
                    messagebox.showinfo(tr("done") if "done" in _TRANSLATIONS else "Listo", tr("file_saved").format(filename=filename) if "file_saved" in _TRANSLATIONS else f"Archivo guardado:\n{filename}")
        except tk.TclError:
            pass
    def _copy_current_to_config(self, config_name):
        """Copia la selección actual de la GUI al sub-config correspondiente."""
        cfg = getattr(self.project_config, config_name)
        # Copia los campos principales de la GUI a la subconfig
        # (esto asume que la GUI mantiene los campos temporales en self.project_config)
        for key in ["data_file", "selected_indicators", "selected_units", "selected_years", "color_groups", "group_labels", "custom_titles", "analysis_results", "footer_note"]:
            if hasattr(self.project_config, key):
                cfg[key] = getattr(self.project_config, key, cfg.get(key, None))
        

    # ========== REUTILIZABLES ==========

    def step_select_file(self, callback):
        file = filedialog.askopenfilename(
            title=tr("select_file"),
            initialdir=getattr(self, "last_dir", PROJECTS_DIR) or PROJECTS_DIR,
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not file:
            messagebox.showwarning(tr("warning"), tr("no_file_selected") if "no_file_selected" in _TRANSLATIONS else "No se seleccionó ningún archivo.")
            return
        if not os.path.isfile(file):
            messagebox.showerror(tr("error"), tr("file_not_found") if "file_not_found" in _TRANSLATIONS else "El archivo no existe.")
            return
        config_name = getattr(self, '_last_analysis_type', 'series_config')
        getattr(self.project_config, config_name)["data_file"] = file
        self.last_dir = os.path.dirname(file)
        import data_loader_module as dl
        try:
            all_sheets_data = dl.load_excel_file(file)
        except Exception as e:
            logger.exception("Error loading Excel file")
            messagebox.showerror(tr("error"), tr("file_load_error") + f"\n{e}" if "file_load_error" in _TRANSLATIONS else f"No se pudo cargar el archivo seleccionado.\n{e}")
            self.sheet_names = []
            self.sync_gui_from_cfg()
            return
        if all_sheets_data:
            self.sheet_names = list(all_sheets_data.keys())
            callback()
            self.sync_gui_from_cfg()  # ← nuevo
        else:
            self.sheet_names = []
            messagebox.showerror(tr("error"), tr("file_load_error") if "file_load_error" in _TRANSLATIONS else "No se pudo cargar el archivo seleccionado.")
            self.sync_gui_from_cfg()  # ← nuevo

    def step_select_indicators(self, callback, multi=True):
        """Abre una ventana para seleccionar uno o varios indicadores/hojas del Excel."""
        import tkinter as tk
        from tkinter import messagebox, Toplevel

        if not self.sheet_names:
            messagebox.showerror(tr("error"), tr("select_file_first") if "select_file_first" in _TRANSLATIONS else "Primero selecciona un archivo.")
            return

        win = Toplevel(self)
        win.title(tr("select_indicators"))
        win.geometry("420x480")

        # Instrucción clara
        n_disp = len(self.sheet_names)
        label_text = tr("select_indicators_label") if "select_indicators_label" in _TRANSLATIONS else f"Selecciona {'uno o más' if multi else 'un'} indicador{'es' if multi else ''} para el análisis ({n_disp} disponibles):"
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
                button_frame, text=tr("select_all"), command=lambda: listbox.select_set(0, tk.END),
                bg="lightgreen", fg="black", width=15
            )
            btn_selall.grid(row=0, column=0, padx=5)

            btn_unselall = tk.Button(
                button_frame, text=tr("unselect_all"), command=lambda: listbox.select_clear(0, tk.END),
                bg="lightcoral", fg="black", width=15
            )
            btn_unselall.grid(row=0, column=1, padx=5)

        # Botón OK
        def confirm_selection():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showerror(tr("error"), tr("select_at_least_one_indicator"))
                return
            config_name = getattr(self, '_last_analysis_type', 'series_config')
            getattr(self.project_config, config_name)["selected_indicators"] = [self.sheet_names[i] for i in selected_indices]
            win.destroy()
            callback()
            self.sync_gui_from_cfg()  # ← nuevo

        btn_ok = tk.Button(
            button_frame, text=tr("ok"), command=confirm_selection, bg="lightblue", fg="black", width=15
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
        config_name = getattr(self, '_last_analysis_type', 'series_config')
        cfg = getattr(self.project_config, config_name)
        if not cfg.get("data_file") or not cfg.get("selected_indicators"):
            messagebox.showerror(tr("error"), tr("select_file_and_indicators_first") if "select_file_and_indicators_first" in _TRANSLATIONS else "Primero selecciona archivo e indicadores.")
            return
        try:
            excel_data = pd.read_excel(
                cfg["data_file"],
                sheet_name=cfg["selected_indicators"][0]
            )
        except Exception as e:
            logger.exception("Error reading Excel for units")
            messagebox.showerror(tr("error"), tr("file_load_error") + f"\n{e}" if "file_load_error" in _TRANSLATIONS else f"No se pudo cargar el archivo seleccionado.\n{e}")
            return
        if 'Unnamed: 0' not in excel_data.columns:
            messagebox.showerror(tr("error"), tr("unnamed_col_missing") if "unnamed_col_missing" in _TRANSLATIONS else "No se encontró la columna 'Unnamed: 0' en la hoja seleccionada.")
            return
        all_units = sorted(excel_data['Unnamed: 0'].dropna().unique())
        if not all_units:
            messagebox.showwarning(tr("warning"), tr("no_units_found") if "no_units_found" in _TRANSLATIONS else "No se encontraron unidades en la hoja seleccionada.")
            return
        display_names = [f"{CODE_TO_NAME.get(unit, str(unit))} ({unit})" for unit in all_units]

        win = Toplevel(self)
        win.title(tr("select_units"))
        win.geometry("400x430")
        lbl = tk.Label(win, text=tr("select_units_label") if "select_units_label" in _TRANSLATIONS else "Selecciona unidades para el análisis:")
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
                messagebox.showerror(tr("error"), tr("select_at_least_one_unit"))
                return
            cfg["selected_units"] = [all_units[i] for i in selected_indices]
            win.destroy()
            callback()
            self.sync_gui_from_cfg()  # ← nuevo

        tk.Button(button_frame, text=tr("select_all"), command=select_all, bg="lightgreen", fg="black").grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text=tr("unselect_all"), command=unselect_all, bg="lightcoral", fg="black").grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text=tr("ok"), command=confirm_selection, bg="lightblue", fg="black").grid(row=0, column=2, padx=5)

    def step_select_year(self, callback=None, multi=True):
        config_name = getattr(self, '_last_analysis_type', 'series_config')
        cfg = getattr(self.project_config, config_name)
        try:
            df = pd.read_excel(
                cfg["data_file"],
                sheet_name=cfg["selected_indicators"][0]
            )
        except Exception as e:
            logger.exception("Error reading Excel for years")
            messagebox.showerror(tr("error"), tr("file_load_error") + f"\n{e}" if "file_load_error" in _TRANSLATIONS else f"No se pudo cargar el archivo seleccionado.\n{e}")
            return
        year_columns = [col for col in df.columns if col != 'Unnamed: 0' and str(col).isdigit()]
        year_columns = sorted(year_columns, key=lambda x: int(x))  # ordena por año
        if not year_columns:
            messagebox.showwarning(tr("warning"), tr("no_years_found") if "no_years_found" in _TRANSLATIONS else "No se encontraron años válidos en la hoja seleccionada.")
            return

        win = Toplevel(self)
        win.title(tr("select_years"))
        win.geometry("300x400")
        tk.Label(win, text=tr("select_years_label") if "select_years_label" in _TRANSLATIONS else "Select year(s) for analysis:").pack(pady=10)
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
                messagebox.showerror(tr("error"), tr("select_at_least_one_year"))
                return
            cfg["selected_years"] = [year_columns[i] for i in idxs]
            win.destroy()
            self.status.config(text=f"{tr('select_years')}: {cfg['selected_years']}")
            if callback:
                callback()
            self.sync_gui_from_cfg()

        button_frame = tk.Frame(win)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text=tr("select_all"), command=select_all, bg="lightgreen").grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text=tr("unselect_all"), command=unselect_all, bg="lightcoral").grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text=tr("ok"), command=confirm, bg="lightblue").grid(row=0, column=2, padx=5)

    def gui_select_imputation_strategy(self):
        estrategia = None
        params = {}

        STRATEGIAS = [
            ("interpolacion", tr("impute_interpolation") if "impute_interpolation" in _TRANSLATIONS else "Interpolación (lineal por defecto, o especificar método)"),
            ("mean", tr("impute_mean") if "impute_mean" in _TRANSLATIONS else "Rellenar con la Media"),
            ("median", tr("impute_median") if "impute_median" in _TRANSLATIONS else "Rellenar con la Mediana"),
            ("most_frequent", tr("impute_most_frequent") if "impute_most_frequent" in _TRANSLATIONS else "Rellenar con el Valor Más Frecuente (moda)"),
            ("ffill", tr("impute_ffill") if "impute_ffill" in _TRANSLATIONS else "Rellenar con valor anterior (Forward Fill)"),
            ("bfill", tr("impute_bfill") if "impute_bfill" in _TRANSLATIONS else "Rellenar con valor siguiente (Backward Fill)"),
            ("iterative", tr("impute_iterative") if "impute_iterative" in _TRANSLATIONS else "Imputación Iterativa (multivariada)"),
            ("knn", tr("impute_knn") if "impute_knn" in _TRANSLATIONS else "Imputación KNN (basada en vecinos)"),
            ("valor_constante", tr("impute_constant") if "impute_constant" in _TRANSLATIONS else "Rellenar con un Valor Constante específico"),
            ("eliminar_filas", tr("impute_drop_rows") if "impute_drop_rows" in _TRANSLATIONS else "Eliminar filas con datos faltantes"),
            ("ninguna", tr("impute_none") if "impute_none" in _TRANSLATIONS else "No aplicar ninguna imputación (mantener NaNs)"),
        ]

        win = Toplevel(self)
        win.title(tr("select_imputation_strategy") if "select_imputation_strategy" in _TRANSLATIONS else "Selecciona Estrategia de Imputación")
        win.geometry("480x420")
        tk.Label(win, text=tr("select_how_to_impute") if "select_how_to_impute" in _TRANSLATIONS else "Selecciona cómo quieres imputar los datos faltantes:", font=("Arial", 11, "bold")).pack(pady=10)

        estrategia_var = tk.StringVar(value="interpolacion")
        for key, txt in STRATEGIAS:
            tk.Radiobutton(win, text=txt, variable=estrategia_var, value=key, anchor="w", justify="left").pack(fill="x", padx=25)

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

        tk.Button(win, text=tr("ok"), command=on_ok, bg="lightblue").pack(pady=14)
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
        win.title(tr("select_n_components_title") if "select_n_components_title" in _TRANSLATIONS else "Seleccionar número de componentes principales")
        win.geometry("420x250")
        mensaje = tr("select_n_components_msg").format(max_components=max_components, n90=suggested_n_90, n95=suggested_n_95) if "select_n_components_msg" in _TRANSLATIONS else f"Ingrese cuántos componentes principales deseas retener (1-{max_components}).\n"
        if suggested_n_90:
            mensaje += f"{tr('suggestion_80') if 'suggestion_80' in _TRANSLATIONS else 'Sugerencia:'} {suggested_n_90} componentes ≈ 80% varianza.\n"
        if suggested_n_95:
            mensaje += f"{tr('suggestion_90') if 'suggestion_90' in _TRANSLATIONS else 'Sugerencia:'} {suggested_n_95} componentes ≈ 90% varianza.\n"
        mensaje += f"{tr('leave_empty_for_all') if 'leave_empty_for_all' in _TRANSLATIONS else f'Deja vacío para usar todos ({max_components}).'}"

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
                        messagebox.showerror(tr("error"), tr("n_components_range").format(max_components=max_components) if "n_components_range" in _TRANSLATIONS else f"El número debe estar entre 1 y {max_components}.")
                        return
                except Exception:
                    messagebox.showerror(tr("error"), tr("must_be_integer") if "must_be_integer" in _TRANSLATIONS else "Debes ingresar un número entero válido.")
                    return
            win.destroy()

        tk.Button(win, text=tr("ok"), command=on_ok, bg="lightblue", width=12).pack(pady=16)
        win.grab_set()
        self.wait_window(win)
        return selected_n[0]

    def run_project_from_cfg(self):
        cfg = self.project_config
        ready = {
            'series': all([
                cfg.series_config.get('data_file'),
                cfg.series_config.get('selected_indicators'),
                cfg.series_config.get('selected_units'),
                cfg.series_config.get('selected_years')
            ]),
            'cross_section': all([
                cfg.cross_section_config.get('data_file'),
                cfg.cross_section_config.get('selected_indicators'),
                cfg.cross_section_config.get('selected_units'),
                cfg.cross_section_config.get('selected_years')
            ]),
            'panel': all([
                cfg.panel_config.get('data_file'),
                cfg.panel_config.get('selected_indicators'),
                cfg.panel_config.get('selected_units'),
                cfg.panel_config.get('selected_years')
            ])
        }
        available = [k for k, v in ready.items() if v]
        if not available:
            messagebox.showinfo("Selector de flujo", "No hay ningún análisis configurado para ejecutar.")
            return
        if len(available) == 1:
            if available[0] == 'series':
                self.run_series_analysis()
            elif available[0] == 'cross_section':
                self.run_cross_section_analysis()
            elif available[0] == 'panel':
                self.run_panel_analysis()
        else:
            # Preguntar al usuario cuál ejecutar
            win = Toplevel(self)
            win.title("¿Qué análisis quieres ejecutar?")
            win.geometry("340x200")
            tk.Label(win, text="Selecciona el análisis a ejecutar:", font=("Arial", 12)).pack(pady=18)
            for tipo, label, func in [
                ('series', 'Serie de tiempo', self.run_series_analysis),
                ('cross_section', 'Corte transversal', self.run_cross_section_analysis),
                ('panel', 'Panel 3D', self.run_panel_analysis)
            ]:
                if tipo in available:
                    tk.Button(win, text=label, width=22, height=2, command=lambda f=func, w=win: (w.destroy(), f())).pack(pady=6)
            tk.Button(win, text="Cancelar", command=win.destroy).pack(pady=8)
            win.grab_set(); win.focus_set()

    @safe_gui_callback
    def edit_title_dialog(self, config_name=None):
        config_name = config_name or 'series_config'
        cfg = getattr(self.project_config, config_name)
        new_title = simpledialog.askstring(
            tr("edit_title"),
            tr("enter_new_title") if "enter_new_title" in _TRANSLATIONS else "Escribe el nuevo título:",
            initialvalue=cfg["custom_titles"].get("biplot", "")
        )
        if new_title is not None:
            cfg["custom_titles"]["biplot"] = new_title.strip()
            self.status.config(text=tr("title_updated") if "title_updated" in _TRANSLATIONS else "Título actualizado.")
            self.sync_gui_from_cfg()

    @safe_gui_callback
    def edit_legend_dialog(self, config_name=None):
        config_name = config_name or 'series_config'
        cfg = getattr(self.project_config, config_name)
        new_txt = simpledialog.askstring(
            tr("edit_legend"),
            tr("enter_legend_title") if "enter_legend_title" in _TRANSLATIONS else "Escribe cómo quieres que aparezca el encabezado de la leyenda:",
            initialvalue=cfg["custom_titles"].get("legend", "")
        )
        if new_txt is not None:
            cfg["custom_titles"]["legend"] = new_txt.strip()
            self.status.config(text=tr("legend_title_updated") if "legend_title_updated" in _TRANSLATIONS else "Título de leyenda actualizado.")
            self.sync_gui_from_cfg()

    @safe_gui_callback
    def edit_colors_dialog(self, config_name=None):
        config_name = config_name or 'series_config'
        cfg = getattr(self.project_config, config_name)
        win = Toplevel(self); win.title(tr("assign_colors"))
        win.geometry("360x420"); win.resizable(False, False)
        tk.Label(win, text=tr("choose_units") if "choose_units" in _TRANSLATIONS else "Elige individuos / unidades:").pack(pady=(12,2))
        lst = tk.Listbox(win, selectmode=tk.EXTENDED, height=14, width=34)
        for name in sorted(cfg["selected_units"]):
            lst.insert(tk.END, name)
        lst.pack()
        preview = tk.Label(win, width=4, relief="groove", bg="gray")
        preview.pack(pady=6)
        def refresh_preview(*_):
            sels = lst.curselection()
            if sels:
                unit = lst.get(sels[0])
                preview.config(bg=cfg["color_groups"].get(unit, "gray"))
        lst.bind("<<ListboxSelect>>", refresh_preview)
        def set_color():
            rgb, hex_ = colorchooser.askcolor()
            if not hex_:
                return
            for i in lst.curselection():
                cfg["color_groups"][lst.get(i)] = hex_
            refresh_preview()
        def unset_color():
            for i in lst.curselection():
                cfg["color_groups"].pop(lst.get(i), None)
            refresh_preview()
        frm_btn = tk.Frame(win); frm_btn.pack(pady=4)
        tk.Button(frm_btn, text=tr("choose_color") if "choose_color" in _TRANSLATIONS else "Elegir color",  width=12, command=set_color).grid(row=0, column=0, padx=4)
        tk.Button(frm_btn, text=tr("remove_color") if "remove_color" in _TRANSLATIONS else "Quitar color",  width=12, command=unset_color).grid(row=0, column=1, padx=4)
        def accept():
            self.sync_gui_from_cfg()
            win.destroy()
        tk.Button(win, text=tr("ok"), width=12, bg="#b7e0ee", command=accept).pack(pady=(12,8))
        win.grab_set(); win.focus_set()

    @safe_gui_callback
    def edit_units_dialog(self, config_name=None):
        """
        Permite borrar o agregar unidades en caliente.
        • Muestra dos list-box:
          -  «Disponibles»  (todas las que existen en el Excel)
          -  «Seleccionadas» (las que ya están en cfg.selected_units)
        • Botones  >>  y  <<  para mover.
        """
        config_name = config_name or 'series_config'
        cfg = getattr(self.project_config, config_name)
        if not cfg["data_file"] or not cfg["selected_indicators"]:
            messagebox.showwarning(tr("warning"), tr("select_file_and_indicators_first") if "select_file_and_indicators_first" in _TRANSLATIONS else "Primero elige archivo/indicadores")
            return
        all_units = sorted(
            pd.read_excel(
                cfg["data_file"],
                sheet_name=cfg["selected_indicators"][0]
            )['Unnamed: 0'].dropna().unique()
        )
        win = Toplevel(self); win.title(tr("edit_units")); win.resizable(False, False)
        tk.Label(win, text=tr("available") if "available" in _TRANSLATIONS else "Disponibles").grid(row=0, column=0, padx=8, pady=6)
        tk.Label(win, text=tr("selected") if "selected" in _TRANSLATIONS else "Seleccionadas").grid(row=0, column=2, padx=8, pady=6)
        lst_all  = tk.Listbox(win, height=18, selectmode=tk.EXTENDED, exportselection=False)
        lst_sel  = tk.Listbox(win, height=18, selectmode=tk.EXTENDED, exportselection=False)
        for u in all_units:         lst_all.insert(tk.END, u)
        for u in cfg["selected_units"]: lst_sel.insert(tk.END, u)
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
                cfg["color_groups"].pop(item, None)
        tk.Button(frm_btn, text=tr("move_right") if "move_right" in _TRANSLATIONS else ">>", command=to_sel).pack(pady=10)
        tk.Button(frm_btn, text=tr("move_left") if "move_left" in _TRANSLATIONS else "<<", command=to_all).pack(pady=10)
        def accept():
            cfg["selected_units"] = list(lst_sel.get(0, tk.END))
            self.sync_gui_from_cfg()
            win.destroy()
        tk.Button(win, text=tr("ok"), width=12, command=accept).grid(row=2, column=0, columnspan=3, pady=12)
        win.grab_set(); win.focus_set()

    @safe_gui_callback
    def edit_footer_dialog(self, config_name=None):
        config_name = config_name or 'series_config'
        cfg = getattr(self.project_config, config_name)
        new_note = simpledialog.askstring(
            tr("edit_footer"),
            tr("enter_footer") if "enter_footer" in _TRANSLATIONS else "Texto que aparecerá debajo del gráfico:",
            initialvalue=cfg["custom_titles"].get("footer", "")
        )
        if new_note is not None:
            cfg["custom_titles"]["footer"] = new_note.strip()
            self.status.config(text=tr("footer_updated") if "footer_updated" in _TRANSLATIONS else "Fuente/leyenda actualizada.")
            self.sync_gui_from_cfg()

# ------------- FIN CLASE --------------

if __name__ == "__main__":
    app = PCAApp()
    app.mainloop()
