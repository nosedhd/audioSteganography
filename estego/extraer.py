"""Módulo CLI para extraer y decodificar mensajes de audio en vivo (para exposiciones y pruebas)."""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from estego.metricas import normalizar_y_alinear
from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import bits_a_texto, texto_a_bits

TECNICAS = {
    "lsb": "LSB (Least Significant Bit)",
    "eco": "Eco Hiding (Análisis Cepstral)",
    "espectro": "Espectro Ensanchado (DSSS)",
    "fase": "Codificación de Fase (Phase Coding)",
}


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrae y decodifica un mensaje secreto oculto en un archivo de audio.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-t", "--tecnica",
        choices=("lsb", "eco", "espectro", "fase"),
        help="Técnica esteganográfica utilizada.",
    )
    parser.add_argument(
        "-a", "--audio",
        type=Path,
        help="Ruta al archivo de audio estego a analizar.",
    )
    parser.add_argument(
        "-b", "--bits",
        type=int,
        default=None,
        help="Número exacto de bits a extraer.",
    )
    parser.add_argument(
        "-c", "--caracteres",
        type=int,
        default=None,
        help="Número de caracteres de texto a extraer (multiplica por 8 bits).",
    )
    parser.add_argument(
        "-m", "--mensaje-referencia",
        help="Texto del mensaje original esperado para comparar y calcular el BER.",
    )
    parser.add_argument(
        "-r", "--audio-referencia",
        type=Path,
        default=None,
        help="Audio estego original (.wav) para alinear desfases si el audio pasó por MP3/WhatsApp/Micrófono.",
    )
    parser.add_argument(
        "--clave",
        type=int,
        default=1234,
        help="Clave/semilla numérica para espectro ensanchado (DSSS).",
    )
    parser.add_argument(
        "--seg",
        type=int,
        default=4096,
        help="Muestras por bit para eco, espectro y fase.",
    )
    return parser


def solicitar_datos_interactivos() -> tuple[str, Path, int, str | None, Path | None, int, int]:
    """Modo interactivo en consola para presentaciones en vivo."""
    print("\n" + "=" * 70)
    print("   🔍  ESTEGANOGRAFÍA DE AUDIO - EXTRACCIÓN EN VIVO  🔍")
    print("=" * 70)
    print("Selecciona la técnica:")
    print("  1) LSB (Dominio temporal, 1 bit/muestra)")
    print("  2) Eco Hiding (Dominio temporal/cepstral)")
    print("  3) Espectro Ensanchado / DSSS (Dominio frecuencial con clave)")
    print("  4) Codificación de Fase (Modificación de fase en banda audible)")
    opcion = input("Opción [1-4] (default 1): ").strip() or "1"
    mapa = {"1": "lsb", "2": "eco", "3": "espectro", "4": "fase"}
    tecnica = mapa.get(opcion, "lsb")

    audio_default = f"stego_{tecnica}_demo.wav"
    audio_input = input(f"Ruta del audio a analizar [default: {audio_default}]: ").strip()
    audio = Path(audio_input or audio_default)

    mensaje_ref = input("Mensaje esperado para comparar (opcional, presiona Enter para omitir): ").strip() or None
    if mensaje_ref:
        n_bits = len(texto_a_bits(mensaje_ref))
    else:
        caracteres_str = input("Número aproximado de caracteres a extraer [default 10]: ").strip() or "10"
        n_bits = int(caracteres_str) * 8

    ref_input = input("¿El audio viene de MP3/WhatsApp/Micrófono? Ruta de referencia para alinear (opcional): ").strip()
    audio_ref = Path(ref_input) if ref_input else None

    clave = 1234
    if tecnica == "espectro":
        clave_str = input("Clave numérica para DSSS [default 1234]: ").strip()
        clave = int(clave_str) if clave_str.isdigit() else 1234

    return tecnica, audio, n_bits, mensaje_ref, audio_ref, clave, 4096


