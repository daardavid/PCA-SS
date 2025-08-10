# test_pca_integration.py
"""
Script de prueba para verificar que la integración del módulo PCA funciona correctamente.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Asegurar que el directorio actual esté en el path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_pca_integration():
    """Prueba la integración del módulo PCA con los nuevos sistemas."""
    print("🧪 Probando integración del módulo PCA...")
    
    try:
        # Importar módulos necesarios
        from pca_module import realizar_pca
        from data_validation import validate_dataframe_for_pca
        from config_manager import get_config
        
        print("✅ Importaciones exitosas")
        
        # Crear datos de prueba
        np.random.seed(42)
        data = {
            'Variable1': np.random.normal(0, 1, 50),
            'Variable2': np.random.normal(0, 1, 50),
            'Variable3': np.random.normal(0, 1, 50),
            'Variable4': np.random.normal(0, 1, 50)
        }
        
        df_test = pd.DataFrame(data, index=[f"Obs_{i+1}" for i in range(50)])
        print(f"✅ DataFrame de prueba creado: {df_test.shape}")
        
        # Estandarizar datos (PCA espera datos estandarizados)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        df_estandarizado = pd.DataFrame(
            scaler.fit_transform(df_test),
            columns=df_test.columns,
            index=df_test.index
        )
        print("✅ Datos estandarizados")
        
        # Probar validación
        is_valid, validation_info = validate_dataframe_for_pca(df_estandarizado)
        if is_valid:
            print("✅ Validación de datos exitosa")
        else:
            print(f"❌ Validación falló: {validation_info}")
            return False
        
        # Probar configuración
        config = get_config()
        print(f"✅ Configuración cargada: n_components={config.pca.default_n_components}")
        
        # Ejecutar PCA
        pca_model, df_components = realizar_pca(df_estandarizado, n_components=2)
        
        if pca_model is not None and df_components is not None:
            print(f"✅ PCA ejecutado exitosamente:")
            print(f"   - Componentes generados: {df_components.shape[1]}")
            print(f"   - Varianza explicada: {pca_model.explained_variance_ratio_}")
            print(f"   - Varianza acumulada: {pca_model.explained_variance_ratio_.cumsum()}")
            return True
        else:
            print("❌ PCA falló - retornó None")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_system():
    """Prueba el sistema de rendimiento."""
    try:
        from performance_optimizer import get_performance_report, cached, profiled
        
        # Función de prueba con cache
        @cached
        def expensive_function(x):
            return x ** 2
        
        # Función de prueba con profiling
        @profiled
        def profiled_function():
            import time
            time.sleep(0.01)  # Simular trabajo
            return "done"
        
        # Ejecutar funciones
        result1 = expensive_function(5)  # Cache miss
        result2 = expensive_function(5)  # Cache hit
        
        result3 = profiled_function()
        
        # Obtener reporte
        report = get_performance_report()
        print("✅ Sistema de rendimiento funcionando")
        print(f"   - Cache funcionando: {result1 == result2}")
        print(f"   - Profiling funcionando: {result3 == 'done'}")
        return True
        
    except Exception as e:
        print(f"❌ Error en sistema de rendimiento: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("=" * 60)
    print("    PRUEBA DE INTEGRACIÓN - MÓDULOS PCA")
    print("=" * 60)
    
    # Configurar logging
    try:
        from logging_config import setup_application_logging, get_logger
        setup_application_logging(debug_mode=False)
        logger = get_logger("test")
        logger.info("Iniciando pruebas de integración")
        print("✅ Sistema de logging configurado")
    except Exception as e:
        print(f"⚠️  Warning: Sistema de logging no disponible: {e}")
    
    success = True
    
    # Probar PCA
    print("\n1️⃣  Probando módulo PCA...")
    if not test_pca_integration():
        success = False
    
    # Probar sistema de rendimiento
    print("\n2️⃣  Probando sistema de rendimiento...")
    if not test_performance_system():
        success = False
    
    # Resultado final
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("✅ La integración está funcionando correctamente")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("⚠️  Revisa los errores arriba")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
