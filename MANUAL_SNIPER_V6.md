# 🎯 TRADING BOT SNIPER V6.2 — MANUAL DE OPERACIONES 🎯

> **Versión:** 6.2 · **Fecha:** Abril 2026  
> **Clasificación:** Documento técnico interno — uso exclusivo del desarrollador

---

## Resumen Ejecutivo

Sniper v6.2 es un bot de trading algorítmico de alta precisión con arquitectura híbrida que combina Machine Learning clásico y Deep Learning recurrente. El sistema analiza datos de mercado en tiempo real provenientes de MetaTrader 5, extrae 31 indicadores técnicos avanzados y genera señales de entrada BUY/SELL con probabilidad calibrada.

El pipeline se divide en **4 fases progresivas** de IA, cada una más compleja y precisa que la anterior, orquestadas desde un dashboard web construido en Django.

**Objetivos de rendimiento globales:**

| Métrica    | Target mínimo |
|------------|--------------|
| Precision  | ≥ 70 %       |
| Recall     | ≥ 65 %       |
| ROC-AUC    | ≥ 85 %       |
| Win Rate   | ≥ 64 %       |

---

## 1. Especificaciones de Hardware y Entorno

| Componente       | Especificación                        |
|------------------|---------------------------------------|
| Sistema Operativo| Windows 11 (64-bit)                   |
| CPU              | AMD Ryzen 7                           |
| GPU              | NVIDIA RTX 4050 Laptop (6 GB VRAM)    |
| RAM              | 16 GB DDR5                            |
| Python           | 3.14 (CPython)                        |
| CUDA Toolkit     | 12.1                                  |
| cuDNN            | Compatible con CUDA 12.1              |
| IDE              | Visual Studio Code                    |

### Stack de Software

```
Django 4.x          ← Dashboard web + ORM
LightGBM            ← CPU (AMD Ryzen)
XGBoost             ← GPU (CUDA / tree_method='hist')
CatBoost            ← GPU principal / CPU fallback automático
PyTorch 2.x+cpu     ← LSTM en CPU (Python 3.14 sin soporte CUDA nativo)
Optuna              ← Hyperparameter tuning automático
scikit-learn        ← Scaler, métricas, TimeSeriesSplit
pandas / numpy      ← Ingeniería de features
MetaTrader5         ← Conexión al broker
joblib              ← Serialización de modelos
```

> **⚠️ Nota Python 3.14 + CUDA:**  
> A la fecha de este manual, PyTorch no publica wheels oficiales con soporte CUDA para Python 3.14.  
> La Fase 4 (LSTM) opera **completamente en CPU**. Cuando PyTorch publique soporte oficial, solo se necesita cambiar `device = torch.device('cpu')` por `torch.device('cuda')` en `entrenador_fase4_pytorch.py`.

---

## 2. Arquitectura del Sistema — Las 4 Fases

```
 MT5 / Datos Históricos
         │
         ▼
 ┌───────────────┐     ┌───────────────┐
 │    FASE 1     │────▶│    FASE 2     │
 │  LightGBM     │     │  31 Features  │
 │  5 features   │     │  Indicadores  │
 └───────────────┘     └───────┬───────┘
                               │
                 ┌─────────────▼─────────────┐
                 │          FASE 3           │
                 │   Voting Ensemble GPU     │
                 │  LightGBM+XGBoost+CatB.  │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │          FASE 4           │
                 │    LSTM PyTorch (CPU)     │
                 │   Secuencias 50 velas     │
                 └─────────────┬─────────────┘
                               │
                     Señal BUY / SELL
                    + Probabilidad [0,1]
```

---

### Fase 1 — Fundamentos (LightGBM Baseline)

**Archivo:** `sniper/ai_module/entrenador.py`

**Objetivo:** Establecer un clasificador binario rápido y sin data leakage como baseline del pipeline.

