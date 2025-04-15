import streamlit as st
import pandas as pd
import os
import json

# 단가 저장 파일 경로
PRICE_DB_PATH = "unit_prices.json"

# 단가 저장소 불러오기 (없으면 새로 생성)
def load_price_db():
    if os.path.exists(PRICE_DB_PATH):
        with open(PRICE_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

# 단가 저장
def save_price_db(price_dict):
    with open(PRICE_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(price_dict, f, ensure_ascii=False, indent=2)

# BOM에서 필요한 열만 추출하고 단가 계산
def process_bom(df, price_dict, allow_edit=False):
    df = df.iloc[7:]
    df = df.reset_index(drop=True)
    df.columns = ["순번", "", "", "", "품명", "규격", "타입", "수량", "단가", "금액", "발주처", "비고"]

    results = []
    for _, row in df.iterrows():
        품명 = str(row["품명"]).strip()
        규격 = str(row["규격"]).strip()
        타입 = str(row["타입"]).strip()
        수량 = pd.to_numeric(row["수량"], errors="coerce")

        key = f"{품명}|{규격}|{타입}"
        단가 = price_dict.get(key, row["단가"] if not pd.isna(row["단가"]) else 0)

        if allow_edit:
            단가 = st.number_input(f"단가 수정: {품명} ({규격})", value=float(단가), step=1.0, key=key)
            price_dict[key] = 단가

        금액 = 수량 * float(단가)
        results.append({"품명": 품명, "규격": 규격, "타입": 타입, "수량": 수량, "단가": 단가, "금액": 금액})

    return pd.DataFrame(results), price_dict

# Streamlit 앱 시작
st.title("📦 제조원가 자동 계산기")
st.write("엑셀 파일을 업로드하면 총 자재비(제조원가)를 계산해줍니다.")

uploaded_file = st.file_uploader("BOM 엑셀 파일 업로드", type=["xlsx"])

is_editor = st.checkbox("🔑 단가 수정 권한 (관리자만 체크)")

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    price_db = load_price_db()

    result_df, updated_prices = process_bom(df, price_db, allow_edit=is_editor)

    st.subheader("📊 원가 분석 결과")
    st.dataframe(result_df)

    total = result_df["금액"].sum()
    st.success(f"💰 총 자재비 (제조원가): {total:,.0f} 원")

    if is_editor:
        save_price_db(updated_prices)
        st.info("✏️ 수정된 단가가 저장되었습니다.")
