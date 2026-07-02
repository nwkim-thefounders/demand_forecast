# app_99_regist_edit.py — 코드 리뷰

## 파일 목적
ADMIN 전용 Edit 탭 페이지. `MONTH_FORECAST_CONSOL` 테이블의 데이터를 조건별로 검색하고
계층별 피벗 테이블·KPI 카드·Delta Metric·Graph로 시각화한다.

---

## 함수 목록 및 위치

| 함수명 | 라인(약) | 설명 |
|---|---|---|
| `_get_option_df_cached()` | 12~15 | 필터 옵션 캐시 로드 (TTL 600s) — 내부 전용 |
| `_fetch_option_df()` | 18~34 | 필터 옵션 Snowflake 직접 조회 — 내부 전용 |
| `get_option_df(use_cache)` | 37~51 | 공개: 캐시/비캐시 분기 |
| `init_data()` | 54~63 | 세션 상태에 필터 옵션 목록 초기화 |
| `search_data()` | 66~105 | 사이드바 필터 조건으로 Snowflake 조회 후 세션 저장 |
| `_merge_product_master(df, use_cache)` | 107~124 | DESC 제거 후 PRODUCT_MASTER merge |
| `_result_df_edit(df)` | 127~155 | SIGNOFF_DT 최신·SIGNOFF 우선 정책 적용 |
| `_build_pivot_df(df, selected_levels)` | 158~207 | 피벗 테이블 생성 (합계/평균 행·열 포함) |
| `_calc_kpi_delta(df, fcst_mth_list)` | 210~231 | 최신/전월 KPI delta 계산 |
| `_render_sidebar()` | 234~319 | 사이드바 필터 + 캐시 토글 UI 렌더링 |
| `show_dashboard(df)` | 321~ | 피벗·KPI·Delta·Graph UI 렌더링 |
| `show_edit_page()` | ~700 | Edit 탭 전체 렌더링 진입점 |

---

## 현재 상태 (2026-07-02 리팩토링 기준)

✅ 완료:
- `search_data()`: Snowflake 조회, WHERE 조건 동적 구성, PRODUCT_MASTER merge
- `_result_df_edit()`: Google Style Docstring 추가, SIGNOFF 우선 정책
- `_build_pivot_df()`: 피벗 로직 show_dashboard에서 분리 (streamlit_guide §3 준수)
- `_calc_kpi_delta()`: KPI delta 계산 로직 분리 (streamlit_guide §3 준수)
- `get_option_df(use_cache)`: 캐시/비캐시 분기 (streamlit_guide §4 준수)
- `_render_sidebar()`: "캐시 설정" expander에 use_option_cache / use_product_cache 토글 추가
- `_merge_product_master(df, use_cache)`: use_cache 파라미터 추가
- Delta + Graph: 단일 expander + st.tabs(["Delta","Graph"]) 구조로 통합
- PRODUCT_MASTER merge: 품목명·라인·대분류·중분류·용량·유통코드·버전 전체 포함

---

### 🟡 MEDIUM (코드 품질)

8. **`get_option_df`의 `@st.cache_data`가 DB 스키마 변경 시 stale 캐시 문제를 일으킬 수 있음**
   `ttl` 파라미터 설정 권장 (예: `ttl=600`).

9. **`get_option_df` 내 `query`에서 테이블명에 스키마 경로 미지정**
   ```python
   "SELECT DISTINCT ... FROM MONTH_FORECAST_CONSOL;"
   ```
   `TESTDB.PUBLIC.MONTH_FORECAST_CONSOL`처럼 완전한 경로 명시 권장 (다른 파일들과 일관성 유지).

---

### 🟢 LOW

10. **라인 47~48: `st.write("")` 이중 사용** — `st.divider()` 또는 CSS margin으로 대체 가능.

---

## 전체 흐름 요약

```
show_edit_page()
├── session["option_df"] 없으면 → init_data() → get_option_df()
├── 사이드바
│   ├── FCST_MTH 범위 슬라이더
│   ├── MONTH 범위 슬라이더
│   ├── DEPT 멀티셀렉트
│   ├── CHANNEL 멀티셀렉트
│   ├── REGISTANT 멀티셀렉트
│   └── 검색 버튼 (⚠️ 미구현)
└── 메인 영역
    └── target_month_list 디버그 출력 (⚠️ 제거 필요)
```
