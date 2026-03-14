import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, time
import plotly.express as px

# 1. 데이터베이스 설정 (v7 새 테이블)
conn = sqlite3.connect('life_rpg_v7.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS stats_v7 
             (date TEXT PRIMARY KEY, sleep REAL, study REAL, steps INTEGER, 
              spending INTEGER, work_hours REAL, work_status TEXT, school_status TEXT)''')
conn.commit()

# --- 헬퍼 함수 ---
def format_time(float_hours):
    h = int(float_hours)
    m = int(round((float_hours - h) * 60))
    return f"{h}시간 {m}분"

def split_time(val):
    h = int(val)
    m = int(round((val - h) * 60))
    return h, m

st.set_page_config(page_title="Life RPG: Clean UI", page_icon="🏆", layout="centered")

# 2. 날짜 선택 (맨 위로 이동)
st.title("🏆 인생 RPG: 전적 시스템 v7")
target_date = st.date_input("📅 전적을 기록할 날짜를 선택하세요", date.today())
date_str = target_date.strftime('%Y-%m-%d')

# 개발자 모드만 살짝 사이드바에 남겨둘게 (화면을 넓게 쓰기 위해)
is_dev_mode = st.sidebar.checkbox("과거 데이터 수정 허용", value=True)

# 기존 데이터 불러오기
c.execute("SELECT * FROM stats_v7 WHERE date=?", (date_str,))
existing = c.fetchone()

can_edit = is_dev_mode or target_date == date.today()

# 3. 입력 폼 (전체 UI 메인 화면 집중)
with st.form("stat_form_v7"):
    # --- 수면 섹션 ---
    st.subheader("🌙 수면 전적")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        bed_time = st.time_input("어제 몇 시에 잠들었나요?", time(23, 0))
    with col_t2:
        wake_time = st.time_input("오늘 몇 시에 일어났나요?", time(7, 0))
    
    # 수면 시간 자동 계산
    dt_bed = datetime.combine(date.today(), bed_time)
    dt_wake = datetime.combine(date.today(), wake_time)
    if dt_wake <= dt_bed: dt_wake += pd.Timedelta(days=1)
    sleep_duration = (dt_wake - dt_bed).total_seconds() / 3600
    st.info(f"💡 시스템 계산 수면 시간: {format_time(sleep_duration)}")

    st.divider()

    # --- 자기계발 섹션 (시/분 분리) ---
    st.subheader("📚 자기계발 시간")
    d_study_h, d_study_m = split_time(existing[2]) if existing else (0, 0)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        study_h = st.number_input("시간(hour)", 0, 15, d_study_h, key="study_h")
    with col_s2:
        study_m = st.number_input("분(minute)", 0, 59, d_study_m, key="study_m")
    
    st.divider()

    # --- 활동 및 경제 섹션 ---
    st.subheader("👟 활동 및 지출")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        steps = st.number_input("걸음 수", 0, 30000, existing[3] if existing else 5000)
    with col_a2:
        spending = st.number_input("오늘의 지출(원)", 0, 1000000, existing[4] if existing else 0, step=1000)

    st.divider()

    # --- 근태 섹션 ---
    st.subheader("💼 근태 및 출석")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        work_status = st.selectbox("알바 상태", ["해당 없음", "정시 출근", "지각", "조퇴"], 
                                   index=["해당 없음", "정시 출근", "지각", "조퇴"].index(existing[6] if existing else "해당 없음"))
    with col_w2:
        school_status = st.selectbox("학교 상태", ["해당 없음", "출석", "지각", "결석"], 
                                     index=["해당 없음", "출석", "지각", "결석"].index(existing[7] if existing else "해당 없음"))

    submitted = st.form_submit_button("🔥 오늘의 전적 저장하기")

# 저장 로직
if submitted and can_edit:
    final_study = study_h + (study_m / 60)
    # 알바 시간은 이전 데이터 유지 혹은 0으로 세팅 (필요시 추가 가능)
    final_work = existing[5] if existing else 0.0 
    
    c.execute('''INSERT OR REPLACE INTO stats_v7 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
              (date_str, sleep_duration, final_study, steps, spending, final_work, work_status, school_status))
    conn.commit()
    st.success(f"✅ {date_str} 전적 저장 완료!")
    st.rerun()

# 4. 하단 차트 (분석 화면)
st.divider()
all_stats = pd.read_sql_query("SELECT * FROM stats_v7 ORDER BY date ASC", conn)

if not all_stats.empty:
    def calc_score(row):
        score = (row['sleep'] * 5) + (row['study'] * 15) + (row['steps'] / 200) - (row['spending'] / 1000)
        if row['work_status'] == "정시 출근": score += 30
        elif row['work_status'] == "지각": score -= 50
        if row['school_status'] == "출석": score += 20
        elif row['school_status'] == "결석": score -= 100
        return score

    all_stats['total_score'] = all_stats.apply(calc_score, axis=1)
    st.subheader("📈 내 인생 전적 그래프")
    st.line_chart(all_stats.set_index('date')['total_score'])
    
    display_df = all_stats.copy()
    display_df['자기계발'] = display_df['study'].apply(format_time)
    st.dataframe(display_df[['date', '자기계발', 'work_status', 'total_score']].tail(5))

conn.close()