**Logros clave:**
- Eliminación de Data Leakage mediante `TimeSeriesSplit` (Walk-Forward Cross-Validation).  
  Se garantiza que el modelo nunca ve datos futuros durante el entrenamiento.
- 5 features base libres de lookahead: `tipo_orden`, `rsi_entrada`, `distancia_ema`, `hora_dia`, `dia_semana`.
- Validación rigurosa: precision ≥ 65 %, ROC-AUC ≥ 75 %.

**Modelo guardado:** `sniper/ai_module/modelo_sniper.pkl`  
**Validador:** `sniper/ai_module/validador.py`

---

### Fase 2 — Análisis Avanzado (31 Features)

**Archivo:** `sniper/ai_module/entrenador_fase2.py`  
**Extractor:** `sniper/services/extractor_features_fase2.py`

**Objetivo:** Enriquecer el espacio de features con 31 indicadores técnicos agrupados por categoría.

| Grupo | Features | Count |
|-------|---------|-------|
| Originales Fase 1 | tipo_orden, rsi_entrada, distancia_ema, hora_dia, dia_semana | 5 |
| Volatilidad | atr_pips, natr_percent, bb_position, bb_width, volatilidad_regimen | 5 |
| Momentum | macd_value, macd_signal_line, macd_histogram, macd_momentum_flag, stoch_k_percent, stoch_d_percent, stoch_zone, rsi_divergencia | 8 |
| Volumen | obv_trend, mfi_value | 2 |
| Tendencia | adx_strength, di_plus_value, di_minus_value, cci_value | 4 |
| Soporte/Resistencia | distancia_soporte, distancia_resistencia | 2 |
| Patrones de vela | engulfing_pattern, pin_bar_pattern, inside_bar_pattern, patron_fuerza | 4 |
| Régimen | regimen_type (RANGE / TREND_UP / TREND_DOWN / VOLATILE) | 1 |

**Todas las features se normalizan al rango [0, 1]** mediante `NormalizadorFase2`.

**Modelo guardado:** `sniper/ai_module/modelo_sniper_fase2.pkl`  
**Scaler:** `sniper/ai_module/scaler_fase2.pkl`  
**Validador:** `sniper/ai_module/validador_fase2.py`

---

### Fase 3 — Voting Ensemble GPU ("El Glow-Up")

**Archivo:** `sniper/ai_module/entrenador_fase3.py`

**Objetivo:** Superar el baseline con un ensemble de 3 modelos optimizados automáticamente por Optuna.

#### Modelos del Ensemble

| Modelo    | Dispositivo          | Particularidades |
|-----------|----------------------|-----------------|
| LightGBM  | CPU (AMD Ryzen)      | Fit/predict con `pd.DataFrame` + `FEATURE_NAMES_FASE2` |
| XGBoost   | GPU (`device='cuda'`, `tree_method='hist'`) | Fallback CPU automático si CUDA falla |
| CatBoost  | GPU (`task_type='GPU'`) | `devices='0'`, `bootstrap_type='Poisson'` para subsample |

#### Tuning con Optuna

```python
study = optuna.create_study(
    direction='maximize',       # Maximizar ROC-AUC
    sampler=TPESampler(seed=42),
    pruner=MedianPruner()
)
study.optimize(objective, n_trials=10)  # Por modelo
```

Hiperparámetros buscados por modelo:

- **LightGBM:** `n_estimators`, `max_depth`, `learning_rate`, `num_leaves`, `feature_fraction`, `bagging_fraction`
- **XGBoost:** `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`
- **CatBoost:** `iterations`, `depth`, `learning_rate`, `subsample` (con `bootstrap_type='Poisson'`), `colsample_bylevel`

#### Voting ponderado

```python
prob_ensemble = (1/3)*prob_lgb + (1/3)*prob_xgb + (1/3)*prob_catboost
señal = 1 if prob_ensemble >= 0.5 else 0   # BUY / SELL
```

#### Fixes críticos aplicados

