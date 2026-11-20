# Audio Steganography

Herramienta de investigación y experimentación en **esteganografía de audio** y evaluación de robustez frente a canales con pérdida (compresión MP3, transcodificación de voz en WhatsApp y grabación acústica por micrófono).

---

## 🎯 Técnicas soportadas

1. **LSB (*Least Significant Bit*):** Inserción en el bit menos significativo de muestras PCM enteras (`int16`). Muy alta fidelidad perceptual (SNR > 100 dB), pero no sobrevive a canales con pérdida.
2. **Eco Hiding:** Adición de ecos sutiles con diferentes retardos temporales ($d_0$ y $d_1$) decodificables mediante análisis cepstral.
3. **Espectro Ensanchado (DSSS):** Modulación de los bits mediante una secuencia pseudoaleatoria (código PN) distribuida a lo largo de un segmento espectral.
4. **Codificación de Fase:** Modificación de la fase de las componentes frecuenciales en una banda seleccionada (1 kHz – 3 kHz).

---

## 🚀 Inicio rápido (Instalación)

### 1. Requisitos
* Windows 10/11 (o Linux/macOS).
* Python 3.10 o superior (recomendado 3.12 o 3.13).

### 2. Configurar el entorno virtual
Abre PowerShell en la raíz del proyecto y ejecuta:

```powershell
# Crear el entorno virtual
py -m venv .venv

# Activar el entorno (PowerShell en Windows)
.\.venv\Scripts\Activate.ps1

# Actualizar pip e instalar dependencias
pip install --upgrade pip
pip install -e .
```

> **Nota:** Si PowerShell bloquea scripts de activación (`Activate.ps1`), puedes ejecutar directamente usando `.\.venv\Scripts\python.exe` en lugar de `python`.

---

## ⚡ Comandos principales (Uso directo)

El repositorio cuenta con herramientas diseñadas tanto para investigación masiva como para **demostraciones en vivo** en presentaciones y exposiciones.

---

### 🎤 1. Demostración en vivo (Para exposiciones)

Puedes ocultar y recuperar mensajes en vivo de dos formas: **Modo Interactivo** (te va preguntando paso a paso) o mediante **Línea de comandos directa**.

#### A. Ocultar un mensaje en vivo:
```powershell
# Modo interactivo (te pedirá la técnica y el mensaje en pantalla):
python -m estego.ocultar

# O directo con parámetros:
python -m estego.ocultar --tecnica lsb --mensaje "Mensaje secreto para la expo" --salida demo_lsb.wav
python -m estego.ocultar --tecnica espectro --mensaje "Clave segura 2026" --salida demo_esp.wav
```

#### B. Extraer y recuperar el mensaje en vivo:
```powershell
# Modo interactivo:
python -m estego.extraer

# O directo indicando el audio generado:
python -m estego.extraer --tecnica lsb --audio demo_lsb.wav --mensaje-referencia "Mensaje secreto para la expo"
python -m estego.extraer --tecnica espectro --audio demo_esp.wav --caracteres 17
```

*(Si instalaste con `pip install -e .`, también puedes usar los comandos directos `estego-ocultar` y `estego-extraer`).*

---

### 📊 2. Evaluar todas las métricas en un solo comando
Ejecuta la evaluación cruzada de todas las técnicas y canales (imprime una tabla comparativa con BER, Accuracy, SNR y Tasa Efectiva):

```powershell
python -m pruebas.evaluar_todos
```

*Si deseas evaluar un solo canal:*
```powershell
python -m pruebas.evaluar_todos --canal mp3
python -m pruebas.evaluar_todos --canal whatsapp
python -m pruebas.evaluar_todos --canal microfono
```

---

### 📝 3. Desencriptar y guardar mensajes en archivos `.txt` individuales
Para extraer los datos ocultos de todos los audios y generar un reporte de texto por cada archivo analizado:

```powershell
python -m pruebas.desencriptar_audios
```

Los reportes se guardan automáticamente en la carpeta **`Resultados/mensajes_txt/`**:
* Un archivo `.txt` individual para cada audio analizado (ej. `mp3_stego_eco_mp3_desencriptado.txt`).
* Un archivo consolidado: `00_RESUMEN_TODOS.txt`.

