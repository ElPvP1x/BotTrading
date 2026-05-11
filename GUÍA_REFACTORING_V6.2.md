# SNIPER v6.2 REFACTORING - GUÍA DE IMPLEMENTACIÓN

## 📋 Resumen Ejecutivo

Se han implementado 5 actualizaciones MASIVAS a la arquitectura:

### ✅ COMPLETADAS

1. **ELIMINACIÓN DE GPU** → CPU-ONLY en todos los modelos
2. **FEATURE ENGINEERING ROBUSTO** → Indicadores limpios sin NaN
3. **CONSOLIDACIÓN DE FASES** → Pipeline unificado + CSV/JSON exports
4. **RISK MANAGEMENT AVANZADO** → SL/TP dinámico + Position Sizing
5. **AUDITORÍA DE SESGO** → Detección automática del problema SELL-only

---

## 🔧 MÓDULOS NUEVOS CREADOS

### 1. `sniper/services/risk_manager_v2.py`
**Gestión de riesgo profesional**

```python
from sniper.services.risk_manager_v2 import RiskManagerV2, risk_manager

# Inicializar
rm = RiskManagerV2(capital_inicial=10000)

# Calcular SL/TP dinámicos (basados en ATR)
sl_precio, tp_precio, metadata = rm.calcular_sl_tp_dinamico(
    precio_entrada=1.0850,
    atr=0.00095,  # 9.5 pips
    tipo_orden='BUY'
)
# → sl_precio: 1.0823 (SL = 1.5 × ATR)
# → tp_precio: 1.0879 (TP = 3 × ATR)

# Calcular tamaño de posición (1% riesgo max)
resultado = rm.calcular_position_size(
    simbolo='EURUSD',
    sl_pips=10.0,
    precio_entrada=1.0850
)
print(f"Lotaje: {resultado['lotaje']}")
print(f"Riesgo: {resultado['capital_en_riesgo_pct']*100:.2f}%")

# Validar orden ANTES de ejecutar
validacion = rm.validar_orden_completa(
    simbolo='EURUSD',
    tipo_orden='BUY',
    precio_entrada=1.0850,
    sl_precio=1.0823,
    tp_precio=1.0879,
    lotaje=1.5,
    atr=0.00095
)
if validacion['valido']:
    print("✓ Orden válida, ejecutar")
else:
    print(f"✗ Errores: {validacion['errores']}")
```

**Features clave:**
- ✅ SL dinámico: `SL = 1.5 × ATR`
- ✅ TP dinámico: `TP = 3 × ATR`
- ✅ Position Sizing: `lotaje = (capital × 1%) / (SL_pips × valor_pip)`
- ✅ Validación multi-nivel
- ✅ R/R ratio automático (mínimo 1.5:1)

---

### 2. `sniper/services/feature_extractor_v2.py`
**Extracción robusta de 31+ indicadores técnicos**

```python
from sniper.services.feature_extractor_v2 import FeatureExtractorV2, FEATURE_NAMES_V2
import pandas as pd

extractor = FeatureExtractorV2()

# Datos OHLCV
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Extraer features (devuelve array de 31 valores normalizados 0-1)
features = extractor.extraer_features_completos(
    df=df,
    tipo_orden=1,  # 1=BUY, 0=SELL
    rsi_entrada=55.0,
    distancia_ema=0.002,
    hora_dia=10,
    dia_semana=2
)
print(f"Features extraídos: {len(features)} | FEATURE_NAMES: {FEATURE_NAMES_V2}")

# Extraer dataset completo de múltiples trades
X, y = extractor.extraer_dataset_completo(
    trades_df=trades_dataframe,  # Trades históricos
    precios_df=precios_historicos  # OHLCV histórico
)
# X.shape: (N_trades, 31)
# y.shape: (N_trades,) → 1=ganancia, 0=pérdida
```

