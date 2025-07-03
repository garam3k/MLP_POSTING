# delivery.py
import time

import pyautogui

import screen_utils
from config import (INVEN_CONFIG, POST_CONFIG, CLICK_DELAY_SECONDS, OVERLAY_CONFIG,
                    GLOBAL_CONFIDENCE, INVEN_SCAN_TARGET_IMAGE_PATH)
from debug_overlay_util import draw_rects_on_image, draw_base_info_on_image
from grid_cell_utils import scan_grid_for_image
# [수정] get_inven_grid_cells를 직접 호출하기 위해 임포트
from inven_util import get_inven_grid_cells, click_inven_grid_cell
from post_util import click_delivery_button, get_post_grid_cells, click_post_grid_cell, get_delivery_button_rects
from screen_utils import paste_text


def _verify_and_fill_post_grid():
    """우편 그리드(B)가 가득 찼는지 확인하고, 비어있다면 인벤토리(A)의 아이템으로 마저 채웁니다."""
    print("\n--- 우편 그리드 검증 및 채우기 시작 ---")

    b_grid_cells = get_post_grid_cells(POST_CONFIG)
    if not b_grid_cells:
        print("오류: 우편 그리드를 찾을 수 없어 검증을 중단합니다.")
        return

    print(f"B 그리드에서 '{INVEN_SCAN_TARGET_IMAGE_PATH.name}' 스캔하여 빈칸을 확인합니다...")
    found_b_locations = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, b_grid_cells, GLOBAL_CONFIDENCE)
    empty_b_indices = [i for i, loc in enumerate(found_b_locations) if loc is None]

    if not empty_b_indices:
        print("✅ 검증 완료: 우편 그리드의 모든 칸(12개)이 정상적으로 채워져 있습니다.")
        return

    print(f"경고: 우편 그리드에 {len(empty_b_indices)}개의 빈 칸이 있습니다. 추가 채우기 작업을 시작합니다.")

    # [리팩토링] inven_util.perform_inven_grid_actions() 대신 직접 로직 수행
    a_grid_cells = get_inven_grid_cells(INVEN_CONFIG)
    if not a_grid_cells:
        print("오류: 인벤토리 정보를 가져올 수 없어 채우기 작업을 중단합니다.")
        return

    item_locations = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, a_grid_cells, GLOBAL_CONFIDENCE)
    available_a_indices = [i for i, loc in enumerate(item_locations) if loc is not None]

    if not available_a_indices:
        print("오류: 인벤토리에 더 이상 옮길 아이템이 없어 채우기를 중단합니다.")
        return

    print(f"인벤토리에서 옮길 수 있는 아이템 {len(available_a_indices)}개를 추가로 찾았습니다.")

    num_to_fill = min(len(available_a_indices), len(empty_b_indices))
    print(f"총 {num_to_fill}개의 아이템을 추가로 옮깁니다.")

    for i in range(num_to_fill):
        a_idx_to_click = available_a_indices[i]
        b_idx_to_click = empty_b_indices[i]

        print(f"⏩ 추가 적재: A-Grid #{a_idx_to_click} -> B-Grid #{b_idx_to_click}")
        click_inven_grid_cell(a_idx_to_click, a_grid_cells)
        click_post_grid_cell(b_idx_to_click, b_grid_cells)

    print("--- 우편 그리드 채우기 완료 ---")


def _transfer_items_initial():
    """[이름 변경] 인벤토리(A)와 우편(B) 그리드를 번갈아 클릭하여 1차 아이템 이전을 수행합니다."""
    print("--- 1차 아이템 이전 시작 ---")

    # [리팩토링] inven_util.perform_inven_grid_actions() 대신 직접 로직 수행
    a_grid_cells = get_inven_grid_cells(INVEN_CONFIG)
    if not a_grid_cells:
        print("인벤토리 그리드 데이터를 가져올 수 없습니다. 중단합니다.")
        return

    print(f"A 그리드에서 '{INVEN_SCAN_TARGET_IMAGE_PATH.name}' 스캔 중...")
    item_locations = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, a_grid_cells, GLOBAL_CONFIDENCE)
    a_cells_to_click = [i for i, loc in enumerate(item_locations) if loc is not None]

    b_grid_cells = get_post_grid_cells(POST_CONFIG)
    if not b_grid_cells:
        print("우편 그리드 데이터를 가져올 수 없습니다. 중단합니다.")
        return

    print("\n--- A, B 그리드 교차 클릭 시작 ---")
    max_iterations = min(len(a_cells_to_click), len(b_grid_cells))
    print(f"최대 클릭 반복: {max_iterations}회")

    for i in range(max_iterations):
        a_cell_idx = a_cells_to_click[i]
        print(f"⏩ A-Grid 클릭: 셀 #{a_cell_idx}...")
        click_inven_grid_cell(a_cell_idx, a_grid_cells)

        b_cell_idx = i
        print(f"⏩ B-Grid 클릭: 셀 #{b_cell_idx}...")
        click_post_grid_cell(b_cell_idx, b_grid_cells)
        print(f"--- 반복 {i + 1}/{max_iterations} 완료 ---")

    print(f"\n--- 1차 아이템 이전 완료 ({max_iterations}회 반복) ---")