---

### 🌐 4. Benchmark Opus vía FFmpeg (12, 16, 24, 32 kbps) vs WhatsApp Real
Evalúa automáticamente el códec Opus con 1024 bits y calcula los **Intervalos de Confianza de Wilson al 95%** para la BER:

```powershell
python -m pruebas.canal_opus
```
*(Guarda el reporte detallado en `Resultados/comparativa_opus_vs_whatsapp.txt`).*

---

### 📉 5. Generar Gráfica de Compromiso (Trade-off BER vs Alfa en MP3 64k)
Genera automáticamente la curva que demuestra el compromiso entre **Imperceptibilidad (SNR)** y **Robustez (BER)**:

```powershell
python -m pruebas.graficar_tradeoff
```
*(Guarda la imagen en alta resolución en `Resultados/grafica_ber_vs_alfa.png`).*

---

### 🎓 6. Guía completa para la Exposición
Consulta el documento **`Resultados/GUIA_EXPOSICION.md`** para tener:
* Estructura recomendada de las diapositivas.
* Catálogo oficial de metadatos (frecuencias, duraciones, bitrates, dispositivos, volúmenes y distancias).
* Respuestas a las preguntas difíciles del jurado.

---

### 🔬 7. Evaluación individual de un audio específico (`ejecutar_canal.py`)

Para evaluar un archivo particular pasando por el alineador y extractor:

```powershell
python -m pruebas.ejecutar_canal `
  --canal <mp3|whatsapp|microfono> `
  --tecnica <lsb|eco|espectro|fase> `
  --mensaje <"texto" o "secuencia_bits"> `
  --audio-original <ruta_original.wav> `
  --audio-stego <ruta_stego.wav> `
  --audio-recibido <ruta_audio_canal>
```

#### Ejemplos listos para copiar y pegar:

**Canal MP3:**
```powershell
# LSB (Mensaje: "ki ondá")
python -m pruebas.ejecutar_canal --canal mp3 --tecnica lsb --mensaje "ki ondá" --audio-original .\pruebas\audios\original.wav --audio-stego .\pruebas\audios\stego_lsb.wav --audio-recibido .\pruebas\audios\mp3\stego_lsb_mp3.mp3

# Espectro Ensanchado (Mensaje: "01010101")
python -m pruebas.ejecutar_canal --canal mp3 --tecnica espectro --mensaje "01010101" --audio-original .\pruebas\audios\original.wav --audio-stego .\pruebas\audios\stego_espectro.wav --audio-recibido .\pruebas\audios\mp3\stego_espectro_mp3.mp3
```

**Canal WhatsApp:**
```powershell
python -m pruebas.ejecutar_canal --canal whatsapp --tecnica fase --mensaje "01010101" --audio-original .\pruebas\audios\original.wav --audio-stego .\pruebas\audios\stego_fase.wav --audio-recibido .\pruebas\audios\whatsapp\stego_fase_whatsapp.ogg
```

**Canal Micrófono/Parlante:**
```powershell
python -m pruebas.ejecutar_canal --canal microfono --tecnica espectro --mensaje "01010101" --audio-original .\pruebas\audios\original.wav --audio-stego .\pruebas\audios\stego_espectro.wav --audio-recibido .\pruebas\audios\microfono\stego_espectro_micro.ogg
```

---

## 🛠️ Cómo ocultar un mensaje nuevo en un audio

Puedes usar las técnicas directamente desde scripts o interactivo en Python:

```python
import soundfile as sf
from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import texto_a_bits

# 1. Mensaje a ocultar
mensaje = "ki ondá"
bits = texto_a_bits(mensaje)

# 2. Para LSB (requiere audio entero int16):
audio_pcm, fs = sf.read("pruebas/audios/original.wav", dtype="int16")
stego_lsb = lsb.ocultar(audio_pcm, bits)
sf.write("pruebas/audios/stego_lsb.wav", stego_lsb, fs)

# 3. Para técnicas transformadas (Eco, Espectro, Fase en float32):
audio_flt, fs = sf.read("pruebas/audios/original.wav", dtype="float32")

# Eco
stego_eco = eco.ocultar(audio_flt, bits, alfa=0.1)
sf.write("pruebas/audios/stego_eco.wav", stego_eco, fs)

# Espectro Ensanchado (clave pseudoaleatoria)
stego_esp = espectro.ocultar(audio_flt, bits, clave=1234, alfa=0.02)
sf.write("pruebas/audios/stego_espectro.wav", stego_esp, fs)

# Fase
stego_fase = fase.ocultar(audio_flt, bits, fs=fs)
sf.write("pruebas/audios/stego_fase.wav", stego_fase, fs)
```

