import streamlit as st
import pandas as pd
import requests
from datetime import date

st.title("USD/EUR → JPY 月次平均レート取得ツール")

# 期間選択
start = st.sidebar.date_input("開始日", value=date(2019,4,1))
end   = st.sidebar.date_input("終了日",   value=date.today())

@st.cache_data
def get_monthly(base: str):
    # 日付を文字列に
    start_str = start.isoformat()
    end_str   = end.isoformat()
    # API 呼び出し
    url = (
      "https://api.exchangerate.host/timeseries"
      f"?start_date={start_str}&end_date={end_str}"
      f"&base={base}&symbols=JPY"
    )
    data = requests.get(url).json().get("rates", {})
    
    # ← ここで空チェック
    if not data:
        st.warning(f"{base}→JPY データが取得できませんでした。\n期間を確認してください。")
        return pd.DataFrame(columns=["year_month", f"{base}_to_JPY"])
    
    # データ整形
    records = [
        {"date": d, f"{base}_to_JPY": v["JPY"]}
        for d, v in data.items() if "JPY" in v
    ]
    df = pd.DataFrame(records)
    # ここで KeyError は起きません
    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.to_period("M")
    
    # 月平均を計算
    m = (
        df
        .groupby("year_month")[f"{base}_to_JPY"]
        .mean()
        .reset_index()
    )
    m["year_month"] = m["year_month"].astype(str)
    return m

# USD→JPY
usd = get_monthly("USD")
st.subheader("USD → JPY")
if not usd.empty:
    st.line_chart(usd.set_index("year_month"))

# EUR→JPY
eur = get_monthly("EUR")
st.subheader("EUR → JPY")
if not eur.empty:
    st.line_chart(eur.set_index("year_month"))

# Excel ダウンロード
if not usd.empty and not eur.empty:
    merged = usd.merge(eur, on="year_month")
    # バイトバッファに書き込む
    from io import BytesIO
    buf = BytesIO()
    merged.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    st.download_button(
        "Excelでダウンロード",
        data=buf,
        file_name="fx_monthly_avg.xlsx",
        mime=(
          "application/vnd.openxmlformats-"
          "officedocument.spreadsheetml.sheet"
        )
    )
