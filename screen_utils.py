# screen_utils.py
import pyautogui
import time
from pathlib import Path
from typing import Optional, NamedTuple
import pyperclip


class Box(NamedTuple):
    left: int
    top: int
    width: int
    height: int


def find_image_on_screen(image_path: Path, confidence: float) -> Optional[Box]:
    """화면에서 이미지를 찾아 위치를 Box 객체로 반환합니다."""
    try:
        location = pyautogui.locateOnScreen(str(image_path), confidence=confidence)
        if location:
            box_location = Box(location[0], location[1], location[2], location[3])
            print(f"이미지 '{image_path.name}' 찾음: {box_location}")
            return box_location
        return None
    except FileNotFoundError:
        print(f"오류: 이미지 파일 없음 '{image_path}'")
        return None
    except Exception as e:
        print(f"이미지 탐색 중 오류 발생 '{image_path.name}': {e}")
        return None


def find_image_in_region(image_path: Path, region: tuple[int, int, int, int], confidence: float) -> Optional[Box]:
    """
    [수정됨] 지정된 영역에서 이미지를 찾되, 영역이 화면을 벗어나면 자동으로 보정합니다.
    """
    needle_dims = get_image_dimensions(image_path)
    if not needle_dims:
        print(f"오류: '{image_path.name}'의 크기를 읽을 수 없어 탐색을 중단합니다.")
        return None
    needle_width, needle_height = needle_dims

    # --- 화면 좌표 보정 로직 (신규) ---
    screen_width, screen_height = pyautogui.size()
    left, top, width, height = region

    # 1. 음수 좌표를 0으로 보정
    s_left = max(0, left)
    s_top = max(0, top)

    # 2. 화면 경계를 벗어나는 영역을 잘라냄
    s_right = min(left + width, screen_width)
    s_bottom = min(top + height, screen_height)

    # 3. 보정된 너비와 높이 계산
    s_width = s_right - s_left
    s_height = s_bottom - s_top

    # 4. 보정된 영역이 찾으려는 이미지보다 작은지 최종 확인
    if s_width < needle_width or s_height < needle_height:
        print(f"오류: 보정된 탐색 영역({s_width}x{s_height})이 이미지 크기({needle_width}x{needle_height})보다 작습니다.")
        return None

    sanitized_region = (s_left, s_top, s_width, s_height)
    # --- 좌표 보정 로직 끝 ---

    try:
        # 보정된 영역(sanitized_region)을 사용하여 이미지 탐색
        location = pyautogui.locateOnScreen(str(image_path), region=sanitized_region, confidence=confidence)
        if location:
            return Box(location[0], location[1], location[2], location[3])
        return None
    except FileNotFoundError:
        print(f"오류: 이미지 파일 없음 '{image_path}'")
        return None
    except Exception as e:
        print(f"영역 내 이미지 탐색 중 오류 발생 '{image_path.name}': {e}")
        return None


def get_image_dimensions(image_path: Path) -> Optional[tuple[int, int]]:
    """이미지 파일의 (너비, 높이)를 가져옵니다."""
    from PIL import Image
    try:
        with Image.open(image_path) as img:
            return img.width, img.height
    except FileNotFoundError:
        print(f"오류: '{image_path}' 파일이 없어 크기를 확인할 수 없습니다.")
        return None
    except Exception as e:
        print(f"이미지 크기 확인 중 오류 발생 '{image_path}': {e}")
        return None


def paste_text(text: str):
    """클립보드를 사용하여 텍스트를 붙여넣습니다."""
    try:
        original_clipboard = pyperclip.paste()
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
        pyperclip.copy(original_clipboard)
        print(f"붙여넣기 완료: '{text}'")
    except Exception as e:
        print(f"텍스트 붙여넣기 중 오류 발생: {e}")