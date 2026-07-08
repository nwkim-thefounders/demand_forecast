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
- `regist_user` (line 62): 신규 Slack 사용자를 ALLOWED_USERS 테이블에 INSERT
- `show_login` (line 75): 로그인 화면 렌더링 및 인증 처리 메인 함수

## 주의사항
- 캐시 초기화 시 `app_cache_load.load_users_data.clear()` 형태로 호출하면
  `AttributeError: 'function' object has no attribute 'clear'`가 발생함.
  반드시 `app_cache_load.clear_users_cache()`를 사용할 것.