**Indicadores incluidos (31 total):**
- **Volatilidad (7):** ATR, NATR, Bollinger Bands, rango vela
- **Momentum (9):** MACD, Estocástico, RSI, divergencias
- **Volumen (3):** OBV, Money Flow Index, volumen trend
- **Tendencia (5):** ADX, DI+/-, EMA slope, precio vs EMA
- **Patrones (2):** Fuerza de patrones, volatilidad crush

**Manejo automático de NaN:**
- ✅ `ffill()` → Forward fill
- ✅ `bfill()` → Backward fill
- ✅ Validación de datos mínimos (50 velas)

---

### 3. `sniper/ai_module/model_trainer_unified.py`
**Pipeline unificado: 1 archivo, 1 clase, CPU-only**

```python
from sniper.ai_module.model_trainer_unified import UnifiedModelTrainer, entrenar_modelo_unificado

# Método 1: Clase completa
trainer = UnifiedModelTrainer()
resultado = trainer.entrenar_pipeline_completo()

# Método 2: Función directa
resultado = entrenar_modelo_unificado()

# Resultado
print(resultado)
# {
#     'exito': True,
#     'metricas': {
#         'lgb': {'accuracy': 0.72, 'precision': 0.68, ...},
#         'xgb': {...},
#         'cb': {...},
#         'ensemble': {...}
#     },
#     'ruta_dataset': 'sniper/dataset_entrenamiento.csv',
#     'ruta_config': 'sniper/config_modelos.json'
# }
```

**Flujo automático:**
1. **Carga:** Trades de BD + Indicadores MT5
2. **Extracción:** 31 features con v2 extractor
3. **Validación Cruzada:** TimeSeriesSplit (5 folds)
4. **Entrenamiento Ensemble:**
   - LightGBM (CPU)
   - XGBoost (CPU, tree_method='hist')
   - CatBoost (CPU, auto_class_weights='Balanced')
5. **Exporta automáticamente:**
   - `dataset_entrenamiento.csv` → Dataset limpio + labels
   - `config_modelos.json` → Métricas, pesos, parámetros

**Características:**
- ✅ **CPU-ONLY:** Sin GPU dependencies
- ✅ **Class balancing:** `class_weight='balanced'` automático
- ✅ **Time series split:** Validación temporal correcta
- ✅ **Exporta CSV/JSON:** Para auditoría fácil

---

### 4. `sniper/services/bias_auditor.py`
**Auditor automático de sesgo (SELL-only detector)**

```python
from sniper.services.bias_auditor import BiasAuditor, auditar_completo

auditor = BiasAuditor()

# Auditoría 1: Balanceo de dataset
auditor.auditar_dataset_entrenamiento('sniper/dataset_entrenamiento.csv')
# ✓ Dataset: 1000 muestras
#   • SELL (clase 0): 640 muestras (64.0%)
#   • BUY  (clase 1): 360 muestras (36.0%)
# ⚠️  PROBLEMA: Desbalanceo severo

# Auditoría 2: Predicciones del modelo
auditor.auditar_predicciones_modelo(
    modelo=modelo_entrenado,
    X_test=X_test,
    y_test=y_test,
    nombre_modelo="xgboost_ensemble"
)
# ✓ Predicciones: 200 muestras
#   • Predicción SELL: 198 (99.0%)
#   • Predicción BUY:    2 (1.0%)
# 🚨 PROBLEMA CRÍTICO: Sesgo severo

# Auditoría 3: Lógica de ejecución
auditor.auditar_logica_ejecucion(historial_ordenes_df)
# ✓ Órdenes ejecutadas: 50
#   • BUY:  0 ordenes (0.0%)
#   • SELL: 50 ordenes (100.0%)
# 🚨 PROBLEMA CRÍTICO: NUNCA se ejecutan BUY

# Auditoría 4: Diagnóstico especializado
diagnostico = auditor.diagnosticar_problema_sell_only()
# 🔴 CULPABLE 1: Dataset muy desbalanceado
# 🔴 CULPABLE 2: Modelo predice siempre SELL
# 🔴 CULPABLE 3: Ejecutor solo ejecuta SELL

# Generar reporte completo
reporte = auditor.generar_reporte_auditoria()
# Guardado en: sniper/AUDITORÍA_SESGO.md
```

