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

try:
    from logger_setup import setup_file_logger
except ImportError:
    def setup_file_logger(name, file):
        return logging.getLogger(name)

# [수정] INVEN_CONFIG 임포트 추가
from config import GUI_CONFIG, RECEIPT_IMAGE_PATH, GLOBAL_CONFIDENCE, PAYMENT_IMAGE_PATH, POST_CONFIG, INVEN_CONFIG
from delivery import send_action, show_all_overlays_for_debugging
from window_util import remove_window_border, resize_window, activate_maple_window
# prepare_and_activate_window 함수 임포트
from map_util import open_shop, open_post, prepare_and_activate_window
from post_util import click_receive_button
import screen_utils
from grid_cell_utils import click_randomly_in_cell
from whisper_service import WhisperService, Whisper
from firestore_service import FirestoreService, FirestoreConnectionError

app_logger = setup_file_logger('app_main', 'app_main.log')


# [신규] 실시간 귓속말 로그를 표시하는 새 창 클래스
class WhisperLogWindow(tk.Toplevel):
    def __init__(self, parent, whisper_queue: queue.Queue):
        """
        Args:
            parent: 부모 윈도우 (메인 앱의 root)
            whisper_queue: 귓속말 데이터를 수신할 큐
        """
        super().__init__(parent)
        self.title("실시간 귓속말 로그")
        self.geometry("600x400+0+50")  # 메인 창 근처에 위치하도록 좌표 설정
        self.queue = whisper_queue
        self.parent = parent

        # 스크롤 가능한 텍스트 위젯 생성
        self.log_text = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD, font=("Consolas", 10))
        self.log_text.pack(expand=True, fill=tk.BOTH)

        # 창이 닫힐 때의 동작 설정
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    def add_whisper_log(self, whisper: Whisper):
        """로그 텍스트 위젯에 귓속말을 추가합니다."""
        self.log_text.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {whisper.channel} | {whisper.name}: {whisper.content}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)  # 항상 마지막 줄이 보이도록 자동 스크롤

    def process_queue(self):
        """큐를 주기적으로 확인하여 새 귓속말이 있으면 화면에 표시합니다."""
        try:
            # 큐에서 non-blocking 방식으로 아이템 가져오기
            whisper = self.queue.get_nowait()
            self.add_whisper_log(whisper)
        except queue.Empty:
            # 큐가 비어있으면 아무것도 하지 않음
            pass
        finally:
            # 100ms 후에 다시 이 함수를 호출
            self.after(100, self.process_queue)


