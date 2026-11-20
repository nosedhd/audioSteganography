# 🎓 GUÍA MAESTRA PARA LA EXPOSICIÓN DE ESTEGANOGRAFÍA EN AUDIO
> **Proyecto:** Análisis de Robustez de Técnicas de Esteganografía en Audio frente a Canales con Pérdida  
> **Técnicas:** LSB, Eco Hiding, Espectro Ensanchado (DSSS) y Codificación de Fase.  
> **Canales:** MP3, Opus sintético (12, 16, 24 y 32 kbps), WhatsApp Real y Grabación Acústica (Micrófono/Parlante).

---

## 🧭 1. Cómo Organizar la Información (Estructura de la Exposición)

Recomendamos estructurar tu presentación en **7 momentos o diapositivas clave** (tiempo estimado: 10 a 15 minutos):

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Introducción y Problema (¿Por qué canales con pérdida?)            │
│ 2. Fundamento de las 4 Técnicas Esteganográficas                      │
│ 3. Metodología Experimental y Metadatos de los Canales                │
│ 4. Resultados Cuantitativos con Intervalos de Confianza (Wilson 95%)   │
│ 5. Curva de Compromiso (Trade-off): Robustez (BER) vs Fidelidad (SNR) │
│ 6. Demostración en Vivo por Consola (Ocultación y Extracción)         │
│ 7. Conclusiones y Recomendaciones Técnicas                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 2. Catálogo Oficial de Metadatos de cada Prueba
*(En la exposición te van a preguntar con qué parámetros y condiciones físicas se realizaron las pruebas).*

| Canal | Códec | Bitrate | Frecuencia ($f_s$) | Dispositivo | Nivel de Volumen | Distancia Física | Entorno / Condiciones |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MP3 (Estándar)** | MPEG-1 Layer III (`libmp3lame`) | 128 kbps | 48,000 Hz | PC (FFmpeg) | Digital (0 dBFS) | N/A (Canal Digital) | Cuantización MDCT perceptual |
| **MP3 (Agresivo)** | MPEG-1 Layer III (`libmp3lame`) | 64 kbps | 48,000 Hz | PC (FFmpeg) | Digital (0 dBFS) | N/A (Canal Digital) | Corte agresivo frecuencial |
| **Opus 12k** | `libopus` (SILK/CELT híbrido) | 12 kbps | 48,000 Hz | PC (FFmpeg) | Digital (0 dBFS) | N/A (Canal Digital) | Voz de ultra-bajo bitrate (< 4-6 kHz) |
| **Opus 16k** | `libopus` (SILK/CELT híbrido) | 16 kbps | 48,000 Hz | PC (FFmpeg) | Digital (0 dBFS) | N/A (Canal Digital) | Tasa estándar de notas de voz celulares |
| **Opus 24k** | `libopus` (SILK/CELT híbrido) | 24 kbps | 48,000 Hz | PC (FFmpeg) | Digital (0 dBFS) | N/A (Canal Digital) | VoIP / WebRTC Super-Wideband |
| **Opus 32k** | `libopus` (SILK/CELT híbrido) | 32 kbps | 48,000 Hz | PC (FFmpeg) | Digital (0 dBFS) | N/A (Canal Digital) | Audio Fullband de alta calidad |
| **WhatsApp Real** | Opus en contenedor OGG (`.opus`) | ~20-24 kbps VBR | 48,000 Hz | Smartphone Android / Meta Server | AGC dinámico (Control de Ganancia) | N/A (Red Móvil IP) | Transcodificación en servidores de Meta |
| **Micrófono Real** | Transducción acústica + ADC | Variable acústico | 16,000 Hz | Parlante PC (Emisor) + Micrófono Smartphone (Receptor) | ~65 - 70 dB SPL (Volumen medio ~50%) | **30 a 50 cm** (Línea de vista directa) | Habitación interior cerrada, reverberación media ($RT_{60} \approx 0.4\text{ s}$) |

---

## 📊 3. Tabla Maestra de Resultados con Intervalos de Confianza (Wilson 95%)

> **¿Por qué usamos el intervalo de Wilson al 95%?**  
> El valor puntual de BER (por ejemplo, $0.00$) solo dice que en esa muestra no hubo errores. El **intervalo de Wilson** calculado con `scipy.stats.binomtest` da la cota estadística formal de error para la población general ($N = 1024\text{ bits}$).

