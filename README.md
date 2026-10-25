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

## Ejecutar una técnica

Desde la raíz del proyecto:

```powershell
& .\.venv\Scripts\python.exe .\estego\tecnicas\lsb.py
```

También se puede ejecutar con el entorno activado:

```powershell
python .\estego\tecnicas\lsb.py
```

Las rutas de audio usadas por cada técnica son relativas a la carpeta desde la
que se ejecuta el comando. Por tanto, ejecuta los scripts desde la raíz del
repositorio o actualiza la ruta del archivo de audio en el script según la
ubicación real del archivo.

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
