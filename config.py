# config.py
from dataclasses import dataclass, field
from pathlib import Path
import re

# --- Base Paths ---
ASSETS_DIR = Path("assets")

# --- Global Settings ---
GLOBAL_CONFIDENCE = 0.8
CLICK_DELAY_SECONDS = 0.03

# --- Dataclass Definitions for Typed Configs ---
@dataclass(frozen=True)
class GuiConfig:
    """GUI 애플리케이션 창의 설정을 관리합니다."""
    title: str = "자동화 시스템 v2.5"
    initial_width: int = 800
    initial_height: int = 620
    # 화면 좌상단으로부터의 X, Y 좌표 (픽셀 단위)
    initial_pos_x: int = 0
    initial_pos_y: int = 800

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

@dataclass(frozen=True)
class NpcConfig:
    """NPC의 상대 좌표 및 클릭 영역 설정"""
    name: str
    offset_x: int
    offset_y: int
    click_width: int = 10
    click_height: int = 10

@dataclass(frozen=True)
class FirestoreConfig:
    service_account_key_path: str = "serviceAccountKey.json"
    collection_name: str = "whispers"

@dataclass(frozen=True)
class SnifferConfig:
    interface: str = "이더넷"
    display_filter: str = 'tcp and data contains 04:00:30:00:00:00 and not data contains "Item" and data contains "-"'

@dataclass(frozen=True)
class WhisperParserConfig:
    header_pattern: re.Pattern = re.compile(r'544f5a20....0000ffffffff02')
    header_length: int = 106
    data_pattern: re.Pattern = re.compile(r'(.+?)0400..000000(.+?)0400..000000(.+?)040030000000')
    channel_pattern: re.Pattern = re.compile(r'[A-Z]-.\d*')
    # [수정] 사운드 파일 경로를 'assets' 폴더 포함하도록 변경
    sound_file_path: str = "assets/alert.mp3"

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

# --- Configuration Instances ---

# UI Elements
INVEN_CONFIG = WindowConfig(
    base_image_path=ASSETS_DIR / "inven.png",
    grid_offset_x=-5,
    grid_offset_y=58,
    grid_width=201,
    grid_height=291,
    grid_rows=6,
    grid_cols=4
)
POST_CONFIG = WindowConfig(
    base_image_path=ASSETS_DIR / "post.png",
    grid_offset_x=85,
    grid_offset_y=254,
    grid_width=349,
    grid_height=115,
    grid_rows=2,
    grid_cols=6
)
DELIVERY_BUTTONS: dict[str, ButtonConfig] = {
    "standard": ButtonConfig(offset_x=124, offset_y=25, width=80, height=25),
    "express": ButtonConfig(offset_x=208, offset_y=25, width=80, height=25),
    "receiver": ButtonConfig(offset_x=95, offset_y=126, width=58, height=20),
    "request": ButtonConfig(offset_x=264, offset_y=382, width=11, height=10),
    "value": ButtonConfig(offset_x=94, offset_y=410, width=14, height=17),
    "send": ButtonConfig(offset_x=343, offset_y=489, width=67, height=19),
}
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
DEWEY_CONFIG = NpcConfig(name="Dewey", offset_x=1208, offset_y=209)
DORAN_CONFIG = NpcConfig(name="Doran", offset_x=156, offset_y=199)

# Services
FIRESTORE_CONFIG = FirestoreConfig()
SNIFFER_CONFIG = SnifferConfig()
WHISPER_PARSER_CONFIG = WhisperParserConfig()
OVERLAY_CONFIG = OverlayConfig()
GUI_CONFIG = GuiConfig()