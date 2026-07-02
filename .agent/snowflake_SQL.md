# snowflake_SQL.py — 코드 리뷰

## 파일 목적
Snowflake 연결 및 데이터 입출력을 담당하는 데이터베이스 유틸리티 모듈.
RSA 비공개 키 인증 방식으로 Snowflake에 접속하며, DataFrame INSERT와 SELECT 쿼리를 추상화한다.

---

## 함수 목록 및 위치

| 함수명 | 라인 | 설명 |
|---|---|---|
| `connect_snowflake()` | 12~36 | PEM 개인키로 Snowflake SQLAlchemy 엔진 생성 |
| `input_data(conn, df, table_name)` | 39~58 | DataFrame을 Snowflake 테이블에 APPEND 방식으로 INSERT |
| `query_to_snowflake_with_text(query, conn)` | 61~64 | 텍스트 쿼리 실행 후 DataFrame 반환 |

---

## 발견된 버그 / 개선 필요 사항

### 🔴 CRITICAL (버그)

1. **`connect_snowflake` 호출 시마다 새 엔진 생성 (커넥션 풀 미재사용)**
   여러 함수에서 `snowflake_SQL.connect_snowflake()`를 반복 호출하면 매번 새 엔진이 생성된다. 캐싱(`@st.cache_resource`) 또는 싱글톤 패턴 적용 권장.

2. **라인 52~54: `except Exception as e`에서 로깅 없이 `print(e)` 사용** (지침서 §3 위반)
   `print`는 프로덕션 환경에서 로그가 소실된다. `logging.exception(e)` 사용 권장.

---

### 🟠 HIGH (지침 위반)

3. **모든 함수에 타입 힌트 누락** (지침서 §2 위반)
   ```python
   # 현재
   def connect_snowflake():
   def input_data(conn, df: pd.DataFrame, table_name: str):
   def query_to_snowflake_with_text(query, conn):
   # 권장
   def connect_snowflake() -> Engine:
   def input_data(conn: Connection, df: pd.DataFrame, table_name: str) -> None:
   def query_to_snowflake_with_text(query: str, conn: Connection) -> pd.DataFrame:
   ```

4. **Google Style Docstring 없음** (지침서 §2 위반) — 3개 함수 모두 미작성.

---

### 🟡 MEDIUM (코드 품질)

5. **라인 27: 계정 ID 하드코딩**
   ```python
   account='OLQVRGS-BM97392',
   user='NW.KIM',
   warehouse='COMPUTE_WH',
   ```
   지침서 §3 위반. `.env` 또는 `st.secrets`를 통해 접근해야 한다.

6. **`input_data`에서 테이블명 검증 없음**
   `table_name` 입력값 검증 없이 그대로 사용. 화이트리스트 검증 추가 권장.

7. **`query_to_snowflake_with_text`의 `conn.commit()` (라인 63)**
   SELECT 쿼리 후 commit은 불필요하다. INSERT/DELETE 쿼리에만 적용해야 한다.

---

### 🟢 LOW

8. **`import streamlit as st`가 있으나 `st.secrets` 외 사용 없음**
   DB 모듈이 Streamlit에 의존하는 구조는 재사용성을 떨어뜨린다. secrets를 인자로 주입받는 방식 권장.

---

## 전체 흐름 요약

```
connect_snowflake()
└── st.secrets["snowflake"]["key"] → PEM 파싱 → DER 변환 → SQLAlchemy Engine 반환

input_data(conn, df, table_name)
└── df.to_sql(append) → pd_writer(멀티인서트) → conn.commit()

query_to_snowflake_with_text(query, conn)
└── pd.read_sql(text(query), conn) → conn.commit() → DataFrame 반환
```
