# project_save_config.py
import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict

@dataclass
class ProjectConfig:
    # ─── Atributos básicos ────────────────────────────────────────────────
    project_name:        str                      = ""
    data_file:           str                      = ""
    selected_indicators: List[str]                = field(default_factory=list)
    selected_units:      List[str]                = field(default_factory=list)
    selected_years:      List[int]                = field(default_factory=list)

    # personalizaciones de gráfica
    color_groups:  Dict[str, str] = field(default_factory=dict)
    group_labels:  Dict[str, str] = field(default_factory=dict)
    custom_titles: Dict[str, str] = field(default_factory=lambda: {
        "biplot": "",
        "legend": "Grupos de Países",
        "footer": ""
    })

    # resultados intermedios (se guardará lo que quieras)
    analysis_results: Dict[str, str] = field(default_factory=dict)

    # ─── Serialización ───────────────────────────────────────────────────
    def to_dict(self) -> dict:
        """Devuelve la configuración como dict listo para guardar en JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        """Crea un ProjectConfig a partir de un dict (por ejemplo, cargado de JSON)."""
        return cls(**data)

    # ---------- Métodos que necesita la GUI ----------
    def save_to_file(self, filepath: str):
        """Guarda el proyecto en un archivo .json."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ProjectConfig":
        """Carga un proyecto desde un archivo .json."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    footer_note: str = ""  # leyenda / fuente opcional
