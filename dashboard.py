import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from collections import defaultdict
import plotly.express as px 


# --- 페이지 기본 설정 (넓은 레이아웃 사용) ---
st.set_page_config(layout="wide", page_title="스타 여캠 밸런스 티어표")

def highlight_rows(row):
    style = ''

    if 'A' in str(row['현재 티어']):
        return ['background-color: lightsalmon;'] * len(row)

    if row['티어 변동'] == '비활성화':
        return ['background-color: black; color: white;'] * len(row)

    if row['티어 변동'] == '평가유예':
        return ['background-color: #E5E4E2; color: black;'] * len(row)

    if row['티어 변동'] == '승급':
        return ['background-color: lightblue; color: black;'] * len(row)
    
    if row['티어 변동'] == '강등':
        return ['background-color: #FFEC8B; color: black;'] * len(row)
                
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
    
def display_win_rate_top5(column, dataframe, stat_name_kor, stat_name_eng):
    with column:
        st.markdown(f"<p style='font-weight: bold; margin-bottom: 5px;'>{stat_name_kor}</p>", unsafe_allow_html=True)
        if dataframe.empty:
            st.markdown("<p style='font-size: 0.9em; color: grey;'>해당 없음</p>", unsafe_allow_html=True)
        for i, (_, row) in enumerate(dataframe.iterrows()):
            win_rate_col = f'{stat_name_eng} 승률_numeric'
            match_count_col = f'{stat_name_eng}_경기수'
            
            st.markdown(f"""
            <div style="line-height: 1.1; margin-bottom: 2px; font-size: 0.9em;">
                {i+1}. {int(row['현재 티어'])}티어 {row['이름']}<br>
                <span style='font-size:0.9em; color:grey;'>({int(row[match_count_col])}게임, {row[win_rate_col]:.1f}%)</span>
            </div>
            """, unsafe_allow_html=True)

# --------------------
# 메인 대시보드
# --------------------

# --- 대시보드 제목 설정 ---
st.title('⭐ 스타크래프트 여캠 밸런스 티어표 HOTFIX')
st.markdown("""
<div style="text-align: left;">
    <p style="font-size: 1.1em; margin-bottom: 0;"><b>데이터 갱신일: 2025-08-16</b></p>
    <p style="margin-bottom: 0.1em;">평가기간: 2025-05-24 ~ 2025-07-16</p>
    <p style="font-size: 0.9em;">제작자: UnKn0wn1</p>
</div>
""", unsafe_allow_html=True)
# --- 데이터 파일 불러오기 ---
try:
    # 첫 번째 탭(종합 리포트)
    df = pd.read_excel('public_report.xlsx', sheet_name='종합 리포트')
    # 두 번째 탭(점수 상승 Top 5)
    top_5_gainers_df = pd.read_excel('public_report.xlsx', sheet_name='점수 상승 Top 5')
except FileNotFoundError:
    st.error("리포트 파일을 찾을 수 없습니다. (public_report.xlsx)")
    st.stop()
except ValueError as e: 
    st.warning("'점수 상승 Top 5' 탭을 찾을 수 없습니다. 해당 부분은 비워둡니다.")
    # 시트가 없을 경우, 빈 데이터프레임을 생성하여 에러 방지
    top_5_gainers_df = pd.DataFrame(columns=['티어', '종족', '선수이름', '점수상승폭'])

