# firestore_service.py
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any

from config import FIRESTORE_CONFIG


class FirestoreService:
    def __init__(self):
        self.db = self._initialize_firestore()

    def _initialize_firestore(self):
        """Firestore 클라이언트를 초기화하고 반환합니다."""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(FIRESTORE_CONFIG.service_account_key_path)
                firebase_admin.initialize_app(cred)
            return firestore.client()
        except FileNotFoundError:
            print(f"오류: Firestore 서비스 계정 키 파일('{FIRESTORE_CONFIG.service_account_key_path}')을 찾을 수 없습니다.")
            exit()
        except Exception as e:
            print(f"Firestore 초기화 중 오류 발생: {e}")
            exit()

    def add_whisper(self, name: str, channel: str, comment: str):
        """파싱된 귓속말 데이터를 Firestore에 저장합니다."""
        try:
            collection_ref = self.db.collection(FIRESTORE_CONFIG.collection_name)
            data = {
                'name': name,
                'channel': channel,
                'comment': comment,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            collection_ref.add(data)
            print(f"✅ Firestore 저장 완료: {name} / {channel} / {comment}")
        except Exception as e:
            print(f"🚨 Firestore 저장 중 오류 발생: {e}")

    def get_latest_unique_nicknames(self, count: int) -> List[Dict[str, Any]]:
        """최근 귓속말 데이터에서 고유한 닉네임 목록을 지정된 수만큼 가져옵니다."""
        fetch_limit = count * 5
        try:
            query = self.db.collection(FIRESTORE_CONFIG.collection_name) \
                .order_by('created_at', direction=firestore.Query.DESCENDING) \
                .limit(fetch_limit)

            docs = query.stream()
            unique_entries = []
            seen_names = set()

            for doc in docs:
                entry = doc.to_dict()
                name = entry.get('name')
                if name and name not in seen_names:
                    unique_entries.append(entry)
                    seen_names.add(name)
                    if len(unique_entries) >= count:
                        break

            return unique_entries
        except Exception as e:
            if 'ensure an index' in str(e).lower():
                print("🚨 Firestore 색인 필요: Firestore 콘솔에서 필요한 색인을 생성해주세요.")
            else:
                print(f"🚨 Firestore 데이터 조회 중 오류 발생: {e}")
            return []