#!/usr/bin/env python3
# check_dependencies.py
"""
Script de verificación de dependencias para PCA-SS.

Este script verifica que todas las dependencias necesarias estén instaladas
y proporciona instrucciones claras para resolver cualquier problema.
"""

import sys
import importlib
from typing import Dict, List, Tuple


def check_python_version() -> bool:
    """Verifica que la versión de Python sea compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detectado.")
        print("⚠️  Se requiere Python 3.8 o superior.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True


def check_dependencies() -> Tuple[List[str], List[str]]:
    """
    Verifica todas las dependencias del proyecto.
    
    Returns:
        Tuple con listas de dependencias disponibles y faltantes
    """
    # Dependencias críticas (la aplicación no funciona sin estas)
    critical_deps = {
        'pandas': 'Manejo y análisis de datos',
        'numpy': 'Computación numérica',
        'sklearn': 'Algoritmos de machine learning (PCA)',
        'matplotlib': 'Generación de gráficos',
        'openpyxl': 'Lectura/escritura de archivos Excel',
        'tkinter': 'Interfaz gráfica (incluido en Python estándar)'
    }
    
    # Dependencias opcionales (mejoran la experiencia pero no son críticas)
    optional_deps = {
        'adjustText': 'Mejora automática de posicionamiento de etiquetas en gráficos'
    }
    
    available = []
    missing_critical = []
    missing_optional = []
    
    print("=== Verificando Dependencias Críticas ===")
    for package, description in critical_deps.items():
        try:
            if package == 'sklearn':
                importlib.import_module('sklearn')
            elif package == 'tkinter':
                importlib.import_module('tkinter')
            else:
                importlib.import_module(package)
            
            print(f"✅ {package} - {description}")
            available.append(package)
            
        except ImportError:
            print(f"❌ {package} - {description}")
            missing_critical.append(package)
    
    print("\n=== Verificando Dependencias Opcionales ===")
    for package, description in optional_deps.items():
        try:
            importlib.import_module(package)
            print(f"✅ {package} - {description}")
            available.append(package)
        except ImportError:
            print(f"⚠️  {package} - {description} (opcional)")
            missing_optional.append(package)
    
    return available, missing_critical, missing_optional


def generate_install_commands(missing_critical: List[str], missing_optional: List[str]) -> None:
    """Genera comandos de instalación para dependencias faltantes."""
    
    if missing_critical:
        print("\n🔧 DEPENDENCIAS CRÍTICAS FALTANTES:")
        print("Para instalar las dependencias críticas:")
        print(f"pip install {' '.join(missing_critical)}")
        print("\nO instala todas las dependencias de una vez:")
        print("pip install -r requirements.txt")
    
    if missing_optional:
        print("\n🔧 DEPENDENCIAS OPCIONALES FALTANTES:")
        print("Para mejorar la experiencia (opcional):")
        print(f"pip install {' '.join(missing_optional)}")


def check_file_structure() -> bool:
    """Verifica que los archivos principales del proyecto estén presentes."""
    import os
    
    required_files = [
        'pca_gui.py',
        'data_loader_module.py',
        'preprocessing_module.py',
        'pca_module.py',
        'visualization_module.py',
        'constants.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Archivos faltantes: {', '.join(missing_files)}")
        return False
    
    print("\n✅ Estructura de archivos correcta")
    return True


def main():
    """Función principal del script de verificación."""
    print("🔍 PCA-SS - Verificador de Dependencias")
    print("=" * 50)
    
    # Verificar versión de Python
    python_ok = check_python_version()
    
    # Verificar dependencias
    available, missing_critical, missing_optional = check_dependencies()
    
    # Verificar estructura de archivos
    files_ok = check_file_structure()
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN:")
    
    if python_ok and not missing_critical and files_ok:
        print("🎉 ¡Todo listo! La aplicación debería funcionar correctamente.")
        if missing_optional:
            print(f"💡 Tip: Instala las dependencias opcionales para una mejor experiencia.")
    else:
        print("⚠️  Se encontraron problemas que deben resolverse:")
        
        if not python_ok:
            print("   - Actualiza Python a versión 3.8 o superior")
        
        if missing_critical:
            print(f"   - Instala dependencias críticas: {', '.join(missing_critical)}")
        
        if not files_ok:
            print("   - Verifica que todos los archivos del proyecto estén presentes")
    
    # Generar comandos de instalación si es necesario
    if missing_critical or missing_optional:
        generate_install_commands(missing_critical, missing_optional)
    
    print("\n📖 Para más información, consulta el archivo README.md")
    
    # Código de salida
    return 0 if (python_ok and not missing_critical and files_ok) else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
