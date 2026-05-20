import snowflake_SQL
import streamlit as st

engine = snowflake_SQL.connect_snowflake()
with engine.connect() as conn:
    query = "ALTER TABLE TESTDB.PUBLIC.MONTH_FORECAST_CONSOL ADD COLUMN REGISTANT varchar(225);"
    conn.execute(query)
    conn.commit()
