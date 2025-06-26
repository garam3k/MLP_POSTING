# window_util.py
import win32gui
import win32con
import pygetwindow as gw
from typing import Optional
import time

WINDOW_TITLE = 'MapleStory Worlds-Mapleland'


def _get_window() -> Optional[gw.Win32Window]:
    """지정된 제목의 창 객체를 찾아서 반환합니다."""
    try:
        window_list = gw.getWindowsWithTitle(WINDOW_TITLE)
        if window_list:
            return window_list[0]
        else:
            print(f"'{WINDOW_TITLE}' 창을 찾을 수 없습니다.")
            return None
    except Exception as e:
        print(f"창을 찾는 중 오류가 발생했습니다: {e}")
        return None


def activate_maple_window() -> bool:
    """MapleStory Worlds-Mapleland 창을 찾아 활성화하고 맨 앞으로 가져옵니다."""
    window = _get_window()
    if not window:
        print(f"경고: '{WINDOW_TITLE}' 창이 없어 활성화할 수 없습니다.")
        return False

    try:
        if window.isMinimized:
            window.restore()

        window.activate()
        print(f"'{WINDOW_TITLE}' 창을 활성화했습니다.")
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"창 활성화 중 오류 발생: {e}")
        return False


def remove_window_border():
    """창의 제목 표시줄과 테두리를 제거합니다."""
    maple_window = _get_window()
    if not maple_window:
        return

    try:
        hwnd = maple_window._hWnd
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        win32gui.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                              win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
        print(f"'{WINDOW_TITLE}' 창의 테두리가 제거되었습니다.")
    except Exception as e:
        print(f"창 테두리 제거 중 오류 발생: {e}")


def resize_window(width: int, height: int):
    """[수정됨] 창의 크기를 지정된 크기로 변경하고, 화면 좌상단(0, 0)으로 이동시킵니다."""
    maple_window = _get_window()
    if not maple_window:
        print(f"경고: '{WINDOW_TITLE}' 창을 찾을 수 없어 크기를 변경할 수 없습니다.")
        return

    try:
        if maple_window.isMinimized:
            maple_window.restore()
        maple_window.activate()

        # 창 크기 변경
        maple_window.resizeTo(width, height)
        # [신규] 창 위치를 (0, 0)으로 이동
        maple_window.moveTo(0, 0)

        print(f"'{WINDOW_TITLE}' 창 크기가 {width}x{height}로 변경되고 (0,0) 위치로 이동되었습니다.")
    except Exception as e:
        print(f"창 크기/위치 변경 중 오류 발생: {e}")