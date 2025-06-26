# delivery.py
import time
import pyautogui
from inven_util import perform_inven_grid_actions, click_inven_grid_cell, get_inven_grid_cells
from post_util import click_delivery_button, get_post_grid_cells, click_post_grid_cell, get_delivery_button_rects
from debug_overlay_util import draw_rects_on_image, draw_base_info_on_image
from config import (INVEN_CONFIG, POST_CONFIG, CLICK_DELAY_SECONDS, OVERLAY_CONFIG, GLOBAL_CONFIDENCE)
import screen_utils
from screen_utils import paste_text


def automate_dynamic_dual_grids():
    """
    인벤토리(A)와 우편(B) 그리드를 번갈아 클릭하는 작업을 관리합니다.
    """
    print("--- 동적 듀얼 그리드 자동화 시작 ---")

    # perform_inven_grid_actions의 반환값이 3개로 늘어났으므로,それに合わせて 수정
    inven_data = perform_inven_grid_actions(INVEN_CONFIG)
    if not inven_data:
        print("인벤토리 그리드 데이터를 가져올 수 없습니다. 중단합니다.")
        return
    # 자동화 로직에는 item_locations가 필요 없으므로 _ 로 무시합니다.
    a_grid_cells, a_cells_to_click, _ = inven_data

    b_grid_cells = get_post_grid_cells(POST_CONFIG)
    if not b_grid_cells:
        print("우편 그리드 데이터를 가져올 수 없습니다. 중단합니다.")
        return

    # Click Loop
    print("\n--- Alternating A and B Grid Clicks Started ---")
    max_iterations = min(len(a_cells_to_click), len(b_grid_cells))
    print(f"Max click iterations: {max_iterations}")

    for i in range(max_iterations):
        # Click A Grid (Inventory Item)
        a_cell_idx = a_cells_to_click[i]
        print(f"⏩ A-Grid Click on cell #{a_cell_idx}...")
        click_inven_grid_cell(a_cell_idx, a_grid_cells)

        # Click B Grid (Post Slot)
        b_cell_idx = i
        print(f"⏩ B-Grid Click on cell #{b_cell_idx}...")
        click_post_grid_cell(b_cell_idx, b_grid_cells)
        print(f"--- Iteration {i + 1}/{max_iterations} complete ---")

    print(f"\n--- Dynamic Dual Grid Automation Finished ({max_iterations} iterations) ---")


def send_action(delivery_type: str, receiver_name: str, amount: str):
    """배송 작업을 수행하는 일련의 과정을 자동화합니다."""
    print(f"\n--- 발송 작업 시작: 유형='{delivery_type}', 수신인='{receiver_name}', 금액='{amount}' ---")

    if delivery_type not in ["standard", "express"]:
        print(f"오류: 잘못된 배송 유형 '{delivery_type}'. 'standard' 또는 'express'여야 합니다.")
        return

    click_delivery_button(delivery_type)
    time.sleep(CLICK_DELAY_SECONDS)

    print("'수신인' 버튼 클릭 후 이름 입력 중...")
    click_delivery_button("receiver")
    time.sleep(CLICK_DELAY_SECONDS)

    # [수정됨] pyautogui.write 대신 paste_text 함수를 사용하여 한글을 입력합니다.
    paste_text(receiver_name)
    # pyautogui.write(receiver_name)  <- 기존 코드

    print(f"수신인 입력 완료: {receiver_name}")
    time.sleep(CLICK_DELAY_SECONDS)

    print("\n듀얼 그리드 자동화 시작 중...")
    automate_dynamic_dual_grids()
    print("듀얼 그리드 자동화 완료.")
    time.sleep(CLICK_DELAY_SECONDS)

    print("'요청' 버튼 클릭 중...")
    click_delivery_button("request")
    time.sleep(CLICK_DELAY_SECONDS)

    print("'금액' 버튼 클릭 후 금액 입력 중...")
    click_delivery_button("value")
    time.sleep(CLICK_DELAY_SECONDS)

    # 금액은 숫자이므로 pyautogui.write를 사용해도 무방합니다.
    pyautogui.write(amount)

    print(f"금액 입력 완료: {amount}")
    time.sleep(CLICK_DELAY_SECONDS)
    pyautogui.press('enter')
    print("Enter 키 입력 완료.")
    time.sleep(CLICK_DELAY_SECONDS)

    print("'보내기' 버튼 클릭 중...")
    click_delivery_button("send")
    time.sleep(CLICK_DELAY_SECONDS)

    print("--- 발송 작업 완료 ---")


def show_all_overlays_for_debugging():
    """
    한 번의 스크린샷에 모든 디버그 정보를 그려 마지막에 한 번만 표시합니다.
    """
    print("\n--- 디버그 오버레이 표시 시작 ---")

    try:
        screenshot = pyautogui.screenshot()
        print("전체 화면 스크린샷 생성 완료.")
    except Exception as e:
        print(f"스크린샷 생성에 실패했습니다: {e}")
        return

    # 1. 인벤토리(A) 관련 정보 그리기
    print("[1/3] 인벤토리(A 그리드) 정보 그리기...")
    # 이제 반환값이 3개입니다. 오버레이에 필요한 모든 정보를 받습니다.
    inven_data = perform_inven_grid_actions(INVEN_CONFIG)
    if inven_data:
        a_grid_cells, _, item_locations = inven_data

        # 그리드 셀을 스크린샷에 그립니다.
        if a_grid_cells:
            screenshot = draw_rects_on_image(screenshot, a_grid_cells, OVERLAY_CONFIG.color_grid_a,
                                             OVERLAY_CONFIG.thickness)

        # [신규] 발견된 아이템 위치를 스크린샷에 그립니다.
        if item_locations:
            print(f"{len(item_locations)}개의 아이템 위치를 오버레이에 표시합니다.")
            # item_locations는 Box 객체의 리스트이므로, 사각형 튜플로 변환해줍니다.
            item_rects = [(loc.left, loc.top, loc.width, loc.height) for loc in item_locations]
            screenshot = draw_rects_on_image(screenshot, item_rects, OVERLAY_CONFIG.color_inven_item,
                                             OVERLAY_CONFIG.thickness)

    # 기준 이미지 위치는 그리드보다 나중에 그려서 겹쳐 보이도록 합니다.
    inven_base_location = screen_utils.find_image_on_screen(INVEN_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if inven_base_location:
        screenshot = draw_base_info_on_image(screenshot, inven_base_location, OVERLAY_CONFIG.color_base_image,
                                             OVERLAY_CONFIG.color_coord_text, OVERLAY_CONFIG.thickness)
    else:
        print(f"'{INVEN_CONFIG.base_image_path.name}' 이미지를 찾을 수 없어 인벤토리 오버레이를 건너뜁니다.")

    # 2. 우편(B) 관련 정보 그리기 (기존 로직과 유사)
    print("[2/3] 우편(B 그리드) 정보 그리기...")
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
    else:
        print(f"'{POST_CONFIG.base_image_path.name}' 이미지를 찾을 수 없어 우편 오버레이를 건너뜁니다.")

    # 3. 최종 이미지 표시
    print("[3/3] 최종 오버레이 이미지 표시...")
    screenshot.show(title="Debug Overlay (All-in-one)")
    print("--- 모든 디버그 오버레이 표시 완료 ---")

