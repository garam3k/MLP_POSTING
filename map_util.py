# map_util.py
from typing import Optional, Callable
import time
import pyautogui
import pygetwindow as gw
import random

from config import ASSETS_DIR, GLOBAL_CONFIDENCE
# screen_utils에서 find_image_on_screen 함수를 추가로 임포트합니다.
from screen_utils import find_image_in_region, find_image_on_screen
from grid_cell_utils import click_randomly_in_cell
from window_util import WINDOW_TITLE, resize_window, activate_maple_window


# ... (파일 상단의 기존 함수들은 그대로 유지) ...
def _get_target_window_and_check_size(expected_width: int, expected_height: int) -> Optional[gw.Win32Window]:
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
    window = _get_target_window_and_check_size(1366, 768)
    if not window:
        return False

    image_path = ASSETS_DIR / "market.png"
    location = find_image_in_region(image_path, region=window.box, confidence=GLOBAL_CONFIDENCE)

    if location:
        print("마켓 이미지를 찾았습니다.")
        return True
    else:
        return False


def is_village() -> bool:
    window = _get_target_window_and_check_size(1366, 768)
    if not window:
        return False

    image_path = ASSETS_DIR / "maul.png"
    location = find_image_in_region(image_path, region=window.box, confidence=GLOBAL_CONFIDENCE)

    if location:
        print("마을 이미지를 찾았습니다.")
        return True
    else:
        return False


def click_dewey():
    window = _get_target_window_and_check_size(1900, 300)
    if not window:
        return

    image_path = ASSETS_DIR / "dewey.png"
    location = find_image_in_region(image_path, region=window.box, confidence=GLOBAL_CONFIDENCE)

    if location:
        print("NPC 듀이를 찾았습니다. 클릭합니다.")
        click_randomly_in_cell(location.left, location.top, location.width, location.height)
    else:
        print("NPC 듀이를 찾을 수 없습니다.")


def click_doran():
    window = _get_target_window_and_check_size(1900, 300)
    if not window:
        return

    image_path = ASSETS_DIR / "doran.png"
    location = find_image_in_region(image_path, region=window.box, confidence=GLOBAL_CONFIDENCE)

    if location:
        print("NPC 도란을 찾았습니다. 클릭합니다.")
        click_randomly_in_cell(location.left, location.top, location.width, location.height)
    else:
        print("NPC 도란을 찾을 수 없습니다.")


def _wait_for_map_change(check_function: Callable[[], bool], timeout: int = 30) -> bool:
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
    print("맵 이동 시퀀스 시작: ESC 5회, 방향키(위) 1회")
    pyautogui.press('esc', presses=5, interval=0.1)
    time.sleep(0.2)
    pyautogui.press('up')


def goto_village():
    if not _get_target_window_and_check_size(1366, 768):
        return

    if is_village():
        print("이미 마을에 있습니다.")
        return

    _move_map()
    _wait_for_map_change(is_village)


def goto_market():
    if not _get_target_window_and_check_size(1366, 768):
        return

    if is_market():
        print("이미 마켓에 있습니다.")
        return

    _move_map()
    _wait_for_map_change(is_market)


def open_shop():
    if not activate_maple_window():
        return

    print("\n--- 상점 열기 시퀀스 시작 ---")
    goto_market()

    print("해상도를 1900x300으로 변경합니다.")
    resize_window(1900, 300)
    time.sleep(1.5)

    click_doran()
    time.sleep(1.5)

    print("해상도를 1366x768로 복구합니다.")
    resize_window(1366, 768)
    print("--- 상점 열기 시퀀스 완료 ---")


def open_post():
    """
    마을로 이동하여 우체통을 열고, 인벤토리를 열어 드래그하는 과정을 수행합니다.
    """
    if not activate_maple_window():
        return

    print("\n--- 우체통 열기 시퀀스 시작 ---")
    goto_village()

    print("해상도를 1900x300으로 변경합니다.")
    resize_window(1900, 300)
    time.sleep(1.5)

    click_dewey()
    time.sleep(1.5)

    print("해상도를 1366x768로 복구합니다.")
    resize_window(1366, 768)
    time.sleep(1.5)

    # --- [수정됨] 인벤토리를 여는 로직 변경 ---
    print("인벤토리를 엽니다...")
    inventory_opened = False
    inven_image_path = ASSETS_DIR / "inven.png"
    start_time = time.time()

    # 인벤토리가 열릴 때까지 최대 10초간 시도
    while time.time() - start_time < 10:
        # 먼저 현재 화면에 인벤토리가 있는지 확인
        # 여기서는 창 전체를 대상으로 빠르게 확인하기 위해 find_image_on_screen 사용
        inven_location = find_image_on_screen(inven_image_path, confidence=GLOBAL_CONFIDENCE)

        if inven_location:
            print("인벤토리가 열린 것을 확인했습니다.")
            inventory_opened = True
            break
        else:
            # 인벤토리가 없으면 'i' 키를 누릅니다.
            print("인벤토리가 보이지 않아 'i' 키를 누릅니다.")
            pyautogui.press('i')
            # 키 누른 후 게임이 반응할 시간을 줍니다.
            time.sleep(1)

    if not inventory_opened:
        print("오류: 시간 내에 인벤토리가 열리지 않았습니다.")
        return

    # 2. 인벤토리 내에서 드래그 수행
    print("인벤토리 내에서 드래그를 수행합니다...")
    # 드래그 시작/종료 지점을 계산하기 위해 인벤토리 위치를 다시 찾습니다.
    # 위에서 이미 찾았으므로, 해당 위치 정보를 그대로 사용합니다.
    if inven_location:
        # 인벤토리 영역 내에서 랜덤 시작점 지정
        start_x = random.randint(inven_location.left, inven_location.left + inven_location.width)
        start_y = random.randint(inven_location.top, inven_location.top + inven_location.height)

        # 종료점 계산 (x축으로 +200)
        end_x = start_x + 200
        end_y = start_y

        # 드래그 수행 (0.5초 동안)
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5)
        print(f"드래그 완료: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
    else:
        # 이 코드는 실행될 가능성이 낮지만, 안정성을 위해 유지합니다.
        print("오류: 드래그를 위해 인벤토리 위치를 다시 찾는 데 실패했습니다.")

    print("--- 우체통 열기 시퀀스 완료 ---")