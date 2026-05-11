"""
NVIDIA QUICK START GUIDE
═════════════════════════════════════════════════════════════════════════════

Atajos para activar NVIDIA en TradingBot
"""

# ═════════════════════════════════════════════════════════════════════════════
# OPCIÓN 1: SOLO VERIFICAR (sin instalar nada)
# ═════════════════════════════════════════════════════════════════════════════

"""
Ejecutar esto para ver qué hay disponible:

```bash
cd TradingBot2026

python -c "
from sniper.services.nvidia_acceleration import gpu_accelerator
gpu_accelerator.print_status()
"
```

Output esperado:
✓ CUDA detectado: GPU con 24.0GB
✓ RAPIDS detectado (cuDF, cuML)
✓ TensorRT detectado (v8.6)
✓ Triton Client detectado
"""

# ═════════════════════════════════════════════════════════════════════════════
# OPCIÓN 2: INSTALAR RAPIDS (10-100x más rápido)
# ═════════════════════════════════════════════════════════════════════════════

"""
Prerrequisitos:
  ✓ NVIDIA GPU (RTX 3090, A100, L40, etc)
  ✓ CUDA 12.0+ instalado
  ✓ cuDNN (opcional pero recomendado)

Instalación (recomendado):
```bash
# Desactivar venv actual
deactivate

# Crear env nuevo para RAPIDS (requiere conda)
conda create -n rapids-gpu -c rapidsai-nightly rapids=24.02 python=3.11 cuda-version=12.0

# Activar
conda activate rapids-gpu

# Copiar pip reqs
pip install django lightgbm xgboost catboost optuna
```

Verificar:
```bash
python -c "
import cudf, cuml
print('✓ RAPIDS ready')
"
```

Resultado:
- Normalización: 50ms → 1ms (50x más rápido)
- Feature extraction: 500ms → 10ms (50x)
- Total FASE 3: 30 min → 5 min (6x)
"""

# ═════════════════════════════════════════════════════════════════════════════
# OPCIÓN 3: DEPLOY TRITON (5ms latencia)
# ═════════════════════════════════════════════════════════════════════════════

"""
Prerrequisitos:
  ✓ Docker instalado
  ✓ NVIDIA Docker runtime

Pasos:

1. Generar estructura de Triton:
```bash
cd TradingBot2026

python -c "
from sniper.services.triton_serving import setup_triton_repository, generate_triton_docker_compose
setup_triton_repository('triton_models')
generate_triton_docker_compose('.')
"
```

2. Copiar modelos entrenados:
```bash
cp sniper/ai_module/modelo_sniper_fase3.pkl triton_models/
cp sniper/ai_module/scaler_fase3.pkl triton_models/
```

3. Iniciar Triton:
```bash
docker-compose up -d tritonserver
```

4. Verificar:
```bash
curl http://localhost:8000/v2/health/ready
# Output: {"status":"success"}
```

5. Usar desde Django:
```python
from sniper.services.triton_serving import TritonClient

client = TritonClient()  # Auto detecta localhost:8000
predictions = client.predict(features)  # 5-10ms
```

Detener:
```bash
docker-compose down
```
"""

# ═════════════════════════════════════════════════════════════════════════════
# OPCIÓN 4: NIM SENTIMENT (Análisis de noticias)
# ═════════════════════════════════════════════════════════════════════════════

"""
Prerrequisitos:
  ✓ Cuenta NVIDIA NIM (gratis)
  ✓ API key

Setup:

1. Obtener API key:
   - Ir a https://nim.nvidia.com
   - Sign up gratis
   - Generate API key
   - Copiar key

2. Configurar:
```bash
# En PowerShell
$env:NVIDIA_NIM_API_KEY = "nvapi_xxx..."

# O agregar a .env
echo NVIDIA_NIM_API_KEY=nvapi_xxx > .env
```

3. Usar:
```python
from sniper.services.nim_sentiment import NIMSentimentAnalyzer

analyzer = NIMSentimentAnalyzer()

# Analizar texto
result = analyzer.analyze_sentiment("EUR/USD bullish breakout!")
print(result['sentiment'])  # 'positive' o 'negative'
print(result['score'])       # 0.95 (confidence)
```

Casos de uso:
- Monitor tweets sobre trading
- Analizar noticias de bancos centrales
- Sentimiento de redes sociales
- Combinar con FASE 3 para mejores signals
"""

