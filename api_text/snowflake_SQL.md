# snowflake_SQL.py

## 목적

`demand_forcast` 앱에서 Snowflake 데이터베이스에 연결하고, 데이터를 조회/입력하는 공통 모듈입니다.  
Streamlit `st.secrets`에 저장된 PEM 개인키 기반으로 SQLAlchemy 엔진을 생성합니다.

## 주요 기능

- Snowflake SQLAlchemy 엔진 생성 (키 기반 인증)
- DataFrame → Snowflake 테이블 APPEND INSERT (`pd.to_sql` + `pd_writer`)
- 텍스트 SQL 쿼리 실행 후 DataFrame 반환

## 함수 위치

- `snowflake_SQL.py:connect_snowflake()` (line 15): `st.secrets["snowflake"]`에서 PEM 개인키와 접속 정보를 읽어 SQLAlchemy `Engine` 생성
- `snowflake_SQL.py:input_data()` (line 52): DataFrame을 지정 테이블에 append 방식으로 INSERT하고 commit
- `snowflake_SQL.py:query_to_snowflake_with_text()` (line 84): 텍스트 SQL을 실행하여 결과 DataFrame 반환

## 주의사항

- DML(INSERT/UPDATE/DELETE) 수행 후에는 반드시 `conn.commit()`을 호출해야 합니다. `engine.connect()`로 연 커넥션은 명시적 commit 없이 닫히면 자동 rollback됩니다.
- `query_to_snowflake_with_text`는 SELECT용 함수입니다. DML에는 `conn.execute(text(query))` 후 직접 `commit()`을 사용하세요.
