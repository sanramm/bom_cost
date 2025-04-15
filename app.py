import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="📦 제조원가 계산기 with 단가DB", layout="wide")

# 단가 DB 로드 함수
def load_unit_price_db(path="단가DB_webapp용.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

# BOM 처리 함수 (엑셀에서 자재 추출 및 단가 매핑)
def process_bom(file, unit_price_db):
    df = pd.read_excel(file, skiprows=6)
    df = df.iloc[:, 4:11]  # BOM 구조 범위 추출
    df.columns = ["품명", "규격", "타입", "수량", "단가(BOM)", "금액", "발주처"]
    results = []

    for _, row in df.iterrows():
        품명 = str(row["품명"]).strip()
        규격 = str(row["규격"]).strip()
        타입 = str(row["타입"]).strip()
        수량 = pd.to_numeric(row["수량"], errors="coerce")
        bom_단가 = pd.to_numeric(row["단가(BOM)"], errors="coerce")

        key = f"{품명}|{규격}|{타입}"
        기준단가 = unit_price_db.get(key, None)

        if 기준단가 is not None:
            단가 = 기준단가
            단가출처 = "DB"
        elif not pd.isna(bom_단가):
            단가 = bom_단가
            단가출처 = "BOM"
        else:
            단가 = 0
            단가출처 = "없음"

        금액 = 수량 * float(단가) if not pd.isna(수량) else 0

        results.append({
            "품명": 품명,
            "규격": 규격,
            "타입": 타입,
            "수량": int(수량) if not pd.isna(수량) else 0,
            "단가": int(단가),
            "금액": int(금액),
            "단가출처": 단가출처
        })

    return pd.DataFrame(results)

# 앱 시작
st.title("📦 제조원가 자동 계산기 (단가DB 기준)")
st.markdown("BOM 파일을 업로드하면 기준단가로 제조원가를 자동 계산해줍니다.")

uploaded_file = st.file_uploader("BOM 엑셀 파일 업로드 (.xlsx)", type=["xlsx"])

if uploaded_file:
    unit_price_db = load_unit_price_db()
    result_df = process_bom(uploaded_file, unit_price_db)

    st.subheader("📋 원가 계산 결과")
    st.dataframe(result_df, use_container_width=True)

    total = result_df["금액"].sum()
    st.success(f"💰 총 자재비(제조원가): {total:,.0f} 원")

    # 단가출처 통계 (수정된 괄호)
    st.info("📌 단가출처 요약")
    st.dataframe(result_df["단가출처"].value_counts().rename("건수").reset_index().rename(columns={"index": "단가출처"}))
