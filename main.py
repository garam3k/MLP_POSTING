# main.py
import logging
import queue
import random
import sys
import threading
import time
import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from tkinter import messagebox
from tkinter import ttk

import pyautogui
from pynput import keyboard as pynput_keyboard

# --- 신규/수정된 임포트 ---
import shared_state
from config import (GUI_CONFIG, INVEN_CONFIG, PAYMENT_IMAGE_PATH,
                    POST_CONFIG, RECEIPT_IMAGE_PATH, GLOBAL_CONFIDENCE)
from delivery import send_action, show_all_overlays_for_debugging
from firestore_service import FirestoreService, FirestoreConnectionError
from grid_cell_utils import click_randomly_in_cell
from map_util import open_post, open_shop, prepare_and_activate_window
from post_util import click_receive_button
import screen_utils
from window_util import activate_maple_window, remove_window_border, resize_window
from whisper_service import Whisper, WhisperService

try:
    from logger_setup import setup_file_logger
except ImportError:
    def setup_file_logger(name, file):
        return logging.getLogger(name)

app_logger = setup_file_logger('app_main', 'app_main.log')


class WhisperLogWindow(tk.Toplevel):
    def __init__(self, parent, whisper_queue: queue.Queue):
        super().__init__(parent)
        self.title("실시간 귓속말 로그")
        self.geometry("600x400+0+50")
        self.queue = whisper_queue
        self.parent = parent
        self.log_text = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD, font=("Consolas", 10))
        self.log_text.pack(expand=True, fill=tk.BOTH)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    def add_whisper_log(self, whisper: Whisper):
        self.log_text.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {whisper.channel} | {whisper.name}: {whisper.content}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def process_queue(self):
        try:
            whisper = self.queue.get_nowait()
            self.add_whisper_log(whisper)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)


