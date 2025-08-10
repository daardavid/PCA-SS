# example_usage.py
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
