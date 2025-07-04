# delivery.py
import time
from pathlib import Path

import pyautogui

import screen_utils
# --- 신규/수정된 임포트 ---
import shared_state
from config import (CLICK_DELAY_SECONDS, GLOBAL_CONFIDENCE, INVEN_CONFIG,
                    INVEN_SCAN_TARGET_IMAGE_PATH, OVERLAY_CONFIG, POST_CONFIG,
                    SEND_CHECK1_IMAGE_PATH, SEND_CHECK2_IMAGE_PATH)
from debug_overlay_util import draw_base_info_on_image, draw_rects_on_image
from grid_cell_utils import click_randomly_in_cell, scan_grid_for_image
from inven_util import (click_inven_grid_cell, find_item_by_scrolling,
                        get_inven_grid_cells)
from post_util import (click_delivery_button, click_post_grid_cell,
                       get_delivery_button_rects, get_post_grid_cells)
from screen_utils import paste_text


def _fill_post_with_items() -> bool:
    MAX_ATTEMPTS = 10
    for attempt in range(MAX_ATTEMPTS):
        if shared_state.stop_action:
            print("\n작업이 중단되었습니다.")
            return False

        print(f"\n--- 우편 채우기 시도 ({attempt + 1}/{MAX_ATTEMPTS}) ---")
        post_grid_cells = get_post_grid_cells(POST_CONFIG)
        if not post_grid_cells: return False
        empty_post_indices = [i for i, loc in enumerate(
            scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, post_grid_cells, GLOBAL_CONFIDENCE)) if loc is None]
        if not empty_post_indices: return True

        inven_grid_cells = get_inven_grid_cells(INVEN_CONFIG)
        if not inven_grid_cells: return False
        available_inven_indices = [i for i, loc in enumerate(
            scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, inven_grid_cells, GLOBAL_CONFIDENCE)) if loc is not None]

        if available_inven_indices:
            num_to_move = min(len(empty_post_indices), len(available_inven_indices))
            for i in range(num_to_move):
                if shared_state.stop_action: return False
                click_inven_grid_cell(available_inven_indices[i], inven_grid_cells)
                click_post_grid_cell(empty_post_indices[i], post_grid_cells)
            continue
        else:
            if not find_item_by_scrolling(INVEN_SCAN_TARGET_IMAGE_PATH):
                return False
            continue
    return False


def _wait_and_click_confirm(image_path: Path, timeout: int, description: str) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        if shared_state.stop_action:
            print("\n작업이 중단되었습니다.")
            return False
        location = screen_utils.find_image_on_screen(image_path, confidence=GLOBAL_CONFIDENCE)
        if location:
            click_randomly_in_cell(location.left, location.top, location.width, location.height)
            time.sleep(0.2)
            pyautogui.press('enter')
            return True
        time.sleep(0.2)
    return False


def send_action(delivery_type: str, receiver_name: str, amount: str) -> bool:
    if delivery_type not in ["standard", "express"]: return False

    click_delivery_button(delivery_type)
    if shared_state.stop_action: return False

    click_delivery_button("receiver")
    time.sleep(0.1)
    paste_text(receiver_name)
    if shared_state.stop_action: return False

    if not _fill_post_with_items(): return False
    if shared_state.stop_action: return False

    click_delivery_button("request")
    time.sleep(CLICK_DELAY_SECONDS)
    if shared_state.stop_action: return False

    click_delivery_button("value")
    time.sleep(CLICK_DELAY_SECONDS)
    pyautogui.write(amount)
    pyautogui.press('enter')
    if shared_state.stop_action: return False

    click_delivery_button("send")
    if not _wait_and_click_confirm(SEND_CHECK1_IMAGE_PATH, timeout=10, description="1차 확인"): return False
    if not _wait_and_click_confirm(SEND_CHECK2_IMAGE_PATH, timeout=20, description="최종 확인"): return False

    return True


def show_all_overlays_for_debugging():
    screenshot = pyautogui.screenshot()

    a_grid_cells = get_inven_grid_cells(INVEN_CONFIG)
    if a_grid_cells:
        screenshot = draw_rects_on_image(screenshot, a_grid_cells, OVERLAY_CONFIG.color_grid_a,
                                         OVERLAY_CONFIG.thickness)
        item_locations_boxes = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, a_grid_cells, GLOBAL_CONFIDENCE)
        item_rects = [tuple(loc) for loc in item_locations_boxes if loc]
        screenshot = draw_rects_on_image(screenshot, item_rects, OVERLAY_CONFIG.color_inven_item,
                                         OVERLAY_CONFIG.thickness)
    inven_base_location = screen_utils.find_image_on_screen(INVEN_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if inven_base_location:
        screenshot = draw_base_info_on_image(screenshot, inven_base_location, OVERLAY_CONFIG.color_base_image,
                                             OVERLAY_CONFIG.color_coord_text, OVERLAY_CONFIG.thickness)

    post_base_location = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if post_base_location:
        b_grid_cells = get_post_grid_cells(POST_CONFIG)
        if b_grid_cells:
            screenshot = draw_rects_on_image(screenshot, b_grid_cells, OVERLAY_CONFIG.color_grid_b,
                                             OVERLAY_CONFIG.thickness)
        button_rects = get_delivery_button_rects()
        if button_rects:
            screenshot = draw_rects_on_image(screenshot, button_rects, OVERLAY_CONFIG.color_button,
                                             OVERLAY_CONFIG.thickness)
        screenshot = draw_base_info_on_image(screenshot, post_base_location, OVERLAY_CONFIG.color_base_image,
                                             OVERLAY_CONFIG.color_coord_text, OVERLAY_CONFIG.thickness)

    screenshot.show(title="Debug Overlay (All-in-one)")