# 승률 및 경기수 숫자 데이터 추출
for col in ['동티어 승률', '상위티어 승률', '하위티어 승률']:
    df[f'{col}_numeric'] = pd.to_numeric(df[col].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce').fillna(0)
    df[f'{col.split(" ")[0]}_경기수'] = pd.to_numeric(df[col].astype(str).str.extract(r'\((\d+)\s*게임\)')[0], errors='coerce').fillna(0)

# 정렬 키 1: 메인 그룹 (일반 그룹 / 평가유예 / 비활성화)
def get_primary_group(tier_change_value):
    if tier_change_value == '평가유예':
        return 1
    if tier_change_value == '비활성화':
        return 2
    return 0 # 그 외 (유효, 유스, 승급, 강등 등)
df['sort_key_1'] = df['티어 변동'].apply(get_primary_group)

# 정렬 키 2: 숫자 티어 (e.g., '3A' -> 3)
df['sort_key_2'] = df['현재 티어'].apply(lambda x: int(str(x).replace('A', '')))

# 정렬 키 3: 티어 내 A티어 우선 정렬 (A티어는 0, 일반은 1)
df['sort_key_3'] = df['현재 티어'].apply(lambda x: 0 if 'A' in str(x) else 1)

# 최종 정렬
df_sorted = df.sort_values(by=['sort_key_1', 'sort_key_2', 'sort_key_3'])


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

display_columns = [
    col for col in df.columns 
    if not col.endswith(('_numeric', '_경기수')) and not col.startswith('sort_key_') and col != '상태'
]

display_df = df_sorted[display_columns]

styled_df = display_df.style.apply(highlight_rows, axis=1) \
                          .format({'클러치': lambda x: f'{x:.2f}' if isinstance(x, (int, float)) else x})

st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- 기간 내 주요 이슈 ---
st.divider()
st.header('📌 주요 이슈 요약')

# 데이터 추출
promoted_df = df[df['티어 변동'].isin(['승급'])]
demoted_df = df[df['티어 변동'] == '강등']

df['총 경기수_numeric_safe'] = pd.to_numeric(df['총 경기수'], errors='coerce')
df['클러치_numeric_safe'] = pd.to_numeric(df['클러치'].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce')

valid_players_df = df[~df['티어 변동'].isin(['평가유예', '비활성화'])]
if not valid_players_df.empty:
    most_matches_player = valid_players_df.loc[valid_players_df['총 경기수_numeric_safe'].idxmax()]
    if valid_players_df['클러치_numeric_safe'].notna().any():
        highest_clutch_player = valid_players_df.loc[valid_players_df['클러치_numeric_safe'].idxmax()]
else:
    most_matches_player = None
    highest_clutch_player = None

same_tier_filtered_df = valid_players_df[valid_players_df['동티어_경기수'] >= 40]
top5_highest_same = same_tier_filtered_df.sort_values(by='동티어 승률_numeric', ascending=False).head(3)
higher_tier_filtered_df = valid_players_df[valid_players_df['상위티어_경기수'] >= 20]
top5_highest_higher = higher_tier_filtered_df.sort_values(by='상위티어 승률_numeric', ascending=False).head(3)
lower_tier_filtered_df = valid_players_df[valid_players_df['하위티어_경기수'] >= 20]
top5_highest_lower = lower_tier_filtered_df.sort_values(by='하위티어 승률_numeric', ascending=False).head(3)

top5_lowest_same = same_tier_filtered_df.sort_values(by='동티어 승률_numeric', ascending=True).head(3)
top5_lowest_higher = higher_tier_filtered_df[higher_tier_filtered_df['상위티어 승률_numeric'] > 0].sort_values(by='상위티어 승률_numeric', ascending=True).head(3)
top5_lowest_lower = lower_tier_filtered_df[lower_tier_filtered_df['하위티어 승률_numeric'] > 0].sort_values(by='하위티어 승률_numeric', ascending=True).head(3)

metrics_players_df = valid_players_df[~valid_players_df['현재 티어'].astype(str).str.contains('9|8|7|1|0')]
metrics_players_df = metrics_players_df.dropna(subset=['클러치_numeric_safe'])

top_5_matches = valid_players_df.sort_values(by='총 경기수_numeric_safe', ascending=False).head(5)
top_5_clutch = metrics_players_df.sort_values(by='클러치_numeric_safe', ascending=False).head(5)

col1, col2, col3 = st.columns([1.6, 2.8, 1.6])

with col1:
    st.markdown("#### ✒️ 티어 변동")
    st.markdown("##### 📈 승급")
    MAX_LINE_LENGTH = 40

    promoted_grouped = promoted_df.sort_values(by='sort_key_2').groupby('sort_key_2', sort=False)  
    
    final_promotion_texts = []
    
    for _, group in promoted_grouped:
        player_strings = [f"{row['이름']} ({int(row['이전 티어'])}티어 → {row['현재 티어']}티어)" for _, row in group.iterrows()]
        if not player_strings: continue
        
        lines_for_this_tier = []
        current_line = ""
        for p_str in player_strings:
            if not current_line:
                current_line = p_str
            elif len(current_line) + len(", ") + len(p_str) > MAX_LINE_LENGTH:
                lines_for_this_tier.append(current_line) 
                current_line = p_str  
            else:
                current_line += f", {p_str}" 
        
        lines_for_this_tier.append(current_line) 
        
        final_promotion_texts.append("\n".join(lines_for_this_tier))

    # --- 최종 결과 출력 ---
    if not final_promotion_texts:
        st.text("없음")
    else:
        st.text("\n".join(final_promotion_texts))

    # 강등자 목록 표시 
    st.markdown("##### 📉 강등")
    st.text(format_player_list_by_tier(demoted_df, 'promotion'))
        
    # 안내 문구
    st.markdown("※ 누락된 인원은 지속적으로 확인/갱신중입니다. \n\n유스도 가능한 반영하였습니다. \n\n이미지도 지속 갱신중입니다.")
with col2:
    st.markdown("#### 📋 세부 지표 분석 (유효 플레이어 기준)")

    st.markdown("<h5 style='margin-top: 1rem; margin-bottom: 0.5rem;'>🏆 최고 승률 TOP 3</h5>", unsafe_allow_html=True)
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    display_win_rate_top5(sub_col1, top5_highest_same, "vs 동티어(40전⬆️)", "동티어")
    display_win_rate_top5(sub_col2, top5_highest_higher, "vs 상위티어(20전⬆️)", "상위티어")
    display_win_rate_top5(sub_col3, top5_highest_lower, "vs 하위티어(20전⬆️)", "하위티어")

    st.markdown("<h5 style='margin-top: 1.5rem; margin-bottom: 0.5rem;'>💀 최저 승률 TOP 3</h5>", unsafe_allow_html=True)
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    display_win_rate_top5(sub_col1, top5_lowest_same, "vs 동티어(40전⬆️)", "동티어")
    display_win_rate_top5(sub_col2, top5_lowest_higher, "vs 상위티어(20전⬆️)", "상위티어")
    display_win_rate_top5(sub_col3, top5_lowest_lower, "vs 하위티어(20전⬆️)", "하위티어")

    st.markdown("---")
    sub_col1, sub_col2, sub_col3 = st.columns([1.1, 1, 1])

    with sub_col1:
        matches_texts = [f"{i+1}. **{int(row['현재 티어'])}티어** {row['이름']} ({int(row['총 경기수_numeric_safe'])} 게임)" for i, (_, row) in enumerate(top_5_matches.iterrows())]
        st.markdown("💪 **최다 게임 TOP 5**<br>" + "<br>".join(matches_texts), unsafe_allow_html=True)

    with sub_col2:
        clutch_texts = [f"{i+1}. **{int(row['현재 티어'])}티어** {row['이름']} ({float(row['클러치_numeric_safe']):.2f})" for i, (_, row) in enumerate(top_5_clutch.iterrows())]
        st.markdown("🎯 **최고 클러치 TOP 5**<br>" + "<br>".join(clutch_texts), unsafe_allow_html=True)

    with sub_col3:
        top_5_gainers_df['점수상승폭'] = pd.to_numeric(top_5_gainers_df['점수상승폭'], errors='coerce')
        gainer_texts = [f"{i+1}. **{row['티어']}티어** {row['선수이름']} (+{row['점수상승폭']:.1f}점)" 
                        for i, row in top_5_gainers_df.iterrows() if pd.notna(row['점수상승폭'])]
        st.markdown("🔥 **점수상승폭 TOP 5**<br>"+ "<br>".join(gainer_texts), unsafe_allow_html=True)
 
with col3:
    st.markdown("#### ℹ️ 지표 설명")
    st.markdown("""
    <div style="background-color: #e6f3ff; border-left: 5px solid #1a8cff; padding: 10px; border-radius: 5px; margin: 10px 0; color: #31333F;">
        <ul style="list-style-type: none; padding-left: 0; margin-bottom: 0;">
            <li style="margin-bottom: 8px;">
                <strong>클러치</strong>: 스폰 게임 대비 중요 경기 기대 승률<br>
                <span style="font-size: 0.9em;">(높을수록 큰 경기에 강함, 2~6티어 한정으로 표기)</span>
            </li>
            <li style="margin-bottom: 8px;">
                <strong>로직 신뢰도 등급</strong>: 판정 결과의 유효 지속성<br>
                <span style="font-size: 0.9em;">(플레이어의 점수에는 일절 영향을 주지 않음)</span>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📇 플레이어 상세분석 리포트")

    PUBLIC_HTML_URL = "https://koracle0001.github.io/sc-tier-dashboard/"

    st.markdown(f"""
    <a href="{PUBLIC_HTML_URL}" target="_blank" style="text-decoration: none;">
        <div style="
            display: inline-block;
            padding: 0.7em 1.2em;
            color: white;
            background-color: #ff4b4b;
            border-radius: 0.5rem;
            font-weight: bold;
            text-align: center;
            border: 1px solid #ff4b4b;
            transition: all 0.2s;
        ">
            🔍 상세분석 페이지로 바로가기
        </div>
    </a>
    <p style="font-size: 0.9em; margin-top: 10px; color: #555;">
        플레이어 검색, 능력치 비교, 기간별 점수 변화 등<br>
        상세 분석이 가능한 페이지로 이동합니다. (새 탭)
    </p>
    """, unsafe_allow_html=True)
    
# --- 요약 통계 ---
st.divider()
st.header('📊 요약 통계')

total_players = len(df)
inactive_players_count = (df['티어 변동'] == '비활성화').sum()
pending_players_count = (df['티어 변동'] == '평가유예').sum()
valid_players_count = total_players - inactive_players_count - pending_players_count

def get_chart_classification(row):
    if row['티어 변동'] == '비활성화': return '비활성화'
    if row['티어 변동'] == '평가유예': return '평가유예'
    if '9' in str(row['현재 티어']): return '유스'
    return '유효'
df['chart_분류'] = df.apply(get_chart_classification, axis=1)

tier_distribution = df.groupby(['sort_key_2', 'chart_분류']).size().unstack(fill_value=0)
desired_order = ['유효', '유스', '평가유예', '비활성화']
tier_distribution = tier_distribution.reindex(columns=[col for col in desired_order if col in tier_distribution.columns], fill_value=0)
tier_distribution = tier_distribution.sort_index()
tier_distribution.index = tier_distribution.index.astype(str) + "티어"

max_pending_tier_text = "해당 없음"
if '평가유예' in tier_distribution.columns and tier_distribution['평가유예'].sum() > 0:
    max_pending_count = tier_distribution['평가유예'].max()
    if max_pending_count > 0:
        top_pending_tiers = tier_distribution[tier_distribution['평가유예'] == max_pending_count].index.tolist()
        max_pending_tier_text = f"{', '.join(top_pending_tiers)} ({int(max_pending_count)}명)"

col1_sum, col2_sum = st.columns([1, 2])
with col1_sum:
    st.write("#### 평가요약")
    st.markdown(f"##### 평가기간: 54일")
    st.markdown(f"##### 총 경기 수: 5574 경기")
    st.write("#### 전체 인원 현황")
    st.markdown(f"##### 총 플레이어: **{total_players}**명")
    st.markdown(f"##### 유효 플레이어: **{valid_players_count}**명")
    st.markdown(f"##### 평가유예 플레이어: **{pending_players_count}**명")
    st.markdown(f"##### 유예인원 최다티어: **{max_pending_tier_text}**")
    st.markdown(f"##### 비활성화 플레이어: **{inactive_players_count}**명")

with col2_sum:
    st.markdown("<h3 style='text-align: center;'>티어별 인원 분포</h3>", unsafe_allow_html=True)
    
    color_map = {'유효': '#636EFA', '평가유예': '#77dd77', '비활성화': 'darkgrey'}
    
    fig = px.bar(
        tier_distribution, x=tier_distribution.index, y=tier_distribution.columns,
        color_discrete_map=color_map,
        labels={'value': '인원 수', 'x': '티어', 'variable': '분류'}, text_auto=True
    )
    
    fig.update_traces(
        textposition='outside', textfont=dict(color='black', size=12), selector=dict(type='bar')
    )
    fig.for_each_trace(lambda t: t.update(texttemplate = ["" if v == 0 else f"{v:,.0f}" for v in t.y]))
    
    max_y_value = tier_distribution.sum(axis=1).max()

    fig.update_layout(
        xaxis_title="", 
        yaxis_title="", 
        barmode='stack',
        height=500, 
        margin=dict(t=20),
        paper_bgcolor='white',  
        plot_bgcolor='white',   
        font=dict(color="black"),      
        legend=dict(
            title_text='분류',      # 범례 제목
            title_font_color="black",
            font=dict(color="black") # 범례의 모든 글씨(제목 포함) 색상
        )
    )
    
    fig.update_xaxes(
        type='category', 
        tickangle=0, 
        tickfont=dict(color="black", size=11) 
    )
    fig.update_yaxes(
        visible=False, 
        range=[0, max_y_value * 1.25] # 텍스트 공간을 더 넉넉하게 25% 확보
    )
    
    config = {'staticPlot': True}
    st.plotly_chart(fig, use_container_width=True, config=config)
