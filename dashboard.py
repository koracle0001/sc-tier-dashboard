import streamlit as st
import pandas as pd
from collections import defaultdict
import plotly.express as px 


# --- 페이지 기본 설정 (넓은 레이아웃 사용) ---
st.set_page_config(layout="wide", page_title="스타 여캠 밸런스 티어표")

def highlight_rows(row):
    style = ''

    if row['티어 변동'] == '비활성화':
        return ['background-color: black; color: white;'] * len(row)

    if row['티어 변동'] == '승급':
        return ['background-color: lightblue; color: black;'] * len(row)
    
    if row['티어 변동'] == '강등':
        return ['background-color: #FFEC8B; color: black;'] * len(row)
 
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

def classify_player(row):

    if row['티어 변동'] == '비활성화':
        return '비활성화'
    elif row['티어 내 순위'] == '-':
        return '평가유예'
    else:
        return '유효'

# --------------------
# 메인 대시보드
# --------------------

# --- 대시보드 제목 설정 ---
st.title('⭐ 스타크래프트 여캠 밸런스 티어표')
st.markdown("""
<div style="text-align: left;">
    <p style="font-size: 1.1em; color: black; margin-bottom: 0;"><b>데이터 갱신일: 2025-07-16</b></p>
    <p style="margin-bottom: 0.1em;">평가기간: 2025-05-24 ~ 2025-07-16</p>
    <p style="font-size: 0.9em; color: black;">제작자: UnKn0wn1</p>
</div>
""", unsafe_allow_html=True)
# --- 데이터 파일 불러오기 ---
try:
    df = pd.read_excel('public_report.xlsx')
except FileNotFoundError:
    st.error("리포트 파일을 찾을 수 없습니다. (public_report.xlsx)")
    st.stop()

for col in ['동티어 승률', '상위티어 승률', '하위티어 승률']:
    df[f'{col}_numeric'] = df[col].astype(str).str.extract(r'(\d+\.?\d*)').astype(float).fillna(0)
    df[f'{col.split(" ")[0]}_경기수'] = df[col].astype(str).str.extract(r'\((\d+)\s*게임\)').astype(float).fillna(0)
df['분류'] = df.apply(classify_player, axis=1)

status_map = {'유효': 0, '평가유예': 1, '비활성화': 2}
df['정렬순서'] = df['분류'].map(status_map)

df_sorted = df.sort_values(by=['정렬순서', '현재 티어'])

st.header('밸런스 티어표')
st.markdown("""
<style>
/* 데이터프레임의 모든 셀(td)과 헤더(th)를 가운데 정렬 */
.stDataFrame th, .stDataFrame td {
    text-align: center !important;
}
/* 데이터프레임의 첫 번째 열('이름' 컬럼) 스타일 지정 */
.stDataFrame th:nth-child(1), .stDataFrame td:nth-child(1) {
    min-width: 150px !important;  /* 최소 너비를 더 넉넉하게 설정 */
    white-space: nowrap;        /* 텍스트 줄바꿈 방지 */
}
</style>
""", unsafe_allow_html=True)

# 화면에 표시할 최종 데이터프레임
display_columns = [col for col in df.columns if not col.endswith(('_numeric', '_경기수', '분류', '순서'))]
display_df = df_sorted[display_columns]

# 배경색과 숫자 서식만 Styler로 처리
styled_df = display_df.style.apply(highlight_rows, axis=1) \
                          .format({
                              '클러치': lambda x: f'{x:.2f}' if isinstance(x, (int, float)) else x,
                              '표리부동': lambda x: f'{x:.2f}' if isinstance(x, (int, float)) else x
                          })

# 최종적으로 st.dataframe으로 표를 표시
st.dataframe(styled_df, use_container_width=True, hide_index=True)


# --- 기간 내 주요 이슈 ---
st.divider()
st.header('주요 이슈 요약')

# 데이터 추출
promoted_df = df[df['티어 변동'].isin(['승급'])]
demoted_df = df[df['티어 변동'] == '강등']
irregular_df = df[df['상태'] == '이레귤러'] if '상태' in df.columns else pd.DataFrame()

df['총 경기수_numeric_safe'] = pd.to_numeric(df['총 경기수'], errors='coerce')
df['클러치_numeric_safe'] = pd.to_numeric(df['클러치'], errors='coerce')
df['표리부동_numeric_safe'] = pd.to_numeric(df['표리부동'], errors='coerce')

valid_players_df = df[df['분류'] == '유효']
most_matches_player = valid_players_df.loc[valid_players_df['총 경기수_numeric_safe'].idxmax()]
highest_clutch_player = valid_players_df.loc[valid_players_df['클러치_numeric_safe'].idxmax()]
highest_hypocrisy_player = valid_players_df.loc[valid_players_df['표리부동_numeric_safe'].idxmax()]

