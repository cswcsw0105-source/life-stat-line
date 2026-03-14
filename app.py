import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px

# 1. 데이터베이스 설정
conn = sqlite3.connect('life_rpg.db', check_same_thread=False)
c = conn.cursor()

# 테이블 스키마 업데이트 (근태/출석 컬럼 추가)
c.execute('''CREATE TABLE IF NOT EXISTS stats 
             (date TEXT PRIMARY KEY, sleep REAL, study REAL, steps INTEGER, saving INTEGER,
              work_hours REAL, work_status TEXT, school_status TEXT)''')
conn.commit()

st.set_page_config(page_title="Life RPG: Attendance", page_icon="🏫")
st.title("🎮 인생 RPG: 성실도 전적 시스템")

# 2. 날짜 및 모드 설정
st.sidebar.header("📅 설정")
target_date = st.sidebar.date_input("날짜 선택", date.today())
date_str = target_date.strftime('%Y-%m-%d')
is_dev_mode = st.sidebar.checkbox("개발자 모드 (과거 수정 허용)", value=True)

# 3. 데이터 불러오기
c.execute("SELECT * FROM stats WHERE date=?", (date_str,))
existing = c.fetchone()

# 기본값 설정
defaults = {
    "sleep": existing[1] if existing else 7.0,
    "study": existing[2] if existing else 0.0,
    "steps": existing[3] if existing else 5000,
    "saving": existing[4] if existing else 50,
    "work_hours": existing[5] if existing else 0.0,
    "work_status": existing[6] if existing else "해당 없음",
    "school_status": existing[7] if existing else "해당 없음"
}

can_edit = is_dev_mode or target_date == date.today()

# 4. 입력 폼 (근태/출석 섹션 추가)
with st.form("stat_form"):
    st.subheader("👨‍💼 알바 & 학교 근태")
    col1, col2 = st.columns(2)
    
    with col1:
        work_hours = st.number_input("알바 근무 시간", 0.0, 24.0, defaults["work_hours"], disabled=not can_edit)
        work_status = st.selectbox("알바 출근 상태", ["해당 없음", "정시 출근", "지각", "조퇴"], index=["해당 없음", "정시 출근", "지각", "조퇴"].index(defaults["work_status"]), disabled=not can_edit)
    
    with col2:
        school_status = st.selectbox("학교 출석 상태", ["해당 없음", "출석", "지각", "결석", "휴강"], index=["해당 없음", "출석", "지각", "결석", "휴강"].index(defaults["school_status"]), disabled=not can_edit)
    
    st.divider()
    st.subheader("🧘 일상 스탯")
    c3, c4 = st.columns(2)
    with c3:
        sleep = st.slider("수면 시간", 0.0, 12.0, defaults["sleep"], disabled=not can_edit)
        study = st.slider("자기계발 시간", 0.0, 15.0, defaults["study"], disabled=not can_edit)
    with c4:
        steps = st.number_input("걸음 수", 0, 30000, defaults["steps"], disabled=not can_edit)
        saving = st.slider("절약률 (%)", 0, 100, defaults["saving"], disabled=not can_edit)

    submitted = st.form_submit_button("오늘의 전적 기록", disabled=not can_edit)

if submitted and can_edit:
    c.execute('''INSERT OR REPLACE INTO stats (date, sleep, study, steps, saving, work_hours, work_status, school_status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (date_str, sleep, study, steps, saving, work_hours, work_status, school_status))
    conn.commit()
    st.success(f"✅ {date_str} 데이터가 저장되었습니다!")
    st.rerun()

# 5. 전적 분석 및 시각화 (RPG 점수 로직)
all_stats = pd.read_sql_query("SELECT * FROM stats ORDER BY date ASC", conn)

if not all_stats.empty:
    # 점수 계산 함수 (성실도 가중치 강화)
    def calculate_score(row):
        score = (row['sleep'] * 5) + (row['study'] * 15) + (row['steps'] / 200) + (row['saving'] * 0.3)
        
        # 알바 보너스/페널티
        score += row['work_hours'] * 10 # 일한 만큼 점수
        if row['work_status'] == "정시 출근": score += 30
        elif row['work_status'] == "지각": score -= 50
        
        # 학교 출석 페널티
        if row['school_status'] == "출석": score += 20
        elif row['school_status'] == "지각": score -= 30
        elif row['school_status'] == "결석": score -= 100
        
        return score

    all_stats['total_score'] = all_stats.apply(calculate_score, axis=1)
    
    # 예상 수익 계산 (시급 11,000원 기준)
    all_stats['earnings'] = all_stats['work_hours'] * 11000

    # 그래프 출력
    st.subheader("📈 내 인생 랭킹 추이")
    fig = px.area(all_stats, x='date', y='total_score', title='종합 성실도 점수 (RPG 지수)')
    st.plotly_chart(fig)
    
    # 금전적 보상 확인
    st.metric("이번 달 누적 알바 수익 (예상)", f"{all_stats['earnings'].sum():,.0f} 원")
    
    st.subheader("📋 최근 전적 로그")
    st.table(all_stats[['date', 'work_status', 'school_status', 'total_score']].tail(5))
