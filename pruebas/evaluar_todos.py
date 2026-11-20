"""Script para evaluar automáticamente todos los audios en pruebas/audios."""

from pathlib import Path
import subprocess
import tempfile
import soundfile as sf
import numpy as np

from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import texto_a_bits, normalizar_portador, normalizar_lsb
from estego.metricas import evaluar_prueba, normalizar_y_alinear

CONFIGURACION_CANALES = [
    ("mp3", "mp3", "stego_{tec}_mp3.mp3"),
    ("whatsapp", "whatsapp", "stego_{tec}_whatsapp.ogg"),
    ("microfono", "microfono", "stego_{tec}_micro.ogg"),
]

TECNICAS = {
    "lsb": (lsb, 1),
    "eco": (eco, eco.SEGMENTO),
    "espectro": (espectro, espectro.SEGMENTO),
    "fase": (fase, fase.SEGMENTO),
}

MENSAJES_DEFAULT = {
    "lsb": texto_a_bits("ki ondá"),
    "eco": "01010101",
    "espectro": "01010101",
    "fase": "01010101",
}

MICROFONO_ALTERNATIVOS = {
    "lsb": ("stego_lsb_micro.ogg", "Lsbmicro.m4a"),
    "eco": ("stego_eco_micro.ogg", "Ecomicro.m4a"),
    "espectro": ("stego_espectro_micro.ogg", "Espectromicro.m4a"),
    "fase": ("stego_fase_micro.ogg", "Fasemicro.m4a"),
}


def resolver_ruta_recibida(canal: str, subcarpeta: str, patron: str, tec_nombre: str) -> Path:
    ruta_principal = Path("pruebas/audios") / subcarpeta / patron.format(tec=tec_nombre)
    if ruta_principal.exists():
        return ruta_principal

    alternativas = []
    if subcarpeta == "mp3":
        alternativas = [f"stego_{tec_nombre}.mp3"]
    elif subcarpeta == "whatsapp":
        alternativas = [f"stego_{tec_nombre}.ogg"]
    elif subcarpeta == "microfono":
        alternativas = [*MICROFONO_ALTERNATIVOS[tec_nombre]]

    for nombre in alternativas:
        ruta = Path("pruebas/audios") / subcarpeta / nombre
        if ruta.exists():
            return ruta
    return ruta_principal


def leer_audio_recibido(ruta: Path, dtype: str) -> tuple[np.ndarray, int, Path | None]:
    """Lee formatos compatibles y convierte M4A temporalmente con FFmpeg."""
    if ruta.suffix.lower() != ".m4a":
        audio, fs = sf.read(ruta, dtype=dtype)
        return audio, fs, None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporal:
        ruta_temporal = Path(temporal.name)

    resultado = subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(ruta),
            "-vn", "-acodec", "pcm_s16le",
            str(ruta_temporal),
        ],
        capture_output=True,
        text=True,
    )
    if resultado.returncode != 0:
        ruta_temporal.unlink(missing_ok=True)
        raise RuntimeError(f"No se pudo convertir {ruta} con FFmpeg: {resultado.stderr}")

    try:
        audio, fs = sf.read(ruta_temporal, dtype=dtype)
    except Exception:
        ruta_temporal.unlink(missing_ok=True)
        raise
    return audio, fs, ruta_temporal


