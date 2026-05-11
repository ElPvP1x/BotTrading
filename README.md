# Sniper v6.2 — Trading Bot con IA (4 Fases)

> Sistema de trading algorítmico con predicción por Machine Learning y Deep Learning.  
> Stack: Django · LightGBM · XGBoost · CatBoost (GPU) · PyTorch LSTM (CPU) · MetaTrader 5

---

## Arquitectura General

```
┌──────────────────────────────────────────────────────────┐
│                   SNIPER v6.2 — PIPELINE                 │
│                                                          │
│  MT5 / Datos  ──►  FASE 1  ──►  FASE 2  ──►  FASE 3    │
│                   LightGBM   Avanzado    Ensemble GPU    │
│                                    │                     │
│                               FASE 4                     │
│                             LSTM CPU                     │
│                                    │                     │
│                          Señal BUY / SELL                │
│                         Orquestador Django               │
└──────────────────────────────────────────────────────────┘
```

---

## Las 4 Fases de IA

### Fase 1 — LightGBM Baseline
**Archivo:** `sniper/ai_module/entrenador.py`  
**Features:** 5 (tipo_orden, RSI, distancia EMA, hora, día semana)  
**Objetivo:** Clasificador binario rápido como baseline (BUY=1 / SELL=0)  
**Validador:** `sniper/ai_module/validador.py`

### Fase 2 — Análisis Avanzado (31 Features)
**Archivo:** `sniper/ai_module/entrenador_fase2.py`  
**Features:** 31 — volatilidad (ATR, Bollinger), momentum (MACD, Estocástico), volumen (OBV, MFI), tendencia (ADX, CCI), S/R, patrones de vela, régimen de mercado  
**Extractor:** `sniper/services/extractor_features_fase2.py`  
**Validador:** `sniper/ai_module/validador_fase2.py`  
**Modelo guardado:** `sniper/ai_module/modelo_sniper_fase2.pkl`

### Fase 3 — Voting Ensemble con GPU
**Archivo:** `sniper/ai_module/entrenador_fase3.py`  
**Modelos:**

| Modelo     | Dispositivo | Notas |
|------------|-------------|-------|
| LightGBM   | CPU (Ryzen) | Fit/predict con DataFrame para mantener nombres de features |
| XGBoost    | GPU (CUDA)  | `tree_method='hist'`, fallback CPU automático |
| CatBoost   | GPU         | `devices='0'`, `bootstrap_type='Poisson'` para subsample |

**Tuning:** Optuna (TPE Sampler, MedianPruner, 10 trials/modelo)  
**Ensemble:** Promedio ponderado de probabilidades (1/3 cada modelo)  
**Validador:** `sniper/ai_module/validador_fase3.py`  
**Modelo guardado:** `sniper/ai_module/modelo_sniper_fase3.pkl`

> **Fixes aplicados en Fase 3:**
> - LightGBM: se pasa `pd.DataFrame` con `FEATURE_NAMES_FASE2` en fit y predict
> - CatBoost GPU: `bootstrap_type='Poisson'` habilita `subsample`; fallback usa `'Bernoulli'`
> - CatBoost GPU: `devices='0'` (en lugar de `'0:1'` que daba error de rango)

### Fase 4 — LSTM Deep Learning (PyTorch CPU)
**Archivo:** `sniper/ai_module/entrenador_fase4_pytorch.py`  
**Restricción:** Python 3.14 no tiene soporte CUDA nativo → todo en CPU  
**Arquitectura LSTM:**

```
Input [batch, 50, 31]
    │
LSTM Bidireccional (2 capas, hidden=128)
    │
Dropout(0.3) → Linear(256→128) → ReLU
    │
Dropout(0.3) → Linear(128→64)  → ReLU
    │
Dropout(0.15)→ Linear(64→1)    → BCEWithLogitsLoss
```

**Ventana temporal:** 50 pasos (sequence_length=50)  
**Optimizador:** Adam (lr=1e-3, weight_decay=1e-4) + ReduceLROnPlateau  
**Early stopping:** patience=10 épocas sin mejora en Val AUC  
**Guardado:** `torch.save(model.state_dict(), 'modelo_sniper_fase4.pth')`

