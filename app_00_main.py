import streamlit as st
import app_01_login
import app_02_sidebar
import app_03_DF_upload
import app_03_DF_view
import streamlit_antd_components as sac


def show_main() -> None:
    """Streamlit 메인 페이지를 렌더링한다.

    로그인 상태에 따라 로그인 화면 또는 상단 네비게이션 바(Up Load / View)를 표시한다.
    기본 페이지는 Up Load 탭이다.
    """
    st.set_page_config(
        page_title="The Founders IM",
        layout="wide"
    )

    if not st.session_state.get("authentication_status"):
        app_01_login.show_login()
        return
    
    app_02_sidebar.show_sidebar()
    selected_menu = st.session_state["main_menu"]
    
    if selected_menu == "upload":
        app_03_DF_upload.show_upload_page()
    elif selected_menu == "view":
        app_03_DF_view.show_view_page()
    else:
        st.title(f"{selected_menu}")
        st.subheader(f"{selected_menu} 페이지는 현재 준비 중입니다.")


show_main()