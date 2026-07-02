# app_00_main.py — 코드 리뷰

## 파일 목적
Streamlit 기반 수요예측(Demand Forecast) 업로드 앱의 **메인 진입 파일**.
로그인 인증 이후, 사용자가 엑셀 파일을 업로드하고 Snowflake에 데이터를 저장하는 전체 흐름을 담당한다.

---

## 함수 목록 및 위치

| 함수명 | 라인 | 설명 |
|---|---|---|
| `melt_logic(df)` | 43~63 | DataFrame을 wide → long 형태로 피벗(Melt) |
| `read_origin_xl(uploaded_file)` | 65~211 | Monthly Forecast 원본 엑셀(QTY 시트) 파싱 |
| `read_upload_xl(uploaded_file)` | 213~304 | 업로드 양식 엑셀 파싱 + Snowflake 품목명 조인 |
| `read_df_xlsx(uploaded_file)` | 306~319 | 시트 판별 후 위 두 함수로 분기 |
| `is_duplicates(conn)` | 321~330 | 동월·동일 등록자 중복 여부 확인 (미사용 상태) |
| `is_sign_off(conn)` | 332~341 | Sign-off 토글 활성 시 기존 SIGNOFF 데이터 삭제 |
| `make_tamplate_xlsx()` | 343~393 | 업로드용 엑셀 템플릿 생성 후 BytesIO 반환 |
| `save_btn()` | 395~412 | 저장 버튼 콜백 — Snowflake에 데이터 INSERT |
| `show_main()` | 414~499 | Streamlit 페이지 전체 렌더링 (진입점) |

---

## 발견된 버그 / 개선 필요 사항

### 🔴 CRITICAL (버그)

1. **라인 424: SyntaxError — 딕셔너리 키 접근 문법 오류**
   ```python
   # 현재 (오류)
   if st.session_state.get("user_role" "") == "ADMIN":
   # 수정
   if st.session_state.get("user_role", "") == "ADMIN":
   ```
   쉼표(`,`)가 누락되어 실제 실행 시 `SyntaxError`가 발생한다.

2. **`read_upload_xl` — `header_row` 미정의 가능성 (라인 218~223)**
   `for` 루프에서 `"SKU"`를 찾지 못하면 `header_row`가 정의되지 않은 채로 라인 223에서 `UnboundLocalError` 발생한다. `header_row` 초기값 설정 및 미발견 시 에러 처리가 없다.

3. **`read_upload_xl` — `except:` bare except 사용 (라인 241~244)**
   ```python
   except:
       continue
   ```
   지침서 §3 위반. `except ValueError`로 구체화해야 한다.

---

### 🟠 HIGH (지침 위반)

4. **모든 함수에 타입 힌트 누락** (지침서 §2 위반)
   - `melt_logic`, `read_origin_xl`, `read_upload_xl`, `read_df_xlsx`, `save_btn`, `show_main` 등 대부분의 공개 함수에 타입 힌트가 없다.

5. **모든 공개 함수에 Google Style Docstring 누락** (지침서 §2 위반)
   - `melt_logic`, `read_origin_xl`, `read_upload_xl`, `read_df_xlsx`, `save_btn`, `show_main` 미작성.

6. **`is_duplicates` 함수가 정의되었으나 `save_btn`에서 사용되지 않음**
   - 중복 데이터 방지 로직이 실질적으로 비활성화 상태다. 설계 의도 재확인 필요.

7. **SQL 인젝션 취약점 (라인 325, 338)**
   - f-string으로 직접 쿼리 문자열 조합. `user` 값이 오염될 경우 위험. 바인드 파라미터 사용 권장.

---

### 🟡 MEDIUM (코드 품질)

8. **`category_col_idx == None` 비교 (라인 100, 117, 133)** — PEP 8 위반. `is None`으로 변경해야 한다.

9. **`type(col) == str` 비교 (라인 129)** — `isinstance(col, str)` 사용 권장.

10. **`make_tamplate_xlsx` → 오타** — `make_template_xlsx`가 올바른 영문 스펠링이다.

11. **`is_sign_off` — 주석의 오타 (라인 333)** — `SING_OFF` → `SIGN_OFF`.

12. **`read_upload_xl` — `month_col` 참조 문제 (라인 263~264)**
    `melt` 호출 시 `id_vars`와 `value_vars`에서 이미 drop된 컬럼을 참조할 가능성이 있다. drop 후 `month_col` 리스트를 갱신해야 한다.

13. **라인 490: `width="stretch"` — 비표준 파라미터**
    `st.dataframe`의 `width` 인수는 정수 값을 받는다. `"stretch"`는 동작하지 않거나 무시될 수 있다. `use_container_width=True` 사용 권장.

---

### 🟢 LOW (사소한 개선)

14. **`read_df_xlsx`에서 `ExcelFile` 객체를 닫지 않음** — `with pd.ExcelFile(...) as xl:` 형태 권장.

15. **`requirements.txt`에 `python-dateutil` 미기재** — `dateutil`이 코드에서 사용되나 의존성에 명시되지 않음.

16. **`read_origin_xl` 루프 중복** — 라인 72~88에서 같은 df를 두 번 순회한다. 단일 루프로 합칠 수 있다.

---

## 전체 흐름 요약

```
show_main()
├── 로그인 미완료 → app_01_login.show_login()
└── 로그인 완료
    ├── ADMIN → sac.tabs([Up Load, Edit])
    │   ├── Edit → app_99_regist_edit.show_edit_page()
    │   └── Up Load → 업로드 UI
    └── 일반 → Up Load 고정
        ├── 양식 다운로드 → make_tamplate_xlsx()
        ├── 파일 업로드 → read_df_xlsx()
        │   ├── "업로드 양식" 시트 → read_upload_xl()
        │   └── "QTY" 시트 → read_origin_xl()
        │       └── melt_logic()
        └── 저장 버튼 → save_btn()
            └── is_sign_off() → snowflake_SQL.input_data()
```
