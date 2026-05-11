# AmaroDocumentación - Arquitectura Completa de SniperBot v6.2 (Grado Institucional) 🤖📊

¡Qué tal Amaro! Este documento es el manual técnico definitivo del **SniperBot v6.2**. Resume el salto cuántico que dimos, pasando de un simple script de señales a un ecosistema de inversión cuantitativa (Quant Trading) con su propio "feedback loop" y escudos dinámicos.

A continuación, la radiografía total del algoritmo que tenemos activo:

---

## 0. Entorno de Despliegue (Setup Rápido para Amaro) 💻
Para que puedas clonar y correr este proyecto en tu propia máquina (con tu propia cuenta de Antigravity o manual), necesitas configurar el ecosistema exacto. Aquí tienes el mapa:

**Requisitos Base:**
*   **Python:** Versión `3.12` (Obligatorio para compatibilidad matemática).
*   **Terminal:** Windows PowerShell o CMD (se asume SO Windows por MetaTrader 5).
*   **Broker:** Tener instalada y abierta la terminal nativa de MetaTrader 5.

**Instalación de Dependencias (Pégalo en tu terminal):**
```bash
# 1. Crear y activar tu entorno virtual (opcional pero recomendado)
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar el núcleo web y de conexión
pip install django==5.0.3 MetaTrader5

# 3. Instalar el motor de procesamiento matemático
pip install pandas numpy pandas-ta scikit-learn joblib

# 4. Instalar el Ensamble de Inteligencia Artificial y Optimizador
pip install lightgbm xgboost catboost optuna
```

**Parámetros de Arranque:**
Una vez configurado, abres dos terminales simultáneas en la carpeta raíz del proyecto:
1.  **Terminal 1 (Para el Dashboard Institucional):** `python manage.py runserver`
2.  **Terminal 2 (Para el Bot Francotirador):** `python manage.py runbot --simbolos EURUSD GBPUSD USDJPY XAUUSD --intervalo 60`

---

## 1. El Ecosistema Cuantitativo (Visión General) 🌐
El bot ya no es un simple archivo. Está fragmentado en módulos altamente especializados:
*   **Radar y Extractor:** Cosechan la matemática bruta de MetaTrader 5.
*   **Cerebro y Validador:** Ensambles de Inteligencia Artificial que predicen futuros.
*   **Gestor de Riesgos:** Lógica de protección de capital estricta.
*   **Orquestador y Dashboard:** Interfaz web en Django para auditar el progreso.

## 2. Gestión de Riesgos y Geometría del Mercado 🛡️
Para evitar que el ruido del mercado nos pulverice la cuenta, implementamos reglas de Wall Street:
*   **Temporalidad Swing (H1):** El bot fue configurado para leer velas de **1 Hora (H1)**. Esto elimina las fluctuaciones engañosas de minutos y permite que la IA calcule macrotendencias confiables.
*   **Stop Loss Institucional (20 Pips):** Dejamos un rango de respiración lógico para el mercado H1.
*   **🛡️ El Escudo Break-Even (NUEVO):** Programamos un guardián dentro de `ejecutor_ordenes.py`. Si una operación avanza a tu favor el 50% de la ganancia esperada, el bot viaja a MT5 y **mueve tu Stop Loss al precio de entrada**. A partir de ese milisegundo, la operación tiene **Riesgo $0.00**.
*   **Seguro Anti-Ráfagas:** El bot revisa la Base de Datos de Django y el servidor de Axi. Si ya hay 1 operación de EURUSD abierta en cualquier lado, se bloquea y prohíbe abrir otra (límite: 1 trade activo por divisa).

## 3. Extracción Matemática Pura (Feature Engineering) 🔢
*   **Reparación del Underflow (Fix `uint64`):** El broker nos enviaba el volumen de transacciones bloqueado como un entero sin signo (`uint64`). Cuando la IA intentaba restar los volúmenes para calcular el OBV, el sistema crasheaba. Lo solucionamos convirtiendo esos datos brutos a variables de punto flotante (`float64`) antes del análisis.
*   **Los 31 Features:** El bot no lee el precio desnudo. Calcula simultáneamente: Distancias a la EMA de 200 periodos, Anchos de Banda de Bollinger, Momentum MACD, Zonas Estocásticas y Fuerzas de Volumen, normalizándolo en una escala legible para las redes neuronales (de -3 a 3).

## 4. Arquitectura de Shadow Trading (El Feedback Loop) 👻
El mayor logro del sistema. El bot aprende sin perder dinero usando 3 niveles de confianza:
*   **< 50% de Confianza:** La IA ignora por completo la oportunidad. Basura algorítmica.
*   **50% a 74% (SHADOW TRADE):** *"Me parece una buena entrada, pero no estoy 100% seguro"*. El bot no toca tu dinero real. Registra la operación solo en nuestra base de datos (Operación en papel / Fantasma). 
*   **≥ 75% (SNIPER):** La probabilidad es de grado "A". El bot solicita lotaje real y dispara en MT5.
*   **El Auditor Silencioso:** Cada 60 segundos, el bot revisa cómo le está yendo a sus "Fantasmas". Si el mercado real toca sus Take Profits virtuales, los marca como victorias. Esta experiencia nutre la IA sin que hayas arriesgado ni un centavo.

## 5. El Cerebro Algorítmico y Optuna 🧠⚡
*   **El Ensamble Triple:** Detrás del telón, tenemos tres inteligencias distintas votando por cada decisión: **LightGBM**, **XGBoost** y **CatBoost**.
*   **Limpieza de Inferencia:** Arreglamos las advertencias técnicas (UserWarnings) formateando los arrays crudos de numpy en DataFrames nativos de Pandas antes de pasárselos a LightGBM. La consola está ahora 100% silenciosa.
*   **Optuna (Auto-Optimizador):** En caso de datasets pequeños (las primeras semanas), Optuna inyecta "datos sintéticos" para que los árboles de decisión no colapsen, e intenta 10 configuraciones matemáticas distintas para escoger a los ganadores definitivos.

## 6. Dashboard Web Analítico (El Control Room) 🎛️
Reestructuramos el Dashboard HTML (`dashboard.html` y `views.py`) eliminando los colores de juguete y fases muertas para darle una estética sobria de Fondo de Inversión.
*   **Curva de Capital (Equity Curve):** Añadimos una gráfica con tecnología Chart.js completamente vinculada a nuestra base de datos. Cada operación ganadora o perdedora real dibuja el crecimiento o decremento de tu dinero.
*   **Radiografía de IA:** Una segunda gráfica horizontal que desglosa a la perfección "cómo piensa el bot".

## 7. Protocolo de Operación (Para el Usuario) 🕹️
La lógica de desarrollo terminó. Ahora tu único trabajo es de gestión:
1.  **Lunes a Viernes:** Arrancar en la terminal el comando `python manage.py runbot --simbolos EURUSD GBPUSD USDJPY XAUUSD --intervalo 60` y no tocarlo. Que el bot acumule operaciones fantasma y reales.
2.  **Sábado/Domingo:** Abrir el navegador en el Dashboard de Django, pulsar el botón de **REALIZAR ENTRENAMIENTO DE IA**. 
3.  **El Resultado:** El Orquestador mezclará los trades reales + trades fantasmas de la semana. Optuna ajustará las neuronas y el bot del lunes será muchísimo más letal e inteligente que el bot del viernes.

> *"La perfección de un algoritmo quantitativo no es acertar el 100% de las veces, es no quebrar nunca gracias a su gestión de riesgo, y evolucionar con el tiempo gracias al Shadow Learning."* 🎯
