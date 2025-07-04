# shared_state.py
# 이 모듈은 애플리케이션의 여러 부분에서 공유되는 전역 상태를 보유합니다.

# 이 값이 True가 되면, 실행 중인 장기 작업이 정상적으로 중단되어야 합니다.
stop_action = False

# 이 값이 True가 되면, 단축키 리스너가 일시적으로 동작하지 않습니다.
ignore_hotkeys = False