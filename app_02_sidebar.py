import streamlit as st
import streamlit_antd_components as sac

def show_sidebar():
    with st.sidebar:
        st.title("Menu")

        selected = sac.menu(
            [
                # sac.MenuItem("Home", icon="house"),
                # sac.MenuItem("upload", icon="upload"),
                # sac.MenuItem("view", icon="eye"),
                sac.MenuItem("Demand forecast", icon="chart-line", children=[
                    sac.MenuItem("forecast view", icon="eye"),
                    sac.MenuItem("upload", icon="upload"),
                    sac.MenuItem("Sign Off", icon="check2-circle")
                ]),
                # sac.MenuItem("Stock", icon="chart-line", children=[
                #     sac.MenuItem("stock view", icon="eye"),
                #     sac.MenuItem("analysis", icon="bar-chart"),
                # ]),
            ],
            key="main_menu",
            format_func="title",
            open_all=True
        )