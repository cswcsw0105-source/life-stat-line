import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Life Stat-Line", page_icon="🎮")
st.title("🎮 인생 전적 대시보드 (Season 1)")
st.write("당신의 일상을 데이터로 치환하여 티어를 측정합니다.")

# 2. 사이드바 - 데이터 입력 (전적 입력창)
st.sidebar.header("📊 오늘의 스탯 입력")
name = st.sidebar.text_input("닉네임", value="최선웅")
sleep_hr = st.sidebar.slider("수면 시간 (시간)", 0, 12, 7)
study_hr = st.sidebar.slider("자기계발/공부 (시간)", 0, 15, 3)
exercise_step = st.sidebar.number_input("걸음 수", 0, 30000, 5000)
saving_rate = st.sidebar.slider("예산 대비 절약률 (%)", 0, 100, 50)

# 3. 인생 티어 산출 공식 (선웅이의 기획 핵심)
# 임의로 가중치를 둔 수식이야. 나중에 네가 수정해봐!
total_score = (sleep_hr * 10) + (study_hr * 20) + (exercise_step / 100) + (saving_rate * 0.5)

def get_tier(score):
    if score >= 250: return "💎 DIAMOND", "#00BFFF"
    elif score >= 200: return "🥇 PLATINUM", "#00FA9A"
    elif score >= 150: return "🥈 GOLD", "#FFD700"
    elif score >= 100: return "🥉 SILVER", "#C0C0C0"
    else: return "💩 BRONZE", "#CD7F32"

tier_name, tier_color = get_tier(total_score)

# 4. 결과 화면 출력
st.header(f"{name} 님의 현재 티어")
st.markdown(f"<h1 style='color:{tier_color}; text-align:center;'>{tier_name}</h1>", unsafe_allow_html=True)

# 5. 육각형 그래프 (Radar Chart) - 게임 스탯 느낌
df = pd.DataFrame(dict(
    r=[sleep_hr*10, study_hr*20, exercise_step/100, saving_rate, 50], # 마지막은 밸런스용
    theta=['수면','자기계발','활동량','절약','멘탈']
))

fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0,150])
fig.update_traces(fill='toself', line_color=tier_color)
fig.update_layout(title="인생 육각형 스탯")

st.plotly_chart(fig)

# 6. 과거 데이터 비교 (Dummy Data)
st.subheader("📈 전적 추이 (최근 7일)")
chart_data = pd.DataFrame({
    '일자': pd.date_range(start='2026-03-09', periods=7),
    '종합 점수': [120, 150, 140, 180, 130, 160, total_score]
})
st.line_chart(chart_data.set_index('일자'))

st.success(f"현재 종합 점수: {total_score:.2f}점. 지난주 평균보다 15% 상승했습니다!")
