import streamlit as st
from streamlit_oauth import OAuth2Component
import requests
import snowflake_SQL
import app_cache_load
import re
import pandas as pd
import urllib.parse  # URL 쿼리 스트링 빌드용 추가

# --- 1. 설정값 및 OAuth 초기화 ---
CLIENT_ID = st.secrets["slack"]["client_id"]
CLIENT_SECRET = st.secrets["slack"]["client_secret"]
REDIRECT_URI = st.secrets["slack"]["redirect_uri"]
AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
TOKEN_URL = "https://slack.com/api/oauth.v2.access"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, "")

def check_email():
    input_em = st.session_state.get("input_em", "")
    email_pattern = r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    if input_em != "":
        if not re.match(email_pattern, input_em):
            st.session_state["is_valueable"] = False
            st.session_state["login_warning_msg"] = "올바른 이메일 형식이 아닙니다."
        else:
            st.session_state["is_valueable"] = True
            st.session_state["login_warning_msg"] = ""

def login_btn():
    check_email()
    if not st.session_state.get("is_valueable", False):
        return

    input_em = st.session_state.get("input_em", "")
    input_pw = st.session_state.get("input_pw", "")

    if input_pw == "" or input_pw == None:
        st.session_state["is_valueable"] = False
        st.session_state["login_warning_msg"] = "비밀번호를 입력 해주세요"
        return

    user_data = st.session_state.get("user_data")
    checked_df = user_data.loc[(user_data["EMAIL"] == input_em) & (user_data["USER_PW"] == input_pw)]

    if checked_df.empty:
        st.session_state["is_valueable"] = False
        st.session_state["login_warning_msg"] = "등록되어 있지 않은 ID 입니다. 관리자에게 문의 해주세요"
        return

    st.session_state["authentication_status"] = True
    st.session_state['user_email'] = input_em
    st.session_state['user_name_kr'] = user_data.loc[user_data["EMAIL"] == input_em, "USER_NAME"].iloc[0]
    st.session_state['user_role'] = user_data.loc[user_data["EMAIL"] == input_em, "ROLE"].iloc[0]

def regist_user(email: str, name: str):
    engine = snowflake_SQL.connect_snowflake()
    created_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    with engine.connect() as conn:
        query = f"INSERT INTO ALLOWED_USERS (EMAIL, USER_NAME, ROLE, CREATED_AT) VALUES ('{email}', '{name}', 'USER', '{created_at}');"
        snowflake_SQL.query_to_snowflake_with_text(query=query, conn=conn)

