"""
utils_imagen.py — GreenPower
Manejo profesional de imágenes con Pillow
Soporta: JPG, PNG, GIF
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

try:
    from PIL import Image, ImageTk, ImageFilter, ImageOps
    PILLOW_DISPONIBLE = True
except ImportError:
    PILLOW_DISPONIBLE = False

# ── Configuración global ─────────────────────────────────────────
FORMATOS_PERMITIDOS   = {'.jpg', '.jpeg', '.png', '.gif'}
MIME_PERMITIDOS       = {'JPEG', 'PNG', 'GIF'}
TAMANO_MAXIMO_MB      = 5
TAMANO_MAXIMO_BYTES   = TAMANO_MAXIMO_MB * 1024 * 1024

THUMB_SIZE            = (120, 120)   # Miniatura en formulario
PREVIEW_SIZE          = (300, 300)   # Preview ampliado
MAX_GUARDADO_SIZE     = (1920, 1080) # Tamaño máximo al guardar

CARPETA_IMAGENES      = Path("imagenes_greenpower")
CARPETA_PLANTAS       = CARPETA_IMAGENES / "plantas"
CARPETA_EQUIPOS       = CARPETA_IMAGENES / "equipos"


def inicializar_carpetas():
    """Crea las carpetas de imágenes si no existen."""
    for carpeta in [CARPETA_PLANTAS, CARPETA_EQUIPOS]:
        carpeta.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
# VALIDACIÓN
# ══════════════════════════════════════════════════════════════════

class ResultadoValidacion:
    def __init__(self, ok: bool, mensaje: str = ""):
        self.ok      = ok
        self.mensaje = mensaje


def validar_imagen(ruta: str) -> ResultadoValidacion:
    """
    Valida:
      1. Que el archivo exista
      2. Extensión permitida (jpg, png, gif)
      3. Tamaño <= 5 MB
      4. Que Pillow pueda abrirla y el formato sea válido
    """
    if not PILLOW_DISPONIBLE:
        return ResultadoValidacion(False, "Pillow no está instalado. Ejecuta: pip install Pillow")

    ruta_p = Path(ruta)

    if not ruta_p.exists():
        return ResultadoValidacion(False, "El archivo no existe.")

    ext = ruta_p.suffix.lower()
    if ext not in FORMATOS_PERMITIDOS:
        return ResultadoValidacion(False,
            f"Formato no permitido: '{ext}'. Usa JPG, PNG o GIF.")

    tamano = ruta_p.stat().st_size
    if tamano > TAMANO_MAXIMO_BYTES:
        mb = tamano / (1024 * 1024)
        return ResultadoValidacion(False,
            f"Archivo muy grande: {mb:.1f} MB. Máximo permitido: {TAMANO_MAXIMO_MB} MB.")

    try:
        with Image.open(ruta_p) as img:
            fmt = img.format
            if fmt not in MIME_PERMITIDOS:
                return ResultadoValidacion(False,
                    f"Formato interno no válido: '{fmt}'. Se esperaba JPEG, PNG o GIF.")
    except Exception as e:
        return ResultadoValidacion(False, f"No se pudo abrir la imagen: {e}")

    return ResultadoValidacion(True, "Imagen válida ✅")


# ══════════════════════════════════════════════════════════════════
# PROCESAMIENTO
# ══════════════════════════════════════════════════════════════════

def procesar_y_guardar(
    ruta_origen: str,
    codigo: str,
    categoria: str,          # 'planta' | 'equipo'
    convertir_a: str = None, # 'JPG' | 'PNG' | None (mantener original)
    filtro: str = None,      # 'gris' | 'nitidez' | None
) -> Tuple[bool, str]:
    """
    1. Valida la imagen
    2. Redimensiona si supera MAX_GUARDADO_SIZE (mantiene proporción)
    3. Aplica filtro opcional
    4. Convierte formato si se indica
    5. Guarda en la carpeta correspondiente
    Retorna (éxito, ruta_destino_o_mensaje_error)
    """
    val = validar_imagen(ruta_origen)
    if not val.ok:
        return False, val.mensaje

    carpeta = CARPETA_PLANTAS if categoria == 'planta' else CARPETA_EQUIPOS
    carpeta.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        with Image.open(ruta_origen) as img:
            # Convertir GIF a RGBA para procesarlo bien
            if img.format == 'GIF':
                img = img.convert('RGBA')

            # ── Redimensionar si es muy grande ──────────────────
            if img.width > MAX_GUARDADO_SIZE[0] or img.height > MAX_GUARDADO_SIZE[1]:
                img.thumbnail(MAX_GUARDADO_SIZE, Image.LANCZOS)

            # ── Aplicar filtro ──────────────────────────────────
            if filtro == 'gris':
                img = ImageOps.grayscale(img)
            elif filtro == 'nitidez':
                img = img.filter(ImageFilter.SHARPEN)

            # ── Determinar formato de salida ────────────────────
            fmt_salida = convertir_a if convertir_a else img.format or 'JPEG'
            if fmt_salida == 'GIF':
                fmt_salida = 'PNG'   # GIF animado → PNG al procesar

            ext_salida = '.jpg' if fmt_salida == 'JPEG' else f'.{fmt_salida.lower()}'
            nombre     = f"{categoria}_{codigo}_{timestamp}{ext_salida}"
            destino    = carpeta / nombre

            # RGB obligatorio para JPG
            if fmt_salida == 'JPEG' and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            img.save(str(destino), format=fmt_salida, quality=88, optimize=True)

        return True, str(destino)

    except Exception as e:
        return False, f"Error al procesar imagen: {e}"


# ══════════════════════════════════════════════════════════════════
# MINIATURAS para la GUI
# ══════════════════════════════════════════════════════════════════

def generar_miniatura(ruta: str, size: Tuple[int,int] = THUMB_SIZE) -> Optional[object]:
    """
    Retorna un ImageTk.PhotoImage listo para usar en un Label de tkinter.
    Retorna None si Pillow no está disponible o hay error.
    """
    if not PILLOW_DISPONIBLE:
        return None
    try:
        with Image.open(ruta) as img:
            if img.format == 'GIF':
                img = img.convert('RGBA')
            img_copy = img.copy()
            img_copy.thumbnail(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img_copy)
    except Exception:
        return None


def info_imagen(ruta: str) -> str:
    """Devuelve un string con info básica: dimensiones, formato, tamaño."""
    if not PILLOW_DISPONIBLE or not Path(ruta).exists():
        return "Sin información"
    try:
        tamano_kb = Path(ruta).stat().st_size / 1024
        with Image.open(ruta) as img:
            return f"{img.format}  |  {img.width}×{img.height} px  |  {tamano_kb:.1f} KB"
    except Exception:
        return "No se pudo leer"