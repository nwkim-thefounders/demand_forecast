# app_01_login.py — 코드 리뷰

## 파일 목적
Slack OAuth2 + 이메일/패스워드 이중 로그인 처리 모듈.
Slack 인증 코드를 교환하여 유저 정보를 조회하고 Streamlit 세션에 저장한다.
외부 사용자는 이메일/패스워드로 로그인한다.

---

## 함수 목록 및 위치

| 함수명 | 라인 | 설명 |
|---|---|---|
| `check_email()` | 19~29 | 이메일 형식 유효성 검사 |
| `login_btn()` | 31~55 | 이메일/비밀번호 로그인 처리 콜백 |
| `regist_user(email, name)` | 57~62 | 신규 Slack 사용자 DB 등록 |
| `show_login()` | 64~202 | 전체 로그인 페이지 렌더링 (진입점) |

---

## 발견된 버그 / 개선 필요 사항

### 🔴 CRITICAL (버그)

1. **라인 45: 평문 비밀번호 비교**
   ```python
   checked_df = user_data.loc[(user_data["EMAIL"] == input_em) & (user_data["USER_PW"] == input_pw)]
   ```
   DB에 비밀번호가 평문으로 저장되어 있고 그대로 비교한다. 해싱(bcrypt 등) 적용이 반드시 필요하다.

2. **라인 61: SQL 인젝션 취약점 (`regist_user`)**
   ```python
   query = f"INSERT INTO ALLOWED_USERS ... VALUES ('{email}', '{name}', ...)"
   ```
   f-string으로 직접 쿼리를 구성한다. 바인드 파라미터 방식으로 교체해야 한다.

3. **라인 163~166: Slack API 오류 미처리**
   ```python
   response = requests.get(...)
   slack_user = response.json()
   ```
   HTTP 응답 상태코드 체크(`response.raise_for_status()`)가 없다. 네트워크 오류 시 `JSONDecodeError`가 비제어 예외로 전파된다.

---

### 🟠 HIGH (지침 위반)

4. **모든 함수에 타입 힌트 누락** (지침서 §2 위반)
   - `check_email`, `login_btn`, `show_login` 함수에 타입 힌트 없음.
   - `regist_user`는 파라미터 타입은 있으나 반환 타입(`-> None`) 미기재.

5. **`check_email`, `login_btn`, `show_login`에 Google Style Docstring 없음** (지침서 §2 위반)

6. **`except Exception as e`로 예외 처리하나 로깅 없음 (라인 92~94)** (지침서 §3 위반)
   `logging` 모듈을 사용하지 않고 `st.error`로만 표시한다.

---

### 🟡 MEDIUM (코드 품질)

7. **라인 11~13: 모듈 레벨에서 `st.secrets` 접근**
   파일 임포트 시점에 `st.secrets`를 읽는다. Streamlit context 외부에서 임포트 시 오류가 발생할 수 있다. 함수 내부로 이동 권장.

8. **`oauth2` 객체 생성 (라인 17) 후 실제 미사용**
   `OAuth2Component` 인스턴스를 만들지만 `show_login` 내에서 사용하지 않는다 (수동 redirect 방식으로 대체됨). 불필요한 임포트·초기화 코드다.

9. **라인 39: `input_pw == None` 비교** — `is None`으로 변경해야 한다 (PEP 8).

10. **라인 193: `iloc[0]` 사용 시 IndexError 가능성**
    `user_data.loc[...].iloc[0]`에서 결과가 없을 경우 예외 발생. `.get()` 또는 길이 체크 추가 권장.

---

### 🟢 LOW

11. **라인 126: `target="_blank"` 보안 속성 누락**
    `rel="noopener noreferrer"` 추가 권장 (XSS 방지).

12. **`streamlit_oauth` 패키지 임포트하나 실질적으로 미사용** — 의존성 정리 필요.

---

## 전체 흐름 요약

```
show_login()
├── URL에 "code" 파라미터 존재 (Slack redirect 복귀)
│   └── POST 토큰 교환 → 성공시 session["auth"] 저장 → rerun
├── session["auth"] 없음 → 로그인 화면 표시
│   ├── Slack 로그인 버튼 (HTML redirect)
│   └── 외부 사용자 이메일/비밀번호 폼
│       └── login_btn() → check_email() → DB 조회 → 세션 저장
└── session["auth"] 있음 → Slack API 프로필 조회
    ├── DB 유저 확인 → 없으면 regist_user() 자동 등록
    └── 세션에 인증 상태 저장 → rerun
```
