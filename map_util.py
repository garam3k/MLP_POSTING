# map_util.py
import random
import threading
import time
from typing import Callable, Optional

import pyautogui
import pygetwindow as gw
from pynput import keyboard as pynput_keyboard

import screen_utils
# --- 신규/수정된 임포트 ---
import shared_state
from config import (ASSETS_DIR, DEWEY_CONFIG, DORAN_CONFIG, GLOBAL_CONFIDENCE,
                    INVEN_SCAN_TARGET_IMAGE_PATH)
from grid_cell_utils import click_randomly_in_cell
from window_util import activate_maple_window, resize_window


def _interruptible_sleep(duration: float):
    """shared_state.stop_action 플래그에 의해 중단될 수 있는 time.sleep 버전"""
    end_time = time.time() + duration
    while time.time() < end_time:
        if shared_state.stop_action:
            break
        time.sleep(0.1)


class ClickBot:
    def __init__(self, button_pos: tuple[int, int]):
        self.button_pos = button_pos
        self._is_running = False
        self.click_count = 0
        self._thread = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def _click_worker(self):
        while self._is_running and not shared_state.stop_action:
            pyautogui.click(self.button_pos)
            self.click_count += 1
        self._is_running = False

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._is_running = True
        self._thread = threading.Thread(target=self._click_worker, daemon=True)
        self._thread.start()

    def stop(self) -> int:
        if not self._is_running: return self.click_count
        self._is_running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        return self.click_count


def prepare_and_activate_window(sequence_name: str) -> bool:
    if not activate_maple_window(): return False
    print(f"\n--- {sequence_name} 시퀀스 시작 ---")

    # [수정] 자동화된 키 입력을 하는 동안 단축키 감지를 비활성화
    shared_state.ignore_hotkeys = True
    try:
        pyautogui.press('esc', presses=5, interval=0.1)
    finally:
        # 작업이 끝나면 반드시 플래그를 원상 복구
        shared_state.ignore_hotkeys = False

    _interruptible_sleep(0.2)
    return True


def _get_target_window_and_check_size(expected_width: int, expected_height: int) -> Optional[gw.Win32Window]:
    try:
        window_list = gw.getWindowsWithTitle('MapleStory Worlds-Mapleland')
        if not window_list: return None
        window = window_list[0]
        if window.size == (expected_width, expected_height):
            return window
        return None
    except Exception:
        return None


def is_market() -> bool:
    window = _get_target_window_and_check_size(1366, 768)
    if not window: return False
    return screen_utils.find_image_in_region(ASSETS_DIR / "market.png", region=window.box,
                                             confidence=GLOBAL_CONFIDENCE) is not None


def is_village() -> bool:
    window = _get_target_window_and_check_size(1366, 768)
    if not window: return False
    return screen_utils.find_image_in_region(ASSETS_DIR / "maul.png", region=window.box,
                                             confidence=GLOBAL_CONFIDENCE) is not None


def click_npc(npc_config):
    window = _get_target_window_and_check_size(1900, 300)
    if not window: return
    click_center_x = window.left + npc_config.offset_x
    click_center_y = window.top + npc_config.offset_y
    click_randomly_in_cell(click_center_x - (npc_config.click_width // 2),
                           click_center_y - (npc_config.click_height // 2), npc_config.click_width,
                           npc_config.click_height)


def click_dewey():
    click_npc(DEWEY_CONFIG)


def click_doran():
    click_npc(DORAN_CONFIG)


def _wait_for_map_change(check_function: Callable[[], bool], timeout: int = 30) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        if shared_state.stop_action:
            print("\n작업이 중단되었습니다.")
            return False
        if check_function():
            return True
        time.sleep(1)
    return False


def _move_map():
    pyautogui.press('up')
    _interruptible_sleep(0.2)


def goto_village():
    if is_village(): return
    _move_map()
    _wait_for_map_change(is_village)


def goto_market():
    if is_market(): return
    _move_map()
    _wait_for_map_change(is_market)


def open_shop():
    if not prepare_and_activate_window("상점 열기"): return
    if shared_state.stop_action: return
    goto_market()
    if shared_state.stop_action: return
    resize_window(1900, 300)
    _interruptible_sleep(1)
    if shared_state.stop_action: return
    click_doran()
    _interruptible_sleep(1)
    if shared_state.stop_action: return
    resize_window(1366, 768)
    _interruptible_sleep(1)
    if shared_state.stop_action: return

    search_region = (350, 300, 250, 300)
    cider_location = screen_utils.find_image_in_region(INVEN_SCAN_TARGET_IMAGE_PATH, region=search_region,
                                                       confidence=GLOBAL_CONFIDENCE)
    if not cider_location: return
    click_randomly_in_cell(cider_location.left, cider_location.top, cider_location.width, cider_location.height)
    _interruptible_sleep(0.5)

    buy_button_pos = (603, 206)
    nomore_image_path = ASSETS_DIR / "nomore.png"
    click_bot = ClickBot(button_pos=buy_button_pos)
    click_bot.start()

    nomore_search_region = (390, 90, 165, 62)
    start_time = time.time()
    while time.time() - start_time < 30:
        if shared_state.stop_action: break
        if screen_utils.find_image_in_region(nomore_image_path, region=nomore_search_region,
                                             confidence=GLOBAL_CONFIDENCE): break
        time.sleep(0.1)

    click_bot.stop()


def open_post():
    if not prepare_and_activate_window("우체통 열기"): return
    if shared_state.stop_action: return
    goto_village()
    if shared_state.stop_action: return
    resize_window(1900, 300)
    _interruptible_sleep(1.5)
    if shared_state.stop_action: return
    click_dewey()
    _interruptible_sleep(1.5)
    if shared_state.stop_action: return
    resize_window(1366, 768)
    _interruptible_sleep(1.5)

    inven_image_path = ASSETS_DIR / "inven.png"
    start_time = time.time()
    inventory_opened = False
    while time.time() - start_time < 10:
        if shared_state.stop_action: break
        inven_location = screen_utils.find_image_on_screen(inven_image_path, confidence=GLOBAL_CONFIDENCE)
        if inven_location:
            inventory_opened = True
            break
        pyautogui.press('i')
        _interruptible_sleep(1)

    if not inventory_opened or shared_state.stop_action: return

    if inven_location:
        start_x = random.randint(inven_location.left, inven_location.left + inven_location.width)
        start_y = random.randint(inven_location.top, inven_location.top + inven_location.height)
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(start_x + 200, start_y, duration=0.5)