---

## Estructura de Directorios

```
TradingBot2026SegundaCopiaAvanzada/
│
├── manage.py
├── requirements.txt
├── sniperbot.db                        ← SQLite (Django)
├── test_pipeline_completo.py           ← QA unificado (4 fases, sin Django)
├── cleanup_workspace.py                ← Limpieza segura del workspace
│
├── core/                               ← Configuración Django
│   ├── settings.py
│   └── urls.py
│
└── sniper/
    ├── models.py                       ← TradeHistory, ConfiguracionBot, ShadowTrade
    ├── views.py                        ← Dashboard web
    ├── urls.py
    │
    ├── ai_module/                      ← Módulos de IA (4 Fases)
    │   ├── entrenador.py               ← Fase 1: LightGBM
    │   ├── entrenador_fase2.py         ← Fase 2: 31 features
    │   ├── entrenador_fase3.py         ← Fase 3: Ensemble GPU
    │   ├── entrenador_fase4_pytorch.py ← Fase 4: LSTM CPU (ACTIVO)
    │   ├── entrenador_fase4.py         ← Fase 4: version legacy (Keras/TF)
    │   ├── validador.py                ← Inferencia Fase 1
    │   ├── validador_fase2.py          ← Inferencia Fase 2
    │   ├── validador_fase3.py          ← Inferencia Fase 3
    │   ├── validador_fase4.py          ← Inferencia Fase 4
    │   ├── modelo_sniper.pkl           ← Modelo Fase 1 entrenado
    │   ├── modelo_sniper_fase2.pkl     ← Modelo Fase 2 entrenado
    │   ├── modelo_sniper_fase3.pkl     ← Ensemble Fase 3 entrenado
    │   ├── modelo_sniper_lgb.pkl       ← LightGBM standalone
    │   ├── scaler_fase2.pkl            ← StandardScaler Fase 2
    │   └── scaler_fase3.pkl            ← StandardScaler Fase 3
    │
    └── services/
        ├── extractor_features_fase2.py ← 31 features + FEATURE_NAMES_FASE2
        ├── analisis_avanzado.py        ← Indicadores técnicos completos
        ├── orquestador_fases.py        ← Dispatcher de las 4 fases
        ├── cerebro_analitico.py        ← Scoring final
        ├── ejecutor_ordenes.py         ← Envío órdenes a MT5
        ├── gestor_riesgo.py            ← SL/TP dinámico
        ├── radar_mercado.py            ← Escaneo de pares
        ├── sincronizador.py            ← Sincronización de estado
        ├── nvidia_acceleration.py      ← Aceleración GPU helpers
        ├── nim_sentiment.py            ← Sentimiento de mercado
        └── triton_serving.py           ← Serving de modelos (Triton)
```

---

## Hardware

| Componente | Especificación |
|------------|---------------|
| CPU        | AMD Ryzen (usado por LightGBM y LSTM Fase 4) |
| GPU        | NVIDIA RTX 4050 (usada por XGBoost y CatBoost en Fase 3) |
| Python     | 3.14 (sin soporte CUDA nativo → Fase 4 forzada a CPU) |

### Configuración GPU para CatBoost (Fase 3)
```python
# Correcto — evita los dos errores conocidos:
cb.CatBoostClassifier(
    task_type='GPU',
    devices='0',              # NO usar '0:1' (error de rango en GPU única)
    bootstrap_type='Poisson', # Único tipo compatible con subsample en GPU
    subsample=0.8,
)
```

---

## Instalación

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate          # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Migraciones Django
python manage.py migrate

# 4. Servidor de desarrollo
python manage.py runserver
```

### requirements.txt mínimo
```
django
lightgbm
xgboost
catboost
torch
numpy
pandas
scikit-learn
optuna
joblib
MetaTrader5
```

---

## Ejecución de las Fases

### Opción A — Desde el Dashboard Web
```
http://localhost:8000/sniper/
```
Botones: "Entrenar Fase 1", "Fase 2", "Fase 3 (GPU)", "Fase 4 (LSTM)"

### Opción B — Desde Django Shell

```bash
# Fase 1
python manage.py shell -c "from sniper.ai_module.entrenador import entrenar_modelo_historico; entrenar_modelo_historico()"

