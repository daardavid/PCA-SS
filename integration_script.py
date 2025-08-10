# integration_script.py
"""
Script de integración para actualizar todos los módulos con los nuevos sistemas.

Este script facilita la integración de:
- Sistema de logging
- Validación de datos  
- Optimización de rendimiento
- Gestión de configuración

Ejecutar este script una vez para actualizar toda la aplicación.
"""

import sys
from pathlib import Path

# Asegurar que el directorio actual esté en el path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_systems():
    """Inicializa todos los sistemas mejorados."""
    print("🚀 Iniciando configuración de sistemas mejorados...")
    
    # 1. Configurar logging
    try:
        from logging_config import setup_application_logging, get_logger
        setup_application_logging(debug_mode=False)
        logger = get_logger("integration")
        logger.info("Sistema de logging configurado correctamente")
        print("✅ Sistema de logging: OK")
    except Exception as e:
        print(f"❌ Error configurando logging: {e}")
        return False
    
    # 2. Configurar gestión de configuración
    try:
        from config_manager import ConfigManager, get_config
        config_manager = ConfigManager()
        config_manager.create_default_yaml_config()
        config = get_config()
        logger.info(f"Configuración cargada: theme={config.ui.theme}, language={config.ui.language}")
        print("✅ Sistema de configuración: OK")
    except Exception as e:
        print(f"❌ Error configurando gestión de configuración: {e}")
        logger.error(f"Error en configuración: {e}")
        return False
    
    # 3. Verificar sistema de validación
    try:
        from data_validation import DataValidator
        validator = DataValidator()
        print("✅ Sistema de validación: OK")
        logger.info("Sistema de validación inicializado")
    except Exception as e:
        print(f"❌ Error verificando validación: {e}")
        logger.error(f"Error en validación: {e}")
        return False
    
    # 4. Verificar optimización de rendimiento
    try:
        from performance_optimizer import get_performance_report
        report = get_performance_report()
        print("✅ Sistema de optimización: OK")
        logger.info("Sistema de optimización inicializado")
    except Exception as e:
        print(f"❌ Error verificando optimización: {e}")
        logger.error(f"Error en optimización: {e}")
        return False
    
    # 5. Verificar dependencias
    try:
        from check_dependencies import main as check_deps
        missing = check_deps()
        if missing:
            print(f"⚠️  Dependencias faltantes: {missing}")
            logger.warning(f"Dependencias faltantes: {missing}")
        else:
            print("✅ Todas las dependencias: OK")
            logger.info("Todas las dependencias verificadas")
    except Exception as e:
        print(f"❌ Error verificando dependencias: {e}")
        logger.error(f"Error verificando dependencias: {e}")
        return False
    
    return True

def create_example_usage():
    """Crea un archivo de ejemplo de uso de los nuevos sistemas."""
    example_code = '''# example_usage.py
"""
Ejemplo de uso de los sistemas mejorados en la aplicación PCA.
"""

# Importaciones de los nuevos sistemas
from logging_config import get_logger
from config_manager import get_config, update_config
from data_validation import DataValidator
from performance_optimizer import cached, profiled, optimize_memory

# Configurar logger
logger = get_logger("example")

# Ejemplo de función optimizada
@profiled
@cached
def example_analysis(data):
    """Función de ejemplo con cache y profiling."""
    logger.info("Ejecutando análisis de ejemplo")
    
    # Obtener configuración
    config = get_config()
    logger.info(f"Usando configuración: {config.pca.default_n_components} componentes")
    
    # Validar datos
    validator = DataValidator()
    try:
        validator.validate_dataframe_for_pca(data)
        logger.info("Datos validados correctamente")
    except Exception as e:
        logger.error(f"Error de validación: {e}")
        return None
    
    # Optimizar memoria
    data_optimized = optimize_memory(data)
    logger.info(f"Memoria optimizada: {data.memory_usage().sum()} -> {data_optimized.memory_usage().sum()}")
    
    return data_optimized

# Ejemplo de actualización de configuración
def update_app_config():
    """Actualiza configuración de la aplicación."""
    logger.info("Actualizando configuración")
    
    # Cambiar tema y idioma
    update_config('ui', theme='dark', language='en')
    
    # Cambiar configuración de PCA
    update_config('pca', default_n_components=5, random_state=123)
    
    logger.info("Configuración actualizada")

if __name__ == "__main__":
    # Ejemplo de uso
    import pandas as pd
    
    # Crear datos de ejemplo
    data = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': [2, 4, 6, 8, 10],
        'feature3': [1, 3, 5, 7, 9]
    })
    
    # Usar función optimizada
    result = example_analysis(data)
    print("Análisis completado")
    
    # Actualizar configuración
    update_app_config()
    print("Configuración actualizada")
'''
    
    with open(current_dir / "example_usage.py", "w", encoding="utf-8") as f:
        f.write(example_code)
    
    print("📝 Archivo de ejemplo creado: example_usage.py")

def verify_integration():
    """Verifica que la integración funcione correctamente."""
    print("\n🔍 Verificando integración...")
    
    try:
        # Test de importaciones cruzadas
        from pca_module import realizar_pca
        from data_loader_module import cargar_datos_excel
        from preprocessing_module import aplicar_imputacion
        
        print("✅ Módulos principales: OK")
        
        # Test de configuración
        from config_manager import get_config
        config = get_config()
        assert hasattr(config, 'pca')
        assert hasattr(config, 'ui')
        assert hasattr(config, 'performance')
        print("✅ Configuración: OK")
        
        # Test de logging
        from logging_config import get_logger
        logger = get_logger("test")
        logger.info("Test de logging")
        print("✅ Logging: OK")
        
        # Test de validación
        from data_validation import DataValidator
        validator = DataValidator()
        print("✅ Validación: OK")
        
        # Test de rendimiento
        from performance_optimizer import get_performance_report
        report = get_performance_report()
        print("✅ Optimización: OK")
        
        print("\n🎉 ¡Integración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en verificación: {e}")
        return False

def main():
    """Función principal del script de integración."""
    print("="*60)
    print("     SCRIPT DE INTEGRACIÓN - APLICACIÓN PCA")
    print("="*60)
    
    # Configurar sistemas
    if not setup_systems():
        print("\n❌ Error en la configuración inicial")
        return False
    
    # Crear ejemplo de uso
    create_example_usage()
    
    # Verificar integración
    if not verify_integration():
        print("\n❌ Error en la verificación")
        return False
    
    print("\n" + "="*60)
    print("✅ INTEGRACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar 'python check_dependencies.py' para verificar dependencias")
    print("2. Revisar 'example_usage.py' para ejemplos de uso")
    print("3. Personalizar 'config/app_config.yaml' según necesidades")
    print("4. Ejecutar la aplicación principal con 'python main.py'")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