def show_login():
    if "user_data" not in st.session_state:
        st.session_state["user_data"] = app_cache_load.load_users_data()

    # 🌟 [핵심 변경] 전체 창 리다이렉트 후 되돌아왔을 때 URL 파라미터(code) 수동 감지 및 처리
    if "code" in st.query_params:
        auth_code = st.query_params["code"]
        with st.spinner("Slack 사용자 인증 정보를 확인 중입니다..."):
            try:
                # 슬랙 토큰 교환 요청 (POST)
                payload = {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "code": auth_code,
                    "redirect_uri": REDIRECT_URI
                }
                res = requests.post(TOKEN_URL, data=payload)
                result_json = res.json()
                
                if result_json.get("ok"):
                    # 기존 팝업 성공 시 구조와 데이터 스펙 싱크 레이어 매핑
                    st.session_state["auth"] = {"token": result_json}
                    # URL에 노출된 code 정보 청소 및 루프 방지
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"Slack 인증 토큰 발급에 실패했습니다: {result_json.get('error')}")
                    st.query_params.clear()
            except Exception as e:
                st.error(f"인증 통신 중 오류 발생: {e}")
                st.query_params.clear()

    # auth가 세션에 없으면 슬랙 로그인 화면
    if "auth" not in st.session_state:
        if "is_valueable" not in st.session_state:
            st.session_state["is_valueable"] = True
            st.session_state["login_warning_msg"] = ""

        t1, t2, t3 = st.columns([1,2,1])
        with t2:
            st.title("The Founders Demand Forecast")

            # 외부 인원 로그인창
            with st.container(border=False, horizontal_alignment="center"):
                with st.container(border=True, horizontal_alignment="center"):
                    st.text_input(label="이메일",placeholder="anua@thefounders.kr", key="input_em", on_change=check_email)
                    st.text_input(label="비밀번호", type="password", key="input_pw", on_change=login_btn)
                    if not st.session_state["is_valueable"]:
                        st.error(st.session_state["login_warning_msg"])
                    else:
                        st.write("")
                        st.write("")

                    with st.container(border=False, horizontal=True):
                        with st.container(border=False, horizontal_alignment="left", gap="xxsmall"):
                            st.write("외부 사용자를 위한 로그인 창 입니다.")
                            st.caption("아이디 등록은 관리자에게 문의 해주세요")
                        with st.container(border=False, horizontal=True, horizontal_alignment="right"):
                            st.button(label="로그인", on_click=login_btn)
                            st.write("")

                st.write("The Founders 직원은 슬랙으로 로그인해주세요")
                
                # 🌟 [핵심 변경] oauth2.authorize_button 대신 현재창 전환용 HTML 마크다운 버튼 배치
                scopes = "users.profile:read users:read users:read.email"
                params = {
                    "client_id": CLIENT_ID,
                    "redirect_uri": REDIRECT_URI,
                    "scope": scopes,
                    "response_type": "code"
                }
                encoded_params = urllib.parse.urlencode(params)
                slack_direct_url = f"{AUTHORIZE_URL}?{encoded_params}"

                # 슬랙 기본 디자인톤의 블록 버튼 구현 및 target="_self" 부여
                st.markdown(
                                    f'''
                                    <a href="{slack_direct_url}" target="_parent" style="text-decoration: none;">
                                        <div style="background-color: #4A154B; color: white; padding: 12px 24px; 
                                                    text-align: center; border-radius: 4px; font-weight: bold; 
                                                    cursor: pointer; font-size: 16px; margin-top: 10px;">
                                            Slack으로 로그인
                                        </div>
                                    </a>
                                    ''',
                                    unsafe_allow_html=True
                                )
    else:
        token_data = st.session_state["auth"]["token"]
        bot_token = token_data["access_token"]
        authed_user_id = token_data.get("authed_user", {}).get("id")

        # 슬랙 API로 프로필 조회
        response = requests.get(
            f"https://slack.com/api/users.profile.get?user={authed_user_id}",
            headers={"Authorization": f"Bearer {bot_token}"}
        )
        slack_user = response.json()

        if slack_user.get("ok"):
            st.session_state["profile"] = slack_user["profile"]
            email = slack_user["profile"]["email"]
            name = slack_user["profile"]["real_name"]

            # DB에 유저가 있는지 확인하고 없으면 신규 등록
            user_data = st.session_state["user_data"]
            user_df = user_data.loc[(user_data["EMAIL"] == email)]

            if user_df.empty:
                default_allowed_domains = st.secrets["founders_email"]["domains"]
                if email.split("@")[-1] not in default_allowed_domains:
                    st.warning("자동 가입이 허용되지 않은 이메일 도메인 입니다. 관리자에게 문의 해주세요")
                    st.stop()

                with st.spinner("신규 유저 등록 중..."):
                    regist_user(email=email, name=name)
                    app_cache_load.load_users_data.clear()
                    st.session_state["user_data"] = app_cache_load.load_users_data()
                    user_data = st.session_state["user_data"]

            # 스트림릿 자체 세션에 로그인 상태 기록
            st.session_state['authentication_status'] = True
            st.session_state['user_email'] = email
            st.session_state['user_name_kr'] = name
            st.session_state['user_role'] = user_data.loc[user_data["EMAIL"] == email, "ROLE"].iloc[0]

            st.success(f"{name}님, 환영합니다!")
            st.rerun()

        else:
            st.error("슬랙 사용자 정보를 가져오는데 실패했습니다.")
            if st.button("처음으로 돌아가기"):
                del st.session_state["auth"]
                st.rerun()