class AutomationApp:
    def __init__(self, root):
        self.root = root
        app_logger.info("Initializing AutomationApp UI...")

        self.is_f5_loop_running = False
        self.automation_running = False

        self.root.title(GUI_CONFIG.title)
        geometry_string = f"{GUI_CONFIG.initial_width}x{GUI_CONFIG.initial_height}+{GUI_CONFIG.initial_pos_x}+{GUI_CONFIG.initial_pos_y}"
        self.root.geometry(geometry_string)
        self.root.resizable(True, True)

        self.whisper_queue = queue.Queue()
        self.firestore_service = FirestoreService()
        self.whisper_service = WhisperService(self.whisper_queue)
        self.whisper_service.start()

        style = ttk.Style(self.root)
        style.configure("TFrame", padding=10)
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5, font=('calibri', 10, 'bold'))
        style.configure("TLabelframe.Label", font=('calibri', 11, 'bold'))
        style.configure("Outline.TButton", padding=2)

        self.delivery_type_var = tk.StringVar(value="standard")
        self.set_count_var = tk.IntVar(value=1)
        self.receiver_var = tk.StringVar(value="")
        self.standard_amount_var = tk.StringVar(value="45000")
        self.express_amount_var = tk.StringVar(value="60000")
        self.run_open_post_after_shop_var = tk.BooleanVar(value=True)

        self._setup_ui_layout()
        app_logger.info("UI layout setup complete.")

        self.whisper_log_window = WhisperLogWindow(self.root, self.whisper_queue)
        self.whisper_log_window.process_queue()
        app_logger.info("Whisper log window initialized and started.")

        self._setup_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui_layout(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        right_frame = ttk.LabelFrame(main_frame, text="최근 귓속말 (고유 닉네임 10명)", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        sequence_options_frame = ttk.LabelFrame(left_frame, text="F2 동작 설정", padding=10)
        sequence_options_frame.pack(fill=tk.X, pady=(0, 10), anchor='n')
        open_post_checkbox = ttk.Checkbutton(
            sequence_options_frame, text="상점 열기 후 우체통 자동 열기",
            variable=self.run_open_post_after_shop_var, onvalue=True, offvalue=False
        )
        open_post_checkbox.pack(fill=tk.X)

        delivery_frame = ttk.LabelFrame(left_frame, text="배송", padding=10)
        delivery_frame.pack(fill=tk.X, anchor='n')
        delivery_type_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        delivery_type_frame.pack(fill=tk.X)
        ttk.Label(delivery_type_frame, text="유형:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(delivery_type_frame, text="Standard", variable=self.delivery_type_var, value="standard").pack(
            side=tk.LEFT, padx=5)
        ttk.Radiobutton(delivery_type_frame, text="Express", variable=self.delivery_type_var, value="express").pack(
            side=tk.LEFT, padx=5)

        set_count_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        set_count_frame.pack(fill=tk.X)
        ttk.Label(set_count_frame, text="세트수:").pack(side=tk.LEFT, padx=(0, 10))
        for i in [1, 2, 3]:
            ttk.Radiobutton(set_count_frame, text=str(i), variable=self.set_count_var, value=i).pack(side=tk.LEFT,
                                                                                                     padx=5)

        receiver_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        receiver_frame.pack(fill=tk.X)
        ttk.Label(receiver_frame, text="수신인:").pack(side=tk.LEFT, padx=(0, 10))
        self.receiver_entry = ttk.Entry(receiver_frame, textvariable=self.receiver_var)
        self.receiver_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(receiver_frame, text="저장", command=self._save_receiver_as_whisper, width=5).pack(side=tk.LEFT)

        amount_frame = ttk.Frame(delivery_frame, padding=(0, 10))
        amount_frame.pack(fill=tk.X)
        ttk.Label(amount_frame, text="Standard 금액:").grid(row=0, column=0, sticky="w", pady=2)
        self.standard_amount_entry = ttk.Entry(amount_frame, textvariable=self.standard_amount_var)
        self.standard_amount_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(amount_frame, text="Express 금액:").grid(row=1, column=0, sticky="w", pady=2)
        self.express_amount_entry = ttk.Entry(amount_frame, textvariable=self.express_amount_var)
        self.express_amount_entry.grid(row=1, column=1, sticky="ew", padx=5)
        amount_frame.columnconfigure(1, weight=1)

        quick_copy_frame = ttk.LabelFrame(left_frame, text="빠른 응답 복사", padding=10)
        quick_copy_frame.pack(fill=tk.X, pady=(10, 0), anchor='n')
        response1 = "일반/특배 어떻게 보내드릴까요?"
        response2 = "세트수 + 일반/특배 알려주시면 보내드려요~"
        ttk.Button(quick_copy_frame, text=response1, command=lambda: self._copy_response_to_clipboard(response1)).pack(
            pady=(0, 2), fill=tk.X)
        ttk.Button(quick_copy_frame, text=response2, command=lambda: self._copy_response_to_clipboard(response2)).pack(
            pady=2, fill=tk.X)

        whisper_top_frame = ttk.Frame(right_frame)
        whisper_top_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(whisper_top_frame, text="새로고침", command=self._refresh_whisper_list).pack(fill=tk.X)
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
        ttk.Button(right_frame, text="오버레이 보기", command=self._run_overlay_debug).pack(fill=tk.X, pady=(10, 0))
        self._refresh_whisper_list()

    def _save_receiver_as_whisper(self):
        name = self.receiver_var.get()
        if not name:
            messagebox.showwarning("입력 오류", "저장할 수신인 닉네임을 입력해주세요.")
            return
        try:
            self.firestore_service.add_whisper(name=name, channel="수동입력", comment="수동저장")
            print(f"✅ 수동 저장 완료: {name} / 수동저장")
            self._refresh_whisper_list()
        except Exception as e:
            messagebox.showerror("저장 실패", f"DB에 저장하는 중 오류가 발생했습니다:\n{e}")

    def _toggle_f5_loop(self):
        if self.is_f5_loop_running:
            print("\n[단축키 F12] 아이템 받기 루프 중단 신호를 보냅니다...")
            self.is_f5_loop_running = False
        else:
            print("\n[단축키 F12] 아이템 받기 루프를 시작합니다 (최대 100회)...")
            self.is_f5_loop_running = True
            threading.Thread(target=self._run_receive_sequence, daemon=True).start()

    def _run_receive_sequence(self):
        if not activate_maple_window():
            self.is_f5_loop_running = False
            return
        try:
            for i in range(100):
                if not self.is_f5_loop_running:
                    print("사용자 요청에 의해 아이템 받기 루프를 중단했습니다.")
                    break
                print(f"\n--- 아이템 받기 시작 ({i + 1}/100) ---")

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

                print(f"'{PAYMENT_IMAGE_PATH.name}' 이미지를 탐색합니다...")
                while time.time() - search_start_time < 5:
                    if not self.is_f5_loop_running: break
                    payment_location = screen_utils.find_image_in_region(PAYMENT_IMAGE_PATH, search_region,
                                                                         GLOBAL_CONFIDENCE)
                    if payment_location:
                        print(f"'{PAYMENT_IMAGE_PATH.name}' 이미지 발견.")
                        break
                    time.sleep(0.2)

                if not self.is_f5_loop_running: break
                if not payment_location:
                    print("시간 초과: 5초 내에 다음 받을 아이템을 찾지 못해 루프를 종료합니다.")
                    break

                click_randomly_in_cell(
                    payment_location.left, payment_location.top,
                    payment_location.width, payment_location.height
                )
                time.sleep(0.1)
                click_receive_button()

                receipt_found = False
                receipt_start_time = time.time()
                print(f"'{RECEIPT_IMAGE_PATH.name}' 이미지를 탐색합니다...")
                while time.time() - receipt_start_time < 5:
                    if not self.is_f5_loop_running: break
                    if screen_utils.find_image_on_screen(RECEIPT_IMAGE_PATH, confidence=GLOBAL_CONFIDENCE):
                        print(f"'{RECEIPT_IMAGE_PATH.name}' 이미지 발견.")
                        receipt_found = True
                        break
                    time.sleep(0.2)

                if not self.is_f5_loop_running: break
                if receipt_found:
                    pyautogui.press('enter')
                    time.sleep(1.5)
                else:
                    print(f"경고: 5초 내에 '{RECEIPT_IMAGE_PATH.name}' 이미지를 찾지 못했습니다.")
            else:
                print("\n--- 아이템 받기 100회 루프가 모두 완료되었습니다. ---")

        finally:
            print("아이템 받기 작업을 종료합니다.")
            self.is_f5_loop_running = False

    def _setup_window_preset_f5(self):
        if activate_maple_window():
            remove_window_border()
            resize_window(1366, 768)

    def _handle_hotkey(self, key):
        if shared_state.ignore_hotkeys:
            return

        if key == pynput_keyboard.Key.esc:
            if self.automation_running:
                print("\n[중단 신호] ESC 키가 감지되었습니다. 진행 중인 작업을 중단합니다.")
                shared_state.stop_action = True
            return

        if self.automation_running:
            print("경고: 다른 자동화 작업이 이미 실행 중입니다. 잠시 후 다시 시도해주세요.")
            return

        try:
            if key == pynput_keyboard.Key.f1:
                self.root.after(0, self._run_delivery)
            elif key == pynput_keyboard.Key.f2:
                self.root.after(0, self._run_f2_sequence)
            elif key == pynput_keyboard.Key.f3:
                self.root.after(0, lambda: resize_window(1366, 768))
            elif key == pynput_keyboard.Key.f4:
                self.root.after(0, lambda: resize_window(1900, 300))
            elif key == pynput_keyboard.Key.f5:
                self.root.after(0, self._setup_window_preset_f5)
            elif key == pynput_keyboard.Key.f12:
                self._toggle_f5_loop()
        except Exception as e:
            print(f"단축키 처리 중 오류 발생: {e}")
            self.automation_running = False

    def _run_f2_sequence(self):
        self.automation_running = True
        shared_state.stop_action = False
        try:
            print("\n[단축키 F2] 상점/우체통 열기 동작을 실행합니다.")
            open_shop()
            if shared_state.stop_action:
                print("\n사용자 요청에 의해 작업이 중단되었습니다.")
                return

            if self.run_open_post_after_shop_var.get():
                print("\n'우체통 자동 열기' 옵션이 활성화되어, 이어서 우체통 열기를 시작합니다.")
                open_post()
            else:
                print("\n'우체통 자동 열기' 옵션이 비활성화되어, 창 초기화를 추가로 수행합니다.")
                prepare_and_activate_window("창 초기화")

            if not shared_state.stop_action:
                print("\n[단축키 F2] 동작이 완료되었습니다.")

        finally:
            self.automation_running = False
            shared_state.stop_action = False

    def _setup_hotkeys(self):
        self.hotkey_listener = pynput_keyboard.Listener(on_press=self._handle_hotkey)
        self.hotkey_listener.start()

    def _on_closing(self):
        if self.hotkey_listener.is_alive():
            self.hotkey_listener.stop()
        self.root.destroy()

    def _refresh_whisper_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        latest_whispers = self.firestore_service.get_latest_unique_nicknames(count=10)
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

    def _handle_whisper_selection(self, nickname: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(nickname)
        self.receiver_var.set(nickname)

    def _run_delivery(self):
        self.automation_running = True
        shared_state.stop_action = False
        try:
            print("F1 조건 확인: post.png와 inven.png를 찾습니다...")
            post_loc = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
            inven_loc = screen_utils.find_image_on_screen(INVEN_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
            if not post_loc or not inven_loc:
                messagebox.showwarning("이미지 없음", "'post.png' 또는 'inven.png'를 화면에서 찾을 수 없습니다.")
                return

            x_diff = abs(post_loc.left - inven_loc.left)
            if x_diff < 845:
                pyautogui.moveTo(inven_loc.left + inven_loc.width / 2, inven_loc.top + inven_loc.height / 2,
                                 duration=0.2)
                pyautogui.dragRel(150, 0, duration=0.5)
                time.sleep(0.3)

            if not activate_maple_window(): return

            num_sets = self.set_count_var.get()
            delivery_type = self.delivery_type_var.get()
            receiver_name = self.receiver_var.get()
            amount = self.standard_amount_var.get() if delivery_type == "standard" else self.express_amount_var.get()

            if not receiver_name or not amount.isdigit():
                messagebox.showwarning("입력 오류", "수신인과 금액을 올바르게 입력해주세요.")
                return

            print(f"총 {num_sets}세트 발송을 시작합니다. 수신인: {receiver_name}")

            for i in range(num_sets):
                if shared_state.stop_action:
                    print("\n사용자 요청에 의해 배송 작업을 중단합니다.")
                    break
                print(f"\n--- {i + 1}/{num_sets} 세트 발송 중 ---")
                success = send_action(delivery_type, receiver_name, amount)
                if not success:
                    if not shared_state.stop_action:
                        print("배송 실패(재고 부족 또는 오류 발생). F2(상점 열기) 동작을 실행하고 모든 발송을 중단합니다.")
                        open_shop()
                    return
                if i < num_sets - 1:
                    time.sleep(0.5)

            if not shared_state.stop_action:
                print(f"\n--- 총 {num_sets}세트 발송 작업이 모두 완료되었습니다. ---")

        finally:
            self.automation_running = False
            shared_state.stop_action = False

    def _run_overlay_debug(self):
        if activate_maple_window():
            show_all_overlays_for_debugging()


if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()