def ejecutar_extraccion(
    tecnica: str,
    audio_path: Path,
    n_bits: int,
    mensaje_ref: str | None = None,
    audio_ref_path: Path | None = None,
    clave: int = 1234,
    seg: int = 4096,
) -> None:
    if not audio_path.exists():
        raise FileNotFoundError(f"No se encontró el audio a analizar: {audio_path}")

    dtype = "int16" if tecnica == "lsb" else "float32"
    audio, fs = sf.read(audio_path, dtype=dtype)

    # Alinear si se proporcionó audio de referencia
    if audio_ref_path is not None:
        if not audio_ref_path.exists():
            raise FileNotFoundError(f"No se encontró el audio de referencia para alinear: {audio_ref_path}")
        ref_audio, fs_ref = sf.read(audio_ref_path, dtype=dtype)
        al = normalizar_y_alinear(ref_audio, audio, fs_referencia=fs_ref, fs_recibido=fs)
        if tecnica == "lsb":
            info = np.iinfo(np.int16)
            audio = np.clip(np.rint(al), info.min, info.max).astype(np.int16)
        else:
            audio = al.astype(np.float32)
        fs = fs_ref

    print("\n" + "=" * 70)
    print("  AUDIO STEGANOGRAPHY - REPORTE DE EXTRACCIÓN (EN VIVO)")
    print("=" * 70)
    print(f"[+] Técnica analizada    : {TECNICAS[tecnica]}")
    print(f"[+] Archivo de audio     : {audio_path}")
    print(f"[+] Bits solicitados     : {n_bits} bits (~{n_bits // 8} bytes de texto)")

    t0 = time.perf_counter()

    if tecnica == "lsb":
        bits_recuperados = lsb.extraer(audio, n_bits)
    elif tecnica == "eco":
        bits_recuperados = eco.extraer(audio, n_bits, seg=seg)
    elif tecnica == "espectro":
        bits_recuperados = espectro.extraer(audio, n_bits, seg=seg, clave=clave)
    elif tecnica == "fase":
        bits_recuperados = fase.extraer(audio, n_bits, seg=seg, fs=fs)
    else:
        raise ValueError(f"Técnica no soportada: {tecnica}")

    t_proc = (time.perf_counter() - t0) * 1000
    texto_recuperado = bits_a_texto(bits_recuperados)
    print(f"[+] Extracción completada: [OK] en {t_proc:.2f} ms")
    print("-" * 70)
    print(f"[+] BITS EXTRAÍDOS       : {bits_recuperados}")
    print(f"[+] TEXTO RECUPERADO     : {repr(texto_recuperado)}")

    if mensaje_ref is not None:
        bits_esperados = texto_a_bits(mensaje_ref) if not all(c in "01" for c in mensaje_ref) else mensaje_ref
        comparables = min(len(bits_esperados), len(bits_recuperados))
        errores = sum(b1 != b2 for b1, b2 in zip(bits_esperados[:comparables], bits_recuperados[:comparables]))
        errores += abs(len(bits_esperados) - len(bits_recuperados))
        ber = errores / max(len(bits_esperados), len(bits_recuperados))
        accuracy = 1.0 - ber

        print("-" * 70)
        print(f"[+] COMPARACIÓN CON EL MENSAJE ESPERADO:")
        print(f"    - Mensaje esperado   : {repr(mensaje_ref)}")
        print(f"    - Bits correctos     : {comparables - errores} / {len(bits_esperados)}")
        print(f"    - Accuracy de bits   : {accuracy * 100:.2f} %")
        print(f"    - BER (Error de Bit) : {ber:.4f}")
        print(f"    - Resultado          : {'RECUPERACIÓN EXACTA (100%)' if errores == 0 else 'CON ERRORES'}")

    print("=" * 70 + "\n")


def main() -> None:
    parser = construir_parser()
    args = parser.parse_args()

    # Si se ejecuta sin técnica o sin audio, activar modo interactivo
    if not args.tecnica or not args.audio:
        tecnica, audio, n_bits, mensaje_ref, audio_ref, clave, seg = solicitar_datos_interactivos()
    else:
        tecnica = args.tecnica
        audio = args.audio
        audio_ref = args.audio_referencia
        mensaje_ref = args.mensaje_referencia
        clave = args.clave
        seg = args.seg

        if args.bits is not None:
            n_bits = args.bits
        elif args.caracteres is not None:
            n_bits = args.caracteres * 8
        elif mensaje_ref is not None:
            n_bits = len(texto_a_bits(mensaje_ref)) if not all(c in "01" for c in mensaje_ref) else len(mensaje_ref)
        else:
            n_bits = 64  # Por defecto 64 bits = 8 caracteres

    try:
        ejecutar_extraccion(
            tecnica=tecnica,
            audio_path=audio,
            n_bits=n_bits,
            mensaje_ref=mensaje_ref,
            audio_ref_path=audio_ref,
            clave=clave,
            seg=seg,
        )
    except Exception as e:
        print(f"\n[ERROR] No se pudo completar la extracción: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
