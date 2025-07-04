# inven_util.py
import time
from typing import Optional, List, Tuple
from pathlib import Path

import pyautogui
import screen_utils
from config import (WindowConfig, ScrollCheckConfig, GLOBAL_CONFIDENCE, CLICK_DELAY_SECONDS, INVEN_SCROLL_CONFIG,
                    ASSETS_DIR, INVEN_CONFIG)
from grid_cell_utils import get_grid_cell_coords, click_randomly_in_grid_cell, scan_grid_for_image, \
    click_randomly_in_cell

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
    """[수정됨] 인벤토리 스크롤이 최상단 또는 최하단에 있는지 확인합니다."""
    base_location = screen_utils.find_image_on_screen(config.base_image_path, GLOBAL_CONFIDENCE)
    if not base_location:
        print(f"스크롤 확인 실패: 기준 이미지 '{config.base_image_path.name}'를 찾을 수 없습니다.")
        return False

    image_path = None
    search_region = None

    if check == "top":
        image_path = ASSETS_DIR / "inventop.png"

        region_left = base_location.left + 155
        region_top = base_location.top + 50
        region_width = 200
        region_height = 100
        search_region = (region_left, region_top, region_width, region_height)

    elif check == "bottom":
        image_path = ASSETS_DIR / "invenbot.png"

        region_left = base_location.left + 155
        region_top = base_location.top + 300
        region_width = 200
        region_height = 100
        search_region = (region_left, region_top, region_width, region_height)
    else:
        raise ValueError("Check 값은 'top' 또는 'bottom'이어야 합니다.")

    return screen_utils.find_image_in_region(image_path, search_region, GLOBAL_CONFIDENCE) is not None


def is_scroll_on_top() -> bool:
    return is_scroll_at_limit(INVEN_SCROLL_CONFIG, "top")


def is_scroll_on_bottom() -> bool:
    return is_scroll_at_limit(INVEN_SCROLL_CONFIG, "bottom")


def scroll_to_top() -> bool:
    """인벤토리 스크롤을 최상단으로 올립니다. 성공 시 True, 실패 시 False를 반환합니다."""
    print("인벤토리 스크롤을 최상단으로 이동합니다...")
    inven_loc = screen_utils.find_image_on_screen(INVEN_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if not inven_loc:
        print("오류: 인벤토리 창을 찾을 수 없어 스크롤할 수 없습니다.")
        return False

    click_randomly_in_cell(inven_loc.left, inven_loc.top, inven_loc.width, inven_loc.height)

    for _ in range(30):
        if is_scroll_on_top():
            print("인벤토리 최상단에 도달했습니다.")
            return True
        pyautogui.scroll(200)
        time.sleep(0.1)

    print("경고: 최상단으로 스크롤하지 못했습니다.")
    return False


def find_item_by_scrolling(item_image_path: Path) -> bool:
    """인벤토리를 스크롤하며 특정 아이템을 찾습니다. 찾으면 True, 끝까지 못찾으면 False를 반환합니다."""
    if not scroll_to_top():
        return False

    max_scroll_attempts = 30  # 무한 루프 방지
    for i in range(max_scroll_attempts):
        # 1. 현재 뷰에서 아이템 스캔
        grid_cells = get_inven_grid_cells(INVEN_CONFIG)
        if grid_cells:
            locations = scan_grid_for_image(item_image_path, grid_cells, GLOBAL_CONFIDENCE)
            if any(loc is not None for loc in locations):
                print(f"스크롤 중 '{item_image_path.name}' 아이템을 발견했습니다.")
                return True  # 아이템 찾음, 성공

        # 2. 스크롤하기 전, 최하단인지 먼저 확인
        if is_scroll_on_bottom():
            print("인벤토리 최하단입니다. 더 이상 스크롤할 수 없습니다.")
            # 혹시 모르니 마지막으로 한 번 더 스캔
            grid_cells = get_inven_grid_cells(INVEN_CONFIG)
            if grid_cells and any(
                    loc is not None for loc in scan_grid_for_image(item_image_path, grid_cells, GLOBAL_CONFIDENCE)):
                print(f"최하단에서 '{item_image_path.name}' 아이템을 발견했습니다.")
                return True

            print(f"최종적으로 '{item_image_path.name}'을(를) 인벤토리에서 찾지 못했습니다.")
            return False  # 최하단 도달, 아이템 없음

        # 3. 최하단이 아닐 경우에만 아래로 스크롤
        print(f"아이템 미발견, 아래로 스크롤합니다... (시도 {i + 1}/{max_scroll_attempts})")
        for _ in range(6):
            # 매 스크롤마다 최하단에 도달했는지 다시 확인하여 불필요한 스크롤 방지
            if is_scroll_on_bottom():
                print("스크롤 중 최하단에 도달하여 중단합니다.")
                break
            pyautogui.scroll(-100)  # 아래로 스크롤
            time.sleep(0.05)

        time.sleep(0.2)  # 스크롤 후 UI가 안정될 때까지 대기

    print("경고: 최대 스크롤 시도 횟수에 도달했습니다.")
    return False