```python
# FIX 1 — LightGBM: mantener nombres de columna
X_df = pd.DataFrame(X_scaled, columns=FEATURE_NAMES_FASE2)
model_lgb.fit(X_df, y)              # ← siempre DataFrame, nunca ndarray crudo

# FIX 2 — CatBoost GPU: bootstrap compatible con subsample
cb.CatBoostClassifier(
    task_type='GPU',
    devices='0',                    # ← NO '0:1' (error de rango en GPU única)
    bootstrap_type='Poisson',       # ← único tipo que admite subsample en GPU
    subsample=0.8,
)
```

**Modelo guardado:** `sniper/ai_module/modelo_sniper_fase3.pkl`  
**Scaler:** `sniper/ai_module/scaler_fase3.pkl`  
**Validador:** `sniper/ai_module/validador_fase3.py`

---

### Fase 4 — Deep Learning LSTM (PyTorch CPU)

**Archivo:** `sniper/ai_module/entrenador_fase4_pytorch.py`

**Objetivo:** Capturar dependencias temporales en secuencias de 50 velas mediante una red LSTM bidireccional.

#### Preprocesamiento: Time Windows

```python
# DataFrame [N, 31] → Tensor 3D [M, 50, 31]
def crear_ventanas_temporales(X, y, sequence_length=50):
    for i in range(sequence_length, len(X)):
        X_win.append(X[i - sequence_length : i])   # ventana [50, 31]
        y_win.append(y[i])
    return np.array(X_win), np.array(y_win)
```

#### Arquitectura del Modelo

```
Input  [batch, 50, 31]
   │
LSTM Bidireccional — 2 capas, hidden=128
   │  dropout entre capas (si num_layers > 1)
   │
Último timestep  [batch, 256]   (128 × 2 direcciones)
   │
Dropout(0.30) → Linear(256 → 128) → ReLU
Dropout(0.30) → Linear(128 → 64)  → ReLU
Dropout(0.15) → Linear(64  → 1)   → logit
   │
BCEWithLogitsLoss durante entrenamiento
torch.sigmoid()  durante inferencia  →  P(BUY) ∈ [0, 1]
```

#### Loop de Entrenamiento

```python
optimizer = Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)
criterion = BCEWithLogitsLoss()

# Early-stopping: patience=10 épocas sin mejora en Val AUC
# Gradient clipping: max_norm=1.0
# Split temporal (NO shuffle) — 80% train / 20% val
```

#### Guardado del Modelo

```python
torch.save(model.state_dict(), 'sniper/ai_module/modelo_sniper_fase4.pth')
joblib.dump(scaler, 'sniper/ai_module/scaler_fase4.pkl')
```

**Constantes clave:**

| Parámetro | Valor |
|-----------|-------|
| `SEQUENCE_LENGTH` | 50 |
| `N_FEATURES` | 31 |
| `HIDDEN_SIZE` | 128 |
| `NUM_LAYERS` | 2 |
| `DROPOUT` | 0.30 |
| `BATCH_SIZE` | 64 |
| `EPOCHS` | 50 |
| `LEARNING_RATE` | 0.001 |
| `device` | `torch.device('cpu')` |

---

## 3. Estructura de Directorios

