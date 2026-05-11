import os
from pathlib import Path

# Definición de la estructura y contenido
files = {
    "requirements.txt": "django>=4.2\nMetaTrader5>=5.0.45\npandas>=2.0\nnumpy>=1.24\nscikit-learn>=1.3\njoblib>=1.3",
    "core/settings.py": "# Configuración básica de Django\n# Asegúrate de añadir 'sniper' a INSTALLED_APPS",
    "core/urls.py": "from django.contrib import admin\nfrom django.urls import path, include\n\nurlpatterns = [\n    path('admin/', admin.site.urls),\n    path('', include('sniper.urls')),\n]",
    "sniper/models.py": "from django.db import models\n\nclass ConfiguracionBot(models.Model):\n    bot_encendido = models.BooleanField(default=True)\n    ia_encendida = models.BooleanField(default=False)\n    ultima_precision_ia = models.FloatField(default=0.0)\n\nclass TradeHistory(models.Model):\n    simbolo = models.CharField(max_length=20)\n    resultado = models.CharField(max_length=10) # PROFIT/SL\n    fecha = models.DateTimeField(auto_now_add=True)",
    "sniper/services/radar_mercado.py": "import pandas as pd\nimport MetaTrader5 as mt5\n\nclass RadarMercado:\n    def obtener_datos(self, simbolo):\n        # Lógica de EMA 200, 50 y RSI 21\n        pass",
    "sniper/services/cerebro_analitico.py": "class CerebroAnalitico:\n    def evaluar(self, datos):\n        # Sistema de puntuación 8/10\n        pass",
    "sniper/ai_module/entrenador.py": "def entrenar_modelo_historico():\n    # Lógica de Random Forest\n    pass",
    "sniper/templates/dashboard.html": "<html><body><h1>Dashboard SniperBot</h1></body></html>",
}

def build():
    for path_str, content in files.items():
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print("✅ ¡Estructura de SniperBot creada con éxito!")

if __name__ == "__main__":
    build()