# app_99_regist_edit.py

## 목적

`demand_forcast` 앱의 "View" 탭을 담당하는 모듈입니다.  
Snowflake `TESTDB.PUBLIC.MONTH_FORECAST_CONSOL` 테이블의 예측 수량 데이터를 조회하고, 필터/피벗/KPI/추이 그래프로 시각화합니다.

## 흐름

1. `show_edit_page()`에서 사이드바 필터 UI를 렌더링합니다.
2. `init_data()`로 필터 옵션(등록 월, 예측 월, 사업부, 채널, 등록자) 목록을 캐시에서 초기화합니다.
3. "검색" 버튼 클릭 시 `search_data()`가 WHERE 조건을 조립해 Snowflake에서 데이터를 조회합니다.
4. `_result_df_edit()`로 SIGNOFF 정책 및 중복 데이터를 정리합니다.
5. `_merge_product_master()`로 `PRODUCT_MASTER`를 left merge하여 품목 정보를 보강합니다.
6. `show_dashboard()`에서 피벗 테이블, KPI 카드, Plotly 추이 그래프를 렌더링합니다.

## 함수 위치

- `app_99_regist_edit.py:_get_option_df_cached()` / `_fetch_option_df()` / `get_option_df()` (line 12-51): 필터 옵션용 distinct 데이터 캐시 조회
- `app_99_regist_edit.py:init_data()` (line 54): 세션 상태에 필터 옵션 목록 초기화
- `app_99_regist_edit.py:search_data()` (line 66): 사이드바 필터 조건으로 `MONTH_FORECAST_CONSOL` 조회
- `app_99_regist_edit.py:_merge_product_master()` (line 109): `PRODUCT_MASTER`와 merge하여 품목 정보 추가
- `app_99_regist_edit.py:_result_df_edit()` (line 134): KEY별 최신 SIGNOFF 데이터 정리
- `app_99_regist_edit.py:_build_pivot_df()` (line 170): 선택 계층/월 기준 피벗 테이블 생성
- `app_99_regist_edit.py:_calc_kpi_delta()` (line 222): 최신 등록 월 vs 직전 등록 월 delta 계산
- `app_99_regist_edit.py:_render_sidebar()` (line 247): 사이드바 필터 UI 렌더링
- `app_99_regist_edit.py:show_dashboard()` (line 331): 검색 결과 대시보드(피벗, KPI, 그래프) 렌더링
- `app_99_regist_edit.py:show_edit_page()` (line 702): View 탭 메인 진입 함수

## 주의사항

- `search_data()`에서 조건 조립 시 문자열 컬럼은 `IN` 절에 직접 문자열 삽입을 사용합니다. 현재 입력값은 `st.multiselect`로 제한되지만, 일반 사용자 입력이 들어오는 경우 추가 검증/파라미터 바인딩이 필요합니다.
- `PRODUCT_MASTER` merge 실패 시 원본 데이터를 그대로 반환하며, 이 경우 품목명/라인/대분류 등 컬럼이 비어 있을 수 있습니다.
