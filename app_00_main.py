import streamlit as st
import app_01_login
import app_02_sidebar
import app_03_DF_upload
import app_03_DF_view
import app_03_DF_sign_off
import app_04_STOCK_view
import app_99_home
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
    if selected_menu == "Demand forecast": # 최초 접속시 여기로 리다이렉트됨
        app_99_home.show_home()
    elif selected_menu == "upload":
        app_03_DF_upload.show_upload_page()
    elif selected_menu == "forecast view":
        app_03_DF_view.show_forecast_view_page()
    elif selected_menu == "stock view":
        app_04_STOCK_view.show_stock_view()
    elif selected_menu == "Sign Off":
        app_03_DF_sign_off.show_sign_off()
    else:
        st.title(f"{selected_menu}")
        st.subheader(f"{selected_menu} 페이지는 현재 준비 중입니다.")


show_main()