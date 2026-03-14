import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, time

# 1. DB 설정 (v6)
conn = sqlite3.connect('life_rpg_v6.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS stats_v6 
             (date TEXT PRIMARY KEY, sleep REAL, study REAL, steps INTEGER, 
              spending INTEGER, work_hours REAL, work_status TEXT, school_status TEXT)''')
conn.commit()

st.title("⏰ 인생 RPG: 수면 시간 자동 계산 v6")

# 2. 날짜 설정
target_date = st.sidebar.date_input("날짜 선택", date.today())
date_str = target_date.strftime('%Y-%m-%d')

# 3. 입력 폼
with st.form("stat_form_v6"):
    st.subheader("🌙 수면 전적 (시간을 몰라도 OK)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        # 취침/기상 시각으로 입력 (폰 확인하면 알 수 있는 정보)
        bed_time = st.time_input("어제 몇 시에 잠들었나요?", time(23, 0))
    with col_t2:
        wake_time = st.time_input("오늘 몇 시에 일어났나요?", time(7, 0))
    
    # 시간 차이 계산 로직
    # (예: 밤 11시 취침 -> 아침 7시 기상 = 8시간)
    dt_bed = datetime.combine(date.today(), bed_time)
    dt_wake = datetime.combine(date.today(), wake_time)
    if dt_wake <= dt_bed: # 자정을 넘겨서 일어난 경우 처리
        from datetime import timedelta
        dt_wake += timedelta(days=1)
    
    sleep_duration = (dt_wake - dt_bed).total_seconds() / 3600
    st.info(f"💡 시스템이 계산한 수면 시간: {int(sleep_duration)}시간 {int((sleep_duration%1)*60)}분")

    st.divider()
    # 나머지 입력 항목들 (생략 가능하게 구성)
    study = st.number_input("자기계발 시간(시간 단위)", 0.0, 15.0, 0.0)
    steps = st.number_input("걸음 수", 0, 30000, 5000)
    spending = st.number_input("오늘의 지출(원)", 0, 500000, 0, step=1000)
    
    st.subheader("💼 근태 및 출석")
    work_status = st.selectbox("알바 상태", ["해당 없음", "정시 출근", "지각", "조퇴"])
    school_status = st.selectbox("학교 상태", ["해당 없음", "출석", "지각", "결석"])

    submitted = st.form_submit_button("전적 저장하기")

if submitted:
    c.execute('''INSERT OR REPLACE INTO stats_v6 VALUES (?, ?, ?, ?, ?, 0, ?, ?)''', 
              (date_str, sleep_duration, study, steps, spending, work_status, school_status))
    conn.commit()
    st.success("전적이 저장되었습니다!")
