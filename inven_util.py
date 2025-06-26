# inven_util.py
import time
from typing import Optional, List, Tuple

# config.py에서 필요한 모든 클래스와 상수를 임포트합니다.
from config import (WindowConfig, ScrollCheckConfig, INVEN_SCAN_TARGET_IMAGE_PATH,
                    GLOBAL_CONFIDENCE, CLICK_DELAY_SECONDS, INVEN_CONFIG, INVEN_SCROLL_CONFIG)

from grid_cell_utils import get_grid_cell_coords, scan_grid_for_image, click_randomly_in_grid_cell
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


def perform_inven_grid_actions(inven_config: WindowConfig) -> Optional[Tuple[List[Cell], List[int], List[Box]]]:
    """
    인벤토리 그리드를 계산하고, 대상 이미지를 스캔하여
    (1) 전체 그리드 셀, (2) 클릭할 셀 인덱스, (3) 찾은 아이템의 실제 위치(Box)를 반환합니다.
    """
    grid_cells = get_inven_grid_cells(inven_config)
    if not grid_cells:
        return None

    print(f"A 그리드에서 '{INVEN_SCAN_TARGET_IMAGE_PATH.name}' 스캔 중...")
    found_locations = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, grid_cells, GLOBAL_CONFIDENCE)

    cells_to_click = [i for i, loc in enumerate(found_locations) if loc is not None]
    item_locations = [loc for loc in found_locations if loc is not None]

    print(f"A 그리드: {len(cells_to_click)}개의 대상 이미지를 찾았습니다.")

    if not cells_to_click:
        print("경고: 인벤토리 그리드에서 대상 아이템을 찾지 못했습니다.")

    return grid_cells, cells_to_click, item_locations


def click_inven_grid_cell(cell_index: int, grid_cells: List[Cell]):
    """인벤토리 그리드의 특정 셀을 클릭합니다."""
    click_randomly_in_grid_cell(cell_index, grid_cells)
    time.sleep(CLICK_DELAY_SECONDS)


def is_scroll_at_limit(config: ScrollCheckConfig, check: str) -> bool:
    """
    인벤토리 스크롤이 최상단 또는 최하단에 있는지 확인합니다.
    """
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


# 스크롤 확인을 위한 헬퍼 함수
def is_scroll_on_top() -> bool:
    return is_scroll_at_limit(INVEN_SCROLL_CONFIG, "top")


def is_scroll_on_bottom() -> bool:
    return is_scroll_at_limit(INVEN_SCROLL_CONFIG, "bottom")