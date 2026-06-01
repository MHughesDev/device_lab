"""
Observation extension tools — OCR and visual text search.
Implemented at the control-plane level: take screenshot → run pytesseract.
Falls back gracefully if pytesseract is not installed.
"""
from __future__ import annotations
import asyncio
import base64

from app.mcp.gateway import mcp
from app.mcp.dispatch import get_device_and_family, screenshot_b64_for_device


def _png_bytes(device_id: str) -> bytes | None:
    b64 = asyncio.get_event_loop().run_until_complete(screenshot_b64_for_device(device_id))
    if not b64:
        return None
    return base64.b64decode(b64)


@mcp.tool()
def ocr_screenshot(device_id: str) -> dict:
    """
    Run OCR on the current device screen. Returns all visible text as a string.
    Requires pytesseract + tesseract-ocr to be installed on the control plane.
    """
    try:
        import pytesseract  # type: ignore[import]
        from PIL import Image  # type: ignore[import]
        from io import BytesIO
    except ImportError:
        return {"error": "pytesseract and Pillow are required: pip install pytesseract Pillow"}

    png = _png_bytes(device_id)
    if png is None:
        return {"error": "Screenshot failed"}

    img = Image.open(BytesIO(png))
    text = pytesseract.image_to_string(img)
    return {"device_id": device_id, "text": text.strip()}


@mcp.tool()
def find_on_screen(device_id: str, text: str) -> dict:
    """
    Search for a text string on screen using OCR. Returns the bounding box
    {x, y, width, height} of the first match, or found=False if not present.
    Use the returned x + width/2, y + height/2 to calculate the click target.
    """
    try:
        import pytesseract  # type: ignore[import]
        from PIL import Image  # type: ignore[import]
        from io import BytesIO
    except ImportError:
        return {"error": "pytesseract and Pillow are required: pip install pytesseract Pillow"}

    png = _png_bytes(device_id)
    if png is None:
        return {"error": "Screenshot failed"}

    img = Image.open(BytesIO(png))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    search = text.lower()
    for i, word in enumerate(data["text"]):
        if search in word.lower() and int(data["conf"][i]) > 30:
            x = data["left"][i]
            y = data["top"][i]
            w = data["width"][i]
            h = data["height"][i]
            return {
                "found": True,
                "text": word,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "center_x": x + w // 2,
                "center_y": y + h // 2,
            }

    return {"found": False, "text": text}
