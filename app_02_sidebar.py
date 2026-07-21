import streamlit as st
import streamlit_antd_components as sac

def show_sidebar():
    with st.sidebar:
        st.title("Menu")

        selected = sac.menu(
            [
                sac.MenuItem("Home", icon="house"),
                sac.MenuItem("Demand forecast", icon="chart-line", children=[
                    sac.MenuItem("upload", icon="upload"),
                    sac.MenuItem("view", icon="eye"),
                ]),
            ],
            key="main_menu",
            format_func="title",
            open_all=True
        )