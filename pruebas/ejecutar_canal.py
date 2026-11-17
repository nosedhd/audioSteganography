"""Ejecutor de evaluación para MP3, WhatsApp o grabación acústica."""

import argparse
from pathlib import Path

import soundfile as sf

from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import normalizar_lsb, normalizar_portador, texto_a_bits

if __package__:
    from .canal_microfono import evaluar_microfono
    from .canal_mp3 import evaluar_mp3
    from .canal_whatsapp import evaluar_whatsapp
else:
    from canal_microfono import evaluar_microfono
    from canal_mp3 import evaluar_mp3
    from canal_whatsapp import evaluar_whatsapp


TECNICAS = {
    "lsb": (lsb, 1),
    "eco": (eco, eco.SEGMENTO),
    "espectro": (espectro, espectro.SEGMENTO),
    "fase": (fase, fase.SEGMENTO),
}


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evalúa una técnica después de pasar por un canal con pérdida.",
    )
    parser.add_argument("--canal", choices=("mp3", "whatsapp", "microfono"), required=True)
    parser.add_argument("--tecnica", choices=tuple(TECNICAS), required=True)
    parser.add_argument("--mensaje", default=None, help="Texto del mensaje (ej: 'ki ondá') o secuencia binaria.")
    parser.add_argument("--bits", default=None, help="Cadena binaria explícita (ej: '01010101').")
    parser.add_argument("--audio-original", type=Path, required=True)
    parser.add_argument("--audio-stego", type=Path, required=True)
    parser.add_argument("--audio-recibido", type=Path, required=True)
    parser.add_argument("--clave", type=int, default=1234)
    parser.add_argument("--alfa", type=float, default=None)
    parser.add_argument("--sin-alinear", action="store_true")
    return parser


def main() -> None:
    args = construir_parser().parse_args()
    tecnica, muestras_por_bit = TECNICAS[args.tecnica]
    tipo = "int16" if args.tecnica == "lsb" else "float32"
    audio_original, fs = sf.read(args.audio_original, dtype=tipo)
    audio_stego, fs_stego = sf.read(args.audio_stego, dtype=tipo)
    if fs_stego != fs:
        raise ValueError("El audio original y el audio estego deben tener el mismo fs.")

    # Normalizar el audio original con la misma referencia usada al ocultar para cálculo fiel de SNR
    if args.tecnica == "lsb":
        audio_original = normalizar_lsb(audio_original)
    else:
        audio_original = normalizar_portador(audio_original)

    parametros = {"alinear_audio": not args.sin_alinear}
    parametros["dtype"] = "int16" if args.tecnica == "lsb" else "float32"
    if args.tecnica in ("eco", "espectro", "fase"):
        parametros["seg"] = muestras_por_bit
    if args.tecnica == "espectro":
        parametros["clave"] = args.clave
    if args.tecnica == "eco" and args.alfa is not None:
        parametros["alfa"] = args.alfa

    if args.bits is not None:
        bits = args.bits
    elif args.mensaje is not None:
        bits = args.mensaje if all(c in "01" for c in args.mensaje) else texto_a_bits(args.mensaje)
    else:
        raise ValueError("Debe indicar --mensaje o --bits.")
    if args.canal == "mp3":
        evaluar_mp3(
            bits, audio_original, audio_stego, fs, tecnica.extraer,
            ruta_audio_recibido=args.audio_recibido,
            muestras_por_bit=muestras_por_bit, **parametros,
        )
    elif args.canal == "whatsapp":
        evaluar_whatsapp(
            bits, audio_original, audio_stego, fs, tecnica.extraer,
            ruta_audio_recibido=args.audio_recibido,
            muestras_por_bit=muestras_por_bit, **parametros,
        )
    else:
        evaluar_microfono(
            bits, audio_original, audio_stego, fs, tecnica.extraer,
            ruta_audio_recibido=args.audio_recibido,
            muestras_por_bit=muestras_por_bit, **parametros,
        )


if __name__ == "__main__":
    main()
