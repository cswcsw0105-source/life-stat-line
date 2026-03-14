import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, time
import plotly.express as px

# 1. 데이터베이스 설정 (v8 새 테이블)
conn = sqlite3.connect('life_rpg_v8.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS stats_v8 
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

st.set_page_config(page_title="Life RPG: Complete", page_icon="💪", layout="centered")

# 2. 메인 UI 상단
st.title("💪 인생 RPG: 전적 시스템 v8")
st.write("알바 시간과 근태가 모두 통합된 최종 프로토타입입니다.")
target_date = st.date_input("📅 기록할 날짜 선택", date.today())
date_str = target_date.strftime('%Y-%m-%d')

is_dev_mode = st.sidebar.checkbox("과거 데이터 수정 허용", value=True)

# 기존 데이터 로드
c.execute("SELECT * FROM stats_v8 WHERE date=?", (date_str,))
existing = c.fetchone()
can_edit = is_dev_mode or target_date == date.today()

# 3. 입력 폼
with st.form("stat_form_v8"):
    # --- 수면 섹션 ---
    st.subheader("🌙 수면 전적")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        bed_time = st.time_input("어제 몇 시에 잠들었나요?", time(23, 0))
    with col_t2:
        wake_time = st.time_input("오늘 몇 시에 일어났나요?", time(7, 0))
    
    dt_bed = datetime.combine(date.today(), bed_time)
    dt_wake = datetime.combine(date.today(), wake_time)
    if dt_wake <= dt_bed: dt_wake += pd.Timedelta(days=1)
    sleep_duration = (dt_wake - dt_bed).total_seconds() / 3600
    st.info(f"💡 계산된 수면 시간: {format_time(sleep_duration)}")

    st.divider()

    # --- 알바 및 근태 섹션 (복구 완료!) ---
    st.subheader("💼 알바 & 학교 전적")
    d_work_h, d_work_m = split_time(existing[5]) if existing else (0, 0)
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.write("알바 근무 시간")
        wh = st.number_input("시(h)", 0, 24, d_work_h, key="wh")
        wm = st.number_input("분(m)", 0, 59, d_work_m, key="wm")
    with col_w2:
        st.write("출석 상태")
        work_status = st.selectbox("알바", ["해당 없음", "정시 출근", "지각", "조퇴"], 
                                   index=["해당 없음", "정시 출근", "지각", "조퇴"].index(existing[6] if existing else "해당 없음"))
        school_status = st.selectbox("학교", ["해당 없음", "출석", "지각", "결석"], 
                                     index=["해당 없음", "출석", "지각", "결석"].index(existing[7] if existing else "해당 없음"))

    st.divider()

    # --- 자기계발 & 활동 섹션 ---
    st.subheader("📚 성장 및 지출")
    d_study_h, d_study_m = split_time(existing[2]) if existing else (0, 0)
    
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        st.write("자기계발 시간")
        sh = st.number_input("시", 0, 15, d_study_h)
        sm = st.number_input("분", 0, 59, d_study_m)
    with c_s2:
        st.write("활동/경제")
        steps = st.number_input("걸음 수", 0, 30000, existing[3] if existing else 5000)
        spending = st.number_input("지출(원)", 0, 1000000, existing[4] if existing else 0, step=1000)

    submitted = st.form_submit_button("🔥 전적 저장 및 데이터 갱신")

# 저장 로직
if submitted and can_edit:
    final_work = wh + (wm / 60)
    final_study = sh + (sm / 60)
    
    c.execute('''INSERT OR REPLACE INTO stats_v8 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
              (date_str, sleep_duration, final_study, steps, spending, final_work, work_status, school_status))
    conn.commit()
    st.success(f"✅ {date_str} 전적이 업데이트되었습니다!")
    st.rerun()

# 4. 분석 리포트
st.divider()
all_stats = pd.read_sql_query("SELECT * FROM stats_v8 ORDER BY date ASC", conn)

if not all_stats.empty:
    # 랭킹 점수 공식
    def calc_score(row):
        score = (row['sleep'] * 5) + (row['study'] * 15) + (row['steps'] / 200) - (row['spending'] / 1000)
        score += row['work_hours'] * 10 # 일한 시간 보너스
        if row['work_status'] == "정시 출근": score += 30
        elif row['work_status'] == "지각": score -= 50
        return score

    all_stats['total_score'] = all_stats.apply(calc_score, axis=1)
    
    st.subheader("📈 성장 궤적")
    st.line_chart(all_stats.set_index('date')['total_score'])
    
    # 요약 표
    display_df = all_stats.copy()
    display_df['근무시간'] = display_df['work_hours'].apply(format_time)
    display_df['수익(예상)'] = (display_df['work_hours'] * 11000).apply(lambda x: f"{x:,.0f}원")
    st.dataframe(display_df[['date', '근무시간', '수익(예상)', 'total_score']].tail(5))

conn.close()
