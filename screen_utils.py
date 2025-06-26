# screen_utils.py
import pyautogui
import time
from pathlib import Path
from typing import Optional, NamedTuple
import pyperclip

# pyautogui.Box가 없는 구버전과의 호환성을 위해 직접 Box 타입을 정의합니다.
# (left, top, width, height) 구조를 가지는 명명된 튜플입니다.
class Box(NamedTuple):
    left: int
    top: int
    width: int
    height: int

def find_image_on_screen(image_path: Path, confidence: float) -> Optional[Box]:
    """Finds an image on the screen and returns its location as a Box object."""
    try:
        # locateOnScreen은 Box 객체 또는 일반 튜플을 반환할 수 있습니다.
        location = pyautogui.locateOnScreen(str(image_path), confidence=confidence)
        if location:
            # 결과가 있으면, 자체 정의한 Box 타입으로 변환하여 반환합니다.
            box_location = Box(location[0], location[1], location[2], location[3])
            print(f"Image '{image_path.name}' found at: {box_location}")
            return box_location
        return None
    except FileNotFoundError:
        print(f"Error: Image file not found at '{image_path}'")
        return None
    except Exception as e:
        print(f"An error occurred while finding image '{image_path.name}': {e}")
        return None

def find_image_in_region(image_path: Path, region: tuple[int, int, int, int], confidence: float) -> Optional[Box]:
    """Finds an image within a specific region and returns its location as a Box object."""
    try:
        location = pyautogui.locateOnScreen(str(image_path), region=region, confidence=confidence)
        if location:
            # 여기도 마찬가지로 Box 타입으로 변환하여 일관성을 유지합니다.
            return Box(location[0], location[1], location[2], location[3])
        return None
    except FileNotFoundError:
        print(f"Error: Image file not found at '{image_path}'")
        return None
    except Exception as e:
        print(f"An error occurred while finding image '{image_path.name}' in region: {e}")
        return None

def paste_text(text: str):
    """
    클립보드를 사용하여 텍스트를 붙여넣습니다. (한글 등 비-영문자 입력용)
    """
    try:
        # 1. 기존 클립보드 내용을 백업합니다.
        original_clipboard = pyperclip.paste()

        # 2. 입력할 텍스트를 클립보드에 복사합니다.
        pyperclip.copy(text)
        time.sleep(0.1)  # 클립보드가 업데이트될 시간을 잠시 줍니다.

        # 3. 'Ctrl + V' 붙여넣기 단축키를 실행합니다.
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)

        # 4. 백업해둔 원래 내용으로 클립보드를 복원합니다.
        pyperclip.copy(original_clipboard)
        print(f"붙여넣기 완료: '{text}'")
    except Exception as e:
        print(f"텍스트 붙여넣기 중 오류 발생: {e}")

def get_image_dimensions(image_path: Path) -> Optional[tuple[int, int]]:
    """Gets the (width, height) of an image file."""
    # 이 파일은 Pillow 라이브러리에 의존하므로 변경이 필요 없습니다.
    from PIL import Image
    try:
        with Image.open(image_path) as img:
            return img.width, img.height
    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found for dimension check.")
        return None
    except Exception as e:
        print(f"Error reading dimensions for '{image_path}': {e}")
        return None