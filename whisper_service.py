# whisper_service.py
import asyncio
import threading

import whisper_parser  # whisper_parser 모듈을 임포트
from firestore_service import FirestoreService
from network_sniffer import start_sniffing


class WhisperService:
    def __init__(self):
        self.firestore_service = FirestoreService()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _handle_packet(self, payload_hex: str):
        """캡처된 패킷을 처리하는 콜백 함수"""
        # 여기서 whisper_parser의 parse_from_payload 함수를 호출합니다.
        whisper = whisper_parser.parse_from_payload(payload_hex)
        if whisper:
            self.firestore_service.add_whisper(whisper.name, whisper.channel, whisper.content)

    def _run(self):
        """백그라운드 스레드에서 실행될 메인 로직"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_sniffing(on_packet=self._handle_packet)
        except Exception as e:
            print(f"🚨 Whisper 서비스 스레드 실행 중 예외 발생: {e}")

    def start(self):
        """서비스 스레드를 시작합니다."""
        print("Whisper 감지 서비스를 시작합니다.")
        self.thread.start()