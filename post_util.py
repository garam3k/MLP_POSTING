# post_util.py
import time
from typing import List, Tuple, Optional

from config import CLICK_DELAY_SECONDS, DELIVERY_BUTTONS, POST_CONFIG, WindowConfig, GLOBAL_CONFIDENCE
from grid_cell_utils import click_randomly_in_cell, get_grid_cell_coords, click_randomly_in_grid_cell
import screen_utils
from screen_utils import Box

Cell = Tuple[int, int, int, int]


def get_post_grid_cells(config: WindowConfig) -> Optional[List[Cell]]:
    """우편 그리드 셀 좌표를 계산합니다."""
    print(f"\n--- 우편(B 그리드) 셀 계산 중 ---")
    base_location = screen_utils.find_image_on_screen(config.base_image_path, GLOBAL_CONFIDENCE)
    if not base_location:
        print("우편 기준 이미지를 찾지 못해 B 그리드 셀을 계산할 수 없습니다.")
        return None

    grid_tl_x = base_location.left + config.grid_offset_x
    grid_tl_y = base_location.top + config.grid_offset_y
    grid_br_x = grid_tl_x + config.grid_width
    grid_br_y = grid_tl_y + config.grid_height

    cells = get_grid_cell_coords(grid_tl_x, grid_tl_y, grid_br_x, grid_br_y, config.grid_rows, config.grid_cols)
    print(f"우편(B 그리드): {len(cells)}개의 셀이 계산되었습니다.")
    return cells


def click_post_grid_cell(cell_index: int, b_grid_cells: List[Cell]):
    """우편 그리드의 특정 셀을 클릭합니다."""
    click_randomly_in_grid_cell(cell_index, b_grid_cells)
    time.sleep(CLICK_DELAY_SECONDS)


def click_delivery_button(button_name: str):
    """지정된 배송 관련 버튼을 클릭합니다."""
    if button_name not in DELIVERY_BUTTONS:
        print(f"오류: '{button_name}' 버튼이 config에 정의되지 않았습니다.")
        return

    post_base_location = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if not post_base_location:
        print(f"오류: 우편 창 기준 이미지('{POST_CONFIG.base_image_path.name}')를 찾지 못했습니다.")
        return

    button_info = DELIVERY_BUTTONS[button_name]
    btn_x = post_base_location.left + button_info.offset_x
    btn_y = post_base_location.top + button_info.offset_y

    print(f"배송 버튼 클릭 시도: '{button_name}'...")
    click_randomly_in_cell(btn_x, btn_y, button_info.width, button_info.height)
    time.sleep(CLICK_DELAY_SECONDS)


def get_delivery_button_rects() -> Optional[List[Cell]]:
    """모든 배송 관련 버튼들의 화면 좌표를 계산합니다."""
    print("\n--- 배송 버튼 사각 영역 계산 중 ---")
    base_location = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if not base_location:
        print(f"우편 기준 이미지 ('{POST_CONFIG.base_image_path.name}')를 찾지 못했습니다.")
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
        print(f"  - 버튼 '{name}' 영역: {rect}")

    return button_rects


def click_receive_button():
    """우편 받기 버튼을 클릭합니다."""
    print("\n--- 우편 받기 버튼 클릭 ---")
    # 기존 버튼 클릭 함수를 재사용하여 일관성 유지
    click_delivery_button("receive")