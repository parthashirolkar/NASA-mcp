import io
from PIL import Image
from mcp.types import ImageContent


def _encode_image(image) -> ImageContent:
    """Encodes a PIL Image to a format compatible with ImageContent."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_obj = Image(data=img_bytes, format="png")
    return img_obj.to_image_content()
