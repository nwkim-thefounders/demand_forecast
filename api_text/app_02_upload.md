# app_02_upload.py

## 파일 목적

Demand Forecasting 엑셀 파일을 업로드하고 Snowflake의 `TESTDB.PUBLIC.MONTH_FORECAST_CONSOL` 테이블에 저장하는 Streamlit 페이지입니다.

- Monthly Forecast 원본 엑셀(`QTY` 시트) 또는 등록용 양식 엑셀(`업로드 양식` 시트)을 업로드할 수 있습니다.
- 업로드된 데이터는 유효성 검사 후 Snowflake에 저장됩니다.
- `양식 다운로드` 버튼을 통해 `업로드 양식` 시트를 포함한 템플릿 엑셀을 다운로드할 수 있습니다.

## 함수 목록 및 위치

| 함수 | 위치 | 설명 |
|------|------|------|
| `melt_logic` | `app_02_upload.py:44` | QTY 원본 DataFrame을 wide → long 형태로 변환하고 DB 컬럼명으로 변경합니다. |
| `read_origin_xl` | `app_02_upload.py:75` | `QTY` 시트를 파싱하여 DB 저장 형태로 반환합니다. |
| `read_upload_xl` | `app_02_upload.py:240` | `업로드 양식` 시트를 파싱하여 PRODUCT_MASTER와 조인 후 DB 저장 형태로 반환합니다. |
| `read_df_xlsx` | `app_02_upload.py:350` | 업로드 엑셀의 시트명을 판별하여 `read_origin_xl` 또는 `read_upload_xl`로 분기합니다. |
| `is_sign_off` | `app_02_upload.py:375` | Sign-off 토글 활성화 시 기존 SIGNOFF 데이터를 삭제합니다. |
| `_fetch_distinct_values` | `app_02_upload.py:401` | Snowflake에서 지정 컬럼의 고유 값 목록을 조회합니다. |
| `make_tamplate_xlsx` | `app_02_upload.py:422` | 업로드 양식 템플릿 엑셀을 생성합니다. Status는 강제 드롭다운, 사업부/채널은 비강제 드롭다운을 적용합니다. |
| `save_btn` | `app_02_upload.py:515` | 세션 DataFrame을 Snowflake에 INSERT하는 콜백 함수입니다. |
| `show_upload_page` | `app_02_upload.py:538` | 업로드 페이지 UI를 렌더링합니다. |

## 주요 변경 사항

- `make_tamplate_xlsx`에서 `ABC class` 컬럼을 제거했습니다.
- `사업부`, `채널` 컬럼에 Snowflake `MONTH_FORECAST_CONSOL` 테이블의 고유 값을 기반으로 한 드롭다운을 추가했습니다.
  - `사업부`: `SELECT DISTINCT DEPT FROM TESTDB.PUBLIC.MONTH_FORECAST_CONSOL`
  - `채널`: `SELECT DISTINCT CHANNEL FROM TESTDB.PUBLIC.MONTH_FORECAST_CONSOL`
  - 두 드롭다운은 강제하지 않습니다(`showErrorMessage = False`).
- `read_upload_xl`에서 템플릿에 `ABC class` 컬럼이 없는 경우 `ABC_CLASS`를 `None`으로 추가하여 DB INSERT가 정상적으로 동작하도록 처리했습니다.
