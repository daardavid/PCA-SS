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

# Importar sistemas mejorados
try:
    from logging_config import get_logger, setup_application_logging
    from config_manager import get_config, update_config, save_config
    from performance_optimizer import profiled
    # Configurar logging mejorado
    setup_application_logging(debug_mode=False)
    ENHANCED_SYSTEMS_AVAILABLE = True
except ImportError:
    ENHANCED_SYSTEMS_AVAILABLE = False
    def get_logger(name):
        return logging.getLogger(name)

# Import del gestor de dependencias
try:
    from dependency_manager import dep_manager, safe_import
    DEPENDENCY_MANAGER_AVAILABLE = True
except ImportError:
    DEPENDENCY_MANAGER_AVAILABLE = False
    def safe_import(package_name: str, attribute: str = None):
        """Fallback para importación segura."""
        try:
            module = __import__(package_name)
            if attribute:
                return getattr(module, attribute)
            return module
        except (ImportError, AttributeError):
            return None

# Verificación de dependencias críticas al inicio
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  Warning: matplotlib no disponible. Las visualizaciones no funcionarán.")


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

# Usar sistema de logging mejorado si está disponible
if ENHANCED_SYSTEMS_AVAILABLE:
    logger = get_logger("pca_gui")
else:
    # Fallback al sistema de logging original
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
        self.title("🔬 PCA Socioeconómicos - Análisis Avanzado")
        
        # Configurar tamaño mínimo y inicial
        self.geometry("900x700")
        self.minsize(800, 600)
        
        logger.info("Iniciando aplicación PCA GUI")
        self._setup_config()
        self._setup_ui()
        self._bind_events()

    @safe_gui_callback
    @profiled if ENHANCED_SYSTEMS_AVAILABLE else lambda x: x
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
    @profiled if ENHANCED_SYSTEMS_AVAILABLE else lambda x: x
    def run_series_analysis(self):
        """Ejecuta el análisis de serie de tiempo para la unidad y años seleccionados (pueden ser varios años)."""
        from pca_logic import PCAAnalysisLogic
        cfg = self.project_config.series_config
        estrategia, params = None, None
        # Obtener los años seleccionados (pueden ser varios)
        selected_years = []
        if cfg.get("selected_years"):
            selected_years = cfg["selected_years"] if isinstance(cfg["selected_years"], list) else [cfg["selected_years"]]
        
        # Primero ejecuta una validación para detectar datos faltantes
        temp_results = PCAAnalysisLogic.run_series_analysis_logic(cfg, imputation_strategy=None, imputation_params=None, selected_years=selected_years)
        if "warning" in temp_results and ("faltantes" in temp_results["warning"] or "datos faltantes" in temp_results["warning"]):
            respuesta = messagebox.askyesno(
                "Datos faltantes detectados",
                f"Se encontraron datos faltantes en la serie de tiempo.\n¿Quieres imputar los valores faltantes?\n\nDetalle: {temp_results['warning']}"
            )
            if respuesta:
                estrategia, params = self.gui_select_imputation_strategy()
            else:
                # Si el usuario no quiere imputar, mostrar el warning y salir
                messagebox.showwarning("Advertencia", temp_results["warning"])
                return
        
        # Ejecuta la lógica real con la estrategia de imputación seleccionada
        results = PCAAnalysisLogic.run_series_analysis_logic(cfg, imputation_strategy=estrategia, imputation_params=params, selected_years=selected_years)
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
        # Limpia selección de años al iniciar el flujo
        self.project_config.series_config["selected_years"] = []
        self.step_select_file(lambda: self._series_select_indicators())

    def _series_select_indicators(self):
        # Limpia selección de años al cambiar indicadores
        self.project_config.series_config["selected_years"] = []
        self.step_select_indicators(lambda: self._series_select_units(), multi=True)

    def _series_select_units(self):
        # Limpia selección de años al cambiar unidad
        self.project_config.series_config["selected_years"] = []
        self.step_select_units(lambda: self._series_select_years(), allow_multiple=False)

    def _series_select_years(self):
        self.step_select_year(lambda: self.sync_gui_from_cfg(), multi=True)
    def show_settings_window(self):
        """Ventana de configuración moderna y mejorada."""
        win = Toplevel(self)
        win.title("⚙️ Configuración")
        win.geometry("450x550")
        win.resizable(False, False)
        
        # Aplicar tema a la ventana
        win.configure(bg=getattr(self, 'bg_primary', '#ffffff'))
        
        # Título principal
        title_frame = tk.Frame(win, bg=getattr(self, 'bg_primary', '#ffffff'))
        title_frame.pack(fill='x', pady=(20, 30))
        
        title_label = tk.Label(
            title_frame,
            text="🎨 Personalización",
            font=("Segoe UI", 16, "bold"),
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_primary', '#1e293b')
        )
        title_label.pack()
        
        # Contenedor principal con scroll si es necesario
        main_frame = tk.Frame(win, bg=getattr(self, 'bg_primary', '#ffffff'))
        main_frame.pack(fill='both', expand=True, padx=30)
        
        # Sección Tema
        self._create_settings_section(main_frame, "🌙 Tema", 0)
        theme_var = tk.StringVar(value=getattr(self, "theme", "light"))
        theme_frame = tk.Frame(main_frame, bg=getattr(self, 'bg_primary', '#ffffff'))
        theme_frame.pack(fill='x', pady=(5, 20))
        
        light_btn = tk.Radiobutton(
            theme_frame, text="☀️ Claro", variable=theme_var, value="light",
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_primary', '#1e293b'),
            selectcolor=getattr(self, 'accent_color', '#3b82f6'),
            font=("Segoe UI", 10)
        )
        light_btn.pack(side="left", padx=(20, 30))
        
        dark_btn = tk.Radiobutton(
            theme_frame, text="🌙 Oscuro", variable=theme_var, value="dark",
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_primary', '#1e293b'),
            selectcolor=getattr(self, 'accent_color', '#3b82f6'),
            font=("Segoe UI", 10)
        )
        dark_btn.pack(side="left")

        # Sección Idioma
        self._create_settings_section(main_frame, "🌍 Idioma / Language", 20)
        lang_var = tk.StringVar(value=getattr(self, "lang", "es"))
        lang_frame = tk.Frame(main_frame, bg=getattr(self, 'bg_primary', '#ffffff'))
        lang_frame.pack(fill='x', pady=(5, 20))
        
        es_btn = tk.Radiobutton(
            lang_frame, text="🇪🇸 Español", variable=lang_var, value="es",
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_primary', '#1e293b'),
            selectcolor=getattr(self, 'accent_color', '#3b82f6'),
            font=("Segoe UI", 10)
        )
        es_btn.pack(side="left", padx=(20, 30))
        
        en_btn = tk.Radiobutton(
            lang_frame, text="🇺🇸 English", variable=lang_var, value="en",
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_primary', '#1e293b'),
            selectcolor=getattr(self, 'accent_color', '#3b82f6'),
            font=("Segoe UI", 10)
        )
        en_btn.pack(side="left")

        # Sección Ventana
        self._create_settings_section(main_frame, "📐 Tamaño de Ventana", 20)
        size_var = tk.StringVar(value=self.geometry())
        size_entry = self._create_modern_entry(main_frame, size_var, "Ej: 900x700")
        
        # Sección Fuente
        self._create_settings_section(main_frame, "🔤 Tipografía", 20)
        font_var = tk.StringVar(value=getattr(self, "custom_font", "Segoe UI"))
        font_entry = self._create_modern_entry(main_frame, font_var, "Nombre de la fuente")
        
        fontsize_var = tk.StringVar(value=str(getattr(self, "custom_fontsize", 10)))
        fontsize_entry = self._create_modern_entry(main_frame, fontsize_var, "Tamaño (8-16)", width=15)

        # Botones de acción
        buttons_frame = tk.Frame(win, bg=getattr(self, 'bg_primary', '#ffffff'))
        buttons_frame.pack(fill='x', pady=(30, 20), padx=30)
        
        def save_and_close():
            self.theme = theme_var.get()
            self.custom_font = font_var.get() or "Segoe UI"
            try:
                self.custom_fontsize = max(8, min(16, int(fontsize_var.get())))
            except:
                self.custom_fontsize = 10
            try:
                self.geometry(size_var.get())
            except:
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
        
        # Botón guardar con estilo moderno
        save_btn = self.create_modern_button(
            buttons_frame, 
            text="💾 Guardar Cambios", 
            command=save_and_close,
            style="success",
            width=20
        )
        save_btn.pack(side='right', padx=(10, 0))
        
        # Botón cancelar
        cancel_btn = self.create_modern_button(
            buttons_frame, 
            text="❌ Cancelar", 
            command=win.destroy,
            style="secondary",
            width=15
        )
        cancel_btn.pack(side='right')
        
        win.grab_set()
        win.focus_set()
        
        # Centrar ventana
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")

    def _create_settings_section(self, parent, title, pady_top=0):
        """Crea una sección con título en la ventana de configuración."""
        section_label = tk.Label(
            parent,
            text=title,
            font=("Segoe UI", 12, "bold"),
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'accent_color', '#3b82f6')
        )
        section_label.pack(anchor='w', pady=(pady_top, 5))
        return section_label

    def _create_modern_entry(self, parent, textvariable, placeholder="", width=25):
        """Crea un Entry moderno con placeholder."""
        entry_frame = tk.Frame(parent, bg=getattr(self, 'bg_primary', '#ffffff'))
        entry_frame.pack(fill='x', pady=(5, 10))
        
        entry = tk.Entry(
            entry_frame,
            textvariable=textvariable,
            font=("Segoe UI", 10),
            bg=getattr(self, 'bg_secondary', '#f8fafc'),
            fg=getattr(self, 'fg_primary', '#1e293b'),
            relief="flat",
            bd=1,
            width=width,
            insertbackground=getattr(self, 'fg_primary', '#1e293b')
        )
        entry.pack(padx=(20, 0), anchor='w')
        
        # Añadir placeholder como etiqueta si está vacío
        if placeholder:
            placeholder_label = tk.Label(
                entry_frame,
                text=f"💡 {placeholder}",
                font=("Segoe UI", 8),
                fg=getattr(self, 'fg_secondary', '#64748b'),
                bg=getattr(self, 'bg_primary', '#ffffff')
            )
            placeholder_label.pack(padx=(25, 0), anchor='w')
        
    def create_modern_window(self, title, width=400, height=500, resizable=True):
        """Crea una ventana moderna con el tema aplicado."""
        win = Toplevel(self)
        win.title(title)
        win.geometry(f"{width}x{height}")
        win.resizable(resizable, resizable)
        
        # Usar colores seguros por defecto
        bg_color = getattr(self, 'bg_primary', '#ffffff')
        win.configure(bg=bg_color)
        
        # Centrar ventana
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
        
        return win

    def create_modern_listbox(self, parent, selectmode=tk.MULTIPLE, height=15):
        """Crea un Listbox moderno con scrollbar."""
        # Frame contenedor
        listbox_frame = tk.Frame(parent, bg=getattr(self, 'bg_primary', '#ffffff'))
        
        # Listbox con estilo moderno
        listbox = tk.Listbox(
            listbox_frame,
            selectmode=selectmode,
            font=("Segoe UI", 10),
            bg=getattr(self, 'bg_secondary', '#f8fafc'),
            fg=getattr(self, 'fg_primary', '#1e293b'),
            selectbackground=getattr(self, 'accent_color', '#3b82f6'),
            selectforeground='white',
            relief="flat",
            bd=1,
            height=height,
            activestyle='none'
        )
        
        # Scrollbar moderna
        scrollbar = tk.Scrollbar(
            listbox_frame,
            orient="vertical",
            command=listbox.yview,
            bg=getattr(self, 'bg_secondary', '#f8fafc'),
            troughcolor=getattr(self, 'bg_primary', '#ffffff'),
            relief="flat",
            bd=0
        )
        
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return listbox_frame, listbox

    def apply_matplotlib_style(self):
        import matplotlib.pyplot as plt
        if getattr(self, "theme", "light") == "dark":
            plt.style.use('dark_background')
        else:
            plt.style.use('default')

    def apply_theme(self):
        """Aplica tema visual moderno con colores mejorados y efectos."""
        # Colores modernos mejorados
        if getattr(self, "theme", "light") == "dark":
            # Tema oscuro moderno
            self.bg_primary = "#1e1e2e"
            self.bg_secondary = "#313244" 
            self.fg_primary = "#cdd6f4"
            self.fg_secondary = "#a6adc8"
            self.accent_color = "#89b4fa"
            self.success_color = "#a6e3a1"
            self.warning_color = "#f9e2af"
            self.error_color = "#f38ba8"
            self.btn_primary = "#89b4fa"
            self.btn_secondary = "#585b70"
            self.btn_success = "#a6e3a1"
            self.btn_hover = "#74c7ec"
        else:
            # Tema claro moderno
            self.bg_primary = "#ffffff"
            self.bg_secondary = "#f8fafc"
            self.fg_primary = "#1e293b"
            self.fg_secondary = "#475569"
            self.accent_color = "#3b82f6"
            self.success_color = "#10b981"
            self.warning_color = "#f59e0b"
            self.error_color = "#ef4444"
            self.btn_primary = "#3b82f6"
            self.btn_secondary = "#64748b"
            self.btn_success = "#10b981"
            self.btn_hover = "#2563eb"
        
        # Aplicar colores base
        self.configure(bg=self.bg_primary)
        
        # Actualizar widgets recursivamente
        self._update_widget_theme(self)
        
        # Menú con colores modernos
        if hasattr(self, 'menu_bar'):
            self.menu_bar.configure(
                bg=self.bg_secondary, 
                fg=self.fg_primary,
                activebackground=self.accent_color,
                activeforeground=self.bg_primary
            )

    def _update_widget_theme(self, parent):
        """Actualiza recursivamente el tema de todos los widgets."""
        for widget in parent.winfo_children():
            widget_class = widget.winfo_class()
            
            if widget_class == "Label":
                widget.configure(bg=self.bg_primary, fg=self.fg_primary)
            elif widget_class == "Frame":
                widget.configure(bg=self.bg_primary)
                self._update_widget_theme(widget)  # Recursivo para frames
            elif widget_class == "Button":
                # No aplicar tema automático a botones, se manejan individualmente
                pass
            elif widget_class == "Entry":
                widget.configure(
                    bg=self.bg_secondary, 
                    fg=self.fg_primary,
                    insertbackground=self.fg_primary,
                    relief="flat",
                    bd=1
                )
            elif widget_class == "Listbox":
                widget.configure(
                    bg=self.bg_secondary,
                    fg=self.fg_primary,
                    selectbackground=self.accent_color,
                    relief="flat",
                    bd=1
                )

    def apply_font_settings(self):
        """Aplica configuración de fuente moderna."""
        font = getattr(self, "custom_font", "Segoe UI")
        fontsize = getattr(self, "custom_fontsize", 10)
        
        # Fuentes diferenciadas para jerarquía visual
        self.font_title = (font, fontsize + 4, "bold")
        self.font_button = (font, fontsize, "normal")
        self.font_label = (font, fontsize, "normal")
        self.font_small = (font, fontsize - 1, "normal")
        
        # Aplicar a widgets principales
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                if hasattr(widget, '_is_title'):
                    widget.configure(font=self.font_title)
                else:
                    widget.configure(font=self.font_label)

    def create_modern_button(self, parent, text, command=None, style="primary", width=None, height=2):
        """Crea un botón moderno con efectos hover y colores mejorados."""
        # Asegurar que las fuentes estén definidas
        if not hasattr(self, 'font_button'):
            font = getattr(self, "custom_font", "Segoe UI")
            fontsize = getattr(self, "custom_fontsize", 10)
            self.font_button = (font, fontsize, "normal")
        
        # Configurar colores según el estilo
        if style == "primary":
            bg_normal = getattr(self, 'btn_primary', '#3b82f6')
            bg_hover = getattr(self, 'btn_hover', '#2563eb')
            fg_color = '#ffffff'
        elif style == "success":
            bg_normal = getattr(self, 'btn_success', '#10b981')
            bg_hover = '#059669'
            fg_color = '#ffffff'
        elif style == "secondary":
            bg_normal = getattr(self, 'btn_secondary', '#64748b')
            bg_hover = '#475569'
            fg_color = '#ffffff'
        else:
            bg_normal = getattr(self, 'btn_primary', '#3b82f6')
            bg_hover = getattr(self, 'btn_hover', '#2563eb')
            fg_color = '#ffffff'
        
        # Crear botón con configuración moderna
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_normal,
            fg=fg_color,
            font=self.font_button,
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            width=width,
            height=height
        )
        
        # Añadir efectos hover
        btn.bind("<Enter>", lambda e: btn.configure(bg=bg_hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg_normal))
        
        return btn

    def load_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "last_dir": "", 
                "theme": "light",
                "window_size": "900x700",
                "custom_font": "Segoe UI",
                "custom_fontsize": 10,
                "lang": "es"
            }

    def save_settings(self):
        settings = {
            "last_dir": getattr(self, "last_dir", ""),
            "theme": getattr(self, "theme", "light"),
            "window_size": self.geometry(),
            "custom_font": getattr(self, "custom_font", "Segoe UI"),
            "custom_fontsize": getattr(self, "custom_fontsize", 10),
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
        
        # Inicializar colores de tema y fuentes antes de crear UI
        self.apply_theme()
        self.apply_font_settings()
        
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
        # Interfaz principal moderna
        
        # Título principal con estilo moderno
        title_frame = tk.Frame(self, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        title_frame.pack(pady=(30, 20), fill='x')
        
        self.lbl_analysis_type = tk.Label(
            title_frame, 
            text="🔬 " + tr("select_analysis_type"), 
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff',
            fg=self.fg_primary if hasattr(self, 'fg_primary') else '#1e293b'
        )
        self.lbl_analysis_type._is_title = True
        self.lbl_analysis_type.pack()
        
        # Contenedor principal con mejor organización
        main_container = tk.Frame(self, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        main_container.pack(pady=20, padx=40, fill='both', expand=True)
        
        # --- Serie de Tiempo ---
        series_frame = tk.Frame(main_container, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        series_frame.pack(pady=10, fill='x')
        
        series_label = tk.Label(
            series_frame, 
            text="📈 Serie de Tiempo", 
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff',
            fg=self.fg_primary if hasattr(self, 'fg_primary') else '#1e293b'
        )
        series_label.pack(anchor='w', pady=(0, 5))
        
        frm_series = tk.Frame(series_frame, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        frm_series.pack(fill='x')
        
        self.btn_series = self.create_modern_button(
            frm_series, 
            text=tr("series_analysis"), 
            command=self.start_series_analysis,
            style="primary",
            width=35
        )
        self.btn_series.pack(side="left", padx=(0, 10))
        
        self.btn_run_series = self.create_modern_button(
            frm_series, 
            text="▶ Ejecutar", 
            command=self.run_series_analysis,
            style="success",
            width=12
        )
        self.btn_run_series.pack(side="left")
        self.btn_run_series.config(state=tk.DISABLED)
        
        # --- Corte Transversal ---
        cross_frame = tk.Frame(main_container, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        cross_frame.pack(pady=10, fill='x')
        
        cross_label = tk.Label(
            cross_frame, 
            text="📊 Corte Transversal", 
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff',
            fg=self.fg_primary if hasattr(self, 'fg_primary') else '#1e293b'
        )
        cross_label.pack(anchor='w', pady=(0, 5))
        
        frm_cross = tk.Frame(cross_frame, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        frm_cross.pack(fill='x')
        
        self.btn_cross = self.create_modern_button(
            frm_cross, 
            text=tr("cross_section_analysis"), 
            command=self.start_cross_section_analysis,
            style="primary",
            width=35
        )
        self.btn_cross.pack(side="left", padx=(0, 10))
        
        self.btn_run_cross = self.create_modern_button(
            frm_cross, 
            text="▶ Ejecutar", 
            command=self.run_cross_section_analysis,
            style="success",
            width=12
        )
        self.btn_run_cross.pack(side="left")
        self.btn_run_cross.config(state=tk.DISABLED)
        
        # --- Panel 3D ---
        panel_frame = tk.Frame(main_container, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        panel_frame.pack(pady=10, fill='x')
        
        panel_label = tk.Label(
            panel_frame, 
            text="🎯 PCA 3D", 
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff',
            fg=self.fg_primary if hasattr(self, 'fg_primary') else '#1e293b'
        )
        panel_label.pack(anchor='w', pady=(0, 5))
        
        frm_panel = tk.Frame(panel_frame, bg=self.bg_primary if hasattr(self, 'bg_primary') else '#ffffff')
        frm_panel.pack(fill='x')
        
        self.btn_panel = self.create_modern_button(
            frm_panel, 
            text=tr("panel_analysis"), 
            command=self.start_panel_analysis,
            style="primary",
            width=35
        )
        self.btn_panel.pack(side="left", padx=(0, 10))
        
        self.btn_run_panel = self.create_modern_button(
            frm_panel, 
            text="▶ Ejecutar", 
            command=self.run_panel_analysis,
            style="success",
            width=12
        )
        self.btn_run_panel.pack(side="left")
        self.btn_run_panel.config(state=tk.DISABLED)
        
        # Barra de estado moderna
        status_frame = tk.Frame(self, bg=self.bg_secondary if hasattr(self, 'bg_secondary') else '#f8fafc', height=60)
        status_frame.pack(side='bottom', fill='x', pady=(20, 0))
        status_frame.pack_propagate(False)
        
        self.status = tk.Label(
            status_frame, 
            text="⏳ " + tr("status_waiting"), 
            fg=self.accent_color if hasattr(self, 'accent_color') else '#3b82f6',
            bg=self.bg_secondary if hasattr(self, 'bg_secondary') else '#f8fafc',
            font=("Segoe UI", 10, "italic")
        )
        self.status.pack(pady=15)

        self.lbl_project = tk.Label(
            status_frame, 
            text=f"📁 {tr('project')}: Ninguno", 
            fg=self.fg_secondary if hasattr(self, 'fg_secondary') else '#475569',
            bg=self.bg_secondary if hasattr(self, 'bg_secondary') else '#f8fafc',
            font=("Segoe UI", 9)
        )
        self.lbl_project.pack()

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
        # Limpia selección de años al cambiar archivo en serie de tiempo
        if config_name == "series_config":
            getattr(self.project_config, config_name)["selected_years"] = []
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
        """Ventana moderna para seleccionar indicadores/hojas del Excel."""
        if not self.sheet_names:
            messagebox.showerror(tr("error"), tr("select_file_first") if "select_file_first" in _TRANSLATIONS else "Primero selecciona un archivo.")
            return

        # Crear ventana moderna
        win = self.create_modern_window("📊 " + tr("select_indicators"), 500, 600)
        
        # Título y descripción
        title_frame = tk.Frame(win, bg=getattr(self, 'bg_primary', '#ffffff'))
        title_frame.pack(fill='x', pady=(20, 10), padx=20)
        
        title_label = tk.Label(
            title_frame,
            text="📊 Seleccionar Indicadores",
            font=("Segoe UI", 16, "bold"),
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_primary', '#1e293b')
        )
        title_label.pack()
        
        # Descripción
        n_disp = len(self.sheet_names)
        desc_text = f"Selecciona {'uno o más' if multi else 'un'} indicador{'es' if multi else ''} para el análisis\n({n_disp} disponibles)"
        
        desc_label = tk.Label(
            title_frame,
            text=desc_text,
            font=("Segoe UI", 10),
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_secondary', '#64748b'),
            wraplength=450
        )
        desc_label.pack(pady=(5, 0))

        # Contenedor del listbox
        content_frame = tk.Frame(win, bg=getattr(self, 'bg_primary', '#ffffff'))
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Listbox moderno
        listbox_frame, listbox = self.create_modern_listbox(
            content_frame, 
            selectmode=tk.MULTIPLE if multi else tk.SINGLE,
            height=18
        )
        listbox_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Llenar listbox con indicadores
        for ind in self.sheet_names:
            listbox.insert(tk.END, f"📈 {ind}")

        # Frame de botones
        buttons_frame = tk.Frame(content_frame, bg=getattr(self, 'bg_primary', '#ffffff'))
        buttons_frame.pack(fill='x')

        # Botones de selección (solo para múltiple)
        if multi:
            selection_frame = tk.Frame(buttons_frame, bg=getattr(self, 'bg_primary', '#ffffff'))
            selection_frame.pack(fill='x', pady=(0, 15))
            
            select_all_btn = self.create_modern_button(
                selection_frame,
                text="✅ Seleccionar Todo",
                command=lambda: listbox.select_set(0, tk.END),
                style="secondary",
                width=20
            )
            select_all_btn.pack(side="left", padx=(0, 10))

            unselect_all_btn = self.create_modern_button(
                selection_frame,
                text="❌ Deseleccionar Todo",
                command=lambda: listbox.select_clear(0, tk.END),
                style="secondary",
                width=20
            )
            unselect_all_btn.pack(side="left")

        # Botones de acción
        action_frame = tk.Frame(buttons_frame, bg=getattr(self, 'bg_primary', '#ffffff'))
        action_frame.pack(fill='x')

        def confirm_selection():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showerror(tr("error"), tr("select_at_least_one_indicator"))
                return
                
            config_name = getattr(self, '_last_analysis_type', 'series_config')
            getattr(self.project_config, config_name)["selected_indicators"] = [self.sheet_names[i] for i in selected_indices]
            
            # Limpia selección de años al cambiar indicadores en serie de tiempo
            if config_name == "series_config":
                getattr(self.project_config, config_name)["selected_years"] = []
                
            win.destroy()
            callback()
            self.sync_gui_from_cfg()

        # Botón confirmar
        confirm_btn = self.create_modern_button(
            action_frame,
            text="✅ Confirmar Selección",
            command=confirm_selection,
            style="success",
            width=20
        )
        confirm_btn.pack(side="right", padx=(10, 0))

        # Botón cancelar
        cancel_btn = self.create_modern_button(
            action_frame,
            text="❌ Cancelar",
            command=win.destroy,
            style="secondary",
            width=15
        )
        cancel_btn.pack(side="right")

        # Eventos
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
                messagebox.showerror(tr("error"), tr("select_at_least_one_unit") if "select_at_least_one_unit" in _TRANSLATIONS else "Selecciona al menos una unidad.")
                return
            config_name = getattr(self, '_last_analysis_type', 'series_config')
            selected_units = [all_units[i] for i in selected_indices]
            getattr(self.project_config, config_name)["selected_units"] = selected_units
            # Limpia selección de años al cambiar unidad en serie de tiempo
            if config_name == "series_config":
                getattr(self.project_config, config_name)["selected_years"] = []
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
                messagebox.showerror(tr("error"), tr("select_at_least_one_year") if "select_at_least_one_year" in _TRANSLATIONS else "Selecciona al menos un año.")
                return
            config_name = getattr(self, '_last_analysis_type', 'series_config')
            selected_years = [year_columns[i] for i in idxs]
            getattr(self.project_config, config_name)["selected_years"] = selected_years
            win.destroy()
            self.status.config(text=f"{tr('select_years') if 'select_years' in _TRANSLATIONS else 'Años seleccionados'}: {selected_years}")
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

    def show_loading(self, text="Procesando..."):
        """Muestra un indicador de carga moderno."""
        if hasattr(self, '_loading_window'):
            return  # Ya hay una ventana de carga
            
        self._loading_window = Toplevel(self)
        self._loading_window.title("Procesando")
        self._loading_window.geometry("300x150")
        self._loading_window.resizable(False, False)
        self._loading_window.configure(bg=getattr(self, 'bg_primary', '#ffffff'))
        
        # Centrar ventana
        self._loading_window.update_idletasks()
        x = (self._loading_window.winfo_screenwidth() // 2) - 150
        y = (self._loading_window.winfo_screenheight() // 2) - 75
        self._loading_window.geometry(f"300x150+{x}+{y}")
        
        # Contenido
        content_frame = tk.Frame(self._loading_window, bg=getattr(self, 'bg_primary', '#ffffff'))
        content_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Ícono de carga animado (simplificado)
        loading_label = tk.Label(
            content_frame,
            text="⏳",
            font=("Segoe UI", 24),
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'accent_color', '#3b82f6')
        )
        loading_label.pack()
        
        # Texto
        text_label = tk.Label(
            content_frame,
            text=text,
            font=("Segoe UI", 11),
            bg=getattr(self, 'bg_primary', '#ffffff'),
            fg=getattr(self, 'fg_primary', '#1e293b')
        )
        text_label.pack(pady=(10, 0))
        
        self._loading_window.transient(self)
        self._loading_window.grab_set()
        self._loading_window.update()

    def hide_loading(self):
        """Oculta el indicador de carga."""
        if hasattr(self, '_loading_window'):
            self._loading_window.destroy()
            delattr(self, '_loading_window')

    def update_status(self, message, type="info"):
        """Actualiza la barra de estado con colores según el tipo."""
        icons = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌",
            "loading": "⏳"
        }
        
        colors = {
            "info": getattr(self, 'accent_color', '#3b82f6'),
            "success": getattr(self, 'success_color', '#10b981'),
            "warning": getattr(self, 'warning_color', '#f59e0b'),
            "error": getattr(self, 'error_color', '#ef4444'),
            "loading": getattr(self, 'accent_color', '#3b82f6')
        }
        
        icon = icons.get(type, "ℹ️")
        color = colors.get(type, getattr(self, 'fg_primary', '#1e293b'))
        
        if hasattr(self, 'status'):
            self.status.config(text=f"{icon} {message}", fg=color)

# ------------- FIN CLASE --------------

if __name__ == "__main__":
    app = PCAApp()
    app.mainloop()
