# data_validation.py
"""
Sistema de validación de datos para análisis PCA.

Proporciona validadores robustos para diferentes tipos de datos de entrada,
con mensajes de error descriptivos y sugerencias de corrección.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import warnings
from logging_config import get_logger

logger = get_logger("data_validation")


class ValidationError(Exception):
    """Excepción específica para errores de validación de datos."""
    pass


class DataValidator:
    """Validador centralizado para diferentes tipos de datos."""
    
    def __init__(self, strict_mode: bool = False):
        """
        Inicializa el validador.
        
        Args:
            strict_mode: Si True, lanza excepciones en lugar de warnings
        """
        self.strict_mode = strict_mode
        self.validation_results = []
    
    def _log_issue(self, level: str, message: str, suggestion: str = None):
        """Registra un problema de validación."""
        full_message = message
        if suggestion:
            full_message += f" Sugerencia: {suggestion}"
        
        issue = {
            'level': level,
            'message': message,
            'suggestion': suggestion
        }
        self.validation_results.append(issue)
        
        if level == 'error':
            logger.error(full_message)
            if self.strict_mode:
                raise ValidationError(full_message)
        elif level == 'warning':
            logger.warning(full_message)
            if not self.strict_mode:
                warnings.warn(full_message, UserWarning)
        else:
            logger.info(full_message)
    
    def validate_dataframe_structure(
        self, 
        df: pd.DataFrame, 
        name: str = "DataFrame",
        required_columns: Optional[List[str]] = None,
        min_rows: int = 1,
        min_cols: int = 1
    ) -> bool:
        """
        Valida la estructura básica de un DataFrame.
        
        Args:
            df: DataFrame a validar
            name: Nombre descriptivo para mensajes de error
            required_columns: Lista de columnas que deben estar presentes
            min_rows: Número mínimo de filas requeridas
            min_cols: Número mínimo de columnas requeridas
            
        Returns:
            True si la validación es exitosa
        """
        logger.debug(f"Validating structure of {name}")
        
        # Verificar que sea un DataFrame
        if not isinstance(df, pd.DataFrame):
            self._log_issue('error', f"{name} debe ser un pandas DataFrame, recibido: {type(df)}")
            return False
        
        # Verificar que no esté vacío
        if df.empty:
            self._log_issue('error', f"{name} está vacío", "Proporciona un archivo con datos válidos")
            return False
        
        # Verificar dimensiones mínimas
        if df.shape[0] < min_rows:
            self._log_issue('error', 
                          f"{name} tiene {df.shape[0]} filas, se requieren al menos {min_rows}",
                          "Agrega más observaciones al dataset")
            return False
        
        if df.shape[1] < min_cols:
            self._log_issue('error',
                          f"{name} tiene {df.shape[1]} columnas, se requieren al menos {min_cols}",
                          "Agrega más variables al dataset")
            return False
        
        # Verificar columnas requeridas
        if required_columns:
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                self._log_issue('error',
                              f"{name} le faltan columnas requeridas: {missing_cols}",
                              f"Verifica que el archivo contenga las columnas: {required_columns}")
                return False
        
        logger.info(f"{name} structure validation passed: {df.shape}")
        return True
    
    def validate_numeric_data(
        self, 
        df: pd.DataFrame, 
        name: str = "DataFrame",
        allow_missing: bool = True,
        max_missing_ratio: float = 0.5
    ) -> bool:
        """
        Valida que los datos sean apropiados para análisis numérico.
        
        Args:
            df: DataFrame a validar
            name: Nombre descriptivo
            allow_missing: Si se permiten valores faltantes
            max_missing_ratio: Ratio máximo de valores faltantes permitido
            
        Returns:
            True si la validación es exitosa
        """
        logger.debug(f"Validating numeric data in {name}")
        
        # Verificar tipos de datos
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
        
        if len(numeric_cols) == 0:
            self._log_issue('error',
                          f"{name} no contiene columnas numéricas",
                          "Convierte las columnas a tipos numéricos o usa un dataset diferente")
            return False
        
        if len(non_numeric_cols) > 0:
            self._log_issue('warning',
                          f"{name} contiene columnas no numéricas que serán ignoradas: {list(non_numeric_cols)}",
                          "Considera convertir estas columnas a numéricas si contienen datos relevantes")
        
        # Verificar valores faltantes
        if not allow_missing:
            missing_count = df.isnull().sum().sum()
            if missing_count > 0:
                self._log_issue('error',
                              f"{name} contiene {missing_count} valores faltantes y no se permiten",
                              "Remueve o imputa los valores faltantes antes del análisis")
                return False
        else:
            # Verificar ratio de valores faltantes
            total_values = df.size
            missing_values = df.isnull().sum().sum()
            missing_ratio = missing_values / total_values
            
            if missing_ratio > max_missing_ratio:
                self._log_issue('error',
                              f"{name} tiene {missing_ratio:.2%} de valores faltantes, máximo permitido: {max_missing_ratio:.2%}",
                              "Considera usar un dataset con menos valores faltantes o ajustar la tolerancia")
                return False
            elif missing_ratio > 0.1:  # 10%
                self._log_issue('warning',
                              f"{name} tiene {missing_ratio:.2%} de valores faltantes",
                              "Considera aplicar técnicas de imputación antes del análisis")
        
        logger.info(f"{name} numeric validation passed: {len(numeric_cols)} numeric columns")
        return True
    
    def validate_pca_requirements(
        self, 
        df: pd.DataFrame, 
        name: str = "DataFrame"
    ) -> bool:
        """
        Valida que los datos cumplan los requisitos específicos para PCA.
        
        Args:
            df: DataFrame a validar
            name: Nombre descriptivo
            
        Returns:
            True si la validación es exitosa
        """
        logger.debug(f"Validating PCA requirements for {name}")
        
        # Obtener solo columnas numéricas
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            self._log_issue('error', f"{name} no tiene datos numéricos para PCA")
            return False
        
        # Verificar dimensiones mínimas para PCA
        n_samples, n_features = numeric_df.shape
        
        if n_features < 2:
            self._log_issue('error',
                          f"PCA requiere al menos 2 variables, {name} tiene {n_features}",
                          "Agrega más variables al análisis")
            return False
        
        if n_samples < 3:
            self._log_issue('error',
                          f"PCA requiere al menos 3 observaciones, {name} tiene {n_samples}",
                          "Agrega más observaciones al dataset")
            return False
        
        # Verificar que haya variabilidad en los datos
        constant_cols = []
        for col in numeric_df.columns:
            if numeric_df[col].nunique() <= 1:
                constant_cols.append(col)
        
        if constant_cols:
            self._log_issue('warning',
                          f"Columnas con valores constantes detectadas en {name}: {constant_cols}",
                          "Estas columnas no contribuirán al análisis PCA")
        
        # Verificar correlaciones extremas
        try:
            corr_matrix = numeric_df.corr()
            high_corr_pairs = []
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = abs(corr_matrix.iloc[i, j])
                    if corr_val > 0.95 and not np.isnan(corr_val):
                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
            
            if high_corr_pairs:
                self._log_issue('warning',
                              f"Correlaciones muy altas detectadas en {name}: {high_corr_pairs[:3]}",
                              "Considera remover variables redundantes")
        except Exception as e:
            logger.warning(f"No se pudo calcular matriz de correlación: {e}")
        
        logger.info(f"{name} PCA validation passed: {n_samples} samples, {n_features} features")
        return True
    
    def validate_file_path(self, file_path: Union[str, Path], expected_extensions: List[str] = None) -> bool:
        """
        Valida que un archivo exista y tenga la extensión correcta.
        
        Args:
            file_path: Ruta del archivo
            expected_extensions: Lista de extensiones válidas (ej. ['.xlsx', '.csv'])
            
        Returns:
            True si la validación es exitosa
        """
        path = Path(file_path)
        
        if not path.exists():
            self._log_issue('error',
                          f"Archivo no encontrado: {file_path}",
                          "Verifica que la ruta sea correcta y el archivo exista")
            return False
        
        if not path.is_file():
            self._log_issue('error',
                          f"La ruta no corresponde a un archivo: {file_path}",
                          "Proporciona la ruta a un archivo, no a un directorio")
            return False
        
        if expected_extensions:
            if path.suffix.lower() not in [ext.lower() for ext in expected_extensions]:
                self._log_issue('error',
                              f"Extensión de archivo no válida: {path.suffix}. Esperadas: {expected_extensions}",
                              f"Usa un archivo con una de estas extensiones: {expected_extensions}")
                return False
        
        logger.info(f"File validation passed: {file_path}")
        return True
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Retorna un resumen de todos los problemas de validación encontrados."""
        summary = {
            'total_issues': len(self.validation_results),
            'errors': [r for r in self.validation_results if r['level'] == 'error'],
            'warnings': [r for r in self.validation_results if r['level'] == 'warning'],
            'info': [r for r in self.validation_results if r['level'] == 'info']
        }
        
        summary['error_count'] = len(summary['errors'])
        summary['warning_count'] = len(summary['warnings'])
        summary['info_count'] = len(summary['info'])
        
        return summary
    
    def clear_results(self):
        """Limpia los resultados de validación acumulados."""
        self.validation_results.clear()


