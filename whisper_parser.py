# whisper_parser.py
from dataclasses import dataclass
from typing import Optional

from playsound import playsound

from config import WHISPER_PARSER_CONFIG
from logger_setup import setup_whisper_logger

logger = setup_whisper_logger()


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
    """[수정] 페이로드에서 고정 텍스트 헤더를 찾고, 지정된 길이만큼 건너뛴 후 파싱합니다."""
    cfg = WHISPER_PARSER_CONFIG

    logger.debug(f"Received payload for parsing (len: {len(payload_hex)}): {payload_hex}")

    # [수정] 정규식 검색 대신, 고정된 텍스트(header_text)를 찾습니다.
    header_start_index = payload_hex.find(cfg.header_text)

    # [수정] .find()는 텍스트를 못 찾으면 -1을 반환합니다.
    if header_start_index == -1:
        return None

    # [수정] 콘텐츠 시작 위치를 (헤더 시작점 + 헤더 텍스트 길이 + 건너뛸 길이)로 계산합니다.
    content_start_index = header_start_index + len(cfg.header_text) + cfg.skip_after_header
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
            logger.error(f"Failed to play sound: {e}")
            print(f"🚨 효과음 재생 오류: {e}")

        decoded_name = _decode_hex_to_utf8(part_a)
        decoded_content = _decode_hex_to_utf8(part_c)

        log_message = f"Whisper Parsed Successfully: Name='{decoded_name}', Channel='{decoded_channel}', Content='{decoded_content}'"
        logger.info(log_message)

        print(f"  [귓속말 발견!] 이름={decoded_name}, 채널={decoded_channel}, 내용={decoded_content}")
        return Whisper(name=decoded_name, channel=decoded_channel, content=decoded_content)

    return None