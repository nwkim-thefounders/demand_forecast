# app_02_upload.py — 파일 설명

## 파일 목적
`app_00_main.py`에서 분화된 업로드 탭 전용 모듈.
엑셀 파일 파싱, 유효성 검사, Snowflake 저장, 템플릿 생성 및 업로드 UI 렌더링을 담당한다.

## 함수 목록 및 위치

| 함수명 | 설명 |
|---|---|
| `melt_logic(df)` | wide → long 피벗 변환 |
| `read_origin_xl(uploaded_file)` | QTY 시트 원본 엑셀 파싱 |
| `read_upload_xl(uploaded_file)` | 업로드 양식 엑셀 파싱 + 품목명 조인 |
| `read_df_xlsx(uploaded_file)` | 시트 판별 후 파싱 함수 분기 |
| `is_sign_off(conn)` | Sign-off 토글 활성 시 기존 데이터 삭제 |
| `make_tamplate_xlsx()` | 업로드 양식 엑셀 템플릿 생성 |
| `save_btn()` | 저장 버튼 콜백 — Snowflake INSERT |
| `show_upload_page()` | 업로드 탭 전체 UI 렌더링 (진입점) |
