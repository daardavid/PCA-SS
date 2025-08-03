"""
Módulo de lógica para el análisis PCA y procesamiento de datos.
Separa la lógica de negocio de la GUI.
"""
import pandas as pd
import numpy as np
import data_loader_module as dl
import preprocessing_module as dl_prep
import pca_module as pca_mod
from constants import MAPEO_INDICADORES

class PCAAnalysisLogic:
    @staticmethod
    def run_series_analysis_logic(cfg, imputation_strategy=None, imputation_params=None):
        """
        Ejecuta el flujo de análisis de serie de tiempo (sin GUI).
        Retorna un diccionario con todos los resultados intermedios y finales.
        """
        all_sheets_data = dl.load_excel_file(cfg["data_file"])
        selected_indicators = cfg["selected_indicators"]
        selected_unit = cfg["selected_units"][0]

        # 2. Transformar cada hoja
        data_transformada = {}
        for ind in selected_indicators:
            df = all_sheets_data[ind]
            df_trans = dl.transformar_df_indicador_v1(df)
            if df_trans is not None and not df_trans.empty:
                data_transformada[ind] = df_trans

        # 3. Consolidar los datos para el país elegido
        df_consolidado = dl.consolidate_data_for_country(
            data_transformada,
            selected_unit,
            selected_indicators
        )
        if df_consolidado is None or df_consolidado.empty:
            return {"error": "No se pudieron consolidar los datos para el país seleccionado."}

        ncols = df_consolidado.shape[1]
        if ncols == 1:
            return {"warning": "Solo seleccionaste un indicador. El PCA no es informativo con un solo indicador."}

        # Imputación de datos faltantes
        df_imputado = df_consolidado.copy()
        mascara_imputados = pd.DataFrame(False, index=df_imputado.index, columns=df_imputado.columns)
        if imputation_strategy and imputation_strategy != 'ninguna':
            df_imputado, mascara_imputados = dl_prep.manejar_datos_faltantes(
                df_consolidado,
                estrategia=imputation_strategy,
                devolver_mascara=True,
                **(imputation_params or {})
            )

        df_para_scaler = df_imputado.dropna(axis=0, how='any') if df_imputado.isnull().sum().sum() > 0 else df_imputado
        if df_para_scaler.empty:
            return {"error": "No se puede estandarizar. DataFrame vacío tras imputación."}

        df_estandarizado, scaler = dl_prep.estandarizar_datos(df_para_scaler, devolver_scaler=True)
        df_covarianza = df_estandarizado.cov()

        # --- PCA sólo si hay más de una columna ---
        df_varianza_explicada = None
        df_componentes = None
        pca_model_final = None
        if df_estandarizado.shape[1] > 1:
            pca_model, _ = pca_mod.realizar_pca(df_estandarizado, n_components=None)
            evr, cum_evr = pca_mod.obtener_varianza_explicada(pca_model)
            sugg_90 = np.where(cum_evr >= 0.90)[0]
            sugg_95 = np.where(cum_evr >= 0.95)[0]
            n_sugg_90 = sugg_90[0] + 1 if len(sugg_90) > 0 else None
            n_sugg_95 = sugg_95[0] + 1 if len(sugg_95) > 0 else None
            df_varianza_explicada = pd.DataFrame({
                'Componente': [f'PC{i+1}' for i in range(len(evr))],
                'Varianza Explicada': evr,
                'Varianza Acumulada': cum_evr
            }).set_index('Componente')
            # El número de componentes a usar debe ser pasado por la GUI
            # Aquí solo devolvemos sugerencias
        else:
            pca_model_final, df_componentes = None, None

        # Prepara resultados
        results = {
            "df_consolidado": df_consolidado,
            "df_imputado": df_imputado,
            "mascara_imputados": mascara_imputados,
            "df_estandarizado": df_estandarizado,
            "scaler": scaler,
            "df_covarianza": df_covarianza,
            "pca_sugerencias": {
                "n_sugg_90": n_sugg_90 if df_estandarizado.shape[1] > 1 else None,
                "n_sugg_95": n_sugg_95 if df_estandarizado.shape[1] > 1 else None,
                "evr": evr if df_estandarizado.shape[1] > 1 else None,
                "cum_evr": cum_evr if df_estandarizado.shape[1] > 1 else None,
                "df_varianza_explicada": df_varianza_explicada
            },
            # El PCA final y componentes se calculan aparte, según la selección del usuario
        }
        return results

    @staticmethod
    def run_pca_final(df_estandarizado, n_componentes):
        pca_model_final, df_componentes = pca_mod.realizar_pca(df_estandarizado, n_components=n_componentes)
        return pca_model_final, df_componentes