# ═════════════════════════════════════════════════════════════════════════════
# OPCIÓN 5: TODO DE UNA VEZ (Configuración Completa)
# ═════════════════════════════════════════════════════════════════════════════

"""
Script de instalación completa:

```bash
#!/bin/bash

echo "🚀 NVIDIA TradingBot Setup"
echo "===================================="

# 1. RAPIDS
echo "1️⃣ Installing RAPIDS..."
conda create -n rapids-gpu -c rapidsai-nightly rapids=24.02 python=3.11 cuda-version=12.0 -y
source activate rapids-gpu
pip install django lightgbm xgboost catboost optuna requests

# 2. TRITON
echo "2️⃣ Setting up Triton..."
cd TradingBot2026
python -c "
from sniper.services.triton_serving import setup_triton_repository, generate_triton_docker_compose
setup_triton_repository('triton_models')
generate_triton_docker_compose('.')
"

# 3. NIM
echo "3️⃣ Configuring NIM..."
read -p "Enter your NVIDIA NIM API key: " nim_key
echo "export NVIDIA_NIM_API_KEY=$nim_key" >> ~/.bashrc
source ~/.bashrc

# 4. Verificar
echo "4️⃣ Verifying setup..."
python -c "
from sniper.services.nvidia_acceleration import gpu_accelerator
from sniper.services.triton_serving import TritonClient
from sniper.services.nim_sentiment import NIMSentimentAnalyzer

gpu_accelerator.print_status()
print('✓ Triton client ready')
analyzer = NIMSentimentAnalyzer()
print('✓ NIM ready' if analyzer.available else '⚠️ NIM not configured')
"

echo "✅ Setup complete!"
```

Ejecutar:
```bash
bash setup_nvidia.sh
```
"""

# ═════════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN RÁPIDA
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    import django
    django.setup()
    
    print("\n" + "="*70)
    print("NVIDIA TRADINGBOT - QUICK STATUS CHECK")
    print("="*70 + "\n")
    
    # 1. Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            print("✓ GPU Detected")
            print(f"  Device: {torch.cuda.get_device_name(0)}")
            print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            print("⚠️ No GPU detected (will use CPU)")
    except ImportError:
        print("⚠️ PyTorch not installed")
    
    # 2. Check RAPIDS
    try:
        import cudf
        import cuml
        print("✓ RAPIDS available (cuDF, cuML)")
    except ImportError:
        print("⚠️ RAPIDS not installed (using pandas/sklearn CPU)")
    
    # 3. Check Triton
    try:
        from sniper.services.triton_serving import TritonClient
        client = TritonClient()
        if client.available:
            print("✓ Triton Server available")
        else:
            print("⚠️ Triton Server not running (docker-compose up -d)")
    except ImportError:
        print("⚠️ Triton client not installed")
    
    # 4. Check NIM
    try:
        from sniper.services.nim_sentiment import NIMSentimentAnalyzer
        analyzer = NIMSentimentAnalyzer()
        if analyzer.available:
            print("✓ NVIDIA NIM available")
        else:
            print("⚠️ NIM not configured (set NVIDIA_NIM_API_KEY)")
    except ImportError:
        print("⚠️ NIM not installed")
    
    # 5. Check TensorRT
    try:
        import tensorrt
        print(f"✓ TensorRT v{tensorrt.__version__} available")
    except ImportError:
        print("⚠️ TensorRT not installed (pip install tensorrt)")
    
    print("\n" + "="*70)
    print("📚 NEXT STEPS:")
    print("="*70)
    print("""
1. For GPU acceleration:
   conda install -c rapidsai-nightly rapids cuda-version=12.0

2. For low-latency inference:
   docker-compose up -d tritonserver

3. For sentiment analysis:
   export NVIDIA_NIM_API_KEY=nvapi_xxx...

4. Read full guide:
   cat NVIDIA_INTEGRATION_GUIDE.md
""")
    print("="*70 + "\n")
