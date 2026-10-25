"""Image preparation for insertion into the generated document.

python-docx inserts images at a chosen width and scales height proportionally on
its own, so the main job here is: validate the file, normalise the format (e.g.
WEBP, which Word can't embed directly) and decide a sensible width in cm.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from PIL import Image, UnidentifiedImageError

SUPPORTED_INPUT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
# Formats Word/python-docx can embed directly without conversion.
NATIVE_DOCX = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

DEFAULT_MAX_WIDTH_CM = 8.0


class ImageError(Exception):
    """Raised with a friendly message when an image can't be used."""


def _emu_per_cm() -> int:
    # 1 cm = 360000 EMU (English Metric Units) used by Office.
    return 360000


def prepare_image(
    path: str, max_width_cm: float = DEFAULT_MAX_WIDTH_CM
) -> "PreparedImage":
    """Validate and (if needed) convert an image for docx insertion.

    Returns a :class:`PreparedImage` carrying the path to embed and the width to
    use. Raises :class:`ImageError` for anything the user might have done wrong.
    """
    if not path or not os.path.isfile(path):
        raise ImageError("That image file doesn't exist any more.")

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_INPUT:
        raise ImageError(
            "That file type isn't supported. Please use a JPEG, PNG or WEBP image."
        )

    try:
        with Image.open(path) as img:
            img.verify()  # cheap integrity check
        with Image.open(path) as img:
            width_px, height_px = img.size
            needs_convert = ext not in NATIVE_DOCX
            embed_path = path
            if needs_convert:
                embed_path = _convert_to_png(img)
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageError(
            "Couldn't read that image — is it a valid JPEG, PNG or WEBP?"
        ) from exc

    if width_px <= 0 or height_px <= 0:
        raise ImageError("That image appears to be empty.")

    # Don't upscale tiny images past their natural size.
    natural_width_cm = width_px / 96.0 * 2.54  # assume 96 dpi source
    width_cm = min(max_width_cm, natural_width_cm) if natural_width_cm else max_width_cm
    width_cm = max(1.0, width_cm)

    return PreparedImage(
        embed_path=embed_path,
        width_cm=width_cm,
        is_temp=needs_convert,
    )


def _convert_to_png(img: "Image.Image") -> str:
    """Save a copy of ``img`` as a temp PNG and return its path."""
    rgb = img.convert("RGBA") if img.mode in ("P", "LA") else img.convert("RGB")
    fd, tmp = tempfile.mkstemp(suffix=".png", prefix="pprbase_img_")
    os.close(fd)
    rgb.save(tmp, format="PNG")
    return tmp


class PreparedImage:
    """A docx-ready image: where to embed from and how wide to draw it."""

    def __init__(self, embed_path: str, width_cm: float, is_temp: bool) -> None:
        self.embed_path = embed_path
        self.width_cm = width_cm
        self.is_temp = is_temp

    def width_emu(self) -> int:
        return int(self.width_cm * _emu_per_cm())

    def cleanup(self) -> None:
        """Delete the temp file if this image was converted."""
        if self.is_temp and os.path.isfile(self.embed_path):
            try:
                os.remove(self.embed_path)
            except OSError:
                pass


def make_thumbnail(path: str, max_px: int = 240) -> Optional[bytes]:
    """Return PNG bytes of a downscaled preview, or ``None`` if it can't load.

    Used by the UI image picker for a preview without depending on Qt here.
    """
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((max_px, max_px))
            import io

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    except (UnidentifiedImageError, OSError):
        return None
