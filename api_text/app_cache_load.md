# app_cache_load.py

## 목적
제품 마스터와 허용 사용자 목록을 Snowflake에서 조회하고 선택적으로 Streamlit 캐시를 적용한다.

## 함수 위치 및 흐름
- `_fetch_product_master()`: `TESTDB.PUBLIC.PRODUCT_MASTER`에서 읽는다. 이 위치는 이번 변경 대상이 아니다.
- `_fetch_users_data()`: `snowflake_SQL.get_allowed_users_fqn()`으로 ALLOWED_USERS 위치를 선택해 조회한다.
- `_load_users_data_cached()` / `load_users_data()`: 사용자 목록을 캐시하거나 직접 불러온다.

## 설정
기본 ALLOWED_USERS 위치는 `TESTDB.PUBLIC.ALLOWED_USERS`다. 전환일에는 Streamlit Cloud Secrets의 최상위 `ALLOWED_USERS_FQN = "DATA_DB.ADMIN.ALLOWED_USERS"`를 설정한다.
