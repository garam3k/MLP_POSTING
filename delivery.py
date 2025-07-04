# delivery.py
import time
from pathlib import Path

import pyautogui

import screen_utils
from config import (INVEN_CONFIG, POST_CONFIG, CLICK_DELAY_SECONDS, OVERLAY_CONFIG,
                    GLOBAL_CONFIDENCE, INVEN_SCAN_TARGET_IMAGE_PATH)
from debug_overlay_util import draw_rects_on_image, draw_base_info_on_image
from grid_cell_utils import scan_grid_for_image
# [수정] inven_util의 새로운 함수 임포트
from inven_util import get_inven_grid_cells, click_inven_grid_cell, find_item_by_scrolling
from post_util import click_delivery_button, get_post_grid_cells, click_post_grid_cell, get_delivery_button_rects
from screen_utils import paste_text


def _fill_post_with_items() -> bool:
    """우편함이 가득 찰 때까지 인벤토리에서 아이템을 옮깁니다. 성공 시 True, 재고 부족 시 False를 반환합니다."""
    MAX_ATTEMPTS = 50  # 아이템을 하나씩 옮기므로, 최대 50번 시도 후 중단
    for attempt in range(MAX_ATTEMPTS):
        print(f"\n--- 우편 채우기 시도 ({attempt + 1}/{MAX_ATTEMPTS}) ---")

        # 1. Post 그리드의 빈 칸 확인
        post_grid_cells = get_post_grid_cells(POST_CONFIG)
        if not post_grid_cells:
            print("오류: 우편 그리드를 찾을 수 없습니다.")
            return False

        found_in_post = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, post_grid_cells, GLOBAL_CONFIDENCE)
        empty_post_indices = [i for i, loc in enumerate(found_in_post) if loc is None]

        if not empty_post_indices:
            print("성공: 우편 그리드가 모두 채워졌습니다.")
            return True

        print(f"우편 그리드에 {len(empty_post_indices)}개의 빈 칸이 있습니다.")

        # 2. Inven 그리드에서 아이템 확인
        inven_grid_cells = get_inven_grid_cells(INVEN_CONFIG)
        if not inven_grid_cells:
            print("오류: 인벤토리 그리드를 찾을 수 없습니다.")
            return False

        found_in_inven = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, inven_grid_cells, GLOBAL_CONFIDENCE)
        available_inven_indices = [i for i, loc in enumerate(found_in_inven) if loc is not None]

        if available_inven_indices:
            # 3. 인벤토리에 아이템이 보이면 하나 옮기기
            inven_idx_to_click = available_inven_indices[0]
            post_idx_to_click = empty_post_indices[0]
            print(f"아이템 이동: Inven Cell #{inven_idx_to_click} -> Post Cell #{post_idx_to_click}")
            click_inven_grid_cell(inven_idx_to_click, inven_grid_cells)
            click_post_grid_cell(post_idx_to_click, post_grid_cells)
        else:
            # 4. 인벤토리에 아이템이 안 보이면 스크롤해서 찾기
            print("현재 인벤토리 뷰에 아이템이 없습니다. 스크롤하여 탐색합니다...")
            if not find_item_by_scrolling(INVEN_SCAN_TARGET_IMAGE_PATH):
                # 스크롤해도 아이템이 없으면 재고 부족으로 판단하고 실패 반환
                print("재고 부족: 인벤토리를 모두 탐색했으나 아이템을 찾지 못했습니다.")
                return False
            # 스크롤 후 아이템을 찾았으므로, 다음 루프에서 옮길 것임

    print(f"오류: 최대 시도 횟수({MAX_ATTEMPTS})를 초과했습니다. 우편을 채우지 못했습니다.")
    return False


def send_action(delivery_type: str, receiver_name: str, amount: str) -> bool:
    """배송 작업을 수행하는 일련의 과정을 자동화합니다. 성공 시 True, 실패(재고 부족 등) 시 False를 반환합니다."""
    print(f"\n--- 발송 작업 시작: 유형='{delivery_type}', 수신인='{receiver_name}', 금액='{amount}' ---")

    if delivery_type not in ["standard", "express"]:
        print(f"오류: 잘못된 배송 유형 '{delivery_type}'.")
        return False

    click_delivery_button(delivery_type)
    time.sleep(CLICK_DELAY_SECONDS / 2)

    print("'수신인' 버튼 클릭 후 이름 입력 중...")
    click_delivery_button("receiver")
    time.sleep(CLICK_DELAY_SECONDS / 2)
    paste_text(receiver_name)
    print(f"수신인 입력 완료: {receiver_name}")
    time.sleep(CLICK_DELAY_SECONDS / 2)

    # [수정] 새로운 아이템 이전 로직을 호출하고, 실패 시 즉시 False 반환
    if not _fill_post_with_items():
        return False

    # 아이템을 12개 모두 채웠을 때만 아래 로직 실행
    print("우편함이 가득 찼습니다. 발송 절차를 계속 진행합니다.")
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
    return True


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
    a_grid_cells = get_inven_grid_cells(INVEN_CONFIG)
    if a_grid_cells:
        screenshot = draw_rects_on_image(screenshot, a_grid_cells, OVERLAY_CONFIG.color_grid_a,
                                         OVERLAY_CONFIG.thickness)

        item_locations_boxes = scan_grid_for_image(INVEN_SCAN_TARGET_IMAGE_PATH, a_grid_cells, GLOBAL_CONFIDENCE)
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