# app_cache_load.py — 코드 리뷰

## 파일 목적
Snowflake `ALLOWED_USERS` 테이블을 캐시하여 로그인 검증 속도를 향상시키는 유틸리티 모듈.
`@st.cache_data` 데코레이터로 최초 1회만 DB 조회 후 메모리에 보관한다.

---

## 함수 목록 및 위치

| 함수명 | 라인 | 설명 |
|---|---|---|
| `load_users_data()` | 6~13 | ALLOWED_USERS 테이블 전체 로드 및 컬럼 대문자 변환 |

---

## 발견된 버그 / 개선 필요 사항

### 🟠 HIGH (지침 위반)

1. **타입 힌트 누락** (지침서 §2 위반)
   ```python
   def load_users_data():
   # 수정
   def load_users_data() -> pd.DataFrame:
   ```

2. **Google Style Docstring 불완전** (지침서 §2 위반)
   Docstring은 존재하나 `Returns:` 및 `Raises:` 섹션이 없다.

---

### 🟡 MEDIUM (코드 품질)

3. **`@st.cache_data`에 `ttl` 미지정**
   유저 데이터가 DB에서 변경되어도 앱 재시작 전까지 반영되지 않는다. `ttl=300` 등 설정 권장.

4. **`SELECT *` 쿼리 사용**
   필요한 컬럼(EMAIL, USER_NAME, ROLE, USER_PW)만 명시적으로 조회하는 것이 안전하다.

---

### 🟢 LOW

5. **파일 전체가 14줄로 매우 짧음** — `connect_snowflake` 호출을 함수 내부에서 완전히 캡슐화하는 현재 구조는 좋음.

---

## 전체 흐름 요약

```
load_users_data()
└── snowflake_SQL.connect_snowflake() → engine
    └── query_to_snowflake_with_text("SELECT * FROM ALLOWED_USERS")
        └── df.columns 대문자 변환 → 반환
```