class AutomationApp:
    def __init__(self, root):
        self.root = root
        app_logger.info("Initializing AutomationApp UI...")

        self.is_f5_loop_running = False

        self.root.title(GUI_CONFIG.title)
        geometry_string = f"{GUI_CONFIG.initial_width}x{GUI_CONFIG.initial_height}+{GUI_CONFIG.initial_pos_x}+{GUI_CONFIG.initial_pos_y}"
        self.root.geometry(geometry_string)
        self.root.resizable(True, True)

        # [수정] WhisperService와 GUI 간의 통신을 위한 큐 생성
        self.whisper_queue = queue.Queue()

        app_logger.info("Initializing services...")
        self.firestore_service = FirestoreService()
        app_logger.info("FirestoreService initialized successfully.")

        # [수정] WhisperService에 큐를 전달
        self.whisper_service = WhisperService(self.whisper_queue)
        app_logger.info("WhisperService initialized.")
        self.whisper_service.start()
        app_logger.info("WhisperService background thread started.")

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

        self.run_open_post_after_shop_var = tk.BooleanVar(value=True)

        self._setup_ui_layout()
        app_logger.info("UI layout setup complete.")

        # [신규] 실시간 로그 창 생성 및 시작
        self.whisper_log_window = WhisperLogWindow(self.root, self.whisper_queue)
        self.whisper_log_window.process_queue()
        app_logger.info("Whisper log window initialized and started.")

        self._setup_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui_layout(self):
        """UI 위젯들을 생성하고 배치합니다."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        right_frame = ttk.LabelFrame(main_frame, text="최근 귓속말 (고유 닉네임 10명)", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- 왼쪽 프레임 ---
        sequence_options_frame = ttk.LabelFrame(left_frame, text="F2 동작 설정", padding=10)
        sequence_options_frame.pack(fill=tk.X, pady=(0, 10), anchor='n')

        open_post_checkbox = ttk.Checkbutton(
            sequence_options_frame,
            text="상점 열기 후 우체통 자동 열기",
            variable=self.run_open_post_after_shop_var,
            onvalue=True,
            offvalue=False
        )
        open_post_checkbox.pack(fill=tk.X)

        delivery_frame = ttk.LabelFrame(left_frame, text="배송", padding=10)
        delivery_frame.pack(fill=tk.X, anchor='n')
        delivery_type_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        delivery_type_frame.pack(fill=tk.X)
        ttk.Label(delivery_type_frame, text="유형:").pack(side=tk.LEFT, padx=(0, 10))
        standard_radio = ttk.Radiobutton(delivery_type_frame, text="Standard", variable=self.delivery_type_var,
                                         value="standard")
        standard_radio.pack(side=tk.LEFT, padx=5)
        express_radio = ttk.Radiobutton(delivery_type_frame, text="Express", variable=self.delivery_type_var,
                                        value="express")
        express_radio.pack(side=tk.LEFT, padx=5)

        receiver_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        receiver_frame.pack(fill=tk.X)
        ttk.Label(receiver_frame, text="수신인:").pack(side=tk.LEFT, padx=(0, 10))
        self.receiver_entry = ttk.Entry(receiver_frame, textvariable=self.receiver_var)
        self.receiver_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
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

        quick_copy_frame = ttk.LabelFrame(left_frame, text="빠른 응답 복사", padding=10)
        quick_copy_frame.pack(fill=tk.X, pady=(10, 0), anchor='n')
        response1 = "일반/특배 어떻게 보내드릴까요?"
        response2 = "세트수 + 일반/특배 알려주시면 보내드려요~"
        copy_button1 = ttk.Button(quick_copy_frame, text=response1,
                                  command=lambda: self._copy_response_to_clipboard(response1))
        copy_button1.pack(pady=(0, 2), fill=tk.X)
        copy_button2 = ttk.Button(quick_copy_frame, text=response2,
                                  command=lambda: self._copy_response_to_clipboard(response2))
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

        debug_button = ttk.Button(right_frame, text="오버레이 보기", command=self._run_overlay_debug)
        debug_button.pack(fill=tk.X, pady=(10, 0))

        self._refresh_whisper_list()

    def _save_receiver_as_whisper(self):
        """'수신인' 입력창의 닉네임을 DB에 저장합니다. 내용은 '수동저장'으로 고정됩니다."""
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
            print(f"🚨 수동 저장 중 오류 발생: {e}")

    def _toggle_f5_loop(self):
        """아이템 받기 루프의 시작/중단 상태를 토글합니다."""
        if self.is_f5_loop_running:
            print("\n[단축키 F12] 아이템 받기 루프 중단 신호를 보냅니다...")
            self.is_f5_loop_running = False
        else:
            print("\n[단축키 F12] 아이템 받기 루프를 시작합니다 (최대 100회)...")
            self.is_f5_loop_running = True
            threading.Thread(target=self._run_receive_sequence, daemon=True).start()

    def _run_receive_sequence(self):
        """아이템을 탐색하고 작업을 수행하는 시퀀스를 반복합니다."""
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
                while time.time() - search_start_time < 5:
                    if not self.is_f5_loop_running: break
                    payment_location = screen_utils.find_image_in_region(PAYMENT_IMAGE_PATH, search_region,
                                                                         GLOBAL_CONFIDENCE)
                    if payment_location:
                        break
                    time.sleep(0.2)
                if not self.is_f5_loop_running: break
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
                if not self.is_f5_loop_running: break
                if receipt_found:
                    pyautogui.press('enter')
                    time.sleep(1.5)
                else:
                    print(f"경고: 5초 내에 '{RECEIPT_IMAGE_PATH.name}' 이미지를 찾지 못했습니다.")
            else:
                print("\n--- 아이템 받기 100회 루프가 모두 완료되었습니다. ---")
        finally:
            self.is_f5_loop_running = False

    def _setup_window_preset_f5(self):
        """F5 프리셋: 창 테두리 제거 및 크기/위치 조정을 수행합니다."""
        print("\n[단축키 F5] 창 설정 프리셋을 적용합니다.")
        if activate_maple_window():
            remove_window_border()
            resize_window(1366, 768)
            print("창 설정이 완료되었습니다.")

    def _handle_hotkey(self, key):
        try:
            if key == pynput_keyboard.Key.f1:
                print("\n[단축키 F1] 배송 시작 동작을 실행합니다.")
                self.root.after(0, self._run_delivery)
            elif key == pynput_keyboard.Key.f2:
                self.root.after(0, self._run_f2_sequence)
            elif key == pynput_keyboard.Key.f3:
                print("\n[단축키 F3] 창 크기를 1366x768로 변경합니다.")
                self.root.after(0, lambda: resize_window(1366, 768))
            elif key == pynput_keyboard.Key.f4:
                print("\n[단축키 F4] 창 크기를 1900x300으로 변경합니다.")
                self.root.after(0, lambda: resize_window(1900, 300))
            elif key == pynput_keyboard.Key.f5:
                self.root.after(0, self._setup_window_preset_f5)
            elif key == pynput_keyboard.Key.f12:
                print("\n[단축키 F12] 아이템 받기 시작/중단을 토글합니다.")
                self.root.after(0, self._toggle_f5_loop)
        except Exception as e:
            print(f"단축키 처리 중 오류 발생: {e}")

    def _run_f2_sequence(self):
        """[수정] F2 단축키의 동작을 체크박스 값에 따라 분기하여 처리합니다."""
        # '상점 열기'는 체크박스 상태와 관계없이 항상 먼저 실행됩니다.
        open_shop()

        if self.run_open_post_after_shop_var.get():
            # 체크박스 ON: '우체통 열기'를 추가로 실행합니다.
            print("\n'우체통 자동 열기' 옵션이 활성화되어 있어, 이어서 우체통 열기를 시작합니다.")
            open_post()
            print("\n[단축키 F2] 전체 동작(상점->우체통)이 완료되었습니다.")
        else:
            # 체크박스 OFF: '상점 열기' 완료 후, '창 초기화'를 추가로 실행합니다.
            print("\n'우체통 자동 열기' 옵션이 비활성화되어 있어, 창 초기화를 추가로 수행합니다.")
            prepare_and_activate_window("창 초기화")
            print("\n[단축키 F2] 상점 열기 및 창 초기화 동작이 완료되었습니다.")

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
        """귓속말 목록을 닉네임만 표시하도록 간소화합니다."""
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
        print(f"📋 클립보드에 복사됨: '{response}'")

    def _handle_whisper_selection(self, nickname: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(nickname)
        print(f"📋 '{nickname}'가 클립보드에 복사되었습니다.")
        self.receiver_var.set(nickname)
        print(f"🖋️ 수신인에 '{nickname}'이(가) 입력되었습니다.")

    def _run_delivery(self):
        """배송 작업을 수행하는 일련의 과정을 자동화합니다."""
        # --- F1 실행 조건 검사 ---
        print("F1 조건 확인: post.png와 inven.png를 찾습니다...")
        post_loc = screen_utils.find_image_on_screen(POST_CONFIG.base_image_path, GLOBAL_CONFIDENCE)
        inven_loc = screen_utils.find_image_on_screen(INVEN_CONFIG.base_image_path, GLOBAL_CONFIDENCE)

        if not post_loc or not inven_loc:
            print("오류: 'post.png' 또는 'inven.png'를 찾을 수 없어 F1 동작을 중단합니다.")
            messagebox.showwarning("이미지 없음", "'post.png' 또는 'inven.png'를 화면에서 찾을 수 없습니다.")
            return
        print(f"두 이미지 모두 찾았습니다: post={post_loc}, inven={inven_loc}")

        x_diff = abs(post_loc.left - inven_loc.left)
        print(f"좌표 X 차이: {x_diff}")

        if x_diff < 845:
            print(f"좌표 X 차이({x_diff})가 845 미만이므로 인벤토리 위치를 조정합니다.")

            h_margin = inven_loc.width * 0.2
            v_margin = inven_loc.height * 0.2

            click_x = random.randint(int(inven_loc.left + h_margin), int(inven_loc.left + inven_loc.width - h_margin))
            click_y = random.randint(int(inven_loc.top + v_margin), int(inven_loc.top + inven_loc.height - v_margin))

            pyautogui.moveTo(click_x, click_y, duration=0.2)
            pyautogui.dragRel(150, 0, duration=0.5)
            print(f"인벤토리 드래그 완료: ({click_x}, {click_y}) -> (+150, 0)")
            time.sleep(0.3)

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
            # [수정] send_action의 결과(True/False)를 받아 후속 조치 결정
            success = send_action(delivery_type, receiver_name, amount)
            if success:
                print(f"정보: 배송 작업 완료! 유형: {delivery_type}, 수신인: {receiver_name}, 금액: {amount}")
            else:
                # 재고 부족 또는 기타 오류로 배송 실패 시 F2 동작 실행
                print("배송 실패(재고 부족). F2(상점 열기) 동작을 실행합니다.")
                messagebox.showinfo("재고 부족", "인벤토리에서 아이템을 모두 찾을 수 없습니다. 상점을 엽니다.")
                open_shop()
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
        app_logger.critical("A fatal error occurred during application startup. GUI cannot be displayed.",
                            exc_info=True)
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            messagebox.showerror("치명적 오류",
                                 f"애플리케이션 시작 중 심각한 오류가 발생했습니다.\n\n자세한 내용은 'logs/app_main.log' 파일을 확인해주세요.\n\n오류: {e}")
        except tk.TclError:
            print(f"CRITICAL: 애플리케이션 시작 중 심각한 오류가 발생했습니다. 로그 파일을 확인해주세요. 오류: {e}")
        sys.exit(1)

    app_logger.info("Application shutdown gracefully.")