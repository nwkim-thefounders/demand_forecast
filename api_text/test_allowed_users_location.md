# test_allowed_users_location.py

## 목적
`ALLOWED_USERS` 접속 위치(CUTOVER) 설정이 기본값 불변·화이트리스트·읽기/쓰기 공유를 지키는지 오프라인으로 검증한다.

## 흐름 및 위치
- `tests/test_allowed_users_location.py`: 기본값, 환경 변수, secrets, 화이트리스트 거부(4건), 읽기 쿼리, 쓰기 쿼리(가짜 엔진, 가짜 secrets 사용 — 실제 접속·secrets.toml 미사용).
- 실행: `venv\Scripts\python.exe -m pytest -q`
