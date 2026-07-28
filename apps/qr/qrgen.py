"""QR image generation using the pure-Python `segno` library."""

import io

import segno


def generate_qr_png_data_uri(content: str, scale: int = 6) -> str:
    """Return a data URI containing a PNG QR code for `content`."""
    buffer = io.BytesIO()
    qr = segno.make(content, error="m")
    qr.save(buffer, kind="png", scale=scale, border=2)
    encoded = base64_encode(buffer.getvalue())
    return f"data:image/png;base64,{encoded}"


def generate_qr_png_bytes(content: str, scale: int = 6) -> bytes:
    buffer = io.BytesIO()
    qr = segno.make(content, error="m")
    qr.save(buffer, kind="png", scale=scale, border=2)
    return buffer.getvalue()


def base64_encode(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")
