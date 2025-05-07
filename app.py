import streamlit as st
import pandas as pd
import requests
from datetime import date

st.title("USD/EUR → JPY 月次平均レート取得ツール")

# サイドバーで期間を選択
start = st.sidebar.date_input("開始日", value=date(2019,4,1))
end   = st.sidebar.date_input("終了日", value=date.today())

# 一度に時系列データを取ってくる関数
@st.cache_data
def get_monthly(base):
    url = (
      "https://api.exchangerate.host/timeseries"
      f"?start_date={start}&end_date={end}"
      f"&base={base}&symbols=JPY"
    )
    data = requests.get(url).json().get("rates", {})
    # 日付とレートだけ取り出し
    df = pd.DataFrame([
        {"date": d, "rate": v["JPY"]}
        for d,v in data.items() if "JPY" in v
    ])
    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.to_period("M")
    m = df.groupby("year_month")["rate"].mean().reset_index()
    m["year_month"] = m["year_month"].astype(str)
    return m

# USD→JPY
usd = get_monthly("USD")
st.subheader("USD → JPY")
st.line_chart(usd.set_index("year_month"))

# EUR→JPY
eur = get_monthly("EUR")
st.subheader("EUR → JPY")
st.line_chart(eur.set_index("year_month"))

# テーブルを合体してExcelダウンロード
merged = usd.merge(eur, on="year_month", suffixes=("_USD","_EUR"))
excel_bytes = merged.to_excel(index=False, engine="openpyxl")
st.download_button(
    "Excelでダウンロード",
    data=excel_bytes,
    file_name="fx_monthly_avg.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
