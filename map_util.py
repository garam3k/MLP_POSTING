# map_util.py
import random
import threading
import time
from typing import Optional, Callable

import pyautogui
import pygetwindow as gw
from pynput import keyboard as pynput_keyboard

import screen_utils
from config import ASSETS_DIR, GLOBAL_CONFIDENCE, DEWEY_CONFIG, DORAN_CONFIG, INVEN_SCAN_TARGET_IMAGE_PATH
from grid_cell_utils import click_randomly_in_cell
from window_util import WINDOW_TITLE, resize_window, activate_maple_window


# --- [신규] 반복 클릭 스레드를 관리하는 클래스 ---
class ClickBot:
    """
    백그라운드에서 반복적인 클릭을 수행하고 상태를 관리하는 스레드 제어 클래스.
    """

    def __init__(self, button_pos: tuple[int, int]):
        """
        Args:
            button_pos (tuple[int, int]): 클릭할 화면의 (x, y) 좌표.
        """
        self.button_pos = button_pos
        self._is_running = False
        self.click_count = 0
        self._thread = None

    @property
    def is_running(self) -> bool:
        """스레드가 현재 실행 중인지 여부를 반환합니다."""
        return self._is_running

    def _click_worker(self):
        """실제로 클릭을 수행하는 워커 함수. 스레드에서 실행됩니다."""
        print("백그라운드 클릭 스레드 시작...")
        while self._is_running:
            pyautogui.click(self.button_pos)
            self.click_count += 1
        print(f"백그라운드 클릭 스레드 정지. (최종 클릭 수: {self.click_count})")

    def start(self):
        """클릭 작업을 시작합니다."""
        if self._thread and self._thread.is_alive():
            print("경고: 클릭 스레드가 이미 실행 중입니다.")
            return

        self._is_running = True
        # 데몬 스레드로 설정하여 메인 프로그램 종료 시 함께 종료되도록 함
        self._thread = threading.Thread(target=self._click_worker, daemon=True)
        self._thread.start()

    def stop(self) -> int:
        """클릭 작업을 중지하고 총 클릭 횟수를 반환합니다."""
        if not self._is_running:
            return self.click_count

        self._is_running = False
        if self._thread:
            # 스레드가 완전히 종료될 때까지 최대 1초 대기
            self._thread.join(timeout=1.0)

        return self.click_count


# --- 전역 변수 및 키보드 리스너 콜백 함수 ---
# 동작 중단 플래그
stop_action = False


def on_press(key):
    """키보드 입력 감지 시 호출될 콜백 함수"""
    global stop_action
    try:
        # ESC 키가 눌렸는지 확인
        if key == pynput_keyboard.Key.esc:
            print("\n[중단 신호] ESC 키가 감지되었습니다. 현재 동작을 중단합니다.")
            stop_action = True
            # 리스너 자체를 중지하여 더 이상 입력을 받지 않음
            return False
    except Exception as e:
        print(f"키보드 리스너 콜백 함수에서 오류 발생: {e}")


# [신규] 중복 코드를 제거하기 위한 공통 초기화 함수
def prepare_and_activate_window(sequence_name: str) -> bool:
    """
    공통 시퀀스 초기화 작업을 수행합니다: 창 활성화, 시퀀스 이름 출력, ESC 연타.
    성공 시 True, 창 활성화 실패 시 False를 반환합니다.
    """
    if not activate_maple_window():
        return False

    print(f"\n--- {sequence_name} 시퀀스 시작 ---")
    print("초기화 동작: ESC 5회 입력")
    pyautogui.press('esc', presses=5, interval=0.1)
    time.sleep(0.2)
    return True


def _get_target_window_and_check_size(expected_width: int, expected_height: int) -> Optional[gw.Win32Window]:
    """
    타겟 윈도우를 찾고, 기대하는 크기와 일치하는지 확인합니다.
    일치하면 윈도우 객체를, 아니면 None을 반환합니다.
    """
    try:
        window_list = gw.getWindowsWithTitle(WINDOW_TITLE)
        if not window_list:
            print(f"'{WINDOW_TITLE}' 창을 찾을 수 없습니다.")
            return None

        window = window_list[0]
        current_width, current_height = window.size

        if (current_width, current_height) == (expected_width, expected_height):
            return window
        else:
            print(f"경고: 현재 창 크기({current_width}x{current_height})가 기대 크기({expected_width}x{expected_height})와 다릅니다.")
            return None
    except Exception as e:
        print(f"윈도우 정보 확인 중 오류 발생: {e}")
        return None