same_tier_filtered_df = valid_players_df[valid_players_df['동티어_경기수'] >= 40]
highest_same_tier_wr_player = same_tier_filtered_df.loc[same_tier_filtered_df['동티어 승률_numeric'].idxmax()] if not same_tier_filtered_df.empty else None
higher_tier_filtered_df = valid_players_df[valid_players_df['상위티어_경기수'] >= 20]
highest_higher_tier_wr_player = higher_tier_filtered_df.loc[higher_tier_filtered_df['상위티어 승률_numeric'].idxmax()] if not higher_tier_filtered_df.empty else None
lower_tier_filtered_df = valid_players_df[valid_players_df['하위티어_경기수'] >= 20]
highest_lower_tier_wr_player = lower_tier_filtered_df.loc[lower_tier_filtered_df['하위티어 승률_numeric'].idxmax()] if not lower_tier_filtered_df.empty else None

lowest_same_tier_wr_player = same_tier_filtered_df.loc[same_tier_filtered_df['동티어 승률_numeric'].idxmin()] if not same_tier_filtered_df.empty else None
lowest_higher_tier_wr_player = higher_tier_filtered_df.loc[higher_tier_filtered_df['상위티어 승률_numeric'].idxmin()] if not higher_tier_filtered_df.empty else None
lowest_lower_tier_wr_player = lower_tier_filtered_df.loc[lower_tier_filtered_df['하위티어 승률_numeric'].idxmin()] if not lower_tier_filtered_df.empty else None

top_5_matches = valid_players_df.sort_values(by='총 경기수_numeric_safe', ascending=False).head(5)
top_5_clutch = valid_players_df.sort_values(by='클러치_numeric_safe', ascending=False).head(5)
top_5_hypocrisy = valid_players_df.sort_values(by='표리부동_numeric_safe', ascending=False).head(5)

col1, col2, col3 = st.columns([1.3, 2.7, 2])

with col1:
    st.markdown("#### ✒️ 티어 변동")
    st.markdown("##### 📈 승급")
    st.text(format_player_list_by_tier(promoted_df, 'promotion'))
    st.markdown("##### 📉 강등")
    st.text(format_player_list_by_tier(demoted_df, 'promotion'))
    if '상태' in df.columns:
        st.markdown("##### ⁉️ 이레귤러")
        st.text(format_player_list_by_tier(irregular_df, 'irregular'))

with col2:
    st.markdown("#### 📋 세부 지표 분석 (유효 플레이어 기준)")
    win_rate_texts = []
    if highest_same_tier_wr_player is not None:
        p = highest_same_tier_wr_player
        win_rate_texts.append(f"**동티어(40전 이상)** {int(p['현재 티어'])}티어 {p['이름']} ({int(p['동티어_경기수'])}게임, {p['동티어 승률_numeric']:.1f}%)")
    else:
        win_rate_texts.append("**동티어(40전 이상)**: 해당 없음")
    
    if highest_higher_tier_wr_player is not None:
        p = highest_higher_tier_wr_player
        win_rate_texts.append(f"**상위티어(20전 이상)**:{int(p['현재 티어'])}티어 {p['이름']} ({int(p['상위티어_경기수'])}게임, {p['상위티어 승률_numeric']:.1f}%)")
    else:
        win_rate_texts.append("**상위티어(20전 이상)**: 해당 없음")

    if highest_lower_tier_wr_player is not None:
        p = highest_lower_tier_wr_player
        win_rate_texts.append(f"**하위티어(20전 이상)**: {int(p['현재 티어'])}티어 {p['이름']} ({int(p['하위티어_경기수'])}게임, {p['하위티어 승률_numeric']:.1f}%)")
    else:
        win_rate_texts.append("**하위티어(20전 이상)**: 해당 없음")

    st.markdown("🏆 **최고 승률**<br>" + "<br>".join([f"&nbsp;&nbsp;&nbsp;└ {text}" for text in win_rate_texts]), unsafe_allow_html=True)
    
    lowest_win_rate_texts = []
    p = lowest_same_tier_wr_player
    if p is not None:
        lowest_win_rate_texts.append(f"**동티어(40전 이상)**: {int(p['현재 티어'])}티어 {p['이름']} ({int(p['동티어_경기수'])}게임, {p['동티어 승률_numeric']:.1f}%)")
    else:
        lowest_win_rate_texts.append("**동티어(40전 이상)**: 해당 없음")

    p = lowest_higher_tier_wr_player
    if p is not None:
        lowest_win_rate_texts.append(f"**상위티어(20전 이상)**: {int(p['현재 티어'])}티어 {p['이름']} ({int(p['상위티어_경기수'])}게임, {p['상위티어 승률_numeric']:.1f}%)")
    else:
        lowest_win_rate_texts.append("**상위티어(20전 이상)**: 해당 없음")
    
    p = lowest_lower_tier_wr_player
    if p is not None:
        lowest_win_rate_texts.append(f"**하위티어(20전 이상)**: {int(p['현재 티어'])}티어 {p['이름']} ({int(p['하위티어_경기수'])}게임, {p['하위티어 승률_numeric']:.1f}%)")
    else:
        lowest_win_rate_texts.append("**하위티어(20전 이상)**: 해당 없음")

    st.markdown("💀 **최저 승률**<br>" + "<br>".join([f"&nbsp;&nbsp;&nbsp;└ {text}" for text in lowest_win_rate_texts]), unsafe_allow_html=True)
    st.markdown("---")
    sub_col1, sub_col2, sub_col3 = st.columns(3)

    with sub_col1:
        matches_texts = [f"{i+1}. **{int(row['현재 티어'])}티어** {row['이름']} ({int(row['총 경기수'])} 경기)" for i, (_, row) in enumerate(top_5_matches.iterrows())]
        st.markdown("💪 **최다 경기 Top 5**<br>" + "<br>".join(matches_texts), unsafe_allow_html=True)

    with sub_col2:
        clutch_texts = [f"{i+1}. **{int(row['현재 티어'])}티어** {row['이름']} ({float(row['클러치']):.2f})" for i, (_, row) in enumerate(top_5_clutch.iterrows())]
        st.markdown("🎯 **최고 클러치 Top 5**<br>" + "<br>".join(clutch_texts), unsafe_allow_html=True)

    with sub_col3:
        hypocrisy_texts = [f"{i+1}. **{int(row['현재 티어'])}티어** {row['이름']} ({float(row['표리부동']):.2f})" for i, (_, row) in enumerate(top_5_hypocrisy.iterrows())]
        st.markdown("🤔 **최고 표리부동 Top 5**<br>" + "<br>".join(hypocrisy_texts), unsafe_allow_html=True)
 