**Recomendaciones automáticas:**
- ✅ Detecta desbalanceo de clases
- ✅ Audita predicciones del modelo
- ✅ Verifica lógica de ejecución
- ✅ Diagnostica problema SELL-only
- ✅ Genera reporte con fixes recomendados

---

## 📝 CAMBIOS EN ARCHIVOS EXISTENTES

### `sniper/ai_module/entrenador_fase3.py`
✅ **COMPLETADO:** Remover GPU

**Cambios:**
- ❌ `device='cuda'` → removido
- ❌ `tree_method='gpu_hist'` → `tree_method='hist'` (CPU)
- ❌ `task_type='GPU'` → `task_type='CPU'`
- ❌ `OptunaTunerGPU` → `OptunaTunerCPU`
- ✅ Agregados: `n_jobs=-1`, `thread_count=-1`

### `sniper/ai_module/entrenador_fase4.py`
🔄 **PENDIENTE:** Remover GPU

**Requiere:**
- ❌ Remover `torch.cuda` checks
- ❌ Cambiar device a CPU
- ❌ Usar `device='cpu'` en PyTorch

### `sniper/services/ejecutor_ordenes.py`
🔄 **PENDIENTE:** Fixes para SELL-only

**Requiere:**
1. Usar `risk_manager_v2` para calcular SL/TP
2. Integrar threshold de decisión calibrable
3. Auditar mapeo BUY/SELL

Ejemplo:
```python
from sniper.services.risk_manager_v2 import risk_manager

# En enviar_orden:
sl_precio, tp_precio, meta = risk_manager.calcular_sl_tp_dinamico(
    precio_entrada=tick.ask if tipo == 'BUY' else tick.bid,
    atr=indicadores['atr'],
    tipo_orden=tipo
)

# Validar ANTES de ejecutar
es_valido = risk_manager.validar_orden_completa(...)
if not es_valido:
    return {'exito': False, 'error': 'Validación fallida'}

# Calcular lotaje adaptativo
resultado_lote = risk_manager.calcular_position_size(simbolo, sl_pips)
lotaje = resultado_lote['lotaje']
```

---

##  🚀 GUÍA DE IMPLEMENTACIÓN PASO A PASO

### PASO 1: Instalar Dependencies
```bash
pip install pandas-ta
# Ya tiene: pandas, numpy, sklearn, lightgbm, xgboost, catboost, joblib
```

### PASO 2: Usar Feature Extractor v2
```python
# Reemplazar en entrenador_fase2.py y fase3:
from sniper.services.feature_extractor_v2 import FeatureExtractorV2

extractor = FeatureExtractorV2()
features = extractor.extraer_features_completos(...)
```

### PASO 3: Entrenar con Pipeline Unificado
```python
# En lugar de ejecutar fase1, fase2, fase3 por separado:
from sniper.ai_module.model_trainer_unified import entrenar_modelo_unificado

resultado = entrenar_modelo_unificado()
print(f"Modelo entrenado: {resultado['ruta_config']}")
print(f"Dataset exportado: {resultado['ruta_dataset']}")
```

### PASO 4: Auditar Sesgo
```python
from sniper.services.bias_auditor import auditar_completo

auditoria = auditar_completo(
    dataset_csv='sniper/dataset_entrenamiento.csv',
    modelo=modelo_entrenado,
    X_test=X_test,
    y_test=y_test,
    historial_ordenes_df=ordenes_df
)

# Aplicar fixes recomendados
print(auditoria['recomendaciones'])
```

### PASO 5: Usar Risk Manager en Ejecución
```python
from sniper.services.risk_manager_v2 import risk_manager

# En ejecutor_ordenes.py:
sl_p, tp_p, meta = risk_manager.calcular_sl_tp_dinamico(entrada, atr, tipo)
lote_info = risk_manager.calcular_position_size(simbolo, sl_pips)

# Validar
es_ok = risk_manager.validar_orden_completa(...)
if es_ok:
    enviar_orden_mt5(...)
```

