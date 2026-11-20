"""Script para desencriptar (extraer mensaje) de todos los audios en pruebas/audios
y guardar el resultado de cada uno en un archivo .txt independiente.
"""

import argparse
import subprocess
import tempfile
from pathlib import Path
import soundfile as sf
import numpy as np

from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import bits_a_texto, texto_a_bits
from estego.metricas import normalizar_y_alinear

CARPETA_AUDIOS = Path("pruebas/audios")
CARPETA_SALIDA = Path("Resultados/mensajes_txt")

MENSAJE_POR_DEFECTO = "ki ondá"

# Lista de audios a procesar: (ruta_relativa, tecnica, referencia_stego_para_alinear)
AUDIOS = [
    # Audios estego base (WAV sin canal de pérdida)
    ("stego_lsb.wav", "lsb", None),
    ("stego_eco.wav", "eco", None),
    ("stego_espectro.wav", "espectro", None),
    ("stego_fase.wav", "fase", None),

    # Canal MP3
    ("mp3/stego_lsb.mp3", "lsb", "stego_lsb.wav"),
    ("mp3/stego_eco.mp3", "eco", "stego_eco.wav"),
    ("mp3/stego_espectro.mp3", "espectro", "stego_espectro.wav"),
    ("mp3/stego_fase.mp3", "fase", "stego_fase.wav"),

    # Canal WhatsApp
    ("whatsapp/stego_lsb.ogg", "lsb", "stego_lsb.wav"),
    ("whatsapp/stego_eco.ogg", "eco", "stego_eco.wav"),
    ("whatsapp/stego_espectro.ogg", "espectro", "stego_espectro.wav"),
    ("whatsapp/stego_fase.ogg", "fase", "stego_fase.wav"),

    # Canal Micrófono
    ("microfono/Lsbmicro.m4a", "lsb", "stego_lsb.wav"),
    ("microfono/Ecomicro.m4a", "eco", "stego_eco.wav"),
    ("microfono/Espectromicro.m4a", "espectro", "stego_espectro.wav"),
    ("microfono/Fasemicro.m4a", "fase", "stego_fase.wav"),
]


def extraer_de_audio(audio: np.ndarray, fs: int, tecnica: str, n_bits: int) -> str:
    """Extrae n_bits de un audio según la técnica esteganográfica."""
    if tecnica == "lsb":
        return lsb.extraer(audio, n_bits)
    elif tecnica == "eco":
        return eco.extraer(audio, n_bits)
    elif tecnica == "espectro":
        return espectro.extraer(audio, n_bits, clave=1234)
    elif tecnica == "fase":
        return fase.extraer(audio, n_bits, fs=fs)
    raise ValueError(f"Técnica desconocida: {tecnica}")


def leer_audio(ruta: Path, dtype: str) -> tuple[np.ndarray, int, Path | None]:
    if ruta.suffix.lower() != ".m4a":
        audio, fs = sf.read(ruta, dtype=dtype)
        return audio, fs, None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporal:
        ruta_temporal = Path(temporal.name)
    resultado = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(ruta),
         "-vn", "-acodec", "pcm_s16le", str(ruta_temporal)],
        capture_output=True,
        text=True,
    )
    if resultado.returncode != 0:
        ruta_temporal.unlink(missing_ok=True)
        raise RuntimeError(f"No se pudo convertir {ruta} con FFmpeg: {resultado.stderr}")
    audio, fs = sf.read(ruta_temporal, dtype=dtype)
    return audio, fs, ruta_temporal


def texto_seguro_consola(texto: str) -> str:
    return texto.encode("ascii", errors="backslashreplace").decode("ascii")