---

## 📊 Interpretación de las Métricas

Cada prueba evalúa seis métricas de calidad y fiabilidad:

| Métrica | Descripción | Valor ideal |
| :--- | :--- | :--- |
| **`ber`** (*Bit Error Rate*) | Proporción de bits erróneos ($0.0$ a $1.0$). Si es $\approx 0.5$, la salida es puro ruido aleatorio. | **`0.0`** |
| **`accuracy_bits`** | Porcentaje de bits recuperados correctamente ($1.0 - \text{BER}$). | **`1.0`** (100%) |
| **`recuperacion_exacta`** | `True` si el mensaje se recuperó íntegro (cero errores); `False` si hubo algún bit cambiado. | **`True`** |
| **`snr_db`** (*Signal-to-Noise Ratio*) | Mide la imperceptibilidad del mensaje oculto comparado con el portador base. Valores altos indican que la modificación es inaudible. | **$> 30\text{ dB}$** (LSB: $> 100\text{ dB}$) |
| **`capacidad_bps`** | Tasa nominal de inyección de información del esquema ($f_s / \text{muestras\_por\_bit}$). | Mayor capacidad |
| **`tasa_informacion_efectiva_bps`** | Capacidad real transmitida según el modelo de Shannon (Canal Binario Simétrico). Si $\text{BER} \ge 0.5$, cae a **0.0 bps**. | Próximo a la capacidad |

> **Nota teórica sobre LSB:** LSB es una técnica temporal espacial que no resiste compresión psicoacústica con pérdida (MP3 o WhatsApp Opus) ni perturbaciones acústicas (micrófono). En estos canales, el BER esperado es $\approx 0.5$ (equivalente a ruido blanco equiprobable) y la tasa efectiva es $0.0\text{ bps}$. Para canales degradados, se deben emplear técnicas robustas como **Espectro Ensanchado** o **Fase**.

---

## 📁 Estructura del Proyecto

```text
audioSteganography/
├── estego/                       # Módulo principal de la librería
│   ├── tecnicas/                 # Implementaciones: lsb, eco, espectro, fase
│   ├── metricas.py               # Algoritmos de alineación, SNR, BER y Shannon
│   └── utils.py                  # Conversión de bits, mono y normalización
├── pruebas/
│   ├── audios/                   # Audios de prueba
│   │   ├── original.wav          # Audio portador original limpio
│   │   ├── stego_*.wav           # Audios estego generados en WAV
│   │   ├── mp3/                  # Audios procesados por compresión MP3
│   │   ├── whatsapp/             # Audios procesados por la red de WhatsApp (.ogg)
│   │   └── microfono/            # Grabaciones acústicas ambiente (.ogg)
│   ├── ejecutar_canal.py         # CLI para evaluar una prueba individual
│   ├── evaluar_todos.py          # Script automático para evaluar todas las pruebas
│   └── desencriptar_audios.py    # Script para extraer mensajes y generar .txt
└── Resultados/
    ├── Resultados.docx           # Documento de reporte final
    └── mensajes_txt/             # Reportes .txt individuales generados
```

---

## ❓ Preguntas frecuentes / Solución de problemas

* **Error: `No module named 'soundfile'`:**  
  Asegúrate de ejecutar con el entorno virtual activo o invocando `.\.venv\Scripts\python.exe`.
* **Error de PowerShell con scripts desactivados (`Activate.ps1`):**  
  Ejecuta PowerShell como administrador y corre: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, o ejecuta directamente con el binario del entorno virtual: `.\.venv\Scripts\python.exe`.