# Funciones de conveniencia
def validate_dataframe_for_pca(df: pd.DataFrame, name: str = "DataFrame") -> Tuple[bool, Dict]:
    """
    Función de conveniencia para validar un DataFrame completo para análisis PCA.
    
    Returns:
        Tuple de (éxito, resumen de validación)
    """
    validator = DataValidator()
    
    # Ejecutar todas las validaciones relevantes
    structure_ok = validator.validate_dataframe_structure(df, name, min_rows=3, min_cols=2)
    numeric_ok = validator.validate_numeric_data(df, name)
    pca_ok = validator.validate_pca_requirements(df, name)
    
    overall_success = structure_ok and numeric_ok and pca_ok
    summary = validator.get_validation_summary()
    
    return overall_success, summary


if __name__ == "__main__":
    # Test del sistema de validación
    print("Testing data validation system...")
    
    # Crear datos de prueba
    test_data = pd.DataFrame({
        'var1': [1, 2, 3, 4, 5],
        'var2': [2, 4, 6, 8, 10],
        'var3': ['a', 'b', 'c', 'd', 'e'],  # No numérica
        'var4': [1, 1, 1, 1, 1]  # Constante
    })
    
    success, summary = validate_dataframe_for_pca(test_data, "test_data")
    
    print(f"Validation success: {success}")
    print(f"Summary: {summary}")