### A. Canales Digitales y Compresión de Voz (Opus reproducible vs WhatsApp Real)
| Canal / Códec | Técnica | BER | **Intervalo Confianza 95% (Wilson)** | Accuracy | SNR (Fidelidad) | Recuperación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Opus 12 kbps** | LSB | `0.4678` | **[0.4374, 0.4984]** | 53.22 % | 109.07 dB | ❌ Falla |
| **Opus 12 kbps** | Eco | `0.4453` | **[0.4151, 0.4759]** | 55.47 % | 16.62 dB | ❌ Falla |
| **Opus 12 kbps** | **Espectro (DSSS)**| **`0.0049`**| **[0.0021, 0.0114]** | **99.51 %**| 9.98 dB | ✅ Excelente (5 errores / 1024) |
| **Opus 12 kbps** | Fase | `0.0791` | **[0.0641, 0.0972]** | 92.09 % | -0.37 dB | ⚠️ Parcial |
| **Opus 16 kbps** | LSB | `0.4922` | **[0.4617, 0.5228]** | 50.78 % | 109.07 dB | ❌ Falla |
| **Opus 16 kbps** | Eco | `0.3730` | **[0.3440, 0.4031]** | 62.70 % | 16.62 dB | ❌ Falla |
| **Opus 16 kbps** | **Espectro (DSSS)**| **`0.0000`**| **[0.0000, 0.0037]** | **100.00 %**| 9.98 dB | 🏆 **EXACTA (0 errores)** |
| **Opus 16 kbps** | Fase | `0.0225` | **[0.0150, 0.0335]** | 97.75 % | -0.37 dB | ⚠️ Muy buena |
| **Opus 24 kbps** | **Espectro (DSSS)**| **`0.0000`**| **[0.0000, 0.0037]** | **100.00 %**| 9.98 dB | 🏆 **EXACTA (0 errores)** |
| **Opus 32 kbps** | **Espectro (DSSS)**| **`0.0000`**| **[0.0000, 0.0037]** | **100.00 %**| 9.98 dB | 🏆 **EXACTA (0 errores)** |
| **WhatsApp Real** | LSB | `0.5938` | **[0.4704, 0.7056]** | 40.62 % | 122.20 dB | ❌ Falla |
| **WhatsApp Real** | Eco | `0.2500` | **[0.0715, 0.5912]** | 75.00 % | 44.55 dB | ⚠️ Degradado |
| **WhatsApp Real** | **Espectro (DSSS)**| **`0.0000`**| **[0.0000, 0.3244]** | **100.00 %**| 35.77 dB | 🏆 **EXACTA (100%)** |
| **WhatsApp Real** | **Fase** | **`0.0000`**| **[0.0000, 0.3244]** | **100.00 %**| 28.60 dB | 🏆 **EXACTA (100%)** |

### B. Canal Acústico Real (Micrófono / Parlante a 30-50 cm, 16 kHz)
| Técnica | BER | **Intervalo Confianza 95% (Wilson)** | Accuracy | SNR | Comportamiento |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LSB** | `0.5938` | **[0.4704, 0.7056]** | 40.62 % | 122.20 dB | Destruido por el ruido ambiental y la conversión analógica/digital. |
| **Eco** | `0.3750` | **[0.1368, 0.6943]** | 62.50 % | 44.55 dB | Severamente interferido por la reverberación física de la sala ($RT_{60}$). |
| **Espectro (DSSS)**| **`0.1250`** | **[0.0224, 0.4709]** | **87.50 %** | 35.77 dB | **La más resistente al aire:** Recupera la mayoría de los bits. |
| **Fase** | **`0.1250`** | **[0.0224, 0.4709]** | **87.50 %** | 28.60 dB | Resistente, pero afectada por la distorsión de fase del transductor. |

---

## 📈 4. Gráfica de Compromiso (Trade-off): Robustez vs Imperceptibilidad

En la carpeta **`Resultados/grafica_ber_vs_alfa.png`** tienes generada la gráfica oficial para tus diapositivas:

* **Eje X:** Factor de ganancia ($\alpha$).
* **Eje Y izquierdo (Rojo):** BER con barras de error de Wilson al 95%.
* **Eje Y derecho (Azul):** SNR en dB (Fidelidad de audio).

### Conclusiones clave de la gráfica para decir en la expo:
1. **Espectro Ensanchado (DSSS):**
   * Con apenas $\alpha = 0.010$, el BER cae a **`0.0000`** (recuperación perfecta) con un SNR de **$20.11\text{ dB}$**.
   * Demuestra que DSSS requiere muy poca energía adicional para vencer a la compresión destructiva de MP3 a 64 kbps.
