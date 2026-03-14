import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px

# 1. 데이터베이스 설정 (v5 새 테이블)
# 'saving' 컬럼을 'spending'으로 교체했습니다.
conn = sqlite3.connect('life_rpg_v5.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS stats_v5 
             (date TEXT PRIMARY KEY, sleep REAL, study REAL, steps INTEGER, 
              spending INTEGER, work_hours REAL, work_status TEXT, school_status TEXT)''')
conn.commit()

# --- 헬퍼 함수 ---
def format_time(float_hours):
    h = int(float_hours)
    m = int(round((float_hours - h) * 60))
    return f"{h}시간 {m}분"

st.set_page_config(page_title="Life RPG: Expense Tracker", page_icon="💰")
st.title("💰 인생 RPG: 실전 지출 전적 v5")

# 2. 날짜 및 설정
st.sidebar.header("⚙️ 설정")
target_date = st.sidebar.date_input("날짜 선택", date.today())
date_str = target_date.strftime('%Y-%m-%d')
is_dev_mode = st.sidebar.checkbox("과거 데이터 수정 허용", value=True)

# 1일 권장 지출 목표 (예시 점수 계산용)
budget_goal = st.sidebar.number_input("일일 지출 목표(원)", 0, 100000, 20000)

c.execute("SELECT * FROM stats_v5 WHERE date=?", (date_str,))
existing = c.fetchone()

# 기존 데이터 파싱
def split_time(val):
    h = int(val)
    m = int(round((val - h) * 60))
    return h, m

d_sleep_h, d_sleep_m = split_time(existing[1]) if existing else (7, 0)
d_study_h, d_study_m = split_time(existing[2]) if existing else (0, 0)
d_work_h, d_work_m = split_time(existing[5]) if existing else (0, 0)

can_edit = is_dev_mode or target_date == date.today()

# 3. 입력 폼
with st.form("stat_form_v5"):
    st.subheader("💼 근태 및 출석")
    c1, c2 = st.columns(2)
    with c1:
        st.write("알바 시간")
        wh = st.number_input("시", 0, 24, d_work_h, key="wh", disabled=not can_edit)
        wm = st.number_input("분", 0, 59, d_work_m, key="wm", disabled=not can_edit)
    with c2:
        work_status = st.selectbox("알바 상태", ["해당 없음", "정시 출근", "지각", "조퇴"], 
                                   index=["해당 없음", "정시 출근", "지각", "조퇴"].index(existing[6] if existing else "해당 없음"), disabled=not can_edit)
        school_status = st.selectbox("학교 상태", ["해당 없음", "출석", "지각", "결석", "휴강"], 
                                     index=["해당 없음", "출석", "지각", "결석", "휴강"].index(existing[7] if existing else "해당 없음"), disabled=not can_edit)

    st.divider()
    st.subheader("🧘 일상 및 경제 스탯")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write("수면 시간")
        sh = st.number_input("시", 0, 24, d_sleep_h, key="sh", disabled=not can_edit)
        sm = st.number_input("분", 0, 59, d_sleep_m, key="sm", disabled=not can_edit)
    with col_s2:
        st.write("자기계발 시간")
        th = st.number_input("시", 0, 24, d_study_h, key="th", disabled=not can_edit)
        tm = st.number_input("분", 0, 59, d_study_m, key="tm", disabled=not can_edit)
    
    steps = st.number_input("걸음 수", 0, 30000, existing[3] if existing else 5000, disabled=not can_edit)
    # 절약률 대신 실제 지출 금액 입력
    spending = st.number_input("오늘의 지출 총액(원)", 0, 1000000, existing[4] if existing else 0, step=1000, disabled=not can_edit)

    submitted = st.form_submit_button("오늘의 전적 기록")

if submitted and can_edit:
    final_work = wh + (wm / 60)
    final_sleep = sh + (sm / 60)
    final_study = th + (tm / 60)
    
    c.execute('''INSERT OR REPLACE INTO stats_v5 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
              (date_str, final_sleep, final_study, steps, spending, final_work, work_status, school_status))
    conn.commit()
    st.success(f"✅ {date_str} 데이터가 저장되었습니다!")
    st.rerun()

# 4. 분석 및 시각화
st.divider()
all_stats = pd.read_sql_query("SELECT * FROM stats_v5 ORDER BY date ASC", conn)

if not all_stats.empty:
    def calc_score(row):
        score = (row['sleep'] * 5) + (row['study'] * 15) + (row['steps'] / 200)
        
        # 지출 점수 계산: 목표 예산보다 적게 쓰면 보너스, 많이 쓰면 감점
        diff = budget_goal - row['spending']
        score += (diff / 1000) * 2  # 1,000원 아낄 때마다 2점 가점 (반대로는 감점)
        
        score += row['work_hours'] * 10
        if row['work_status'] == "정시 출근": score += 30
        elif row['work_status'] == "지각": score -= 50
        if row['school_status'] == "출석": score += 20
        elif row['school_status'] == "결석": score -= 100
        return score

    all_stats['total_score'] = all_stats.apply(calc_score, axis=1)
    
    # 가독성을 위한 데이터 가공
    display_df = all_stats.copy()
    display_df['오늘의 지출'] = display_df['spending'].apply(lambda x: f"{x:,}원")
    display_df['종합 점수'] = display_df['total_score'].apply(lambda x: f"{x:.1f}점")

    st.subheader("📈 종합 랭킹 곡선")
    st.line_chart(all_stats.set_index('date')['total_score'])
    
    st.subheader("📑 최근 전적 로그")
    st.dataframe(display_df[['date', '오늘의 지출', 'work_status', 'school_status', '종합 점수']].tail(7))
else:
    st.info("데이터를 입력하여 인생 전적을 쌓아보세요.")

conn.close()