```
TradingBot2026SegundaCopiaAvanzada/
│
├── manage.py
├── requirements.txt
├── sniperbot.db                         ← SQLite
├── README.md                            ← Referencia rápida
├── MANUAL_SNIPER_V6.md                  ← Este documento
├── test_pipeline_completo.py            ← QA unificado (sin Django)
├── cleanup_workspace.py                 ← Limpieza segura del workspace
│
├── core/                                ← Configuración Django
│   ├── settings.py
│   └── urls.py
│
└── sniper/
    ├── models.py            ← TradeHistory · ConfiguracionBot · ShadowTrade
    ├── views.py             ← Dashboard web
    ├── urls.py
    │
    ├── ai_module/
    │   ├── entrenador.py                ← Fase 1
    │   ├── entrenador_fase2.py          ← Fase 2
    │   ├── entrenador_fase3.py          ← Fase 3 (Ensemble GPU) ★
    │   ├── entrenador_fase4_pytorch.py  ← Fase 4 (LSTM CPU)     ★
    │   ├── validador.py / _fase2 / _fase3 / _fase4
    │   ├── modelo_sniper.pkl
    │   ├── modelo_sniper_fase2.pkl
    │   ├── modelo_sniper_fase3.pkl
    │   ├── modelo_sniper_fase4.pth      ← generado tras Fase 4
    │   └── scaler_fase2.pkl / _fase3.pkl / _fase4.pkl
    │
    └── services/
        ├── extractor_features_fase2.py  ← FEATURE_NAMES_FASE2 (31 names)
        ├── analisis_avanzado.py         ← Indicadores técnicos
        ├── orquestador_fases.py         ← Dispatcher de las 4 fases
        ├── cerebro_analitico.py         ← Scoring final
        ├── ejecutor_ordenes.py          ← Envío órdenes a MT5
        ├── gestor_riesgo.py             ← SL/TP dinámico
        ├── radar_mercado.py             ← Escaneo de pares
        └── nvidia_acceleration.py       ← GPU helpers
```

---

## 4. Instalación y Configuración

### 4.1 CUDA Toolkit 12.1

1. Descargar desde: https://developer.nvidia.com/cuda-12-1-0-download-archive  
2. Instalar con opción **Express** (incluye drivers actualizados).  
3. Verificar instalación:
   ```powershell
   nvcc --version          # debe mostrar release 12.1
   nvidia-smi              # muestra GPU y driver
   ```

### 4.2 Entorno Virtual

```powershell
# Crear venv con Python 3.14
python -m venv venv

# Activar
.\venv\Scripts\activate

# Actualizar pip
python -m pip install --upgrade pip
```

### 4.3 Dependencias

```powershell
pip install -r requirements.txt
```

**`requirements.txt` mínimo:**
```
django>=4.2
lightgbm>=4.0
xgboost>=2.0
catboost>=1.2
torch>=2.0          # instalar versión +cpu si Python 3.14 no tiene wheel CUDA
numpy>=1.26
pandas>=2.0
scikit-learn>=1.3
optuna>=3.0
joblib>=1.3
MetaTrader5
```

> **Nota Python 3.14:**  
> Si `pip install torch` falla por falta de wheel para 3.14, usar el índice CPU explícito:
> ```powershell
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> ```

### 4.4 Configuración Django

```powershell
# Migraciones de BD
python manage.py migrate

# Crear superusuario (opcional, para /admin)
python manage.py createsuperuser

# Verificar configuración
python manage.py check
```

### 4.5 Variable de Entorno

El archivo `core/settings.py` ya referencia `DJANGO_SETTINGS_MODULE`.  
Todos los módulos de IA lo establecen al inicio:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
```

---

## 5. Ejecución y Tests

### 5.1 Servidor de Desarrollo

```powershell
python manage.py runserver
# Dashboard disponible en: http://127.0.0.1:8000/sniper/
```

### 5.2 Entrenar cada Fase

**Opción A — Desde el Dashboard Web**  
Acceder a `http://127.0.0.1:8000/sniper/` y usar los botones de entrenamiento.

**Opción B — Django Shell**

```powershell
# Fase 1 — LightGBM Baseline
python manage.py shell -c "from sniper.ai_module.entrenador import entrenar_modelo_historico; entrenar_modelo_historico()"

# Fase 2 — 31 Features
python manage.py shell -c "from sniper.ai_module.entrenador_fase2 import entrenar_modelo_fase2; entrenar_modelo_fase2()"

# Fase 3 — Ensemble GPU
python manage.py shell -c "from sniper.ai_module.entrenador_fase3 import entrenar_modelo_fase3; entrenar_modelo_fase3()"

# Fase 4 — LSTM CPU
python manage.py shell -c "from sniper.ai_module.entrenador_fase4_pytorch import run_fase4; run_fase4()"
```

