import io
import base64
from PIL import Image as PILImage
from mcp.types import ImageContent


def _encode_image(image) -> ImageContent:
    """Encodes a PIL Image to a format compatible with ImageContent."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return ImageContent(
        type="image",
        data=img_base64,
        mimeType="image/png"
    )
