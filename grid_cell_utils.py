# grid_cell_utils.py
import pyautogui
import random
from typing import List, Tuple, Optional
from pathlib import Path
from screen_utils import Box, find_image_in_region

# Type hint for a cell: (left, top, width, height)
Cell = Tuple[int, int, int, int]


def get_grid_cell_coords(top_left_x: int, top_left_y: int, bottom_right_x: int, bottom_right_y: int,
                         rows: int, cols: int) -> List[Cell]:
    """Calculates coordinates for each cell in a grid."""
    if rows <= 0 or cols <= 0:
        raise ValueError("Rows and columns must be positive integers.")

    total_width = bottom_right_x - top_left_x
    total_height = bottom_right_y - top_left_y

    if total_width <= 0 or total_height <= 0:
        raise ValueError("Grid region must have a positive width and height.")

    cell_width = total_width / cols
    cell_height = total_height / rows

    grid_cells = []
    for row in range(rows):
        for col in range(cols):
            left = top_left_x + col * cell_width
            top = top_left_y + row * cell_height
            grid_cells.append(tuple(map(int, (left, top, cell_width, cell_height))))

    return grid_cells


def scan_grid_for_image(image_path: Path, grid_cells: List[Tuple[int, int, int, int]], confidence: float) -> List[
    Optional[Box]]:
    """
    그리드의 각 셀에서 이미지를 스캔하고, 찾은 위치(Box) 또는 None의 리스트를 반환합니다.
    """
    results = []
    for i, (left, top, width, height) in enumerate(grid_cells):
        region = (left, top, width, height)
        # 이미지를 찾으면 True/False가 아닌, 위치 객체(Box) 또는 None을 리스트에 추가
        location = find_image_in_region(image_path, region, confidence)
        results.append(location)

    return results


def click_randomly_in_cell(left: int, top: int, width: int, height: int):
    """
    지정된 사각형 영역의 중앙 80% 범위 내에서 랜덤한 위치를 클릭합니다.
    """
    # 너비의 10%를 좌/우 여백으로 사용 (총 20% 여백, 80% 클릭 영역)
    horizontal_margin = width * 0.15
    # 높이의 10%를 상/하 여백으로 사용 (총 20% 여백, 80% 클릭 영역)
    vertical_margin = height * 0.15

    x_min = int(left + horizontal_margin)
    x_max = int(left + width - horizontal_margin)

    y_min = int(top + vertical_margin)
    y_max = int(top + height - vertical_margin)

    # 클릭 가능한 영역이 있는지 확인
    if x_min >= x_max or y_min >= y_max:
        raise ValueError(f"Cell size ({width}x{height}) is too small to define a valid random click area.")

    click_x = random.randint(x_min, x_max)
    click_y = random.randint(y_min, y_max)

    pyautogui.click(click_x, click_y)
    print(f"Clicked position ({click_x}, {click_y}) within cell ({left},{top}, {width}x{height}).")


def click_randomly_in_grid_cell(cell_index: int, grid_cells: List[Cell]):
    """
    그리드의 특정 셀 내부에서 랜덤하게 클릭합니다. (padding 인수 제거)
    """
    if not (0 <= cell_index < len(grid_cells)):
        raise IndexError(f"Invalid cell index: {cell_index}. Must be between 0 and {len(grid_cells) - 1}.")

    left, top, width, height = grid_cells[cell_index]
    print(f"Requesting click for cell {cell_index}: ", end="")
    # padding 인수 없이 호출하도록 수정
    click_randomly_in_cell(left, top, width, height)