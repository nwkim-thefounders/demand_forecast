import streamlit as st
import app_01_login
import app_02_upload
import app_99_regist_edit
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

    nav_items = [
        sac.TabsItem(label="Up Load", icon="cloud-upload"),
        sac.TabsItem(label="View", icon="eye"),
    ]

    selected_tab = sac.tabs(
        items=nav_items,
        format_func="title",
        align="start",
        position="top",
        size="md",
        variant="outline",
        use_container_width=False,
    )

    if selected_tab == "View":
        app_99_regist_edit.show_edit_page()
    else:
        app_02_upload.show_upload_page()


show_main()