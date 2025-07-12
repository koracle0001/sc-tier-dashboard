import streamlit as st
import pandas as pd

# --- 페이지 기본 설정 (넓은 레이아웃 사용) ---
st.set_page_config(layout="wide")

# --- 대시보드 제목 설정 ---
st.title('⭐ 스타크래프트 여캠 티어 분석 로그')
st.caption(f"데이터 기준일: 2025-07-12") # 날짜는 수동으로 업데이트

# --- 데이터 파일 불러오기 ---
try:
    df = pd.read_excel('public_report.xlsx')
except FileNotFoundError:
    st.error("리포트 파일을 찾을 수 없습니다. (public_report.xlsx)")
    st.stop()

# --- 전체 순위표 표시 ---
st.header('종합 리포트')
st.dataframe(df)

# --- 간단한 통계 정보 표시 ---
st.divider() # 구분선
st.header('요약 통계')

total_players = len(df)
tier_distribution = df['현재 티어'].value_counts().sort_index()

col1, col2 = st.columns(2)
with col1:
    st.metric("총 분석 인원", f"{total_players} 명")
with col2:
    st.write("#### 티어별 인원 분포")
    st.dataframe(tier_distribution)