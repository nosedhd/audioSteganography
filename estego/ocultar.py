"""Módulo CLI para ocultar mensajes en audio en vivo (para exposiciones y pruebas)."""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from estego.metricas import snr_db
from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import normalizar_lsb, normalizar_portador, texto_a_bits

TECNICAS = {
    "lsb": "LSB (Least Significant Bit)",
    "eco": "Eco Hiding (Análisis Cepstral)",
    "espectro": "Espectro Ensanchado (DSSS)",
    "fase": "Codificación de Fase (Phase Coding)",
}


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Oculta un mensaje secreto en un archivo de audio (Esteganografía en vivo).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-t", "--tecnica",
        choices=("lsb", "eco", "espectro", "fase"),
        help="Técnica esteganográfica a utilizar.",
    )
    parser.add_argument(
        "-m", "--mensaje",
        help="Mensaje de texto a ocultar (ej: 'Hola mundo') o cadena binaria (ej: '01010101').",
    )
    parser.add_argument(
        "-a", "--audio",
        type=Path,
        default=Path("pruebas/audios/original.wav"),
        help="Ruta al audio portador (.wav).",
    )
    parser.add_argument(
        "-s", "--salida",
        type=Path,
        default=Path("pruebas/audios/salida.wav"),
        help="Ruta donde se guardará el audio estego (.wav).",
    )
    parser.add_argument(
        "--clave",
        type=int,
        default=1234,
        help="Clave/semilla para espectro ensanchado (DSSS).",
    )
    parser.add_argument(
        "--alfa",
        type=float,
        default=None,
        help="Factor de amplitud/ganancia (Eco o Espectro).",
    )
    parser.add_argument(
        "--seg",
        type=int,
        default=4096,
        help="Muestras por bit para eco, espectro y fase.",
    )
    return parser


def solicitar_datos_interactivos() -> tuple[str, str, Path, Path | None, int, float | None, int]:
    """Modo interactivo en consola para presentaciones en vivo."""
    print("\n" + "=" * 70)
    print("   🎙️  ESTEGANOGRAFÍA DE AUDIO - OCULTACIÓN EN VIVO  🎙️")
    print("=" * 70)
    print("Selecciona la técnica:")
    print("  1) LSB (Dominio temporal, 1 bit/muestra)")
    print("  2) Eco Hiding (Dominio temporal/cepstral)")
    print("  3) Espectro Ensanchado / DSSS (Dominio frecuencial con clave)")
    print("  4) Codificación de Fase (Modificación de fase en banda audible)")
    opcion = input("Opción [1-4] (default 1): ").strip() or "1"
    mapa = {"1": "lsb", "2": "eco", "3": "espectro", "4": "fase"}
    tecnica = mapa.get(opcion, "lsb")

    mensaje = input("Introduce el mensaje secreto a ocultar: ").strip()
    if not mensaje:
        mensaje = "Mensaje secreto de prueba 2026"
        print(f"Usando mensaje por defecto: '{mensaje}'")

    audio_default = "pruebas/audios/original.wav"
    audio_input = input(f"Ruta del audio portador (.wav) [default: {audio_default}]: ").strip()
    audio = Path(audio_input or audio_default)

    salida_default = f"stego_{tecnica}_demo.wav"
    salida_input = input(f"Ruta del archivo de salida [default: {salida_default}]: ").strip()
    salida = Path(salida_input or salida_default)

    clave = 1234
    if tecnica == "espectro":
        clave_str = input("Clave numérica para DSSS [default 1234]: ").strip()
        clave = int(clave_str) if clave_str.isdigit() else 1234

    return tecnica, mensaje, audio, salida, clave, None, 4096


