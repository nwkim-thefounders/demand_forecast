# app_cache_load.py — 코드 리뷰

## 파일 목적
Snowflake 데이터를 캐시하여 로딩 속도를 향상시키는 유틸리티 모듈.
- `ALLOWED_USERS` 테이블: 로그인 검증용
- `PRODUCT_MASTER` 테이블: 품목명·라인·대분류·중분류·용량·유통코드·버전 정보

`use_cache` 파라미터로 캐시 사용 여부를 런타임에 제어할 수 있다 (streamlit_guide §4 준수).

---

## 함수 목록 및 위치

| 함수명 | 라인(약) | 설명 |
|---|---|---|
| `_load_product_master_cached()` | 8~11 | PRODUCT_MASTER 캐시 로드 (TTL 3600s) — 내부 전용 |
| `_load_users_data_cached()` | 14~17 | ALLOWED_USERS 캐시 로드 (TTL 300s) — 내부 전용 |
| `_fetch_product_master()` | 22~38 | PRODUCT_MASTER Snowflake 직접 조회 — 내부 전용 |
| `_fetch_users_data()` | 41~55 | ALLOWED_USERS Snowflake 직접 조회 — 내부 전용 |
| `load_product_master(use_cache)` | 60~74 | 공개 인터페이스: use_cache=True이면 캐시 버전 반환 |
| `load_users_data(use_cache)` | 77~91 | 공개 인터페이스: use_cache=True이면 캐시 버전 반환 |

---

## 캐시 제어 구조

```
load_product_master(use_cache=True)  ──→  _load_product_master_cached()  ──→  _fetch_product_master()
                   (use_cache=False) ──→  _fetch_product_master()  (직접 조회)

load_users_data(use_cache=True)      ──→  _load_users_data_cached()       ──→  _fetch_users_data()
               (use_cache=False)     ──→  _fetch_users_data()  (직접 조회)
```

UI 토글은 `app_99_regist_edit.py` 사이드바의 "캐시 설정" expander에서 제어한다.

---

## 전체 흐름 요약

```
load_product_master(use_cache) / load_users_data(use_cache)
├── use_cache=True  → @st.cache_data 캐시 함수 호출
└── use_cache=False → _fetch_* 직접 Snowflake 조회
    └── snowflake_SQL.connect_snowflake() → engine
        └── query_to_snowflake_with_text(query, conn) → DataFrame 반환
```

---

## 최종 수정 이력
- 2026-07-02: 캐시/비캐시 분리 리팩토링, use_cache 파라미터 추가 (streamlit_guide §4 준수)
- `load_product_master`에 라인·대분류·중분류·용량·유통코드·버전 컬럼 추가
