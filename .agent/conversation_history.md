# Conversation History — demand_forcast 프로젝트

---

## [2026-06-30] 세션 1 — 전체 코드 리뷰

### 요청
- `.windsurf.md` 지침서 로드 후 현재 프로젝트 전체 파일 코드 리뷰 작성

### 대상 파일
| 파일 | 크기 | 상태 |
|---|---|---|
| `app_00_main.py` | 500줄 | ✅ 리뷰 완료 |
| `app_01_login.py` | 203줄 | ✅ 리뷰 완료 |
| `app_99_regist_edit.py` | 60줄 | ✅ 리뷰 완료 |
| `app_cache_load.py` | 14줄 | ✅ 리뷰 완료 |
| `snowflake_SQL.py` | 65줄 | ✅ 리뷰 완료 |

### 주요 발견 사항 요약

#### 🔴 CRITICAL 버그 (즉시 수정 필요)
1. `app_00_main.py:424` — `st.session_state.get("user_role" "")` **SyntaxError** (쉼표 누락)
2. `app_00_main.py:218~223` — `read_upload_xl`에서 `header_row` **UnboundLocalError** 가능성
3. `app_00_main.py:241~244` — **bare `except:`** 사용 (지침 §3 위반)
4. `app_99_regist_edit.py:33,36` — `select_slider` 옵션 1개 이하 시 **IndexError**
5. `app_99_regist_edit.py:50~54` — f-string 내 중첩 따옴표 **SyntaxError** (Python 3.11 이하)
6. `app_01_login.py:45` — 평문 비밀번호 DB 비교 (**보안 취약점**)
7. `snowflake_SQL.py:27` — 계정/사용자명 **하드코딩** (지침 §3 위반)

#### 🟠 공통 지침 위반
- 전체 파일에 걸쳐 **타입 힌트 누락** (지침 §2)
- 전체 파일에 걸쳐 **Google Style Docstring 미작성** (지침 §2)
- `logging` 모듈 미사용, `print`/`st.error`로 대체 중 (지침 §3)

#### 🟡 기능 미완성
- `app_99_regist_edit.py` — 검색 버튼 기능 미구현, 결과 표시 없음
- `app_00_main.py` — `is_duplicates()` 함수 정의되었으나 호출되지 않음

### 생성된 리뷰 파일
- `.agent/app_00_main.md`
- `.agent/app_01_login.md`
- `.agent/app_99_regist_edit.md`
- `.agent/app_cache_load.md`
- `.agent/snowflake_SQL.md`
- `.agent/conversation_history.md`

### 다음 작업 제안
1. `app_00_main.py:424` SyntaxError 즉시 수정
2. `app_99_regist_edit.py` f-string 문법 수정
3. 타입 힌트 + Docstring 일괄 추가
4. `snowflake_SQL.py` 하드코딩 값 → `st.secrets`로 이전
5. `app_99_regist_edit.py` 검색 기능 구현

---

## [2026-06-30] 세션 2 — 전체 버그 수정 완료

### 수정 완료 목록

| # | 파일 | 내용 | 상태 |
|---|---|---|---|
| 1 | `app_00_main.py:424` | `get("user_role" "")` → `get("user_role", "")` 쉼표 추가 | ✅ |
| 2 | `app_99_regist_edit.py` | f-string 내 중첩 따옴표 → 변수 추출 후 삽입 | ✅ |
| 3 | `app_99_regist_edit.py` | `select_slider` 옵션 0/1개 시 IndexError 방어 코드 | ✅ |
| 4 | `app_99_regist_edit.py` | 디버그 `st.write` 제거, 검색 버튼 `on_click=search_data` 연결 + 결과 표시 구현 | ✅ |
| 5 | `app_00_main.py` | `bare except` → `except ValueError`, `header_row` 미발견 에러 처리 | ✅ |
| 5 | `app_00_main.py` | `== None` → `is None`, `type(col) == str` → `isinstance`, `width="stretch"` → `use_container_width=True` | ✅ |
| 6 | `snowflake_SQL.py` | account/user/warehouse/database/schema 하드코딩 → `st.secrets["snowflake"]` 이전 | ✅ |
| 7 | 전체 5개 파일 | 타입 힌트 + Google Style Docstring 추가, `logging` 모듈 적용, `print` → `logger` 교체 | ✅ |
| 8 | `app_cache_load.py` | `@st.cache_data(ttl=300)` 추가, `pd` 임포트 추가 | ✅ |
| 9 | `app_99_regist_edit.py` | `@st.cache_data(ttl=600)` 추가, 쿼리 완전경로 수정 | ✅ |

---

## [2026-06-30] 세션 3 — Edit 탭 고도화 및 버그 수정

### 수정 완료 목록

