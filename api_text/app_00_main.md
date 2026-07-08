# app_00_main.py

## 목적

`demand_forcast` Streamlit 앱의 진입점(entry point)입니다.  
로그인 상태에 따라 로그인 화면을 보여주거나, 상단 탭 네비게이션(Up Load / View)을 통해 주요 기능 페이지로 라우팅합니다.

## 흐름

1. `show_main()` 실행 시 `st.set_page_config`로 페이지 타이틀과 레이아웃을 설정합니다.
2. `authentication_status`가 `False`면 `app_01_login.show_login()`을 호출하여 로그인 화면을 표시합니다.
3. 로그인 상태이면 `streamlit_antd_components` 탭으로 "Up Load"와 "View" 메뉴를 렌더링합니다.
4. 선택된 탭에 따라:
   - "Up Load" → `app_02_upload.show_upload_page()`
   - "View" → `app_99_regist_edit.show_edit_page()`

## 함수 위치

- `app_00_main.py:show_main()` (line 8): Streamlit 메인 페이지 렌더링 및 탭 라우팅
