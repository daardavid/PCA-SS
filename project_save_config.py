# project_save_config.py
import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict

@dataclass

class ProjectConfig:
    project_name: str = ""
    # Cada análisis tiene su propia configuración
    series_config: dict = field(default_factory=lambda: {
        "data_file": "",
        "selected_indicators": [],
        "selected_units": [],
        "selected_years": [],
        "color_groups": {},
        "group_labels": {},
        "custom_titles": {"biplot": "", "legend": "Grupos de Países", "footer": ""},
        "analysis_results": {},
        "footer_note": ""
    })
    cross_section_config: dict = field(default_factory=lambda: {
        "data_file": "",
        "selected_indicators": [],
        "selected_units": [],
        "selected_years": [],
        "color_groups": {},
        "group_labels": {},
        "custom_titles": {"biplot": "", "legend": "Grupos de Países", "footer": ""},
        "analysis_results": {},
        "footer_note": ""
    })
    panel_config: dict = field(default_factory=lambda: {
        "data_file": "",
        "selected_indicators": [],
        "selected_units": [],
        "selected_years": [],
        "color_groups": {},
        "group_labels": {},
        "custom_titles": {"biplot": "", "legend": "Grupos de Países", "footer": ""},
        "analysis_results": {},
        "footer_note": ""
    })

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "series_config": self.series_config,
            "cross_section_config": self.cross_section_config,
            "panel_config": self.panel_config
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        obj = cls()
        obj.project_name = data.get("project_name", "")
        obj.series_config = data.get("series_config", obj.series_config)
        obj.cross_section_config = data.get("cross_section_config", obj.cross_section_config)
        obj.panel_config = data.get("panel_config", obj.panel_config)
        return obj

    def save_to_file(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ProjectConfig":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
