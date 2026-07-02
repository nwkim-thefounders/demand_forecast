# app_99_regist_edit.py — 코드 리뷰

## 파일 목적
ADMIN 전용 Edit 탭 페이지. `MONTH_FORECAST_CONSOL` 테이블의 데이터를 조건별로 검색하는 사이드바 필터 UI를 제공한다.
현재는 검색 버튼이 구현되어 있으나 **실제 쿼리 실행 및 결과 표시 기능이 미완성** 상태다.

---

## 함수 목록 및 위치

| 함수명 | 라인(약) | 설명 |
|---|---|---|
| `get_option_df()` | 8~15 | 필터 옵션용 distinct 데이터 Snowflake 조회 (캐시 적용) |
| `init_data()` | 17~40 | 세션 상태에 필터 옵션 목록 초기화 |
| `search_data()` | 41~78 | 사이드바 필터 조건으로 Snowflake 데이터 조회 후 세션 저장 |
| `_result_df_edit()` | 80~101 | 조회 결과 가공 (KEY별 최신 SIGNOFF_DT 유지, SIGNOFF 우선) |
| `show_dashboard()` | 150~295 | 검색 결과를 다중 선택 계층 기반 피벗 테이블로 표시 |
| `_render_sidebar()` | 105~148 | Edit 탭 사이드바 필터 UI 렌더링 |
| `show_edit_page()` | 297~ | Edit 탭 전체 렌더링 진입점 |

---

## 현재 상태 (2026-06-30 세션3 기준)

✅ 수정 완료:
- `search_data()` 구현 완료 (Snowflake 조회, WHERE 조건 동적 구성)
- `_result_df_edit()` 구현: KEY(FCST_MTH+DEPT+CHANNEL+REGISTANT)별 최신 SIGNOFF_DT 유지, SIGNOFF 상태 우선
- `show_dashboard()` 구현: multiselect 계층 피벗 테이블, KPI 카드, 평균/합계 행, highlight_max
- `SIGNOFF_DT` 파싱: `format="mixed"` 적용으로 초 없는 형식(`15:28`) NaT 파싱 문제 해결
- 원본 데이터 보기: `SIGN_STATUS`, `SIGNOFF_DT` 컬럼 추가
- 피벗 테이블 합계 None 버그 수정 (reset_index 후 concat으로 변경)

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
