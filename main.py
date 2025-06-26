# main.py
import tkinter as tk
from tkinter import ttk
from delivery import send_action, show_all_overlays_for_debugging
from window_util import remove_window_border, resize_window, activate_maple_window
from map_util import open_shop, open_post


class DeliveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("자동화 시스템")
        # 새 레이아웃에 맞게 창 크기 조정
        self.root.geometry("450x520")
        self.root.resizable(False, False)

        # 프로그램 시작 시 창 테두리 제거
        remove_window_border()

        # 스타일 설정
        style = ttk.Style(self.root)
        style.configure("TFrame", padding=10)
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5, font=('calibri', 10, 'bold'))
        style.configure("TLabelframe.Label", font=('calibri', 11, 'bold'))

        # --- 위젯 변수 설정 ---
        self.delivery_type_var = tk.StringVar(value="standard")
        self.receiver_var = tk.StringVar(value="")
        # Standard와 Express 금액 변수를 그대로 사용
        self.standard_amount_var = tk.StringVar(value="45000")
        self.express_amount_var = tk.StringVar(value="60000")

        # --- UI 구성 ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 상단 제어 프레임 ---
        top_control_frame = ttk.Frame(main_frame)
        top_control_frame.pack(fill=tk.X, pady=(0, 10))

        macro_frame = ttk.LabelFrame(top_control_frame, text="매크로 실행", padding=10)
        macro_frame.pack(side=tk.LEFT, padx=(0, 5), fill=tk.BOTH, expand=True)
        shop_button = ttk.Button(macro_frame, text="상점 열기", command=open_shop)
        shop_button.pack(pady=2, fill=tk.X)
        post_button = ttk.Button(macro_frame, text="우체통 열기", command=open_post)
        post_button.pack(pady=2, fill=tk.X)

        window_control_frame = ttk.LabelFrame(top_control_frame, text="창 크기 조절", padding=10)
        window_control_frame.pack(side=tk.LEFT, padx=(5, 0), fill=tk.BOTH, expand=True)
        preset1_button = ttk.Button(window_control_frame, text="1366 x 768", command=lambda: resize_window(1366, 768))
        preset1_button.pack(pady=2, fill=tk.X)
        preset2_button = ttk.Button(window_control_frame, text="1900 x 300", command=lambda: resize_window(1900, 300))
        preset2_button.pack(pady=2, fill=tk.X)

        # --- 배송 프레임 ---
        delivery_frame = ttk.LabelFrame(main_frame, text="배송", padding=10)
        delivery_frame.pack(fill=tk.BOTH, expand=True)

        # 배송 유형 선택 (라디오 버튼)
        delivery_type_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        delivery_type_frame.pack(fill=tk.X)
        ttk.Label(delivery_type_frame, text="유형:").pack(side=tk.LEFT, padx=(0, 10))
        # 금액 입력창 업데이트 함수(command)는 더 이상 필요 없으므로 제거
        standard_radio = ttk.Radiobutton(delivery_type_frame, text="Standard", variable=self.delivery_type_var,
                                         value="standard")
        standard_radio.pack(side=tk.LEFT, padx=5)
        express_radio = ttk.Radiobutton(delivery_type_frame, text="Express", variable=self.delivery_type_var,
                                        value="express")
        express_radio.pack(side=tk.LEFT, padx=5)

        # 수신인 입력
        receiver_frame = ttk.Frame(delivery_frame, padding=(0, 5))
        receiver_frame.pack(fill=tk.X)
        ttk.Label(receiver_frame, text="수신인:").pack(side=tk.LEFT, padx=(0, 10))
        self.receiver_entry = ttk.Entry(receiver_frame, textvariable=self.receiver_var)
        self.receiver_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # [수정됨] 금액 입력 (두 개의 분리된 입력창)
        amount_frame = ttk.Frame(delivery_frame, padding=(0, 10))
        amount_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(amount_frame, text="Standard 금액:").grid(row=0, column=0, sticky="w", pady=2)
        self.standard_amount_entry = ttk.Entry(amount_frame, textvariable=self.standard_amount_var)
        self.standard_amount_entry.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(amount_frame, text="Express 금액:").grid(row=1, column=0, sticky="w", pady=2)
        self.express_amount_entry = ttk.Entry(amount_frame, textvariable=self.express_amount_var)
        self.express_amount_entry.grid(row=1, column=1, sticky="ew", padx=5)
        amount_frame.columnconfigure(1, weight=1)  # 입력창이 가로로 확장되도록 설정

        # 실행 버튼
        action_button_frame = ttk.Frame(delivery_frame)
        action_button_frame.pack(fill=tk.X)
        run_button = ttk.Button(action_button_frame, text="배송 시작", command=self._run_delivery)
        run_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        debug_button = ttk.Button(action_button_frame, text="오버레이 보기", command=self._run_overlay_debug)
        debug_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    def _run_delivery(self):
        """사용자가 입력한 값으로 배송 작업을 시작합니다."""
        if not activate_maple_window():
            return

        delivery_type = self.delivery_type_var.get()
        receiver_name = self.receiver_var.get()

        # [수정됨] 선택된 배송 유형에 따라 해당 금액 변수에서 값을 가져옵니다.
        if delivery_type == "standard":
            amount = self.standard_amount_var.get()
        else:  # "express"
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
        """디버그 오버레이 표시 함수를 실행합니다."""
        if not activate_maple_window():
            return

        try:
            show_all_overlays_for_debugging()
            print("정보: 디버그 오버레이가 화면에 표시되었습니다. 이미지 뷰어를 확인해주세요.")
        except Exception as e:
            print(f"오류: 오버레이 표시 중 오류 발생: {e}\n(이미지 파일 경로를 확인해주세요.)")


if __name__ == "__main__":
    root = tk.Tk()
    app = DeliveryApp(root)
    root.mainloop()