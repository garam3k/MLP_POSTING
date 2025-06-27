# whisper_parser.py
from dataclasses import dataclass
from typing import Optional
from playsound import playsound

from config import WHISPER_PARSER_CONFIG
# [신규] 로거 설정을 임포트합니다.
from logger_setup import setup_whisper_logger

# [신규] 파서 전용 로거를 가져옵니다.
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
    """페이로드에서 헤더 패턴을 찾고, 고정된 헤더 길이만큼 건너뛴 후 파싱합니다."""
    cfg = WHISPER_PARSER_CONFIG

    # [신규] 1. display_filter를 통과한 모든 메시지를 헤더 매칭 전에 로깅합니다.
    logger.debug(f"Received payload for parsing (len: {len(payload_hex)}): {payload_hex}")

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
            # 기존 print 외에 에러 로그도 기록합니다.
            logger.error(f"Failed to play sound: {e}")
            print(f"🚨 효과음 재생 오류: {e}")

        decoded_name = _decode_hex_to_utf8(part_a)
        decoded_content = _decode_hex_to_utf8(part_c)

        # [신규] 2. 귓속말 파싱 성공 시, 해당 내용을 로깅합니다.
        log_message = f"Whisper Parsed Successfully: Name='{decoded_name}', Channel='{decoded_channel}', Content='{decoded_content}'"
        logger.info(log_message)

        print(f"  [귓속말 발견!] 이름={decoded_name}, 채널={decoded_channel}, 내용={decoded_content}")
        return Whisper(name=decoded_name, channel=decoded_channel, content=decoded_content)

    return None