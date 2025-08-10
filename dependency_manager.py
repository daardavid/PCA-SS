# dependency_manager.py
"""
Gestor de dependencias para manejar imports opcionales de manera robusta.
Proporciona fallbacks graceful cuando una dependencia no está disponible.
"""
import sys
import importlib
import warnings
from typing import Optional, Any, Callable


class DependencyManager:
    """Gestor centralizado de dependencias opcionales."""
    
    def __init__(self):
        self._missing_packages = set()
        self._fallbacks = {}
    
    def require_package(self, package_name: str, fallback: Optional[Any] = None, 
                       install_hint: Optional[str] = None) -> Any:
        """
        Importa un paquete requerido con fallback opcional.
        
        Args:
            package_name: Nombre del paquete a importar
            fallback: Valor/función de fallback si el paquete no está disponible
            install_hint: Sugerencia de instalación para el usuario
            
        Returns:
            El módulo importado o el fallback
            
        Raises:
            ImportError: Si el paquete es crítico y no está disponible
        """
        try:
            return importlib.import_module(package_name)
        except ImportError as e:
            if package_name not in self._missing_packages:
                self._missing_packages.add(package_name)
                hint = install_hint or f"pip install {package_name}"
                warnings.warn(
                    f"Paquete opcional '{package_name}' no disponible. "
                    f"Para instalarlo: {hint}",
                    UserWarning
                )
            
            if fallback is not None:
                return fallback
            else:
                raise ImportError(
                    f"Paquete requerido '{package_name}' no está disponible. "
                    f"Instálalo con: {install_hint or f'pip install {package_name}'}"
                ) from e
    
    def safe_import(self, package_name: str, attribute: Optional[str] = None) -> Any:
        """
        Importa un paquete de manera segura, retornando None si no está disponible.
        
        Args:
            package_name: Nombre del paquete
            attribute: Atributo específico del paquete a importar
            
        Returns:
            El módulo/atributo o None si no está disponible
        """
        try:
            module = importlib.import_module(package_name)
            if attribute:
                return getattr(module, attribute)
            return module
        except (ImportError, AttributeError):
            return None
    
    def register_fallback(self, package_name: str, fallback_func: Callable):
        """Registra una función de fallback para un paquete específico."""
        self._fallbacks[package_name] = fallback_func
    
    def get_missing_packages(self) -> set:
        """Retorna el conjunto de paquetes faltantes detectados."""
        return self._missing_packages.copy()
    
    def check_all_dependencies(self) -> dict:
        """
        Verifica todas las dependencias principales y retorna un reporte.
        
        Returns:
            Dict con el estado de cada dependencia
        """
        dependencies = {
            'pandas': 'Requerido para análisis de datos',
            'numpy': 'Requerido para cálculos numéricos',
            'sklearn': 'Requerido para PCA',
            'matplotlib': 'Requerido para visualizaciones',
            'adjustText': 'Opcional para mejorar etiquetas en gráficos',
            'openpyxl': 'Requerido para archivos Excel',
            'tkinter': 'Requerido para GUI (incluido en Python estándar)'
        }
        
        status = {}
        for package, description in dependencies.items():
            try:
                if package == 'sklearn':
                    importlib.import_module('sklearn')
                elif package == 'tkinter':
                    importlib.import_module('tkinter')
                else:
                    importlib.import_module(package)
                status[package] = {'available': True, 'description': description}
            except ImportError:
                status[package] = {'available': False, 'description': description}
        
        return status


# Instancia global del gestor de dependencias
dep_manager = DependencyManager()

# Funciones de conveniencia
def require(package_name: str, fallback: Any = None, install_hint: str = None) -> Any:
    """Función de conveniencia para requerir un paquete."""
    return dep_manager.require_package(package_name, fallback, install_hint)

def safe_import(package_name: str, attribute: str = None) -> Any:
    """Función de conveniencia para importación segura."""
    return dep_manager.safe_import(package_name, attribute)


# Configuración de fallbacks comunes
def _adjusttext_fallback(*args, **kwargs):
    """Fallback silencioso para adjustText cuando no está disponible."""
    pass

dep_manager.register_fallback('adjustText', _adjusttext_fallback)


if __name__ == "__main__":
    # Script para verificar dependencias
    print("=== Verificación de Dependencias PCA-SS ===\n")
    
    status = dep_manager.check_all_dependencies()
    
    print("Estado de dependencias:")
    for package, info in status.items():
        symbol = "✓" if info['available'] else "✗"
        print(f"{symbol} {package}: {info['description']}")
    
    missing = [pkg for pkg, info in status.items() if not info['available']]
    if missing:
        print(f"\n⚠️  Paquetes faltantes: {', '.join(missing)}")
        print("Para instalar todas las dependencias:")
        print("pip install -r requirements.txt")
    else:
        print("\n✅ Todas las dependencias están disponibles!")