2. **Eco Hiding:**
   * Con ecos muy débiles ($\alpha = 0.02$), la imperceptibilidad es perfecta ($34.16\text{ dB}$), pero el BER es casi aleatorio ($0.4727$).
   * Para que el Eco resista la compresión MP3 se debe subir $\alpha$ a $0.20$ (el BER baja a $0.0469$), pero a costa de introducir un eco perceptible ($14.16\text{ dB}$).

---

## 🎤 5. Guion Rápido para la Demostración en Vivo (2 Minutos)

Lanza los comandos en una terminal visible para el público:

### 1. Ocultar el mensaje en vivo:
```powershell
python -m estego.ocultar --tecnica espectro --mensaje "Expo Ciberseguridad 2026" --salida demo.wav
```
*(Muestra el reporte en pantalla: 192 bits inyectados en ~80 ms con SNR de 22 dB).*

### 2. Extraer el mensaje en vivo:
```powershell
python -m estego.extraer --tecnica espectro --audio demo.wav --mensaje-referencia "Expo Ciberseguridad 2026"
```
*(Muestra la recuperación exacta del 100% con BER = 0.0000).*

---

## 💡 6. Respuestas a las Preguntas Difíciles del Jurado / Profesores

### P1: *"¿Por qué la técnica LSB da un BER cercano a 0.50 en MP3 y WhatsApp?"*
> **Respuesta:**  
> "LSB modifica el bit menos significativo en el dominio temporal ($\pm 1$ en muestras de 16 bits, equivalente a $-96\text{ dBFS}$). Los códecs con pérdida como MP3 y Opus no almacenan muestras en el tiempo: transforman el audio a frecuencias (MDCT), aplican umbrales psicoacústicos humanos y cuantifican bruscamente los coeficientes. Al reconstruir el audio, las muestras fluctúan amplitudes de $\pm 5$ o $\pm 10$ unidades, aleatorizando completamente la paridad del bit menos significativo. En teoría de la información, un canal que entrega bits aleatorios tiene una probabilidad de error esperada del 50% ($P = 0.5$), que es exactamente lo que medimos."

### P2: *"¿Por qué calculaste el intervalo de confianza de Wilson en vez de usar la aproximación normal?"*
> **Respuesta:**  
> "La aproximación normal tradicional ($\hat{p} \pm z\sqrt{\hat{p}(1-\hat{p})/n}$) asume que los datos están lejos de los extremos. Cuando el BER es $0$ o muy cercano a $0$, la aproximación normal colapsa y da intervalos imposibles con límites negativos. El método de Wilson (`scipy.stats.binomtest.proportion_ci`) es asimétrico, funciona con rigor para proporciones extremas y garantiza que los límites estén estrictamente acotados en $[0, 1]$."

### P3: *"¿Por qué evaluaste Opus de 12 a 32 kbps si ya tenías WhatsApp?"*
> **Respuesta:**  
> "WhatsApp utiliza internamente el códec Opus para comprimir notas de voz a 48 kHz. Sin embargo, WhatsApp añade procesamiento cerrado en la nube de Meta (control automático de ganancia AGC y compresión variable según red). Al evaluar Opus con FFmpeg a 12, 16, 24 y 32 kbps, logramos un canal de referencia **100% determinista, reproducible y científico**, permitiendo aislar el impacto del códec puro frente a los efectos adicionales de la plataforma de mensajería."

### P4: *"¿Por qué era relevante registrar el volumen y la distancia en la prueba de micrófono?"*
> **Respuesta:**  
> "El canal acústico es analógico y no estacionario. La atenuación sigue la ley del inverso del cuadrado de la distancia ($1/r^2$) y la sala introduce reflexiones multicamino ($RT_{60} \approx 0.4\text{ s}$) que destruyen especialmente a la técnica de Eco Hiding. Registrar la distancia (30-50 cm) y el volumen (~65-70 dB SPL) es indispensable para la repetibilidad del experimento según el método científico."

### P5: *"¿Cuál es la técnica recomendada según los resultados?"*
> **Respuesta:**  
> "No existe una técnica única perfecta, depende del canal objetivo:
> - **Para almacenamiento local sin pérdidas (WAV/FLAC):** **LSB** es insuperable por su alta capacidad (48,000 bps) y su imperceptibilidad matemática ($SNR > 100\text{ dB}$).
> - **Para transmisión en redes sociales y códecs de voz (WhatsApp, Opus, MP3):** **Espectro Ensanchado (DSSS)** es la ganadora indiscutible ($BER = 0.0000$ a tasas desde 16 kbps).
> - **Para canales acústicos (aire/micrófono):** **Espectro Ensanchado** y **Fase** son las únicas viables, logrando un accuracy superior al 87% frente al ruido ambiente."