def evaluar_todos(canales=None, mensaje: str | None = None, bits: str | None = None) -> list[dict]:
    canales_a_evaluar = [
        conf for conf in CONFIGURACION_CANALES
        if canales is None or conf[0] in canales
    ]
    if bits is not None:
        if any(c not in "01" for c in bits):
            raise ValueError("--bits solo puede contener ceros y unos.")
        mensajes = {tecnica: bits for tecnica in TECNICAS}
    elif mensaje is not None:
        mensajes = {tecnica: texto_a_bits(mensaje) for tecnica in TECNICAS}
    else:
        mensajes = MENSAJES_DEFAULT

    resultados = []

    print("\n" + "=" * 115)
    print(f"{'Canal':<12} | {'Técnica':<10} | {'BER':<8} | {'IC 95% Wilson':<18} | {'Accuracy':<8} | {'Exacta':<7} | {'SNR (dB)':<9} | {'Cap (bps)':<10} | {'Tasa Ef (bps)'}")
    print("-" * 115)

    for canal, subcarpeta, patron in canales_a_evaluar:
        for tec_nombre, (tecnica, muestras_por_bit) in TECNICAS.items():
            bits_tecnicas = mensajes[tec_nombre]
            dtype = "int16" if tec_nombre == "lsb" else "float32"

            orig_path = Path("pruebas/audios/original.wav")
            stego_path = Path(f"pruebas/audios/stego_{tec_nombre}.wav")
            rec_path = resolver_ruta_recibida(canal, subcarpeta, patron, tec_nombre)

            if not rec_path.exists():
                print(f"Advertencia: No se encontró {rec_path}")
                continue

            orig_ref, fs = sf.read(orig_path, dtype=dtype)
            stego, fs_s = sf.read(stego_path, dtype=dtype)
            rec, fs_r, ruta_temporal = leer_audio_recibido(rec_path, dtype)
            if ruta_temporal is not None:
                ruta_temporal_actual = ruta_temporal
            else:
                ruta_temporal_actual = None

            # Normalizar referencia para SNR exacto
            if tec_nombre == "lsb":
                orig_ref = normalizar_lsb(orig_ref)
            else:
                orig_ref = normalizar_portador(orig_ref)

            # Alinear audio
            rec_al = normalizar_y_alinear(stego, rec, fs, fs_r)
            if tec_nombre == "lsb":
                info = np.iinfo(np.int16)
                rec_al = np.clip(np.rint(rec_al), info.min, info.max).astype(np.int16)
            else:
                rec_al = rec_al.astype(np.float32)

            capacidad_disponible = len(rec_al) // muestras_por_bit
            if len(bits_tecnicas) > capacidad_disponible:
                print(
                    f"Advertencia: {rec_path} tiene capacidad para "
                    f"{capacidad_disponible} bits, pero se solicitaron {len(bits_tecnicas)}."
                )
                if ruta_temporal_actual is not None:
                    ruta_temporal_actual.unlink(missing_ok=True)
                continue

            # Extraer bits según técnica
            if tec_nombre == "lsb":
                rec_bits = lsb.extraer(rec_al, len(bits_tecnicas))
            elif tec_nombre == "eco":
                rec_bits = eco.extraer(rec_al, len(bits_tecnicas))
            elif tec_nombre == "espectro":
                rec_bits = espectro.extraer(rec_al, len(bits_tecnicas), clave=1234)
            elif tec_nombre == "fase":
                rec_bits = fase.extraer(rec_al, len(bits_tecnicas), fs=fs)

            res = evaluar_prueba(
                bits_originales=bits_tecnicas,
                bits_recuperados=rec_bits,
                audio_original=orig_ref,
                audio_stego=stego,
                fs=fs,
                muestras_por_bit=muestras_por_bit,
            )

            d = {
                "canal": canal,
                "tecnica": tec_nombre,
                "ber": res.ber,
                "accuracy_bits": res.accuracy_bits,
                "recuperacion_exacta": res.recuperacion_exacta,
                "snr_db": res.snr_db,
                "capacidad_bps": res.capacidad_bps,
                "tasa_informacion_efectiva_bps": res.tasa_informacion_efectiva_bps,
            }
            resultados.append(d)

            print(
                f"{canal:<12} | {tec_nombre:<10} | {res.ber:<8.4f} | {res.ber_ci_str:<18} | {res.accuracy_bits:<8.4f} | "
                f"{str(res.recuperacion_exacta):<7} | {res.snr_db:<9.2f} | {res.capacidad_bps:<10.1f} | "
                f"{res.tasa_informacion_efectiva_bps:<.2f}"
            )
            if ruta_temporal_actual is not None:
                ruta_temporal_actual.unlink(missing_ok=True)

    print("=" * 115 + "\n")
    return resultados


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evalúa todas las combinaciones de canales y técnicas.")
    parser.add_argument("--canal", choices=("mp3", "whatsapp", "microfono"), default=None, help="Evaluar un solo canal.")
    parser.add_argument("--mensaje", default=None, help="Mensaje de texto igual para todas las técnicas.")
    parser.add_argument("--bits", default=None, help="Cadena binaria igual para todas las técnicas.")
    args = parser.parse_args()
    evaluar_todos(
        canales=[args.canal] if args.canal else None,
        mensaje=args.mensaje,
        bits=args.bits,
    )
