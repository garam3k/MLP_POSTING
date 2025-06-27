# logger_setup.py
import logging
import os
from logging.handlers import RotatingFileHandler

# 로그 파일을 저장할 디렉터리와 파일 이름 설정
LOG_DIR = "logs"
LOG_FILENAME = "whisper_parsing_debug.log"


def setup_whisper_logger():
    """귓속말 파서 전용 로거를 설정하고 반환합니다."""

    # 'logs' 디렉터리가 없으면 생성
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # 로그 메시지 포맷 지정 (시간 - 로그레벨 - 메시지)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 로그 파일 경로
    log_file_path = os.path.join(LOG_DIR, LOG_FILENAME)

    # 로거 인스턴스 생성
    logger = logging.getLogger("whisper_parser")
    logger.setLevel(logging.DEBUG)  # DEBUG 레벨 이상의 모든 로그를 기록

    # 핸들러 중복 추가 방지
    if not logger.handlers:
        # 로그 파일이 5MB를 초과하면 새 파일로 교체하고, 최대 3개의 백업 파일을 유지합니다.
        handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
        handler.setFormatter(log_formatter)
        logger.addHandler(handler)

    return logger