def procesar_audio(ruta_relativa: str, tecnica: str, ref_relativa: str | None,
                   carpeta_salida: Path, texto_esperado: str, bits_esperados: str) -> dict:
    ruta_audio = CARPETA_AUDIOS / ruta_relativa
    if not ruta_audio.exists():
        return {"archivo": ruta_relativa, "error": "Archivo no encontrado"}

    dtype = "int16" if tecnica == "lsb" else "float32"
    audio, fs, temporal = leer_audio(ruta_audio, dtype)

    # Si tiene audio de referencia, alinear para compensar retardos del canal
    if ref_relativa is not None:
        ruta_ref = CARPETA_AUDIOS / ref_relativa
        ref_audio, fs_ref = sf.read(ruta_ref, dtype=dtype)
        al = normalizar_y_alinear(ref_audio, audio, fs_referencia=fs_ref, fs_recibido=fs)
        if tecnica == "lsb":
            info = np.iinfo(np.int16)
            audio = np.clip(np.rint(al), info.min, info.max).astype(np.int16)
        else:
            audio = al.astype(np.float32)
        fs = fs_ref

    n_bits = len(bits_esperados)
    muestras_por_bit = 1 if tecnica == "lsb" else 4096
    if n_bits > len(audio) // muestras_por_bit:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
        return {
            "archivo": ruta_relativa,
            "error": f"Capacidad insuficiente: requiere {n_bits} bits",
        }

    # Extraer los bits del mensaje base
    bits_extraidos = extraer_de_audio(audio, fs, tecnica, n_bits)
    texto_extraido = bits_a_texto(bits_extraidos)

    # Calcular errores
    comparables = min(len(bits_esperados), len(bits_extraidos))
    errores = sum(
        b1 != b2
        for b1, b2 in zip(bits_esperados[:comparables], bits_extraidos[:comparables])
    )
    errores += abs(len(bits_esperados) - len(bits_extraidos))
    ber = errores / n_bits
    accuracy = 1.0 - ber
    exacta = (errores == 0)

    # También extraer 64 bits si la técnica es eco/espectro/fase para ver qué decodifica a 64 bits
    bits_64 = extraer_de_audio(audio, fs, tecnica, 64) if audio.size >= 64 * 4096 else None
    texto_64 = bits_a_texto(bits_64) if bits_64 else None

    # Generar nombre del archivo txt de salida
    nombre_txt = ruta_relativa.replace("/", "_").replace("\\", "_")
    nombre_txt = Path(nombre_txt).stem + "_desencriptado.txt"
    ruta_txt = carpeta_salida / nombre_txt

    # Redactar contenido del .txt individual
    lineas = [
        "=" * 70,
        "REPORTE DE DESENCRIPTACIÓN / EXTRACCIÓN ESTEGANOGRÁFICA",
        "=" * 70,
        f"Archivo analizado : {ruta_audio}",
        f"Técnica           : {tecnica.upper()}",
        f"Audio referencia  : {ref_relativa if ref_relativa else 'N/A (Audio original estego)'}",
        f"Frecuencia (fs)   : {fs} Hz",
        "",
        "-" * 70,
        "RESULTADO DE LA EXTRACCIÓN DEL MENSAJE",
        "-" * 70,
        f"Mensaje esperado  : '{texto_esperado}'",
        f"Bits esperados    : {bits_esperados}",
        f"Bits extraídos    : {bits_extraidos}",
        f"Texto decodificado: '{texto_extraido}'",
        "",
        f"Bits correctos    : {n_bits - errores} / {n_bits}",
        f"Accuracy          : {accuracy * 100:.2f} %",
        f"BER (Bit Error)   : {ber:.4f}",
        f"Recuperación OK   : {'SÍ (EXACTA)' if exacta else 'NO (CON ERRORES)'}",
    ]

    if bits_64 and n_bits != 64:
        lineas.extend([
            "",
            "-" * 70,
            "EXTRACCIÓN A 64 BITS (Equivalente al mensaje 'ki ondá')",
            "-" * 70,
            f"Bits (64 bits)    : {bits_64}",
            f"Texto decodificado: '{texto_64}'",
        ])

    lineas.extend(["=" * 70, ""])

    contenido_txt = "\n".join(lineas)
    ruta_txt.write_text(contenido_txt, encoding="utf-8")
    if temporal is not None:
        temporal.unlink(missing_ok=True)

    return {
        "archivo": ruta_relativa,
        "tecnica": tecnica,
        "bits": bits_extraidos,
        "texto": texto_extraido,
        "accuracy": accuracy,
        "exacta": exacta,
        "txt_salida": ruta_txt,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extrae el mismo mensaje de todos los audios disponibles."
    )
    parser.add_argument("--mensaje", default=MENSAJE_POR_DEFECTO)
    parser.add_argument("--bits", default=None, help="Cadena binaria explícita.")
    args = parser.parse_args()

    if args.bits is not None:
        if any(bit not in "01" for bit in args.bits):
            parser.error("--bits solo puede contener ceros y unos.")
        texto_esperado = args.mensaje
        bits_esperados = args.bits
    else:
        texto_esperado = args.mensaje
        bits_esperados = texto_a_bits(texto_esperado)

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 95)
    print("INICIANDO DESENCRIPTACIÓN DE TODOS LOS AUDIOS...")
    print(f"Los resultados individuales se guardarán en: {CARPETA_SALIDA.resolve()}")
    print("=" * 95)
    print(f"{'Archivo':<36} | {'Técnica':<8} | {'Exacta':<7} | {'Texto Decodificado':<20} | {'Archivo .txt generado'}")
    print("-" * 95)

    resumen = []
    for rel, tec, ref in AUDIOS:
        res = procesar_audio(
            rel, tec, ref, CARPETA_SALIDA,
            texto_esperado, bits_esperados,
        )
        if "error" in res:
            print(f"{rel:<36} | ERROR: {res['error']}")
            continue

        resumen.append(res)
        txt_nombre = res["txt_salida"].name
        texto_mostrar = repr(texto_seguro_consola(res["texto"]))
        print(f"{rel:<36} | {tec:<8} | {str(res['exacta']):<7} | {texto_mostrar:<20} | {txt_nombre}")

    # Guardar también un resumen consolidado con todos
    ruta_resumen = CARPETA_SALIDA / "00_RESUMEN_TODOS.txt"
    lineas_resumen = [
        "=" * 95,
        "RESUMEN GENERAL DE DESENCRIPTACIÓN DE TODOS LOS AUDIOS",
        "=" * 95,
        f"{'Archivo':<36} | {'Técnica':<8} | {'Exacta':<7} | {'Accuracy':<10} | {'Texto Decodificado':<20} | {'Bits Extraídos'}",
        "-" * 95,
    ]
    for r in resumen:
        lineas_resumen.append(
            f"{r['archivo']:<36} | {r['tecnica']:<8} | {str(r['exacta']):<7} | {r['accuracy']*100:<6.2f} %  | {repr(texto_seguro_consola(r['texto'])):<20} | {r['bits']}"
        )
    lineas_resumen.extend(["=" * 95, ""])
    ruta_resumen.write_text("\n".join(lineas_resumen), encoding="utf-8")

    print("=" * 95)
    print(f"\n[OK] Se generaron con éxito {len(resumen)} archivos .txt individuales")
    print(f"[OK] Archivo resumen creado en: {ruta_resumen.resolve()}\n")


if __name__ == "__main__":
    main()
