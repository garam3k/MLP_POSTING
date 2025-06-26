# map_util.py
from typing import Optional, Callable
import time
import pyautogui
import pygetwindow as gw
import random
# [신규] pynput 라이브러리 임포트
from pynput import keyboard as pynput_keyboard

from config import ASSETS_DIR, GLOBAL_CONFIDENCE, DEWEY_CONFIG, DORAN_CONFIG, INVEN_SCAN_TARGET_IMAGE_PATH
import screen_utils
from grid_cell_utils import click_randomly_in_cell
from window_util import WINDOW_TITLE, resize_window, activate_maple_window

# --- [신규] 전역 변수 및 키보드 리스너 콜백 함수 ---
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


# --- 기존 함수들 (변경 없음) ---

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
    [수정됨] 마켓으로 이동하여 상점을 열고, 지정된 아이템을 반복 구매하는 전체 과정을 수행합니다.
    ESC 키를 눌러 아이템 구매를 중단할 수 있습니다.
    """
    if not activate_maple_window():
        return

    print("\n--- 상점 열기 시퀀스 시작 ---")
    print("초기화 동작: ESC 5회 입력")
    pyautogui.press('esc', presses=5, interval=0.1)
    time.sleep(0.2)

    goto_market()

    print("해상도를 1900x300으로 변경합니다.")
    resize_window(1900, 300)
    time.sleep(1.5)

    click_doran()
    time.sleep(1.5)

    print("해상도를 1366x768로 복구합니다.")
    resize_window(1366, 768)
    time.sleep(1.5)

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

    # --- [신규] 키보드 리스너 설정 ---
    global stop_action
    stop_action = False  # 루프 시작 전 플래그 초기화
    listener = pynput_keyboard.Listener(on_press=on_press)
    listener.start()

    click_count = 0
    # [수정] 반복 횟수를 300회로 줄임
    for _ in range(300):
        # [수정] 루프 시작 시 중단 플래그(ESC) 확인
        if stop_action:
            break

        # '더 이상 살 수 없다'는 이미지 확인
        if screen_utils.find_image_on_screen(nomore_image_path, confidence=GLOBAL_CONFIDENCE):
            print(f"'{nomore_image_path.name}' 이미지를 발견하여 반복 클릭을 중단합니다.")
            break

        pyautogui.click(buy_button_pos)
        click_count += 1
        time.sleep(0.05)
    else:
        # for 루프가 break 없이 정상적으로(300회) 종료되었을 경우
        print("경고: 최대 300회 클릭 후에도 중단 조건을 만족하지 못해 작업을 중지합니다.")

    # [신규] 리스너 스레드를 안전하게 정리
    listener.stop()

    if stop_action:
        print(f"사용자의 요청(ESC)에 의해 총 {click_count}회 구매 시도 후 작업을 중단했습니다.")
    else:
        print(f"총 {click_count}회 구매를 시도했습니다.")

    print("--- 상점 열기 시퀀스 완료 ---")


def open_post():
    """
    마을로 이동하여 우체통을 열고, 인벤토리를 열어 드래그하는 과정을 수행합니다.
    """
    if not activate_maple_window():
        return

    print("\n--- 우체통 열기 시퀀스 시작 ---")
    print("초기화 동작: ESC 5회 입력")
    pyautogui.press('esc', presses=5, interval=0.1)
    time.sleep(0.2)

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