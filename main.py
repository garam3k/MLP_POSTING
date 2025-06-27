# main.py
import tkinter as tk
from tkinter import ttk
from pynput import keyboard as pynput_keyboard

from delivery import send_action, show_all_overlays_for_debugging
from window_util import remove_window_border, resize_window, activate_maple_window
from map_util import open_shop, open_post
from whisper_service import WhisperService
from firestore_service import FirestoreService


class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("자동화 시스템 v2.3 (Quick-Copy Added)")
        # [수정] 새 위젯을 위해 기본 창 높이 증가
        self.root.geometry("800x620")
        self.root.resizable(True, True)

        # --- 서비스 초기화 ---
        self.firestore_service = FirestoreService()
        self.whisper_service = WhisperService()
        self.whisper_service.start()

        remove_window_border()
        resize_window(1366, 768)

        # --- 스타일 설정 ---
        style = ttk.Style(self.root)
        style.configure("TFrame", padding=10)
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5, font=('calibri', 10, 'bold'))
        style.configure("TLabelframe.Label", font=('calibri', 11, 'bold'))
        style.configure("Outline.TButton", padding=2)

        # --- 위젯 변수 설정 ---
        self.delivery_type_var = tk.StringVar(value="standard")
        self.receiver_var = tk.StringVar(value="")
        self.standard_amount_var = tk.StringVar(value="45000")
        self.express_amount_var = tk.StringVar(value="60000")

        # --- UI 레이아웃 구성 ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        right_frame = ttk.LabelFrame(main_frame, text="최근 귓속말 (고유 닉네임 15명)", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- 왼쪽 프레임 내부 위젯 구성 ---
        top_control_frame = ttk.Frame(left_frame)
        top_control_frame.pack(fill=tk.X, pady=(0, 10), anchor='n')

        macro_frame = ttk.LabelFrame(top_control_frame, text="기능 실행", padding=10)
        macro_frame.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        shop_button = ttk.Button(macro_frame, text="상점 열기 (F2-1)", command=open_shop)
        shop_button.pack(pady=2, fill=tk.X)
        post_button = ttk.Button(macro_frame, text="우체통 열기 (F2-2)", command=open_post)
        post_button.pack(pady=2, fill=tk.X)

        window_control_frame = ttk.LabelFrame(top_control_frame, text="창 크기 조절", padding=10)
        window_control_frame.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        preset1_button = ttk.Button(window_control_frame, text="1366 x 768 (F3)",
                                    command=lambda: resize_window(1366, 768))
        preset1_button.pack(pady=2, fill=tk.X)
        preset2_button = ttk.Button(window_control_frame, text="1900 x 300 (F4)",
                                    command=lambda: resize_window(1900, 300))
        preset2_button.pack(pady=2, fill=tk.X)

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
        self.receiver_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

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

        # --- [신규] 빠른 응답 복사 프레임 ---
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

        # --- 오른쪽 프레임 내부 위젯 구성 ---
        whisper_top_frame = ttk.Frame(right_frame)
        whisper_top_frame.pack(fill=tk.X, pady=(0, 5))

        refresh_button = ttk.Button(whisper_top_frame, text="새로고침", command=self._refresh_whisper_list)
        refresh_button.pack(fill=tk.X)

        canvas = tk.Canvas(right_frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._refresh_whisper_list()

        # --- 전역 단축키 리스너 설정 ---
        self._setup_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _copy_response_to_clipboard(self, response: str):
        """[신규] 지정된 응답 문구를 클립보드에 복사합니다."""
        self.root.clipboard_clear()
        self.root.clipboard_append(response)
        print(f"📋 클립보드에 복사됨: '{response}'")

    def _handle_whisper_selection(self, nickname: str):
        """귓속말 목록의 이름을 클립보드에 복사하고 수신인 칸에도 입력합니다."""
        self.root.clipboard_clear()
        self.root.clipboard_append(nickname)
        print(f"📋 '{nickname}'가 클립보드에 복사되었습니다.")
        self.receiver_var.set(nickname)
        print(f"🖋️ 수신인에 '{nickname}'이(가) 입력되었습니다.")

    def _run_f2_sequence(self):
        """F2 단축키에 대한 순차적 동작을 실행합니다."""
        print("\n[단축키 F2] 상점 열기 -> 우체통 열기 순차 실행 시작...")
        open_shop()
        print("\n상점 열기 완료. 이어서 우체통 열기를 시작합니다.")
        open_post()
        print("\n[단축키 F2] 모든 동작이 완료되었습니다.")

    def _handle_hotkey(self, key):
        """눌린 키에 따라 지정된 동작을 실행하는 콜백 함수"""
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
        except Exception as e:
            print(f"단축키 처리 중 오류 발생: {e}")

    def _setup_hotkeys(self):
        """전역 단축키 리스너를 시작합니다."""
        self.hotkey_listener = pynput_keyboard.Listener(on_press=self._handle_hotkey)
        self.hotkey_listener.start()
        print("✅ 전역 단축키가 활성화되었습니다.")
        print("  - F1: 배송 시작")
        print("  - F2: 상점 열기 → 우체통 열기")
        print("  - F3: 창 크기 1366x768")
        print("  - F4: 창 크기 1900x300")

    def _on_closing(self):
        """애플리케이션 종료 시 리스너를 중지합니다."""
        print("애플리케이션을 종료합니다. 단축키 리스너를 중지합니다.")
        if self.hotkey_listener.is_alive():
            self.hotkey_listener.stop()
        self.root.destroy()

    def _refresh_whisper_list(self):
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

    def _run_delivery(self):
        if not activate_maple_window():
            return

        delivery_type = self.delivery_type_var.get()
        receiver_name = self.receiver_var.get()

        if delivery_type == "standard":
            amount = self.standard_amount_var.get()
        else:
            amount = self.express_amount_var.get()

        if not receiver_name:
            print("경고: 수신인 이름을 입력해주세요.")
            return
        if not amount.isdigit():
            print("경고: 금액은 숫자만 입력 가능합니다.")
            return

        try:
            send_action(delivery_type, receiver_name, amount)
            print(f"정보: 배송 작업 완료! 유형: {delivery_type}, 수신인: {receiver_name}, 금액: {amount}")
        except Exception as e:
            print(f"오류: 자동화 중 오류 발생: {e}")

    def _run_overlay_debug(self):
        if not activate_maple_window():
            return

        try:
            show_all_overlays_for_debugging()
            print("정보: 디버그 오버레이가 화면에 표시되었습니다. 이미지 뷰어를 확인해주세요.")
        except Exception as e:
            print(f"오류: 오버레이 표시 중 오류 발생: {e}\n(이미지 파일 경로를 확인해주세요.)")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()