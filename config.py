# config.py
from dataclasses import dataclass
from pathlib import Path

# --- Base Paths ---
ASSETS_DIR = Path("assets")

# --- Global Settings ---
GLOBAL_CONFIDENCE = 0.85
CLICK_DELAY_SECONDS = 0.045

# --- Configuration using Dataclasses for Clarity and Type Safety ---

@dataclass(frozen=True)
class WindowConfig:
    """Represents the configuration for a specific window's grid area."""
    base_image_path: Path
    grid_offset_x: int
    grid_offset_y: int
    grid_width: int
    grid_height: int
    grid_rows: int
    grid_cols: int

@dataclass(frozen=True)
class ButtonConfig:
    """Represents a single button's properties relative to a base image."""
    offset_x: int
    offset_y: int
    width: int
    height: int

@dataclass(frozen=True)
class ScrollCheckConfig:
    """Configuration for checking scroll status relative to a base image."""
    base_image_path: Path
    top_image_path: Path
    bottom_image_path: Path
    top_offset_x: int
    top_offset_y: int
    bottom_offset_x: int
    bottom_offset_y: int

# --- Inventory (A Grid) Configuration ---
# [수정됨] 사용자가 제공한 새로운 값으로 업데이트
INVEN_CONFIG = WindowConfig(
    base_image_path=ASSETS_DIR / "inven.png",
    grid_offset_x=-5,
    grid_offset_y=58,
    grid_width=201,
    grid_height=291,
    grid_rows=6,
    grid_cols=4
)
INVEN_SCAN_TARGET_IMAGE_PATH = ASSETS_DIR / "cider.png"

INVEN_SCROLL_CONFIG = ScrollCheckConfig(
    base_image_path=ASSETS_DIR / "inven.png",
    top_image_path=ASSETS_DIR / "scroll_top.png",
    bottom_image_path=ASSETS_DIR / "scroll_bottom.png",
    top_offset_x=50,
    top_offset_y=150,
    bottom_offset_x=50,
    bottom_offset_y=250,
)

# --- Post (B Grid) Configuration ---
# [수정됨] 사용자가 제공한 새로운 값으로 업데이트
POST_CONFIG = WindowConfig(
    base_image_path=ASSETS_DIR / "post.png",
    grid_offset_x=85,
    grid_offset_y=254,
    grid_width=349,
    grid_height=115,
    grid_rows=2,
    grid_cols=6
)

# --- Delivery Buttons Configuration ---
# [수정됨] 사용자가 제공한 새로운 값으로 업데이트
DELIVERY_BUTTONS: dict[str, ButtonConfig] = {
    "standard": ButtonConfig(offset_x=124, offset_y=25, width=80, height=25),
    "express": ButtonConfig(offset_x=208, offset_y=25, width=80, height=25),
    "receiver": ButtonConfig(offset_x=95, offset_y=126, width=58, height=20),
    "request": ButtonConfig(offset_x=264, offset_y=382, width=11, height=10),
    "value": ButtonConfig(offset_x=94, offset_y=410, width=14, height=17),
    "send": ButtonConfig(offset_x=343, offset_y=489, width=67, height=19),
}

# --- Debug Overlay Settings ---
@dataclass(frozen=True)
class OverlayConfig:
    """Typed configuration for debug overlays."""
    duration: float = 2.0
    thickness: int = 2
    color_grid_a: tuple[int, int, int] = (255, 0, 0)
    color_grid_b: tuple[int, int, int] = (0, 0, 255)
    color_button: tuple[int, int, int] = (0, 255, 0)
    color_base_image: tuple[int, int, int] = (255, 0, 255)
    color_coord_text: tuple[int, int, int] = (255, 255, 0)
    color_inven_item: tuple[int, int, int] = (0, 255, 255)


OVERLAY_CONFIG = OverlayConfig()