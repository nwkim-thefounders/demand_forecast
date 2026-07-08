# app_cache_load.py

## 목적
Snowflake 테이블(`PRODUCT_MASTER`, `ALLOWED_USERS`)을 `st.cache_data` 기반으로 캐시하여 로드하는 공용 모듈.

## 흐름
1. 내부 캐시 함수(`_load_product_master_cached`, `_load_users_data_cached`)가 `st.cache_data` 데코레이터로 캐시됨 (TTL: 3600s / 300s).
2. 실제 조회는 `_fetch_product_master`, `_fetch_users_data`가 `snowflake_SQL` 모듈을 통해 수행.
3. 외부에는 캐시 사용 여부를 선택할 수 있는 래퍼 함수만 공개.

## 함수 위치
- `_load_product_master_cached` (line 8): PRODUCT_MASTER 캐시 로드 (TTL 3600초)
- `_load_users_data_cached` (line 14): ALLOWED_USERS 캐시 로드 (TTL 300초)
- `_fetch_product_master` (line 22): PRODUCT_MASTER 직접 조회
- `_fetch_users_data` (line 41): ALLOWED_USERS 직접 조회
- `load_product_master` (line 60): 공개 인터페이스 (use_cache 인자)
- `clear_users_cache` (line 77): ALLOWED_USERS 캐시 초기화 (신규 유저 등록 직후 호출)
- `load_users_data` (line 86): 공개 인터페이스 (use_cache 인자)

## 주의사항
- `load_users_data`는 일반 함수(래퍼)이므로 `.clear()` 속성이 없음.
  캐시 초기화는 반드시 `clear_users_cache()`를 사용할 것.
