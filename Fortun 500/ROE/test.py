import pandas as pd, numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import roc_auc_score, accuracy_score
from scipy.stats.mstats import winsorize

FILE = "panel_empresas_ROE.xlsx"
df   = pd.read_excel(FILE, sheet_name="Panel")

# ----------------  mapeo supplier ----------------
supplier_map = {
    "BMW Group": 0,  "Continental": 1, "Denso": 1,      "Ford Motor": 0,
    "General Motors": 0, "Hitachi": 1,  "Honeywell International": 1,
    "Kia": 0,  "LG Electronics": 1,  "Nissan Motor": 0,
    "Panasonic Holdings": 1, "Samsung Electronics": 1, "Sony": 1,
    "BYD": 0, "Tesla": 0, "Volkswagen": 0, "Volvo": 0, "Geely": 0,
    "Hon Hai": 1, "Toyota Motor": 0,
    "Magna International": 1, "Valeo": 1, "Aptiv": 1,
    "Qualcomm": 1, "Baidu": 1, "Texas Instruments": 1
}

df["supplier_dummy"] = df["Empresa"].map(supplier_map)

# (opcional) descartar firmas con pocos años
df = df[~df["Empresa"].isin(["Valeo", "Aptiv"])]

# ----------------  ROE y bandera ------------------
df["ROE_w"] = winsorize(df["ROE"], limits=[0.01,0.01])
df["roe_mediana_año"] = df.groupby("Año")["ROE_w"].transform("median")
df["rentable"] = (df["ROE_w"] > df["roe_mediana_año"]).astype(int)

# ----------------  lags t‑1 -----------------------
base_cols = [c for c in df.columns
             if c not in ["Empresa","Año","rentable","roe_mediana_año"]]
lags = (df.sort_values(["Empresa","Año"])
          .groupby("Empresa")[base_cols]
          .shift(1)
          .add_suffix("_lag1"))
df = pd.concat([df, lags], axis=1).dropna()

# ----------------  solo numéricas -----------------
num_feats = df.select_dtypes(include="number").columns.drop("rentable")

# partición temporal  (test más amplio)
train = df[df["Año"].between(2011, 2016)]
valid = df[df["Año"].isin([2017, 2019])]
test  = df[df["Año"].isin([2020, 2021, 2022])]

X_train, y_train = train[num_feats], train["rentable"]
X_valid, y_valid = valid[num_feats], valid["rentable"]
X_test,  y_test  = test[num_feats],  test["rentable"]

# ----------------  Random Forest ------------------
rf = RandomForestClassifier(class_weight="balanced", random_state=42)
param_grid = {
    "n_estimators":[300,600],
    "max_depth":[4,6,8],
    "min_samples_leaf":[1,3]
}
gcv = GridSearchCV(
        rf, param_grid,
        cv=TimeSeriesSplit(n_splits=3),   # pliegues más gruesos
        scoring="roc_auc",
        error_score="raise",
        n_jobs=-1
     ).fit(X_train, y_train)

best_rf = gcv.best_estimator_

# ---------- helper para AUC ----------
def safe_auc(y_true, proba):
    if len(np.unique(y_true)) < 2:
        return None
    return roc_auc_score(y_true, proba)

# ----------------  métricas final -----------------
# ------------- métricas finales -------------
auc_val  = safe_auc(y_valid, best_rf.predict_proba(X_valid)[:,1])
acc_val  = accuracy_score(y_valid, best_rf.predict(X_valid))

auc_test = safe_auc(y_test,  best_rf.predict_proba(X_test)[:,1])
acc_test = accuracy_score(y_test,  best_rf.predict(X_test))

print("\n---  Validación  ---")
print("AUC :", round(auc_val, 3) if auc_val is not None else "N/A")
print("ACC :", round(acc_val, 3))

print("\n---  Test 2020‑22 ---")
print("AUC :", round(auc_test, 3) if auc_test is not None else "N/A")
print("ACC :", round(acc_test, 3))