**Opción C — Standalone (Fase 4 sin Django)**

```powershell
.\venv\Scripts\python.exe -X utf8 sniper/ai_module/entrenador_fase4_pytorch.py
```

### 5.3 Test QA Integral

Script completamente independiente (no requiere Django, BD, ni MT5):

```powershell
.\venv\Scripts\python.exe -X utf8 test_pipeline_completo.py
```

**Salida esperada:**
```
=================================================================
  Sniper v6.2 — QA Pipeline Completo
=================================================================

  DATOS MOCK
  ✅ DataFrame dummy generado → shape (100, 32)

  FASE 1 & 2 — LightGBM + StandardScaler
  ✅ FASE 1 & 2 LightGBM: Test exitoso. P(BUY) = 0.3369

  FASE 3 — Voting Ensemble (LGB + XGB + CatBoost)
  ✅ FASE 3 Ensemble: Test exitoso. P(BUY) = 0.3097

  FASE 4 — LSTM PyTorch (CPU)
  ✅ FASE 4 LSTM: Test exitoso. Salida: 0.5125

  🏆 PIPELINE COMPLETO: Todos los tests pasaron correctamente.
```

> **⚠️ Usar siempre el Python del venv** — el Python del sistema no tiene las librerías:
> ```powershell
> # Correcto
> .\venv\Scripts\python.exe -X utf8 test_pipeline_completo.py
> 
> # Incorrecto (Python global)
> python -X utf8 test_pipeline_completo.py
> ```

### 5.4 Limpieza del Workspace

```powershell
.\venv\Scripts\python.exe -X utf8 cleanup_workspace.py
# → Lista 27 archivos obsoletos y pide Y/N antes de borrar
```

---

## 6. Roadmap de Optimización (Visión Futura)

### 6.1 RFE por GPU — Recursive Feature Elimination acelerada

**Estado:** Planificado  
**Objetivo:** Reducir los 31 features actuales al subconjunto óptimo (estimado: 18-22 features) usando eliminación recursiva acelerada en GPU.

**Implementación propuesta:**

```python
# Opción A — RAPIDS cuML (cuando soporte Python 3.14)
from cuml.feature_selection import RFE as cuRFE
from cuml.ensemble import RandomForestClassifier as cuRF

selector = cuRFE(estimator=cuRF(n_estimators=100), n_features_to_select=20)
selector.fit(X_gpu, y_gpu)   # X_gpu = cudf.DataFrame en VRAM

# Opción B — XGBoost feature importance + eliminación iterativa (disponible hoy)
importances = model_xgb.get_booster().get_score(importance_type='gain')
top_features = sorted(importances, key=importances.get, reverse=True)[:20]
```

**Beneficios esperados:**
- Reducción del tiempo de entrenamiento: ~30 %
- Mejora de generalización al eliminar features ruidosas
- Reducción de dimensión del tensor LSTM: [batch, 50, 31] → [batch, 50, 20]

### 6.2 NVIDIA TensorRT — Inferencia ultrarrápida

**Estado:** Pendiente soporte CUDA en PyTorch para Python 3.14  
**Objetivo:** Reducir latencia de inferencia del LSTM de ~12 ms a ~2 ms mediante optimización del grafo de cómputo con TensorRT.

**Plan de integración (cuando PyTorch 3.14+CUDA esté disponible):**

```python
# Paso 1 — Exportar modelo a ONNX
import torch.onnx
dummy_input = torch.randn(1, 50, 31, device='cuda')
torch.onnx.export(
    model, dummy_input,
    "sniper_lstm.onnx",
    input_names=['secuencia'],
    output_names=['logit'],
    dynamic_axes={'secuencia': {0: 'batch_size'}}
)

# Paso 2 — Compilar con TensorRT
import tensorrt as trt
# (ver nvidia_acceleration.py y triton_serving.py para integración completa)

# Paso 3 — Servir con Triton Inference Server
# (infraestructura ya preparada en sniper/services/triton_serving.py)
```

