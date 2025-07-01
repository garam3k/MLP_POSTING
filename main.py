# main.py
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys
import logging
import pyautogui
import time
import random
import threading
from pynput import keyboard as pynput_keyboard

try:
    from logger_setup import setup_file_logger
except ImportError:
    def setup_file_logger(name, file):
        return logging.getLogger(name)

from config import GUI_CONFIG, RECEIPT_IMAGE_PATH, GLOBAL_CONFIDENCE, PAYMENT_IMAGE_PATH, POST_CONFIG
from delivery import send_action, show_all_overlays_for_debugging
from window_util import remove_window_border, resize_window, activate_maple_window
from map_util import open_shop, open_post
from post_util import click_receive_button
import screen_utils
from grid_cell_utils import click_randomly_in_cell
from whisper_service import WhisperService
from firestore_service import FirestoreService, FirestoreConnectionError

app_logger = setup_file_logger('app_main', 'app_main.log')


class AutomationApp:
    def __init__(self, root):
        self.root = root
        app_logger.info("Initializing AutomationApp UI...")

        self.is_f5_loop_running = False

        self.root.title(GUI_CONFIG.title)
        geometry_string = f"{GUI_CONFIG.initial_width}x{GUI_CONFIG.initial_height}+{GUI_CONFIG.initial_pos_x}+{GUI_CONFIG.initial_pos_y}"
        self.root.geometry(geometry_string)
        self.root.resizable(True, True)

        app_logger.info("Initializing services...")
        self.firestore_service = FirestoreService()
        app_logger.info("FirestoreService initialized successfully.")

        self.whisper_service = WhisperService()
        app_logger.info("WhisperService initialized.")
        self.whisper_service.start()
        app_logger.info("WhisperService background thread started.")

        remove_window_border()
        resize_window(1366, 768)

        style = ttk.Style(self.root)
        style.configure("TFrame", padding=10)
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5, font=('calibri', 10, 'bold'))
        style.configure("TLabelframe.Label", font=('calibri', 11, 'bold'))
        style.configure("Outline.TButton", padding=2)

        self.delivery_type_var = tk.StringVar(value="standard")
        self.receiver_var = tk.StringVar(value="")
        self.standard_amount_var = tk.StringVar(value="45000")
        self.express_amount_var = tk.StringVar(value="60000")

        self._setup_ui_layout()
        app_logger.info("UI layout setup complete.")

        self._setup_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui_layout(self):
        """UI 위젯들을 생성하고 배치합니다."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        right_frame = ttk.LabelFrame(main_frame, text="최근 귓속말 (고유 닉네임 15명)", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- 왼쪽 프레임 ---
        top_control_frame = ttk.Frame(left_frame)
        top_control_frame.pack(fill=tk.X, pady=(0, 10), anchor='n')

        macro_frame = ttk.LabelFrame(top_control_frame, text="기능 실행", padding=10)
        macro_frame.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        shop_button = ttk.Button(macro_frame, text="상점 열기 (F2-1)", command=open_shop)
        shop_button.pack(pady=2, fill=tk.X)
        post_button = ttk.Button(macro_frame, text="우체통 열기 (F2-2)", command=open_post)
        post_button.pack(pady=2, fill=tk.X)
        self.receive_item_button = ttk.Button(macro_frame, text="아이템 받기 (F5)", command=self._toggle_f5_loop)
        self.receive_item_button.pack(pady=2, fill=tk.X)

        window_control_frame = ttk.LabelFrame(top_control_frame, text="창 크기 조절", padding=10)
        window_control_frame.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        preset1_button = ttk.Button(window_control_frame, text="1366 x 768 (F3)", command=lambda: resize_window(1366, 768))
        preset1_button.pack(pady=2, fill=tk.X)
        preset2_button = ttk.Button(window_control_frame, text="1900 x 300 (F4)", command=lambda: resize_window(1900, 300))
        preset2_button.pack(pady=2, fill=tk.X)

        delivery_frame = ttk.LabelFrame(left_frame, text="배송", padding=10)
        delivery_frame.pack(fill=tk.X, anchor='n')
        delivery_type_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        delivery_type_frame.pack(fill=tk.X)
        ttk.Label(delivery_type_frame, text="유형:").pack(side=tk.LEFT, padx=(0, 10))
        standard_radio = ttk.Radiobutton(delivery_type_frame, text="Standard", variable=self.delivery_type_var, value="standard")
        standard_radio.pack(side=tk.LEFT, padx=5)
        express_radio = ttk.Radiobutton(delivery_type_frame, text="Express", variable=self.delivery_type_var, value="express")
        express_radio.pack(side=tk.LEFT, padx=5)

        # [수정] 수신인 프레임에 '저장' 버튼 추가
        receiver_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        receiver_frame.pack(fill=tk.X)
        ttk.Label(receiver_frame, text="수신인:").pack(side=tk.LEFT, padx=(0, 10))
        self.receiver_entry = ttk.Entry(receiver_frame, textvariable=self.receiver_var)
        self.receiver_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        # [신규] 수신인 옆에 DB 저장 버튼
        save_button = ttk.Button(receiver_frame, text="저장", command=self._save_receiver_as_whisper, width=5)
        save_button.pack(side=tk.LEFT)

        amount_frame = ttk.Frame(delivery_frame, padding=(0, 10))
        amount_frame.pack(fill=tk.X)
        ttk.Label(amount_frame, text="Standard 금액:").grid(row=0, column=0, sticky="w", pady=2)
        self.standard_amount_entry = ttk.Entry(amount_frame, textvariable=self.standard_amount_var)
        self.standard_amount_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(amount_frame, text="Express 금액:").grid(row=1, column=0, sticky="w", pady=2)
        self.express_amount_entry = ttk.Entry(amount_frame, textvariable=self.express_amount_var)
        self.express_amount_entry.grid(row=1, column=1, sticky="ew", padx=5)
        amount_frame.columnconfigure(1, weight=1)

        action_button_frame = ttk.Frame(delivery_frame)
        action_button_frame.pack(fill=tk.X, pady=(10, 0))
        run_button = ttk.Button(action_button_frame, text="배송 시작 (F1)", command=self._run_delivery)
        run_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        debug_button = ttk.Button(action_button_frame, text="오버레이 보기", command=self._run_overlay_debug)
        debug_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        quick_copy_frame = ttk.LabelFrame(left_frame, text="빠른 응답 복사", padding=10)
        quick_copy_frame.pack(fill=tk.X, pady=(10, 0), anchor='n')
        response1 = "일반/특배 어떻게 보내드릴까요?"
        response2 = "세트수 + 일반/특배 알려주시면 보내드려요~"
        copy_button1 = ttk.Button(quick_copy_frame, text=response1, command=lambda: self._copy_response_to_clipboard(response1))
        copy_button1.pack(pady=(0, 2), fill=tk.X)
        copy_button2 = ttk.Button(quick_copy_frame, text=response2, command=lambda: self._copy_response_to_clipboard(response2))
        copy_button2.pack(pady=2, fill=tk.X)

        # --- 오른쪽 프레임 ---
        whisper_top_frame = ttk.Frame(right_frame)
        whisper_top_frame.pack(fill=tk.X, pady=(0, 5))
        refresh_button = ttk.Button(whisper_top_frame, text="새로고침", command=self._refresh_whisper_list)
        refresh_button.pack(fill=tk.X)

        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(canvas_frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_whisper_list()

    # [신규] 수신인 입력창의 닉네임을 '수동저장' 내용으로 DB에 저장하는 메소드
    def _save_receiver_as_whisper(self):
        """'수신인' 입력창의 닉네임을 DB에 저장합니다. 내용은 '수동저장'으로 고정됩니다."""
        name = self.receiver_var.get()

        if not name:
            messagebox.showwarning("입력 오류", "저장할 수신인 닉네임을 입력해주세요.")
            return

        try:
            # Firestore 서비스의 add_whisper 함수를 호출
            self.firestore_service.add_whisper(name=name, channel="수동입력", comment="수동저장")
            print(f"✅ 수동 저장 완료: {name} / 수동저장")

            # 목록을 즉시 새로고침
            self._refresh_whisper_list()

        except Exception as e:
            messagebox.showerror("저장 실패", f"DB에 저장하는 중 오류가 발생했습니다:\n{e}")
            print(f"🚨 수동 저장 중 오류 발생: {e}")

    def _toggle_f5_loop(self):
        """F5 아이템 받기 루프의 시작/중단 상태를 토글합니다."""
        if self.is_f5_loop_running:
            print("\n[사용자 요청] 아이템 받기 루프 중단 신호를 보냅니다...")
            self.is_f5_loop_running = False
            self.receive_item_button.config(text="아이템 받기 (F5)")
        else:
            print("\n[사용자 요청] 아이템 받기 루프를 시작합니다 (최대 100회)...")
            self.is_f5_loop_running = True
            self.receive_item_button.config(text="받는 중... (F5 중단)")
            threading.Thread(target=self._run_receive_sequence, daemon=True).start()

    def _run_receive_sequence(self):
        """다음 아이템을 탐색하고 발견 시 즉시 작업을 수행하는 시퀀스를 100회 반복합니다."""
        if not activate_maple_window():
            self.is_f5_loop_running = False
            return

        try:
            for i in range(100):
                if not self.is_f5_loop_running:
                    print("사용자 요청에 의해 아이템 받기 루프를 중단했습니다.")
                    break

                print(f"\n--- 아이템 받기 시작 ({i + 1}/100) ---")

                print(f"다음 '{PAYMENT_IMAGE_PATH.name}'를 최대 5초간 탐색합니다...")
                payment_location = None
                search_start_time = time.time()

                post_base_location = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
                if not post_base_location:
                    print("오류: 우편 창을 찾을 수 없어 루프를 중단합니다.")
                    break

                search_region = (
                    post_base_location.left + 152, post_base_location.top + 149,
                    281 - 152, 430 - 149
                )

                while time.time() - search_start_time < 5:
                    if not self.is_f5_loop_running: break
                    payment_location = screen_utils.find_image_in_region(PAYMENT_IMAGE_PATH, search_region, GLOBAL_CONFIDENCE)
                    if payment_location:
                        print(f"'{PAYMENT_IMAGE_PATH.name}' 발견!")
                        break
                    time.sleep(0.2)

                if not self.is_f5_loop_running:
                    print("사용자 요청에 의해 루프를 중단합니다.")
                    break

                if not payment_location:
                    print("시간 초과: 다음 아이템을 찾지 못해 루프를 종료합니다.")
                    break

                click_randomly_in_cell(
                    payment_location.left, payment_location.top,
                    payment_location.width, payment_location.height
                )
                time.sleep(0.1)
                click_receive_button()

                receipt_start_time = time.time()
                receipt_found = False
                while time.time() - receipt_start_time < 5:
                    if not self.is_f5_loop_running: break
                    if screen_utils.find_image_on_screen(RECEIPT_IMAGE_PATH, confidence=GLOBAL_CONFIDENCE):
                        receipt_found = True
                        break
                    time.sleep(0.2)

                if not self.is_f5_loop_running:
                    print("사용자 요청에 의해 루프를 중단합니다.")
                    break

                if receipt_found:
                    pyautogui.press('enter')
                else:
                    print(f"경고: 5초 내에 '{RECEIPT_IMAGE_PATH.name}' 이미지를 찾지 못했습니다.")
            else:
                print("\n--- 아이템 받기 100회 루프가 모두 완료되었습니다. ---")
        finally:
            self.is_f5_loop_running = False
            self.root.after(0, self.receive_item_button.config, {'text': '아이템 받기 (F5)'})

    def _handle_hotkey(self, key):
        try:
            if key == pynput_keyboard.Key.f1:
                print("\n[단축키 F1] 배송 시작 동작을 실행합니다.")
                self.root.after(0, self._run_delivery)
            elif key == pynput_keyboard.Key.f2:
                print("\n[단축키 F2] 상점 열기 -> 우체통 열기 순차 실행 시작...")
                self.root.after(0, self._run_f2_sequence)
            elif key == pynput_keyboard.Key.f3:
                print("\n[단축키 F3] 창 크기를 1366x768로 변경합니다.")
                self.root.after(0, lambda: resize_window(1366, 768))
            elif key == pynput_keyboard.Key.f4:
                print("\n[단축키 F4] 창 크기를 1900x300으로 변경합니다.")
                self.root.after(0, lambda: resize_window(1900, 300))
            elif key == pynput_keyboard.Key.f5:
                self.root.after(0, self._toggle_f5_loop)
        except Exception as e:
            print(f"단축키 처리 중 오류 발생: {e}")

    def _run_f2_sequence(self):
        print("\n[단축키 F2] 상점 열기 -> 우체통 열기 순차 실행 시작...")
        open_shop()
        print("\n상점 열기 완료. 이어서 우체통 열기를 시작합니다.")
        open_post()
        print("\n[단축키 F2] 모든 동작이 완료되었습니다.")

    def _setup_hotkeys(self):
        self.hotkey_listener = pynput_keyboard.Listener(on_press=self._handle_hotkey)
        self.hotkey_listener.start()
        app_logger.info("Global hotkeys activated.")

    def _on_closing(self):
        app_logger.info("WM_DELETE_WINDOW triggered. Stopping hotkey listener and destroying root.")
        if self.hotkey_listener.is_alive():
            self.hotkey_listener.stop()
        self.root.destroy()

    def _refresh_whisper_list(self):
        """[수정] 귓속말 목록을 닉네임만 표시하도록 간소화합니다."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        latest_whispers = self.firestore_service.get_latest_unique_nicknames(count=15)
        if not latest_whispers:
            ttk.Label(self.scrollable_frame, text="표시할 귓속말이 없습니다.").pack(pady=10)
            return
        for item in latest_whispers:
            name = item.get('name', 'N/A')
            row_frame = ttk.Frame(self.scrollable_frame)
            row_frame.pack(fill=tk.X, pady=2, padx=2)

            label = ttk.Label(row_frame, text=name, anchor='w')
            label.pack(side=tk.LEFT, expand=True, fill=tk.X)

            copy_button = ttk.Button(row_frame, text="복사", style="Outline.TButton",
                                     command=lambda n=name: self._handle_whisper_selection(n))
            copy_button.pack(side=tk.RIGHT)

    def _copy_response_to_clipboard(self, response: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(response)
        print(f"📋 클립보드에 복사됨: '{response}'")

    def _handle_whisper_selection(self, nickname: str):
        """[수정] 닉네임 복사 시 수신인 입력창만 채우도록 간소화합니다."""
        self.root.clipboard_clear()
        self.root.clipboard_append(nickname)
        print(f"📋 '{nickname}'가 클립보드에 복사되었습니다.")
        self.receiver_var.set(nickname)
        print(f"🖋️ 수신인에 '{nickname}'이(가) 입력되었습니다.")

    def _run_delivery(self):
        if not activate_maple_window(): return
        delivery_type = self.delivery_type_var.get()
        receiver_name = self.receiver_var.get()
        amount = self.standard_amount_var.get() if delivery_type == "standard" else self.express_amount_var.get()
        if not receiver_name:
            messagebox.showwarning("입력 오류", "배송 수신인 이름을 입력해주세요.")
            return
        if not amount.isdigit():
            messagebox.showwarning("입력 오류", "금액은 숫자만 입력 가능합니다.")
            return
        try:
            send_action(delivery_type, receiver_name, amount)
            print(f"정보: 배송 작업 완료! 유형: {delivery_type}, 수신인: {receiver_name}, 금액: {amount}")
        except Exception as e:
            print(f"오류: 자동화 중 오류 발생: {e}")

    def _run_overlay_debug(self):
        if not activate_maple_window(): return
        try:
            show_all_overlays_for_debugging()
            print("정보: 디버그 오버레이가 화면에 표시되었습니다. 이미지 뷰어를 확인해주세요.")
        except Exception as e:
            print(f"오류: 오버레이 표시 중 오류 발생: {e}\n(이미지 파일 경로를 확인해주세요.)")


if __name__ == "__main__":
    app_logger.info("========================================")
    app_logger.info("Application starting up...")
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        app_logger.info("Root Tk window created and withdrawn.")

        app = AutomationApp(root)

        app_logger.info("AutomationApp initialization successful. Showing GUI window.")
        root.deiconify()

        app_logger.info("Starting Tkinter main loop.")
        root.mainloop()

    except (FirestoreConnectionError, Exception) as e:
        app_logger.critical("A fatal error occurred during application startup. GUI cannot be displayed.", exc_info=True)
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            messagebox.showerror("치명적 오류",
                                 f"애플리케이션 시작 중 심각한 오류가 발생했습니다.\n\n자세한 내용은 'logs/app_main.log' 파일을 확인해주세요.\n\n오류: {e}")
        except tk.TclError:
            print(f"CRITICAL: 애플리케이션 시작 중 심각한 오류가 발생했습니다. 로그 파일을 확인해주세요. 오류: {e}")
        sys.exit(1)

    app_logger.info("Application shutdown gracefully.")