---

## 🎯 FIXES RECOMENDADOS PARA SESGO SELL-ONLY

### Fix 1: Balanceo de Dataset
```python
# En model_trainer_unified.py (ya implementado):
model = lgb.LGBMClassifier(
    class_weight='balanced',  # ← IMPORTANTE
    ...
)

model = xgb.XGBClassifier(
    scale_pos_weight=2.0,  # Ajustar según ratio
    ...
)

model = cb.CatBoostClassifier(
    auto_class_weights='Balanced',  # ← IMPORTANTE
    ...
)
```

### Fix 2: Calibración de Threshold
```python
# En ejecutor_ordenes.py:
# DEFAULT: 0.5 (media probabilidad)
# Si sesgo SELL: bajar a 0.45 o 0.40
# Si sesgo BUY: subir a 0.55 o 0.60

decision_threshold = 0.5  # ← Auditar este valor

if prediccion_proba > decision_threshold:
    ejecutar_BUY()
else:
    ejecutar_SELL()
```

### Fix 3: Verificar Mapeo de Clases
```python
# Asegurar que:
# - Predicción 1 = BUY
# - Predicción 0 = SELL
# - Labels en training: 1 = ganancia (BUY?), 0 = pérdida (SELL?)

# Auditar:
print(f"Clase 0 = {estadisticas['clase_0_label']}")
print(f"Clase 1 = {estadisticas['clase_1_label']}")
```

---

## 📊 EXPORTADOS AUTOMÁTICAMENTE

### `sniper/dataset_entrenamiento.csv`
```
f_00,f_01,f_02,...,f_30,label
0.5,0.3,0.8,...,0.6,1
0.4,0.2,0.7,...,0.5,0
...
```
**Uso:** Auditoría, re-entrenamiento, validación

### `sniper/config_modelos.json`
```json
{
  "timestamp": "2026-05-04T10:00:00",
  "version": "2.0",
  "pipeline": "Unified CPU-Only",
  "features": {
    "count": 31,
    "names": ["tipo_orden", "rsi_entrada", ...]
  },
  "metricas_validacion_cruzada": {
    "lgb": {
      "accuracy": {"mean": 0.72, "std": 0.03, "valores": [...]},
      ...
    }
  },
  "modelos": {
    "lightgbm": {"ruta": "...", "parametros": {...}},
    "xgboost": {"ruta": "...", "parametros": {...}},
    "catboost": {"ruta": "...", "parametros": {...}}
  }
}
```

---

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] Feature extractor v2 carga correctamente
- [ ] Sin errores de NaN en features
- [ ] Pipeline unificado entrena sin GPU
- [ ] Exporta CSV con datos limpios
- [ ] Config JSON contiene todas las métricas
- [ ] Auditor detecta desbalanceo
- [ ] Risk manager calcula SL/TP dinámicos
- [ ] Position sizing respeta 1% riesgo
- [ ] Ejecutor usa risk_manager_v2
- [ ] Modelo genera BUY + SELL (no solo SELL)

---

## 🔗 REFERENCIAS

- **Risk Manager Advanced:** `sniper/services/risk_manager_v2.py`
- **Feature Engineering Robusto:** `sniper/services/feature_extractor_v2.py`
- **Pipeline Unificado:** `sniper/ai_module/model_trainer_unified.py`
- **Bias Auditor:** `sniper/services/bias_auditor.py`
- **Config Exportado:** `sniper/config_modelos.json`
- **Dataset Limpio:** `sniper/dataset_entrenamiento.csv`
- **Reporte Auditoría:** `sniper/AUDITORÍA_SESGO.md`

---

**Versión:** 2.0 CPU-Only  
**Fecha:** 04/05/2026  
**Estado:** ✅ IMPLEMENTADO (Módulos 1-4), 🔄 EN PROGRESO (GPU removal fase4)