# Fase 2
python manage.py shell -c "from sniper.ai_module.entrenador_fase2 import entrenar_modelo_fase2; entrenar_modelo_fase2()"

# Fase 3 (Ensemble GPU)
python manage.py shell -c "from sniper.ai_module.entrenador_fase3 import entrenar_modelo_fase3; entrenar_modelo_fase3()"

# Fase 4 (LSTM CPU)
python manage.py shell -c "from sniper.ai_module.entrenador_fase4_pytorch import run_fase4; run_fase4()"
```

### Opción C — Standalone (Fase 4, sin Django)
```bash
.\venv\Scripts\python.exe -X utf8 sniper/ai_module/entrenador_fase4_pytorch.py
```

---

## QA — Validación del Pipeline

Script independiente (no requiere Django ni MT5):

```bash
.\venv\Scripts\python.exe -X utf8 test_pipeline_completo.py
```

**Salida esperada:**
```
✅ Datos Mock        → shape (100, 32)
✅ Fase 1 & 2        → LightGBM P(BUY) = 0.3369
✅ Fase 3 Ensemble   → P(BUY) = 0.3097
✅ Fase 4 LSTM       → sigmoid = 0.5125
🏆 PIPELINE COMPLETO: Todos los tests pasaron correctamente.
```

---

## Limpieza del Workspace

```bash
.\venv\Scripts\python.exe -X utf8 cleanup_workspace.py
```

Muestra la lista de archivos obsoletos y pide confirmación antes de borrar.

---

## Features del Modelo (31 — FEATURE_NAMES_FASE2)

| Grupo | Features |
|-------|---------|
| Originales Fase 1 (5) | tipo_orden, rsi_entrada, distancia_ema, hora_dia, dia_semana |
| Volatilidad (4) | atr_pips, natr_percent, bb_position, bb_width, volatilidad_regimen |
| Momentum (8) | macd_value, macd_signal_line, macd_histogram, macd_momentum_flag, stoch_k_percent, stoch_d_percent, stoch_zone, rsi_divergencia |
| Volumen (2) | obv_trend, mfi_value |
| Tendencia (4) | adx_strength, di_plus_value, di_minus_value, cci_value |
| Soporte/Resistencia (2) | distancia_soporte, distancia_resistencia |
| Patrones de vela (4) | engulfing_pattern, pin_bar_pattern, inside_bar_pattern, patron_fuerza |
| Régimen (1) | regimen_type |

---

## Targets de Rendimiento

| Fase | Precision | Recall | ROC-AUC |
|------|-----------|--------|---------|
| Fase 1 (LightGBM)   | 65%+ | 60%+ | 75%+ |
| Fase 2 (31 features) | 68%+ | 62%+ | 80%+ |
| Fase 3 (Ensemble GPU)| 70%+ | 65%+ | 85%+ |
| Fase 4 (LSTM CPU)    | 75%+ | 70%+ | 90%+ |

---

## Notas de Compatibilidad

- **Python 3.14 + PyTorch:** No existe soporte CUDA oficial. La Fase 4 opera en CPU. Cuando Python 3.14 tenga wheels CUDA oficiales, cambiar `device = torch.device('cpu')` a `torch.device('cuda')`.
- **CatBoost GPU + subsample:** Requiere `bootstrap_type='Poisson'`. El tipo por defecto `'Bayesian'` no admite el parámetro `subsample`.
- **LightGBM + feature names:** Siempre pasar `pd.DataFrame` (con `FEATURE_NAMES_FASE2` como columnas) en `fit()` y `predict_proba()`. Nunca `np.ndarray` crudo si el modelo fue entrenado con DataFrame.

---

*Sniper v6.2 — Última actualización: Abril 2026*
#   B o t T r a d i n g  
 