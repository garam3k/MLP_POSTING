# post_util.py
import time
from typing import List, Tuple, Optional
from config import CLICK_DELAY_SECONDS, DELIVERY_BUTTONS, POST_CONFIG, WindowConfig, GLOBAL_CONFIDENCE
from grid_cell_utils import click_randomly_in_cell, get_grid_cell_coords, click_randomly_in_grid_cell
import screen_utils

Cell = Tuple[int, int, int, int]


def get_post_grid_cells(config: WindowConfig) -> Optional[List[Cell]]:
    """Calculates post (B) grid cell coordinates."""
    print(f"\n--- Calculating Post (B) Grid Cells ---")
    # [수정된 부분] config.GLOBAL_CONFIDENCE -> GLOBAL_CONFIDENCE
    base_location = screen_utils.find_image_on_screen(config.base_image_path, GLOBAL_CONFIDENCE)
    if not base_location:
        print("Post base image not found. Cannot calculate B Grid cells.")
        return None

    grid_tl_x = base_location.left + config.grid_offset_x
    grid_tl_y = base_location.top + config.grid_offset_y
    grid_br_x = grid_tl_x + config.grid_width
    grid_br_y = grid_tl_y + config.grid_height

    cells = get_grid_cell_coords(grid_tl_x, grid_tl_y, grid_br_x, grid_br_y, config.grid_rows, config.grid_cols)
    print(f"Post (B) Grid: {len(cells)} cells calculated.")
    return cells


def click_post_grid_cell(cell_index: int, b_grid_cells: List[Cell]):
    """Clicks a specific cell within the post grid."""
    # padding 인수 없이 호출하도록 수정
    click_randomly_in_grid_cell(cell_index, b_grid_cells)
    time.sleep(CLICK_DELAY_SECONDS)


def click_delivery_button(button_name: str):
    """Finds the post window and clicks a specified delivery button."""
    if button_name not in DELIVERY_BUTTONS:
        print(f"Error: Button '{button_name}' not defined in config.")
        return

    post_base_location = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if not post_base_location:
        print(f"Error: Base image for Post window ('{POST_CONFIG.base_image_path.name}') not found.")
        return

    button_info = DELIVERY_BUTTONS[button_name]
    btn_x = post_base_location.left + button_info.offset_x
    btn_y = post_base_location.top + button_info.offset_y

    print(f"Attempting to click delivery button: '{button_name}'...")
    # padding 인수 없이 호출하도록 수정
    click_randomly_in_cell(btn_x, btn_y, button_info.width, button_info.height)
    time.sleep(CLICK_DELAY_SECONDS)


def get_delivery_button_rects() -> Optional[List[Cell]]:
    """Calculates the on-screen coordinates and sizes of all delivery buttons."""
    print("\n--- Calculating Delivery Button Rectangles ---")
    base_location = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if not base_location:
        print(f"Post base image ('{POST_CONFIG.base_image_path.name}') not found.")
        return None

    button_rects = []
    for name, info in DELIVERY_BUTTONS.items():
        rect = (
            base_location.left + info.offset_x,
            base_location.top + info.offset_y,
            info.width,
            info.height
        )
        button_rects.append(rect)
        print(f"  - Button '{name}' rectangle: {rect}")

    return button_rects