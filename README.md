# Audio Steganography

Proyecto de esteganografía en audio con técnicas LSB, eco, espectro ensanchado
y codificación de fase.

## Requisitos

- Windows 10/11.
- Python 3.10 o superior. Se recomienda Python 3.12 o 3.13 de
  [python.org](https://www.python.org/downloads/windows/).

Las dependencias del proyecto están declaradas en
[pyproject.toml](./pyproject.toml):

- `numpy`
- `scipy`
- `matplotlib`
- `soundfile`

> **Importante:** aunque Python 3.14 puede ser compatible con el proyecto,
> algunas versiones de MSYS2 no tienen wheels precompilados de SciPy. En ese
> caso `pip` intenta compilar SciPy y se necesita un compilador Fortran. Para
> Windows, el Python oficial de python.org evita este problema en la mayoría
> de los casos.

## Crear el entorno virtual

Abre PowerShell en la carpeta raíz del proyecto:

```powershell
cd C:\Codigos\Cibersexo\Esteganografia\Investigacion\audioSteganography
```

Con Python 3.13 instalado desde python.org, crea un entorno virtual local:

```powershell
py -3.13 -m venv .venv
```

El Python oficial de Windows usa la carpeta `.venv\Scripts` para los
ejecutables.

## Instalar las dependencias

Instala el proyecto en modo editable. Esto instala automáticamente las
dependencias de `pyproject.toml`:

```powershell
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e .
```

El modo editable permite modificar el código del paquete sin reinstalarlo
después de cada cambio.

También están disponibles dependencias opcionales:

```powershell
& .\.venv\Scripts\python.exe -m pip install -e ".[extras]"
```

Estas incluyen `pydub`, `sounddevice` y `pandas`. Para convertir archivos MP3
con `pydub`, también es necesario instalar `ffmpeg` y agregarlo al `PATH`.

## Activar el entorno

En PowerShell:

```powershell
& .\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución del script de activación, usa el intérprete
del entorno directamente sin activarlo:

```powershell
& .\.venv\Scripts\python.exe --version
```

Para comprobar que se está usando el entorno correcto:

```powershell
& .\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
& .\.venv\Scripts\python.exe -c "import soundfile; print(soundfile.__version__)"
```

La segunda orden debe mostrar la versión instalada de `soundfile`.

## Flujo de trabajo de un experimento

El experimento se divide en tres pasos:

1. Crear el audio estego en memoria.
2. Pasar ese audio por un canal con pérdida.
3. Evaluar los bits recuperados con las métricas.

Las técnicas disponibles son:

- `lsb`: un bit por muestra PCM.
- `eco`: un bit por segmento de 4096 muestras.
- `espectro`: un bit por segmento de 4096 muestras.
- `fase`: un bit por segmento de 4096 muestras.

### Preparar las carpetas

Puedes organizar los archivos de cada prueba así:

```text
pruebas/
└── audios/
    ├── original.wav
    ├── estego_lsb.wav
    ├── estego_eco.wav
    ├── estego_espectro.wav
    ├── estego_fase.wav
    ├── mp3/
    │   └── estego_eco.mp3
    ├── whatsapp/
    │   └── estego_eco.ogg
    └── microfono/
        └── estego_eco.wav
```

Los archivos de `mp3/`, `whatsapp/` y `microfono/` son los archivos que se
obtienen después de aplicar cada canal. El programa no reproduce, envía ni
graba audio: solo lee el archivo indicado.

### Crear un archivo estego

Por ejemplo, para ocultar un mensaje con eco:

```python
import soundfile as sf

from estego.tecnicas import eco, lsb
from estego.utils import texto_a_bits

audio, fs = sf.read("pruebas/audios/original.wav", dtype="float32")
bits = texto_a_bits("ki ondá")
audio_estego = eco.ocultar(audio, bits, seg=eco.SEGMENTO, alfa=0.1)
sf.write("pruebas/audios/estego_eco.wav", audio_estego, fs)
```

Para cambiar de técnica, sustituye `eco` por `lsb`, `espectro` o `fase`.
Para LSB, lee el portador como `int16`:

```python
audio, fs = sf.read("pruebas/audios/original.wav", dtype="int16")
audio_estego = lsb.ocultar(audio, bits)
sf.write("pruebas/audios/estego_lsb.wav", audio_estego, fs)
```

### Ejecutar una evaluación

El ejecutor se llama desde la raíz del repositorio:

```powershell
& .\.venv\Scripts\python.exe -m pruebas.ejecutar_canal --help
```

La opción `--audio-recibido` debe apuntar al archivo que ya pasó por el canal.

#### Canal MP3

Convierte previamente el archivo estego a MP3 y luego evalúalo:

```powershell
& .\.venv\Scripts\python.exe -m pruebas.ejecutar_canal `
  --canal mp3 `
  --tecnica eco `
  --mensaje "ki ondá" `
  --audio-original .\pruebas\audios\original.wav `
  --audio-stego .\pruebas\audios\estego_eco.wav `
  --audio-recibido .\pruebas\audios\mp3\estego_eco.mp3 `
  --alfa 0.1
```

#### Canal WhatsApp

Envía manualmente el audio estego por WhatsApp, descarga el resultado y
colócalo en la carpeta de la prueba:

```powershell
& .\.venv\Scripts\python.exe -m pruebas.ejecutar_canal `
  --canal whatsapp `
  --tecnica eco `
  --mensaje "ki ondá" `
  --audio-original .\pruebas\audios\original.wav `
  --audio-stego .\pruebas\audios\estego_eco.wav `
  --audio-recibido .\pruebas\audios\whatsapp\estego_eco.ogg `
  --alfa 0.1
```

#### Canal parlante/micrófono

Realiza la reproducción y grabación manualmente. Guarda el resultado y
evalúalo indicando su ruta:

```powershell
& .\.venv\Scripts\python.exe -m pruebas.ejecutar_canal `
  --canal microfono `
  --tecnica eco `
  --mensaje "ki ondá" `
  --audio-original .\pruebas\audios\original.wav `
  --audio-stego .\pruebas\audios\estego_eco.wav `
  --audio-recibido .\pruebas\audios\microfono\estego_eco.wav `
  --alfa 0.1
```

Para evaluar otra técnica, cambia `--tecnica` por `lsb`, `espectro` o `fase`.
En LSB se recomienda añadir `--sin-alinear`, porque normalizar o alinear el
audio altera las muestras enteras y puede destruir los bits menos
significativos:

```powershell
& .\.venv\Scripts\python.exe -m pruebas.ejecutar_canal `
  --canal whatsapp `
  --tecnica lsb `
  --mensaje "ki ondá" `
  --audio-original .\pruebas\audios\original.wav `
  --audio-stego .\pruebas\audios\estego_lsb.wav `
  --audio-recibido .\pruebas\audios\whatsapp\estego_lsb.wav `
  --sin-alinear
```

### Resultado de las métricas

Cada ejecución imprime:

```text
ber: ...
accuracy_bits: ...
recuperacion_exacta: ...
snr_db: ...
capacidad_bps: ...
tasa_informacion_efectiva_bps: ...
```

- `ber`: proporción de bits incorrectos.
- `accuracy_bits`: proporción de bits correctos.
- `recuperacion_exacta`: indica si todos los bits fueron recuperados.
- `snr_db`: degradación causada por ocultar el mensaje.
- `capacidad_bps`: capacidad teórica de la técnica.
- `tasa_informacion_efectiva_bps`: información útil después de considerar la
  BER.

También se pueden usar las funciones directamente desde Python:

```python
from estego.metricas import evaluar_prueba

resultado = evaluar_prueba(
    bits_originales,
    bits_recuperados,
    audio_original,
    audio_estego,
    fs,
    muestras_por_bit=eco.SEGMENTO,
)
print(resultado.como_dict())
```

## Solución al error `No module named 'soundfile'`

El error:

```text
ModuleNotFoundError: No module named 'soundfile'
```

significa que `soundfile` no está instalado en el intérprete que ejecutó el
script. No es suficiente instalarlo en otro Python del sistema. Comprueba el
intérprete y reinstala la dependencia en el entorno del proyecto:

```powershell
& .\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
& .\.venv\Scripts\python.exe -m pip install soundfile
& .\.venv\Scripts\python.exe .\estego\tecnicas\lsb.py
```

## Si se usa MSYS2

El comando `C:\msys64\mingw64\bin\python.exe -m pip install -e .` puede
descargar el código fuente de NumPy/SciPy en lugar de un wheel. SciPy requiere
Fortran para compilarse, por lo que la instalación puede terminar con:

```text
ERROR: Unknown compiler(s)
```

La opción recomendada es instalar Python 3.12 o 3.13 desde python.org y
recrear `.venv` con ese intérprete. Si se desea continuar con MSYS2, hay que
instalar las dependencias nativas mediante `pacman` y configurar el toolchain
de compilación de MSYS2; no se recomienda mezclar paquetes `pip` de Windows
con los paquetes del entorno MSYS2.

## Recrear el entorno

Si el entorno queda inconsistente, elimínalo y créalo nuevamente. Esta acción
solo elimina el entorno virtual generado, no el código del proyecto:

```powershell
Remove-Item -Recurse -Force .\.venv
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
```

El directorio `.venv` está excluido del control de versiones y no debe
subirse al repositorio.
