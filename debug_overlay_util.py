# debug_overlay_util.py
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from screen_utils import Box

Rect = Tuple[int, int, int, int]
Color = Tuple[int, int, int]


def _get_font(size: int = 15) -> ImageFont.FreeTypeFont:
    """사용 가능한 경우 'malgun.ttf' 폰트를 로드하고, 없으면 기본 폰트를 반환합니다."""
    try:
        return ImageFont.truetype("malgun.ttf", size)
    except IOError:
        return ImageFont.load_default()


def draw_rects_on_image(image: Image.Image, rects: List[Rect], color: Color, thickness: int) -> Image.Image:
    """주어진 이미지 위에 여러 개의 사각형을 그립니다."""
    if not rects:
        return image

    draw = ImageDraw.Draw(image)
    for x, y, width, height in rects:
        draw.rectangle([x, y, x + width, y + height], outline=color, width=thickness)
    return image


def draw_base_info_on_image(image: Image.Image, location: Box, rect_color: Color, text_color: Color,
                            thickness: int) -> Image.Image:
    """주어진 이미지 위에 기준 이미지의 위치와 좌표 텍스트를 그립니다."""
    if not location:
        return image

    draw = ImageDraw.Draw(image)
    font = _get_font()

    rect = (location.left, location.top, location.width, location.height)
    draw.rectangle([rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]], outline=rect_color, width=thickness)

    text = f"({location.left}, {location.top})"
    text_pos = (location.left, location.top - 20 if location.top > 20 else location.top + location.height)
    draw.text(text_pos, text, fill=text_color, font=font, stroke_width=1, stroke_fill=(0, 0, 0))

    return image