# Mapleland Automation & Whisper Catcher

## 1\. 프로젝트 개요

이 프로젝트는 '메이플랜드(MapleStory Worlds)' 클라이언트를 위한 파이썬 기반 자동화 및 데이터 수집 도구입니다. GUI를 통해 제어되며, 다음과 같은 두 가지 핵심 기능을 중심으로 설계되었습니다.

1.  **UI 자동화**: `pyautogui`를 기반으로 게임 내의 반복적인 작업을 자동화합니다. (예: 배송, 상점 및 우체통 이용)
2.  **귓속말 캡처**: `pyshark`를 이용한 네트워크 패킷 필터링을 통해 실시간으로 귓속말을 감지하고, 이를 `Cloud Firestore` 데이터베이스에 저장 및 조회합니다.

프로젝트 전체는 \*\*단일 책임 원칙(SRP)\*\*에 따라 철저하게 모듈화되어, 각 파일이 명확하고 독립적인 책임을 갖도록 설계되었습니다. 이는 유지보수, 테스트, 그리고 기능 확장의 용이성을 극대화합니다.

## 2\. 핵심 기능

  - **GUI 기반 제어**: Tkinter를 사용하여 모든 주요 기능을 실행할 수 있는 직관적인 GUI 제공
  - **워크플로우 자동화**: '상점 열기', '우체통 열기', '배송' 등 여러 단계의 작업을 하나의 시나리오로 묶어 자동화
  - **동적 UI 제어**: 이미지 인식과 고정 좌표 방식을 혼용하여 다른 유저나 환경 변화에 강건하게 NPC 상호작용 및 UI 조작 수행
  - **실시간 귓속말 감지**: 네트워크 패킷을 실시간으로 분석하여 조건에 맞는 귓속말만 필터링 후 감지 및 알림
  - **데이터베이스 연동**: 감지된 귓속말 데이터를 Cloud Firestore에 저장하고, GUI에서 최근 데이터를 조회 및 관리
  - **윈도우 제어**: 대상 윈도우의 크기, 테두리, 활성화 상태를 직접 제어
  - **상세한 디버깅 도구**: '오버레이 보기' 기능을 통해 자동화 로직이 인식하는 모든 UI 요소의 위치를 시각적으로 확인 가능

## 3\. 프로젝트 아키텍처

본 프로젝트는 SRP를 기반으로 한 계층형 아키텍처를 따릅니다. 각 계층은 명확한 책임을 가지며, 상위 계층은 하위 계층에 의존합니다.

  - **Presentation Layer (`main.py`)**

      - 사용자에게 보여지는 GUI를 담당합니다. 사용자의 입력을 받아 Service Layer에 전달하는 역할만 수행합니다.

  - **Service / Workflow Layer (`delivery.py`, `map_util.py`, `whisper_service.py`)**

      - '배송', '맵 이동' 등과 같이 여러 단계를 포함하는 고수준의 비즈니스 로직(사용자 시나리오)을 오케스트레이션합니다. 각 시나리오의 순서와 흐름을 정의합니다.

  - **Domain / Utility Layer (`inven_util.py`, `post_util.py`, `whisper_parser.py`)**

      - '인벤토리', '우편', '귓속말'과 같은 특정 도메인에 특화된 기능들을 담당합니다. 예를 들어 `whisper_parser`는 오직 패킷을 귓속말로 해석하는 책임만 가집니다.

  - **Infrastructure / Core Layer (`window_util.py`, `screen_utils.py`, `firestore_service.py`, `network_sniffer.py`)**

      - 운영체제, 화면, 데이터베이스, 네트워크 등 외부 시스템과의 직접적인 상호작용을 추상화합니다. 예를 들어 `screen_utils`는 `pyautogui` 라이브러리에 대한 의존성을 캡슐화합니다.

  - **Configuration Layer (`config.py`)**

      - 모든 설정값, 좌표, 경로, API 키 등을 중앙에서 관리하여 코드 변경 없이 환경에 맞게 동작을 수정할 수 있도록 합니다.

## 4\. 파일 구조

```
.
├── 📂 assets/              # 이미지 에셋 저장 폴더
│
├── 📜 config.py             # (핵심) 모든 설정, 좌표, 경로 등 관리
├── 📜 main.py              # (실행) GUI 애플리케이션 실행 및 UI 구성
│
├── 📜 delivery.py           # '배송' 관련 워크플로우
├── 📜 map_util.py           # '맵/NPC' 관련 워크플로우
├── 📜 whisper_service.py    # '귓속말 감지' 백그라운드 서비스
│
├── 📜 firestore_service.py  # Firestore 데이터베이스 연동 책임
├── 📜 inven_util.py         # 인벤토리 UI 관련 기능
├── 📜 network_sniffer.py    # 네트워크 패킷 캡처 책임
├── 📜 post_util.py          # 우편 UI 관련 기능
├── 📜 whisper_parser.py     # 귓속말 패킷 파싱 책임
│
├── 📜 grid_cell_utils.py    # 범용 그리드/좌표 계산 유틸리티
├── 📜 screen_utils.py       # 저수준 화면 제어 (이미지 탐색 등) 유틸리티
├── 📜 window_util.py        # 윈도우 핸들링 (활성화, 크기 변경) 유틸리티
└── 📜 debug_overlay_util.py # 디버깅용 오버레이 시각화 유틸리티
```

