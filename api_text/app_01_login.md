# app_01_login.py

## 목적
Slack OAuth2 및 이메일/비밀번호 이중 로그인 화면을 렌더링하고 사용자 인증/등록을 처리.

## 흐름
1. `show_login`에서 `app_cache_load.load_users_data()`로 허용 유저 목록을 세션에 로드.
2. Slack redirect `code` 감지 → 토큰 교환 → 프로필 조회.
3. DB에 유저가 없으면 허용 도메인 검증 후 `regist_user`로 신규 등록.
4. 등록 직후 `app_cache_load.clear_users_cache()`로 캐시를 비우고 유저 목록 재조회.
5. 세션(`authentication_status`, `user_email`, `user_name_kr`, `user_role`)에 로그인 상태 기록.

## 함수 위치
- `regist_user` (line 63): 신규 Slack 사용자를 ALLOWED_USERS 테이블에 INSERT (`engine.begin()` + 바인드 파라미터로 자동 commit)
- `show_login` (line 80): 로그인 화면 렌더링 및 인증 처리 메인 함수

## 주의사항
- 캐시 초기화 시 `app_cache_load.load_users_data.clear()` 형태로 호출하면
  `AttributeError: 'function' object has no attribute 'clear'`가 발생함.
  반드시 `app_cache_load.clear_users_cache()`를 사용할 것.
- SQLAlchemy 2.0에서 `engine.connect()`로 연 커넥션은 `commit()` 없이 닫히면 자동 rollback됨.
  INSERT/UPDATE 등 DML은 반드시 `engine.begin()` 또는 명시적 `conn.commit()`을 사용할 것.
  (과거 `regist_user`가 commit 없이 INSERT하여 신규 유저가 저장되지 않고
  line 208 `IndexError: single positional indexer is out-of-bounds`가 발생했던 원인)