**Beneficios esperados:**
- Latencia de inferencia: 12 ms → ~2 ms (6x speedup)
- Throughput: +400 % en señales por segundo
- Uso de VRAM optimizado mediante FP16 (half precision)

### 6.3 Mejoras de Modelo — Próximas versiones

| Mejora | Versión | Estado |
|--------|---------|--------|
| Attention mechanism sobre LSTM | v6.3 | Diseño |
| Walk-forward con retrain incremental | v6.3 | Diseño |
| NIM Sentiment (NVIDIA NIM API) | v6.4 | Parcial (`nim_sentiment.py`) |
| Multi-símbolo simultáneo (EURUSD + GBPUSD + USDJPY) | v6.4 | Planificado |
| RFE por GPU (cuML) | v6.5 | Planificado |
| TensorRT inferencia | v7.0 | Pendiente Python 3.14 + CUDA |
| Reinforcement Learning (PPO) | v7.0 | Investigación |

---

## Apéndice A — Fixes Críticos Documentados

### A.1 LightGBM — Feature Names Warning

**Error:** `X does not have valid feature names, but LGBMClassifier was fitted with feature names`

**Causa:** El modelo fue entrenado con un `pd.DataFrame` (con nombres de columna) pero la predicción recibía un `np.ndarray` sin nombres.

**Fix:**
```python
from sniper.services.extractor_features_fase2 import FEATURE_NAMES_FASE2

X_df = pd.DataFrame(X_scaled, columns=FEATURE_NAMES_FASE2)
model_lgb.fit(X_df, y)           # fit con DataFrame
model_lgb.predict_proba(X_df)    # predict con DataFrame
```

### A.2 CatBoost GPU — Subsample con Bootstrap Bayesian

**Error:** `default bootstrap type (bayesian) doesn't support 'subsample' option`

**Causa:** El tipo de bootstrap por defecto en GPU (`Bayesian`) no acepta el parámetro `subsample`.

**Fix:**
```python
# GPU — usar Poisson (soporta subsample)
CatBoostClassifier(
    task_type='GPU',
    bootstrap_type='Poisson',   # ← fix
    subsample=0.8,
)

# CPU fallback — usar Bernoulli (soporta subsample en CPU)
CatBoostClassifier(
    task_type='CPU',
    bootstrap_type='Bernoulli', # ← fix
    subsample=0.8,
)
```

### A.3 CatBoost GPU — Rango de Dispositivo Inválido

**Error:** `Range specification string '1' is invalid: id 1 greater than limit 1`

**Causa:** El formato `devices='0:1'` especifica GPU 0 con límite 1, pero CatBoost interpreta `1` como un segundo índice de dispositivo que no existe.

**Fix:**
```python
# Incorrecto
devices='0:1'

# Correcto — especificar solo el índice de la GPU
devices='0'
```

---

## Apéndice B — Métricas por Fase

| Fase | Modelo | Precision | Recall | F1 | ROC-AUC |
|------|--------|-----------|--------|----|---------|
| Fase 1 | LightGBM (5 feat.) | 65 %+ | 60 %+ | 62 %+ | 75 %+ |
| Fase 2 | LightGBM (31 feat.) | 68 %+ | 62 %+ | 65 %+ | 80 %+ |
| Fase 3 | Ensemble GPU | 70 %+ | 65 %+ | 67 %+ | 85 %+ |
| Fase 4 | LSTM CPU | 75 %+ | 70 %+ | 72 %+ | 90 %+ |

---

*Sniper v6.2 · Manual de Operaciones · Abril 2026*  
*Documento generado y mantenido por el equipo de desarrollo cuantitativo.*
