import streamlit as st
import pandas as pd

# --- 페이지 기본 설정 (넓은 레이아웃 사용) ---
st.set_page_config(layout="wide", page_title="스타 여캠 밸런스 티어표")

def highlight_rows(row):
    style = ''

    if row['티어 변동'] in ['승급']:
        style = 'background-color: lightblue; color: black;'

    if row['티어 변동'] in ['강등']:
        style = 'background-color: lemonyellow; color: black;'
                
    if '상태' in row and row['상태'] == '이레귤러':
        style = 'background-color: lightsalmon; color: black;'

    return [style] * len(row)


# --- 대시보드 제목 설정 ---
st.title('⭐ 스타크래프트 여캠 밸런스 티어표 및 분석로그')
st.caption(f"데이터 기준일: 2025-07-12")  

# --- 데이터 파일 불러오기 ---
try:
    df = pd.read_excel('public_report.xlsx')
except FileNotFoundError:
    st.error("리포트 파일을 찾을 수 없습니다. (public_report.xlsx)")
    st.stop()

# --- 전체 순위표 표시 ---
st.header('종합 리포트')

styled_df = df.style.apply(highlight_rows, axis=1) \
                    .set_properties(**{'text-align': 'center'}) \
                    .format({'클러치': "{:.2f}", '표리부동': "{:.2f}"})

st.dataframe(styled_df, use_container_width=True)

# --- 간단한 통계 정보 표시 ---
st.divider()  
st.header('요약 통계')

total_players = len(df)
tier_distribution = df['현재 티어'].value_counts().sort_index()

col1, col2 = st.columns(2)
with col1:
    st.metric("총 분석 인원", f"{total_players} 명")
with col2:
    st.write("#### 티어별 인원 분포")
    st.dataframe(tier_distribution)