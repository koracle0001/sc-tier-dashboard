import streamlit as st
import pandas as pd
from collections import defaultdict
import plotly.express as px 


# --- 페이지 기본 설정 (넓은 레이아웃 사용) ---
st.set_page_config(layout="wide", page_title="스타 여캠 밸런스 티어표")

def highlight_rows(row):
    style = ''

    if row['티어 변동'] in ['승급']:
        style = 'background-color: lightblue; color: black;'

    if row['티어 변동'] in ['강등']:
        style = 'background-color: #FFEC8B; color: black;' # Lemonyellow 대체
 
    if row['티어 변동'] in ['유예']:
        style = 'background-color: #E5E4E2; color: black;'
               
    if '상태' in row and row['상태'] == '이레귤러':
        style = 'background-color: lightsalmon; color: black;'

    return [style] * len(row)

def format_player_list_by_tier(player_df, format_type):

    if player_df.empty:
        return "없음"
    
    grouped = defaultdict(list)
    for _, row in player_df.iterrows():
        tier = int(row['현재 티어'])
        if format_type == 'promotion':
            text = f"{row['이름']} ({int(row['이전 티어'])}티어 → {tier}티어)"
        else: # irregular
            text = f"{row['이름']} ({tier}티어)"
        grouped[tier].append(text)

    output_lines = []
    for tier in sorted(grouped.keys()):
        output_lines.append(", ".join(grouped[tier]))
        
    return "\n".join(output_lines)

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

for col in ['동티어 승률', '상위티어 승률', '하위티어 승률']:
    df[f'{col}_numeric'] = df[col].astype(str).str.extract(r'(\d+\.?\d*)').astype(float).fillna(0)
    df[f'{col.split(" ")[0]}_경기수'] = df[col].astype(str).str.extract(r'\((\d+)\s*게임\)').astype(float).fillna(0)

display_columns = [col for col in df.columns if not col.endswith(('_numeric', '_경기수'))]
display_df = df[display_columns]

st.header('밸런스 티어표')
styled_df = display_df.style.apply(highlight_rows, axis=1) \
                          .set_properties(**{'text-align': 'center'}) \
                          .format({
                              '클러치': lambda x: f'{x:.2f}' if isinstance(x, (int, float)) else x,
                              '표리부동': lambda x: f'{x:.2f}' if isinstance(x, (int, float)) else x
                          })
st.dataframe(styled_df, use_container_width=True)


# --- 기간 내 주요 선수 ---
st.divider()
st.header('🏆 기간 내 주요 선수')

# 데이터 추출
promoted_df = df[df['티어 변동'].isin(['승급'])]
demoted_df = df[df['티어 변동'] == '강등']
irregular_df = df[df['상태'] == '이레귤러'] if '상태' in df.columns else pd.DataFrame()

most_matches_player = df.loc[df['총 경기수'].astype(int).idxmax()]
highest_clutch_player = df.loc[df['클러치'].replace('-', -999).astype(float).idxmax()]
highest_hypocrisy_player = df.loc[df['표리부동'].replace('-', -999).astype(float).idxmax()]

same_tier_filtered_df = df[df['동티어_경기수'] >= 40]
highest_same_tier_wr_player = same_tier_filtered_df.loc[same_tier_filtered_df['동티어 승률_numeric'].idxmax()] if not same_tier_filtered_df.empty else None
higher_tier_filtered_df = df[df['상위티어_경기수'] >= 20]
highest_higher_tier_wr_player = higher_tier_filtered_df.loc[higher_tier_filtered_df['상위티어 승률_numeric'].idxmax()] if not higher_tier_filtered_df.empty else None
lower_tier_filtered_df = df[df['하위티어_경기수'] >= 20]
highest_lower_tier_wr_player = lower_tier_filtered_df.loc[lower_tier_filtered_df['하위티어 승률_numeric'].idxmax()] if not lower_tier_filtered_df.empty else None

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("#### 🚀 티어 변동")
    st.markdown("##### 승급")
    st.text(format_player_list_by_tier(promoted_df, 'promotion'))
    st.markdown("##### 강등")
    st.text(format_player_list_by_tier(demoted_df, 'promotion'))
    if '상태' in df.columns:
        st.markdown("##### 이레귤러")
        st.text(format_player_list_by_tier(irregular_df, 'irregular'))

