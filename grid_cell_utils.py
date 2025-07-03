# grid_cell_utils.py
import random
from pathlib import Path
from typing import List, Tuple, Optional

import pyautogui

from screen_utils import Box, find_image_in_region

Cell = Tuple[int, int, int, int]


def get_grid_cell_coords(top_left_x: int, top_left_y: int, bottom_right_x: int, bottom_right_y: int,
                         rows: int, cols: int) -> List[Cell]:
    """그리드 내 각 셀의 좌표를 계산합니다."""
    if rows <= 0 or cols <= 0:
        raise ValueError("행과 열은 양수여야 합니다.")

    total_width = bottom_right_x - top_left_x
    total_height = bottom_right_y - top_left_y

    if total_width <= 0 or total_height <= 0:
        raise ValueError("그리드 영역은 양의 너비와 높이를 가져야 합니다.")

    cell_width = total_width / cols
    cell_height = total_height / rows

    grid_cells = []
    for row in range(rows):
        for col in range(cols):
            left = top_left_x + col * cell_width
            top = top_left_y + row * cell_height
            grid_cells.append(tuple(map(int, (left, top, cell_width, cell_height))))

    return grid_cells


def scan_grid_for_image(image_path: Path, grid_cells: List[Cell], confidence: float) -> List[Optional[Box]]:
    """그리드의 각 셀에서 이미지를 스캔하고, 찾은 위치 또는 None의 리스트를 반환합니다."""
    results = []
    for i, (left, top, width, height) in enumerate(grid_cells):
        region = (left, top, width, height)
        location = find_image_in_region(image_path, region, confidence)
        results.append(location)

    return results


def click_randomly_in_cell(left: int, top: int, width: int, height: int):
    """지정된 사각형 영역의 중앙 80% 범위 내에서 랜덤한 위치를 클릭합니다."""
    horizontal_margin = width * 0.2
    vertical_margin = height * 0.2

    x_min = int(left + horizontal_margin)
    x_max = int(left + width - horizontal_margin)
    y_min = int(top + vertical_margin)
    y_max = int(top + height - vertical_margin)

    if x_min >= x_max or y_min >= y_max:
        raise ValueError(f"셀 크기({width}x{height})가 너무 작아 유효한 클릭 영역을 정의할 수 없습니다.")

    click_x = random.randint(x_min, x_max)
    click_y = random.randint(y_min, y_max)

    pyautogui.click(click_x, click_y)
    print(f"클릭: ({click_x}, {click_y}) / 영역: ({left},{top}, {width}x{height}).")


def click_randomly_in_grid_cell(cell_index: int, grid_cells: List[Cell]):
    """그리드의 특정 셀 내부에서 랜덤하게 클릭합니다."""
    if not (0 <= cell_index < len(grid_cells)):
        raise IndexError(f"잘못된 셀 인덱스: {cell_index}. 범위: 0 ~ {len(grid_cells) - 1}.")

    left, top, width, height = grid_cells[cell_index]
    print(f"셀 #{cell_index} 클릭 요청: ", end="")
    click_randomly_in_cell(left, top, width, height)