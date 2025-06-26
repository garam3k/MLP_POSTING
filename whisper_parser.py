# whisper_parser.py
from dataclasses import dataclass
from typing import Optional
from playsound import playsound

from config import WHISPER_PARSER_CONFIG


@dataclass
class Whisper:
    name: str
    channel: str
    content: str


def _decode_hex_to_utf8(hex_string: str) -> str:
    """16진수 문자열을 UTF-8로 디코딩합니다."""
    try:
        return bytes.fromhex(hex_string).decode('utf-8', errors='replace')
    except (ValueError, TypeError):
        return "[디코딩 불가]"


def parse_from_payload(payload_hex: str) -> Optional[Whisper]:
    """페이로드에서 헤더 패턴을 찾고, 고정된 헤더 길이만큼 건너뛴 후 파싱합니다."""
    cfg = WHISPER_PARSER_CONFIG

    header_match = cfg.header_pattern.search(payload_hex)

    if not header_match:
        return None

    header_start_index = header_match.start()
    content_start_index = header_start_index + cfg.header_length
    content_payload = payload_hex[content_start_index:]

    match = cfg.data_pattern.search(content_payload)

    if not match:
        return None

    part_a, part_b, part_c = match.groups()
    decoded_channel = _decode_hex_to_utf8(part_b)

    if cfg.channel_pattern.match(decoded_channel):
        try:
            playsound(cfg.sound_file_path, block=False)
        except Exception as e:
            print(f"🚨 효과음 재생 오류: {e}")

        decoded_name = _decode_hex_to_utf8(part_a)
        decoded_content = _decode_hex_to_utf8(part_c)

        print(f"  [귓속말 발견!] 이름={decoded_name}, 채널={decoded_channel}, 내용={decoded_content}")
        return Whisper(name=decoded_name, channel=decoded_channel, content=decoded_content)

    return None