def ejecutar_ocultacion(
    tecnica: str,
    mensaje: str,
    audio_path: Path,
    salida_path: Path,
    clave: int = 1234,
    alfa: float | None = None,
    seg: int = 4096,
) -> None:
    if not audio_path.exists():
        raise FileNotFoundError(f"No se encontró el audio portador: {audio_path}")

    # Determinar bits a inyectar
    if all(c in "01" for c in mensaje):
        bits = mensaje
        es_binario = True
    else:
        bits = texto_a_bits(mensaje)
        es_binario = False

    dtype = "int16" if tecnica == "lsb" else "float32"
    audio, fs = sf.read(audio_path, dtype=dtype)

    duracion = len(audio) / fs
    muestras_por_bit = 1 if tecnica == "lsb" else seg
    capacidad_total_bits = len(audio) // muestras_por_bit
    capacidad_bps = fs / muestras_por_bit

    print("\n" + "=" * 70)
    print("  AUDIO STEGANOGRAPHY - REPORTE DE OCULTACIÓN (EN VIVO)")
    print("=" * 70)
    print(f"[+] Técnica seleccionada : {TECNICAS[tecnica]}")
    print(f"[+] Audio portador       : {audio_path}")
    print(f"    - Frecuencia (fs)    : {fs:,} Hz")
    print(f"    - Duración           : {duracion:.2f} s")
    print(f"    - Capacidad máxima   : {capacidad_total_bits:,} bits ({capacidad_bps:.2f} bps)")
    print(f"[+] Mensaje secreto      : {repr(mensaje) if not es_binario else 'Cadena binaria'}")
    print(f"    - Bits a inyectar    : {len(bits):,} bits")
    print(f"    - Secuencia inicial  : {bits[:32]}{'...' if len(bits) > 32 else ''}")
    print(f"    - Uso de capacidad   : {(len(bits) / capacidad_total_bits) * 100:.2f} % del audio")

    if len(bits) > capacidad_total_bits:
        raise ValueError(
            f"El mensaje requiere {len(bits)} bits pero el audio solo soporta {capacidad_total_bits} bits."
        )

    t0 = time.perf_counter()

    # Ocultación según técnica
    if tecnica == "lsb":
        stego = lsb.ocultar(audio, bits)
        orig_ref = normalizar_lsb(audio)
    elif tecnica == "eco":
        kwargs = {"seg": seg}
        if alfa is not None:
            kwargs["alfa"] = alfa
        stego = eco.ocultar(audio, bits, **kwargs)
        orig_ref = normalizar_portador(audio)
    elif tecnica == "espectro":
        kwargs = {"seg": seg, "clave": clave}
        if alfa is not None:
            kwargs["alfa"] = alfa
        stego = espectro.ocultar(audio, bits, **kwargs)
        orig_ref = normalizar_portador(audio)
    elif tecnica == "fase":
        stego = fase.ocultar(audio, bits, seg=seg, fs=fs)
        orig_ref = normalizar_portador(audio)
    else:
        raise ValueError(f"Técnica no soportada: {tecnica}")

    t_proc = (time.perf_counter() - t0) * 1000

    # Guardar audio
    sf.write(salida_path, stego, fs)
    snr = snr_db(orig_ref, stego)

    print(f"[+] Inserción completada : [OK] en {t_proc:.2f} ms")
    print(f"[+] Relación Señal-Ruido : SNR = {snr:.2f} dB (Imperceptibilidad)")
    print(f"[+] Audio estego creado  : {salida_path.resolve()}")
    print("=" * 70 + "\n")


def main() -> None:
    parser = construir_parser()
    args = parser.parse_args()

    # Si se ejecuta sin técnica o sin mensaje, activar modo interactivo
    if not args.tecnica or not args.mensaje:
        tecnica, mensaje, audio, salida, clave, alfa, seg = solicitar_datos_interactivos()
    else:
        tecnica = args.tecnica
        mensaje = args.mensaje
        audio = args.audio
        salida = args.salida or Path(f"stego_{tecnica}_demo.wav")
        clave = args.clave
        alfa = args.alfa
        seg = args.seg

    try:
        ejecutar_ocultacion(
            tecnica=tecnica,
            mensaje=mensaje,
            audio_path=audio,
            salida_path=salida,
            clave=clave,
            alfa=alfa,
            seg=seg,
        )
    except Exception as e:
        print(f"\n[ERROR] No se pudo completar la ocultación: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