| # | 내용 | 상태 |
|---|---|---|
| 1 | `show_dashboard()` 피벗 합계 행 None 버그 수정 (MultiIndex loc → reset_index 후 concat) | ✅ |
| 2 | `_result_df_edit()` 구현: FCST_MTH+DEPT+CHANNEL+REGISTANT 키별 최신 SIGNOFF_DT 유지, SIGNOFF 상태 우선 | ✅ |
| 3 | `SIGNOFF_DT` 파싱 `format="mixed"` 적용 — 초 없는 형식(`15:28`) NaT 처리 해결 | ✅ |
| 4 | `NaT` 행 필터 통과 보장 (`isna() OR == max_dt` 조건) | ✅ |
| 5 | 원본 데이터 보기에 `SIGN_STATUS`, `SIGNOFF_DT` 컬럼 추가 | ✅ |
| 6 | 원본 데이터 보기 건수를 `session_state["edit_result_df"]` 기준으로 표시 | ✅ |
| 7 | 피벗 테이블에 평균 행 추가 (합계 행 위에 삽입) | ✅ |

---

## [2026-07-02] 세션 4 — 계층별 수량 변화 delta 0 버그 수정

### 버그 내용
- `show_dashboard()` 내 "계층별 수량 변화" expander에서 라디오 버튼을 **등록 월 (FCST_MTH)** 로 선택 시
- 등록 월 조건: `202605` → `202606` 범위 검색
- **`202605` 카드의 delta 값이 0으로 표기**되는 버그

### 원인
`app_99_regist_edit.py:265~268` (수정 전):
```python
val_df = df[df[delta_level].astype(str) == val]          # FCST_MTH == "202605" 로 필터
cur = int(val_df[val_df["FCST_MTH"] == latest_mth]...)  # FCST_MTH == "202606" → empty → 0
prv = int(val_df[val_df["FCST_MTH"] == prev_mth]...)    # FCST_MTH == "202605" → 실제 값
delta = cur - prv  # 0 - prv = 음수 (혹은 prv 카드는 0으로 표기)
```
`delta_level == "FCST_MTH"` 일 때 `val_df`가 이미 특정 등록월로 필터된 상태에서
다시 다른 등록월로 필터하므로 반드시 한쪽은 0이 됨.

### 수정 내용
`delta_level == "FCST_MTH"` 분기를 별도 처리:
- 전월(`202605`) 카드: value=전월 전체 수량, delta=None (기준값이므로 delta 표시 안 함)
- 최신월(`202606`) 카드: value=최신월 전체 수량, delta=최신-전월

| 파일 | 수정 위치 | 상태 |
|---|---|---|
| `app_99_regist_edit.py` | `show_dashboard()` 264~292줄 | ✅ |

---

### ⚠️ 수동 조치 필요 사항
- `.streamlit/secrets.toml`에 아래 키 추가 필요 (파일 직접 접근 불가):
  ```toml
  [snowflake]
  key = "-----BEGIN RSA PRIVATE KEY-----..."
  account = "OLQVRGS-BM97392"
  user = "NW.KIM"
  warehouse = "COMPUTE_WH"
  database = "TESTDB"
  schema = "PUBLIC"
  ```

---

## [2026-07-02] 세션 — 전체 리팩토링 (streamlit_guide.md + .windsurf 지침 반영)

### 요청
- `streamlit_guide.md` 신규 생성 및 `.windsurf`에 등록 후 전체 리팩토링 요청

### 변경 파일 및 주요 내용

#### `app_cache_load.py`
- 캐시/비캐시 분리: `_fetch_*` (직접 조회) + `_*_cached` (캐시) + 공개 `load_*(use_cache)` 구조
- `load_product_master(use_cache=True)`, `load_users_data(use_cache=True)` 파라미터 추가

#### `app_99_regist_edit.py`
- `get_option_df` → `_fetch_option_df` + `_get_option_df_cached` + `get_option_df(use_cache)` 분리
- `_result_df_edit()` — Google Style Docstring 추가
- `_build_pivot_df(df, selected_levels)` — 피벗 로직 `show_dashboard`에서 분리 (§3 준수)
- `_calc_kpi_delta(df, fcst_mth_list)` — KPI delta 계산 로직 분리 (§3 준수)
- `_merge_product_master(df, use_cache)` — `use_cache` 파라미터 추가
- `_render_sidebar()` — "캐시 설정" expander + `use_option_cache` / `use_product_cache` 토글 추가 (§4 준수)
- `init_data()`, `search_data()` — 세션 캐시 토글 값 참조

#### `.agent/*.md`
- `app_cache_load.md`, `app_99_regist_edit.md` 함수 목록 및 현황 최신화

#### `tests/test_logic.py` (신규)
- `TestResultDfEdit`: 4개 테스트
- `TestBuildPivotDf`: 5개 테스트
- `TestCalcKpiDelta`: 5개 테스트
- **14/14 PASSED** (pytest 실행 확인)