def is_market() -> bool:
    """
    현재 맵이 마켓인지 확인합니다. (창 크기 1366x768 전용)
    """
    window = _get_target_window_and_check_size(1366, 768)
    if not window:
        return False

    image_path = ASSETS_DIR / "market.png"
    haystack_region = window.box
    location = screen_utils.find_image_in_region(image_path, region=haystack_region, confidence=GLOBAL_CONFIDENCE)

    if location:
        print("마켓 이미지를 찾았습니다.")
        return True
    else:
        return False


def is_village() -> bool:
    """
    현재 맵이 마을인지 확인합니다. (창 크기 1366x768 전용)
    """
    window = _get_target_window_and_check_size(1366, 768)
    if not window:
        return False

    image_path = ASSETS_DIR / "maul.png"
    haystack_region = window.box
    location = screen_utils.find_image_in_region(image_path, region=haystack_region, confidence=GLOBAL_CONFIDENCE)

    if location:
        print("마을 이미지를 찾았습니다.")
        return True
    else:
        return False


def click_dewey():
    """
    NPC 듀이의 고정 좌표를 클릭합니다. (창 크기 1900x300 전용)
    """
    window = _get_target_window_and_check_size(1900, 300)
    if not window:
        return

    print(f"NPC {DEWEY_CONFIG.name}의 고정 좌표로 클릭합니다...")
    click_center_x = window.left + DEWEY_CONFIG.offset_x
    click_center_y = window.top + DEWEY_CONFIG.offset_y
    click_area_left = click_center_x - (DEWEY_CONFIG.click_width // 2)
    click_area_top = click_center_y - (DEWEY_CONFIG.click_height // 2)

    click_randomly_in_cell(
        click_area_left,
        click_area_top,
        DEWEY_CONFIG.click_width,
        DEWEY_CONFIG.click_height
    )


def click_doran():
    """
    NPC 도란의 고정 좌표를 클릭합니다. (창 크기 1900x300 전용)
    """
    window = _get_target_window_and_check_size(1900, 300)
    if not window:
        return

    print(f"NPC {DORAN_CONFIG.name}의 고정 좌표로 클릭합니다...")
    click_center_x = window.left + DORAN_CONFIG.offset_x
    click_center_y = window.top + DORAN_CONFIG.offset_y
    click_area_left = click_center_x - (DORAN_CONFIG.click_width // 2)
    click_area_top = click_center_y - (DORAN_CONFIG.click_height // 2)

    click_randomly_in_cell(
        click_area_left,
        click_area_top,
        DORAN_CONFIG.click_width,
        DORAN_CONFIG.click_height
    )


def _wait_for_map_change(check_function: Callable[[], bool], timeout: int = 30) -> bool:
    """
    지정된 맵 확인 함수가 True를 반환할 때까지 대기합니다.
    """
    start_time = time.time()
    print("맵 로딩 대기 중...", end="")
    while time.time() - start_time < timeout:
        print(".", end="", flush=True)
        if check_function():
            print("\n맵 로딩 완료.")
            return True
        time.sleep(1)

    print(f"\n시간 초과: {timeout}초 내에 맵 이동을 확인하지 못했습니다.")
    return False


def _move_map():
    """
    두 맵 사이를 이동하는 공통 동작을 수행합니다.
    """
    print("맵 이동 시퀀스 시작: 방향키(위) 1회")
    pyautogui.press('up')
    time.sleep(0.2)


def goto_village():
    """
    현재 위치가 마을이 아니면 마을로 이동을 시도합니다. (창 크기 1366x768 전용)
    """
    if not _get_target_window_and_check_size(1366, 768):
        return

    if is_village():
        print("이미 마을에 있습니다.")
        return

    _move_map()
    _wait_for_map_change(is_village)


def goto_market():
    """
    현재 위치가 마켓이 아니면 마켓으로 이동을 시도합니다. (창 크기 1366x768 전용)
    """
    if not _get_target_window_and_check_size(1366, 768):
        return

    if is_market():
        print("이미 마켓에 있습니다.")
        return

    _move_map()
    _wait_for_map_change(is_market)


def open_shop():
    """
    [수정됨] 마켓으로 이동하여 상점을 열고, 지정된 아이템을 반복 구매합니다.
    클릭은 백그라운드 스레드에서 초고속으로 수행되며, 메인 스레드는 중단 조건(이미지 발견, ESC)을 감시합니다.
    """
    # [수정] 공통 초기화 함수 호출
    if not prepare_and_activate_window("상점 열기"):
        return

    goto_market()

    print("해상도를 1900x300으로 변경합니다.")
    resize_window(1900, 300)
    time.sleep(1)

    click_doran()
    time.sleep(1)

    print("해상도를 1366x768로 복구합니다.")
    resize_window(1366, 768)
    time.sleep(1)

    print("\n[아이템 구매 단계] 상점에서 아이템 구매를 시작합니다.")
    search_region = (350, 300, 250, 300)
    print(f"'{INVEN_SCAN_TARGET_IMAGE_PATH.name}' 이미지를 영역 {search_region} 내에서 검색합니다.")

    cider_location = screen_utils.find_image_in_region(
        INVEN_SCAN_TARGET_IMAGE_PATH,
        region=search_region,
        confidence=GLOBAL_CONFIDENCE
    )

    if not cider_location:
        print(f"경고: 지정된 영역에서 '{INVEN_SCAN_TARGET_IMAGE_PATH.name}'을(를) 찾지 못했습니다. 구매를 중단합니다.")
        print("--- 상점 열기 시퀀스 미완료 (아이템 미발견) ---")
        return

    print(f"'{INVEN_SCAN_TARGET_IMAGE_PATH.name}' 발견. 클릭합니다. (위치: {cider_location})")
    click_randomly_in_cell(cider_location.left, cider_location.top, cider_location.width, cider_location.height)
    time.sleep(0.5)

    buy_button_pos = (603, 206)
    nomore_image_path = ASSETS_DIR / "nomore.png"
    print(f"'아이템 사기' 버튼({buy_button_pos}) 반복 클릭을 시작합니다. ('{nomore_image_path.name}' 발견 또는 ESC 입력 시 중단)")

    # --- 스레드를 이용한 고속 클릭 로직 ---
    # 1. 키보드 리스너 설정
    global stop_action
    stop_action = False  # 루프 시작 전 플래그 초기화
    listener = pynput_keyboard.Listener(on_press=on_press)
    listener.start()

    # 2. ClickBot 인스턴스 생성 및 실행
    click_bot = ClickBot(button_pos=buy_button_pos)
    click_bot.start()

    # 3. 메인 스레드는 중단 조건 감시
    start_time = time.time()
    timeout_seconds = 30  # 최대 30초 동안 실행
    stop_reason = "시간 초과"

    nomore_search_region = (390, 90, 555 - 390, 152 - 90)
    print(f"'nomore' 이미지를 영역 {nomore_search_region} 내에서 감시합니다.")

    while time.time() - start_time < timeout_seconds:
        if stop_action:
            stop_reason = "사용자 요청(ESC)"
            break
        if screen_utils.find_image_in_region(nomore_image_path, region=nomore_search_region,
                                             confidence=GLOBAL_CONFIDENCE):
            stop_reason = f"'{nomore_image_path.name}' 이미지 발견"
            break
        time.sleep(0.1)  # 0.1초마다 조건 확인

    print(f"\n[작업 중단] 사유: {stop_reason}")

    # 4. 모든 스레드 정리
    final_click_count = click_bot.stop()
    listener.stop()

    print(f"총 약 {final_click_count}회 구매를 시도했습니다.")
    print("--- 상점 열기 시퀀스 완료 ---")


def open_post():
    """
    마을로 이동하여 우체통을 열고, 인벤토리를 열어 드래그하는 과정을 수행합니다.
    """
    # [수정] 공통 초기화 함수 호출
    if not prepare_and_activate_window("우체통 열기"):
        return

    goto_village()

    print("해상도를 1900x300으로 변경합니다.")
    resize_window(1900, 300)
    time.sleep(1.5)

    click_dewey()
    time.sleep(1.5)

    print("해상도를 1366x768로 복구합니다.")
    resize_window(1366, 768)
    time.sleep(1.5)

    print("인벤토리를 엽니다...")
    inventory_opened = False
    inven_image_path = ASSETS_DIR / "inven.png"
    start_time = time.time()

    while time.time() - start_time < 10:
        inven_location = screen_utils.find_image_on_screen(inven_image_path, confidence=GLOBAL_CONFIDENCE)

        if inven_location:
            print("인벤토리가 열린 것을 확인했습니다.")
            inventory_opened = True
            break
        else:
            print("인벤토리가 보이지 않아 'i' 키를 누릅니다.")
            pyautogui.press('i')
            time.sleep(1)

    if not inventory_opened:
        print("오류: 시간 내에 인벤토리가 열리지 않았습니다.")
        return

    print("인벤토리 내에서 드래그를 수행합니다...")
    if inven_location:
        start_x = random.randint(inven_location.left, inven_location.left + inven_location.width)
        start_y = random.randint(inven_location.top, inven_location.top + inven_location.height)

        end_x = start_x + 200
        end_y = start_y

        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5)
        print(f"드래그 완료: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
    else:
        print("오류: 드래그를 위해 인벤토리 위치를 다시 찾는 데 실패했습니다.")

    print("--- 우체통 열기 시퀀스 완료 ---")