with col2:
    st.markdown("#### 📈 최고 승률")
    if highest_same_tier_wr_player is not None:
        p = highest_same_tier_wr_player
        st.markdown(f"**동티어(40전 이상)**: **{int(p['현재 티어'])}티어** {p['이름']} ({p['동티어 승률']})")
    else:
        st.markdown("**동티어(40전 이상)**: 해당 없음 (40경기 이상자 없음)")

    if highest_higher_tier_wr_player is not None:
        p = highest_higher_tier_wr_player
        st.markdown(f"**상위티어(20전 이상)**: **{int(p['현재 티어'])}티어** {p['이름']} ({p['상위티어 승률']})")
    else:
        st.markdown("**상위티어(20전 이상)**: 해당 없음 (20경기 이상자 없음)")

    if highest_lower_tier_wr_player is not None:
        p = highest_lower_tier_wr_player
        st.markdown(f"**하위티어(20전 이상)**: **{int(p['현재 티어'])}티어** {p['이름']} ({p['하위티어 승률']})")
    else:
        st.markdown("**하위티어(20전 이상)**: 해당 없음 (20경기 이상자 없음)")
        
with col3:
    st.markdown("#### 🎯 세부 지표")
    p = most_matches_player
    st.markdown(f"**최다 경기**: **{int(p['현재 티어'])}티어** {p['이름']} ({p['총 경기수']} 경기)")
    p = highest_clutch_player
    st.markdown(f"**최고 클러치**: **{int(p['현재 티어'])}티어** {p['이름']} ({float(p['클러치']):.2f})")
    p = highest_hypocrisy_player
    st.markdown(f"**최고 표리부동**: **{int(p['현재 티어'])}티어** {p['이름']} ({float(p['표리부동']):.2f})")

# --- 요약 통계 ---
st.divider()
st.header('📊 요약 통계')
total_players = len(df)
pending_players_count = (df['분류'] == '평가유예').sum()
valid_players_count = total_players - pending_players_count

tier_distribution = df.groupby(['현재 티어', '분류']).size().unstack(fill_value=0)
tier_distribution = tier_distribution.sort_index()
tier_distribution.index = tier_distribution.index.astype(int).astype(str) + "티어"

col1, col2 = st.columns([1, 2])
with col1:
    st.write("#### 전체 인원 현황")
    st.markdown(f"##### 총 플레이어: **{total_players}**명")
    st.markdown(f"##### 유효 플레이어: **{valid_players_count}**명")
    st.markdown(f"##### 평가유예 플레이어: **{pending_players_count}**명")

with col2:
    st.write("#### 티어별 인원 분포")
    
    # 누적 막대그래프 생성
    fig = px.bar(
        tier_distribution,
        x=tier_distribution.index,
        y=['유효', '평가유예'],
        color_discrete_map={'유효': '#636EFA', '평가유예': 'lightgrey'},
        labels={'value': '인원 수', 'x': '티어', 'variable': '분류'}
    )

    # 그래프 디자인 세부 조정
    fig.update_layout(
        title_text='<b>티어별 인원 분포 (유효/평가유예)</b>',
        title_x=0.5,
        xaxis_title="",
        yaxis_title="",
        barmode='stack',
        legend_title_text='분류',
        yaxis=dict(visible=False)
    )
    fig.update_xaxes(
        type='category',
        tickangle=0,
        tickfont=dict(color='black', size=12)
    )
    
    config = {'staticPlot': True}
    st.plotly_chart(fig, use_container_width=True, config=config)

 