## 5\. 설치 및 설정

### 5.1. 필수 라이브러리 설치

아래 명령어를 통해 프로젝트 실행에 필요한 모든 Python 라이브러리를 설치합니다.

```bash
pip install pyautogui Pillow pygetwindow pywin32 opencv-python pyperclip pyshark firebase-admin "playsound==1.2.2"
```

### 5.2. `TShark` 설치 (귓속말 감지 기능 필수)

`pyshark` 라이브러리는 **Wireshark**의 커맨드라인 도구인 `TShark`가 시스템에 설치되어 있어야 동작합니다.

1.  [Wireshark 공식 홈페이지](https://www.wireshark.org/download.html)에서 Wireshark를 다운로드하여 설치합니다.
2.  설치 과정에서 `tshark`가 시스템 `PATH`에 추가되도록 옵션을 선택합니다.

### 5.3. `serviceAccountKey.json` 파일 준비

귓속말 데이터를 저장하기 위해 Google Cloud Firestore와의 연동이 필요합니다.

1.  Google Cloud Platform에서 새 프로젝트를 생성하고 Firestore 데이터베이스를 활성화합니다.
2.  프로젝트 설정에서 '서비스 계정(Service Accounts)'으로 이동하여 새 서비스 계정을 만들고, 비공개 키를 생성합니다.
3.  생성된 `.json` 키 파일의 이름을 `serviceAccountKey.json`으로 변경하고, 이 프로젝트의 루트 디렉터리에 위치시킵니다.

### 5.4. `config.py` 설정 검토

코드를 실행하기 전, `config.py` 파일을 열어 사용자 환경에 맞게 다음 값들을 반드시 확인하고 수정해야 합니다.

  - **`SNIFFER_CONFIG.interface`**: 귓속말을 감지할 네트워크 인터페이스 이름 (예: '이더넷', 'Wi-Fi'). `cmd`에서 `tshark -D` 명령어로 확인 가능.
  - **`DEWEY_CONFIG`, `DORAN_CONFIG`**: 고정 좌표 클릭을 위한 NPC의 상대 좌표.
  - 기타 UI 요소(`INVEN_CONFIG`, `POST_CONFIG` 등)의 오프셋 값.

## 6\. 실행 방법

모든 설정이 완료된 후, `main.py` 파일을 실행하여 GUI 애플리케이션을 시작합니다.

```bash
python main.py
```

## 7\. 향후 개발 가이드라인 ("Vibe Coding"을 위하여)

이 프로젝트의 일관성과 유지보수성을 유지하며 새로운 기능을 추가하려면 다음 원칙을 따라주세요.

1.  **단일 책임 원칙 (SRP)을 최우선으로**: 새로운 기능을 추가할 때, "이 코드의 책임은 무엇인가?"를 먼저 생각하고 적절한 모듈에 배치하거나 새로운 모듈을 만드세요.

      - **설정값인가?** -\> `config.py`에 추가
      - **단순한 화면 조작인가?** -\> `screen_utils.py`에 함수 추가
      - **새로운 UI 영역에 대한 기능인가?** -\> `(ui_name)_util.py` 파일 생성
      - **여러 단계를 포함하는 새로운 시나리오인가?** -\> `(feature)_workflow.py` 와 같은 워크플로우 파일 생성

2.  **하드코딩 금지**: 좌표, 경로, 이름 등 바뀔 가능성이 있는 값은 반드시 `config.py`에서 관리합니다.

3.  **GUI는 오직 호출만**: `main.py`에는 비즈니스 로직을 추가하지 마세요. GUI는 오직 다른 모듈의 함수를 호출하고 결과를 보여주는 역할만 수행해야 합니다.

4.  **저수준 기능은 추상화**: 외부 라이브러리(`pyautogui`, `pyshark` 등)를 직접 호출하는 코드는 `screen_utils.py`, `network_sniffer.py` 같은 'Infrastructure/Core' 계층 모듈에 모아주세요. 다른 모듈들은 이 추상화된 함수를 사용해야 합니다.

이 가이드라인을 따르면, 다른 LLM이나 개발자가 프로젝트에 새롭게 기여하더라도 기존의 깔끔한 구조와 "Vibe"를 해치지 않고 생산적으로 협업할 수 있습니다.