with col3:
    st.markdown("#### ℹ️ 지표 설명")
    st.info(
        """
        - **이레귤러**: 특정상황에서 티어 내 강자를 의미합니다. (순위 무관)
        - **클러치**: 스폰 게임 대비 중요 경기 기대 승률을 나타냅니다.(높을 수록 큰 경기에 강함)
        - **표리부동**: wwe/ufc 비율을 나타냅니다. (높을 수록 변수대처 능력이 떨어지거나, 빌드수행력이 떨어짐)
        """
    )

# --- 요약 통계 ---
st.divider()
st.header('📊 요약 통계')

total_players = len(df)
inactive_players_count = (df['분류'] == '비활성화').sum()
pending_players_count = (df['분류'] == '평가유예').sum()
valid_players_count = total_players - inactive_players_count - pending_players_count

tier_distribution = df.groupby(['현재 티어', '분류']).size().unstack(fill_value=0)
desired_order = ['유효', '평가유예', '비활성화']
tier_distribution = tier_distribution.reindex(columns=[col for col in desired_order if col in tier_distribution.columns])
tier_distribution = tier_distribution.sort_index()
tier_distribution.index = tier_distribution.index.astype(int).astype(str) + "티어"

max_pending_tier_text = "해당 없음"
if '평가유예' in tier_distribution.columns and tier_distribution['평가유예'].sum() > 0:
    max_pending_count = tier_distribution['평가유예'].max()
    if max_pending_count > 0:
        top_pending_tiers = tier_distribution[tier_distribution['평가유예'] == max_pending_count].index.tolist()
        max_pending_tier_text = f"{', '.join(top_pending_tiers)} ({int(max_pending_count)}명)"

col1, col2 = st.columns([1, 2])
with col1:
    st.write("#### 전체 인원 현황")
    st.markdown(f"##### 총 플레이어: **{total_players}**명")
    st.markdown(f"##### 유효 플레이어: **{valid_players_count}**명")
    st.markdown(f"##### 유예인원 최다티어: **{max_pending_tier_text}**")
    st.markdown(f"##### 평가유예 플레이어: **{pending_players_count}**명")
    st.markdown(f"##### 비활성화 플레이어: **{inactive_players_count}**명")

with col2:
    st.markdown("<h3 style='text-align: center;'>티어별 인원 분포</h3>", unsafe_allow_html=True)
    
    color_map = {'유효': '#636EFA', '평가유예': 'lightgrey', '비활성화': 'black'}
    
    fig = px.bar(
        tier_distribution,
        x=tier_distribution.index,
        y=tier_distribution.columns,
        color_discrete_map=color_map,
        labels={'value': '인원 수', 'x': '티어', 'variable': '분류'},
        text_auto=True
    )
    
    fig.update_traces(
        textposition='outside',
        textfont=dict(color='black', size=14),
        selector=dict(type='bar')
    )
    fig.for_each_trace(lambda t: t.update(texttemplate = ["" if v == 0 else f"{v:,.0f}" for v in t.y]))
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        barmode='stack',
        legend_title_text='분류',
        yaxis=dict(visible=False),
        height=500,
        margin=dict(t=20) # 차트와 제목 사이의 상단 여백을 줄임
    )
    fig.update_xaxes(type='category', tickangle=0, tickfont=dict(color='black', size=12))
    
    config = {'staticPlot': True}
    st.plotly_chart(fig, use_container_width=True, config=config)

 