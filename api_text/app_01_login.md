# app_01_login.py

## 목적
Slack OAuth2와 이메일/비밀번호 로그인을 처리한다.

## 변경된 함수
- `check_email()`: 하이픈 문자 범위 오해석을 막는 이메일 정규식으로 전체 입력을 검증한다. 일반 이메일에 쓰는 점, 밑줄, 더하기, 하이픈을 허용한다.
- `_ensure_user_data()`: 사용자 목록을 세션에 적재한다. SQLAlchemy 조회 실패 시 예외 상세를 노출하지 않고 오류 안내와 재시도 버튼을 표시하며 False를 반환한다.
- `_retry_user_data_load()`: 사용자 조회 캐시/세션을 초기화하고 Streamlit rerun을 요청한다.
- `show_login()`: 사용자 조회 성공 후 기존 인증 UI를 진행하며, 조회 실패 시 즉시 반환한다.

## 적용 범위
Slack 신규 사용자 등록은 `snowflake_SQL.get_allowed_users_fqn()`이 반환하는 위치에 INSERT한다. 기본값은 `TESTDB.PUBLIC.ALLOWED_USERS`이며 전환일에는 최상위 설정 `ALLOWED_USERS_FQN = "DATA_DB.ADMIN.ALLOWED_USERS"`가 필요하다. 이메일 형식 검증과 오류 복구 동작도 설명한다.

## 관련 테스트
- `tests/test_email_validation.py`: 허용 이메일 문자와 범위 밖 문장부호·잘못된 도메인 라벨 거부를 검증한다.
- `tests/test_login_recovery.py`: 사용자 조회 실패 복구 동작을 검증한다.