def send_action(delivery_type: str, receiver_name: str, amount: str):
    """배송 작업을 수행하는 일련의 과정을 자동화합니다."""
    print(f"\n--- 발송 작업 시작: 유형='{delivery_type}', 수신인='{receiver_name}', 금액='{amount}' ---")

    if delivery_type not in ["standard", "express"]:
        print(f"오류: 잘못된 배송 유형 '{delivery_type}'.")
        return

    click_delivery_button(delivery_type)
    time.sleep(CLICK_DELAY_SECONDS/2)

    print("'수신인' 버튼 클릭 후 이름 입력 중...")
    click_delivery_button("receiver")
    time.sleep(CLICK_DELAY_SECONDS/2)
    paste_text(receiver_name)
    print(f"수신인 입력 완료: {receiver_name}")
    time.sleep(CLICK_DELAY_SECONDS/2)

    # [이름 변경] 워크플로우 함수 호출
    _transfer_items_initial()

    _verify_and_fill_post_grid()
    time.sleep(CLICK_DELAY_SECONDS)

    print("'요청' 버튼 클릭 중...")
    click_delivery_button("request")
    time.sleep(CLICK_DELAY_SECONDS)

    print("'금액' 버튼 클릭 후 금액 입력 중...")
    click_delivery_button("value")
    time.sleep(CLICK_DELAY_SECONDS)
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
    """한 번의 스크린샷에 모든 디버그 정보를 그려 마지막에 한 번만 표시합니다."""
    print("\n--- 디버그 오버레이 표시 시작 ---")

    try:
        screenshot = pyautogui.screenshot()
        print("전체 화면 스크린샷 생성 완료.")
    except Exception as e:
        print(f"스크린샷 생성에 실패했습니다: {e}")
        return

    print("[1/3] 인벤토리(A 그리드) 정보 그리기...")
    # [리팩토링] inven_util.perform_inven_grid_actions() 대신 직접 로직 수행
    a_grid_cells = get_inven_grid_cells(INVEN_CONFIG)
    if a_grid_cells:
        screenshot = draw_rects_on_image(screenshot, a_grid_cells, OVERLAY_CONFIG.color_grid_a,
                                         OVERLAY_CONFIG.thickness)

        item_locations_boxes = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, a_grid_cells, GLOBAL_CONFIDENCE)
        # scan_grid_for_image가 Box 객체 또는 None의 리스트를 반환한다고 가정
        item_locations_found = [loc for loc in item_locations_boxes if loc is not None]

        if item_locations_found:
            print(f"{len(item_locations_found)}개의 아이템 위치를 오버레이에 표시합니다.")
            item_rects = [(loc.left, loc.top, loc.width, loc.height) for loc in item_locations_found]
            screenshot = draw_rects_on_image(screenshot, item_rects, OVERLAY_CONFIG.color_inven_item,
                                             OVERLAY_CONFIG.thickness)

    inven_base_location = screen_utils.find_image_on_screen(INVEN_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
    if inven_base_location:
        screenshot = draw_base_info_on_image(screenshot, inven_base_location, OVERLAY_CONFIG.color_base_image,
                                             OVERLAY_CONFIG.color_coord_text, OVERLAY_CONFIG.thickness)
    else:
        print(f"'{INVEN_CONFIG.base_image_path.name}' 이미지를 찾을 수 없어 인벤토리 오버레이를 건너뜁니다.")

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

    print("[3/3] 최종 오버레이 이미지 표시...")
    screenshot.show(title="Debug Overlay (All-in-one)")
    print("--- 모든 디버그 오버레이 표시 완료 ---")