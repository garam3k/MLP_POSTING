# inven_util.py
import time
from typing import Optional, List, Tuple

from config import (WindowConfig, ScrollCheckConfig, INVEN_SCAN_TARGET_IMAGE_PATH,
                    GLOBAL_CONFIDENCE, CLICK_DELAY_SECONDS, INVEN_SCROLL_CONFIG)
from grid_cell_utils import get_grid_cell_coords, click_randomly_in_grid_cell
import screen_utils
from screen_utils import Box

Cell = Tuple[int, int, int, int]


def get_inven_grid_cells(config: WindowConfig) -> Optional[List[Cell]]:
    """인벤토리 그리드 셀 좌표를 계산합니다."""
    print("\n--- 인벤토리(A 그리드) 셀 계산 중 ---")
    base_location = screen_utils.find_image_on_screen(config.base_image_path, GLOBAL_CONFIDENCE)
    if not base_location:
        print("인벤토리 기준 이미지를 찾지 못해 A 그리드 셀을 계산할 수 없습니다.")
        return None

    grid_tl_x = base_location.left + config.grid_offset_x
    grid_tl_y = base_location.top + config.grid_offset_y
    grid_br_x = grid_tl_x + config.grid_width
    grid_br_y = grid_tl_y + config.grid_height

    cells = get_grid_cell_coords(grid_tl_x, grid_tl_y, grid_br_x, grid_br_y, config.grid_rows, config.grid_cols)
    print(f"인벤토리(A 그리드): {len(cells)}개의 셀이 계산되었습니다.")
    return cells


def click_inven_grid_cell(cell_index: int, grid_cells: List[Cell]):
    """인벤토리 그리드의 특정 셀을 클릭합니다."""
    click_randomly_in_grid_cell(cell_index, grid_cells)
    time.sleep(CLICK_DELAY_SECONDS)


def is_scroll_at_limit(config: ScrollCheckConfig, check: str) -> bool:
    """인벤토리 스크롤이 최상단 또는 최하단에 있는지 확인합니다."""
    base_location = screen_utils.find_image_on_screen(config.base_image_path, GLOBAL_CONFIDENCE)
    if not base_location:
        return False

    if check == "top":
        image_path = config.top_image_path
        offset_x, offset_y = config.top_offset_x, config.top_offset_y
    elif check == "bottom":
        image_path = config.bottom_image_path
        offset_x, offset_y = config.bottom_offset_x, config.bottom_offset_y
    else:
        raise ValueError("Check 값은 'top' 또는 'bottom'이어야 합니다.")

    img_dims = screen_utils.get_image_dimensions(image_path)
    if not img_dims:
        return False

    check_x = base_location.left + offset_x
    check_y = base_location.top + offset_y
    region = (check_x, check_y, img_dims[0], img_dims[1])

    return screen_utils.find_image_in_region(image_path, region, GLOBAL_CONFIDENCE) is not None


def is_scroll_on_top() -> bool:
    return is_scroll_at_limit(INVEN_SCROLL_CONFIG, "top")


def is_scroll_on_bottom() -> bool:
    return is_scroll_at_limit(INVEN_SCROLL_CONFIG, "bottom")