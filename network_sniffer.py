# network_sniffer.py
from typing import Callable

import pyshark

from config import SNIFFER_CONFIG


def start_sniffing(on_packet: Callable[[str], None]):
    """
    네트워크 스니핑을 시작하고, 패킷이 감지될 때마다 콜백 함수를 호출합니다.
    """
    cfg = SNIFFER_CONFIG
    print(f"🚀 패킷 캡처를 시작합니다... (인터페이스: {cfg.interface})")
    try:
        capture = pyshark.LiveCapture(
            interface=cfg.interface,
            display_filter=cfg.display_filter
        )
        for packet in capture.sniff_continuously():
            if hasattr(packet, 'data') and hasattr(packet.data, 'data'):
                on_packet(packet.data.data)
    except Exception as e:
        print(f"🚨 스니퍼 실행 중 심각한 오류 발생: {e}")