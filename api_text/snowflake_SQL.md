# snowflake_SQL.py

## 목적
Snowflake 연결 및 SQL 실행 도우미를 제공한다.

## 함수 위치 및 흐름
- `connect_snowflake()`: 기존 Streamlit secrets의 database/schema로 엔진을 만든다. 변경하지 않았다.
- `get_allowed_users_fqn()`: 환경 변수 `ALLOWED_USERS_FQN`, Streamlit 최상위 secrets 키, 기본값 순으로 ALLOWED_USERS 위치를 고른다. 허용값은 `TESTDB.PUBLIC.ALLOWED_USERS`와 `DATA_DB.ADMIN.ALLOWED_USERS`다.

## 주의
이 설정은 ALLOWED_USERS만 바꾼다. PRODUCT_MASTER와 MONTH_FORECAST_CONSOL 위치에는 영향을 주지 않는다.
