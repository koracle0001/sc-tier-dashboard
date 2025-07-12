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


# --------------------
# 메인 대시보드
# --------------------

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
st.header('밸런스 티어표')

for col in ['동티어 승률', '상위티어 승률', '하위티어 승률']:
    df[f'{col}_numeric'] = df[col].astype(str).str.extract(r'(\d+\.?\d*)').astype(float).fillna(0)
df['동티어_경기수'] = df['동티어 승률'].astype(str).str.extract(r'\((\d+)\s*게임\)').astype(float).fillna(0)

styled_df = df.style.apply(highlight_rows, axis=1) \
                    .set_properties(**{'text-align': 'center'}) \
                    .format({'클러치': "{:.2f}", '표리부동': "{:.2f}"})

columns_to_hide = [col for col in df.columns if '_numeric' in col or '_경기수' in col]
st.dataframe(styled_df.hide(subset=columns_to_hide, axis=1), use_container_width=True)

# --- 요약 통계 ---
st.divider()  
st.header('🏆 기간 내 주요 선수')

promoted_df = df[df['티어 변동'].isin(['승급'])]
promoted_text_list = [f"{row['이름']} ({int(row['이전 티어'])}티어 → {int(row['현재 티어'])}티어)" for _, row in promoted_df.iterrows()]
promoted_text = ', '.join(promoted_text_list) or '없음'

demoted_df = df[df['티어 변동'] == '강등']
demoted_text_list = [f"{row['이름']} ({int(row['이전 티어'])}티어 → {int(row['현재 티어'])}티어)" for _, row in demoted_df.iterrows()]
demoted_text = ', '.join(demoted_text_list) or '없음'

irregular_text = '없음'
if '상태' in df.columns:
    irregular_df = df[df['상태'] == '이레귤러']
    irregular_text_list = [f"{row['이름']} ({int(row['현재 티어'])}티어)" for _, row in irregular_df.iterrows()]
    irregular_text = ', '.join(irregular_text_list) or '없음'

most_matches_player = df.loc[df['총 경기수'].idxmax()]
highest_clutch_player = df.loc[df['클러치'].idxmax()]
highest_hypocrisy_player = df.loc[df['표리부동'].idxmax()]

# 동티어 최고 승률 (40경기 이상 조건)
same_tier_filtered_df = df[df['동티어_경기수'] >= 40]
if not same_tier_filtered_df.empty:
    highest_same_tier_wr_player = same_tier_filtered_df.loc[same_tier_filtered_df['동티어 승률_numeric'].idxmax()]
else:
    highest_same_tier_wr_player = pd.Series({'이름': '해당 없음', '동티어 승률': '(40경기 이상자 없음)'})

# 상위/하위 티어 최고 승률
highest_higher_tier_wr_player = df.loc[df['상위티어 승률_numeric'].idxmax()]
highest_lower_tier_wr_player = df.loc[df['하위티어 승률_numeric'].idxmax()]

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("🚀 티어 변동")
    st.markdown(f"**승급**: {promoted_text}")
    st.markdown(f"**강등**: {demoted_text}")
    if '상태' in df.columns:
        st.markdown(f"**이레귤러**: {irregular_text}")

with col2:
    st.subheader("📈 최고 승률")
    st.markdown(f"**동티어 (40전 이상)**: {highest_same_tier_wr_player['이름']} ({highest_same_tier_wr_player['동티어 승률']})")
    st.markdown(f"**상위티어**: {highest_higher_tier_wr_player['이름']} ({highest_higher_tier_wr_player['상위티어 승률']})")
    st.markdown(f"**하위티어**: {highest_lower_tier_wr_player['이름']} ({highest_lower_tier_wr_player['하위티어 승률']})")

with col3:
    st.subheader("🎯 세부 지표")
    st.markdown(f"**최다 경기**: {most_matches_player['이름']} ({most_matches_player['총 경기수']} 경기)")
    st.markdown(f"**최고 클러치**: {highest_clutch_player['이름']} ({highest_clutch_player['클러치']:.2f})")
    st.markdown(f"**최고 표리부동**: {highest_hypocrisy_player['이름']} ({highest_hypocrisy_player['표리부동']:.2f})")

# =========================
# 요약 통계
# =========================
st.divider()
st.header('📊 요약 통계')
total_players = len(df)
tier_distribution = df['현재 티어'].value_counts().sort_index().reset_index()
tier_distribution.columns = ['티어', '인원 수'] 

st.metric("총 분석 인원", f"{total_players} 명")
st.write(" ") # 약간의 여백
st.write("#### 티어별 인원 분포")
st.dataframe(tier_distribution, use_container_width=True, hide_index=True)