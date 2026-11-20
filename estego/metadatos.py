"""Registro y catálogo de metadatos experimentales para canales de transmisión de audio."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MetadatosCanal:
    """Metadatos formales para la caracterización de un canal de audio."""

    canal: str
    codec: str
    bitrate_kbps: str | int
    frecuencia_muestreo_hz: int
    duracion_s: float
    canales_audio: int
    dispositivo: str
    volumen: str
    distancia: str
    entorno: str
    notas: str = ""

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


# Catálogo oficial de metadatos por canal utilizado en la investigación
METADATOS_CANALES: dict[str, MetadatosCanal] = {
    "mp3": MetadatosCanal(
        canal="MP3 (Sintético)",
        codec="MPEG-1 Audio Layer III (libmp3lame)",
        bitrate_kbps=128,
        frecuencia_muestreo_hz=48000,
        duracion_s=127.40,
        canales_audio=1,
        dispositivo="FFmpeg 0.0 / libmp3lame (PC)",
        volumen="Digital (0 dBFS, sin atenuación)",
        distancia="N/A (Canal digital directo)",
        entorno="Simulación digital determinista",
        notas="Compresión psicoacústica con banco de filtros MDCT y cuantización frecuencial.",
    ),
    "opus_12k": MetadatosCanal(
        canal="Opus (12 kbps)",
        codec="libopus (SILK/CELT híbrido)",
        bitrate_kbps=12,
        frecuencia_muestreo_hz=48000,
        duracion_s=127.40,
        canales_audio=1,
        dispositivo="FFmpeg / libopus (PC)",
        volumen="Digital (0 dBFS)",
        distancia="N/A (Canal digital)",
        entorno="Compresión de voz de ultra-bajo bitrate",
        notas="Corte agresivo de frecuencias altas por encima de 4-6 kHz.",
    ),
    "opus_16k": MetadatosCanal(
        canal="Opus (16 kbps)",
        codec="libopus (SILK/CELT híbrido)",
        bitrate_kbps=16,
        frecuencia_muestreo_hz=48000,
        duracion_s=127.40,
        canales_audio=1,
        dispositivo="FFmpeg / libopus (PC)",
        volumen="Digital (0 dBFS)",
        distancia="N/A (Canal digital)",
        entorno="Tasa típica de notas de voz en redes móviles",
        notas="Ancho de banda de audio equivalente a banda ancha (Wideband ~8 kHz).",
    ),
    "opus_24k": MetadatosCanal(
        canal="Opus (24 kbps)",
        codec="libopus (SILK/CELT híbrido)",
        bitrate_kbps=24,
        frecuencia_muestreo_hz=48000,
        duracion_s=127.40,
        canales_audio=1,
        dispositivo="FFmpeg / libopus (PC)",
        volumen="Digital (0 dBFS)",
        distancia="N/A (Canal digital)",
        entorno="Calidad estándar de VoIP y llamadas WebRTC",
        notas="Ancho de banda Super-Wideband (~12 kHz).",
    ),
    "opus_32k": MetadatosCanal(
        canal="Opus (32 kbps)",
        codec="libopus (SILK/CELT híbrido)",
        bitrate_kbps=32,
        frecuencia_muestreo_hz=48000,
        duracion_s=127.40,
        canales_audio=1,
        dispositivo="FFmpeg / libopus (PC)",
        volumen="Digital (0 dBFS)",
        distancia="N/A (Canal digital)",
        entorno="Calidad alta de voz / música monoaural",
        notas="Ancho de banda completo (Fullband 20 kHz).",
    ),
    "whatsapp": MetadatosCanal(
        canal="WhatsApp (Real)",
        codec="Opus en contenedor OGG (.opus/.ogg)",
        bitrate_kbps="~20-24 kbps VBR",
        frecuencia_muestreo_hz=48000,
        duracion_s=127.40,
        canales_audio=1,
        dispositivo="WhatsApp Android / Servidores de Meta",
        volumen="AGC dinámico (Control Automático de Ganancia)",
        distancia="Transmisión celular / WiFi",
        entorno="Procesamiento en la nube de Meta + red IP",
        notas="Incluye transcodificación interna de la aplicación y normalización de volumen.",
    ),
    "microfono": MetadatosCanal(
        canal="Micrófono / Parlante (Real)",
        codec="Transducción acústica física + PCM/Opus",
        bitrate_kbps="Variable acústico",
        frecuencia_muestreo_hz=16000,
        duracion_s=127.40,
        canales_audio=1,
        dispositivo="Parlante PC (Emisor) + Micrófono Smartphone (Receptor)",
        volumen="Nivel de escucha normal (~65-70 dB SPL, 50% volumen)",
        distancia="~30 a 50 cm en línea de vista directa",
        entorno="Habitación cerrada de prueba, reverberación interior (~0.3-0.5s RT60)",
        notas="Canal analógico con efecto multicamino, ruido ambiental y respuesta en frecuencia no plana.",
    ),
}


def obtener_tabla_metadatos_md() -> str:
    """Genera una tabla Markdown lista para incluir en la documentación y diapositivas."""
    lineas = [
        "| Canal | Códec | Bitrate | Frecuencia (fs) | Dispositivo | Volumen / Ganancia | Distancia / Entorno |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for c in METADATOS_CANALES.values():
        lineas.append(
            f"| **{c.canal}** | {c.codec} | {c.bitrate_kbps if isinstance(c.bitrate_kbps, str) else f'{c.bitrate_kbps} kbps'} | "
            f"{c.frecuencia_muestreo_hz:,} Hz | {c.dispositivo} | {c.volumen} | {c.distancia} ({c.entorno}) |"
        )
    return "\n".join(lineas)
