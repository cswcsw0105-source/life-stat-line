import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px

# 1. 데이터베이스 설정 - 테이블 이름을 v3로 변경하여 충돌 방지
conn = sqlite3.connect('life_rpg_v3.db', check_same_thread=False)
c = conn.cursor()

# 짐 8개가 딱 들어가는 8칸짜리 집 건설
c.execute('''CREATE TABLE IF NOT EXISTS stats_v3 
             (date TEXT PRIMARY KEY, 
              sleep REAL, 
              study REAL, 
              steps INTEGER, 
              saving INTEGER,
              work_hours REAL, 
              work_status TEXT, 
              school_status TEXT)''')
conn.commit()

st.set_page_config(page_title="Life RPG: Final", page_icon="🏆")
st.title("🏆 인생 RPG: 전적 시스템 v3")
st.write("새로운 데이터 구조로 재건축되었습니다. 이제 오류 없이 저장 가능합니다!")

# 2. 날짜 및 개발자 모드 설정
st.sidebar.header("⚙️ 설정")
target_date = st.sidebar.date_input("날짜 선택", date.today())
date_str = target_date.strftime('%Y-%m-%d')
is_dev_mode = st.sidebar.checkbox("개발자 모드 (과거 수정 허용)", value=True)

# 3. 데이터 불러오기 로직
c.execute("SELECT * FROM stats_v3 WHERE date=?", (date_str,))
existing = c.fetchone()

# 기본값 설정 (짐 8개 세팅)
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

# 4. 입력 폼 (8개의 데이터 입력)
with st.form("stat_form_v3"):
    st.subheader(f"📅 {date_str} 전적 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("💼 근태 관리")
        work_hours = st.number_input("알바 시간", 0.0, 24.0, defaults["work_hours"], disabled=not can_edit)
        work_status = st.selectbox("알바 상태", ["해당 없음", "정시 출근", "지각", "조퇴"], 
                                   index=["해당 없음", "정시 출근", "지각", "조퇴"].index(defaults["work_status"]), disabled=not can_edit)
        school_status = st.selectbox("학교 상태", ["해당 없음", "출석", "지각", "결석", "휴강"], 
                                     index=["해당 없음", "출석", "지각", "결석", "휴강"].index(defaults["school_status"]), disabled=not can_edit)
    
    with col2:
        st.info("🧘 일상 스탯")
        sleep = st.slider("수면 시간", 0.0, 12.0, defaults["sleep"], disabled=not can_edit)
        study = st.slider("자기계발 시간", 0.0, 15.0, defaults["study"], disabled=not can_edit)
        steps = st.number_input("걸음 수", 0, 30000, defaults["steps"], disabled=not can_edit)
        saving = st.slider("절약률 (%)", 0, 100, defaults["saving"], disabled=not can_edit)

    submitted = st.form_submit_button("전적 기록 저장 (Save Stats)", disabled=not can_edit)

# 저장 로직 (8개 컬럼에 맞춰 INSERT)
if submitted and can_edit:
    c.execute('''INSERT OR REPLACE INTO stats_v3 
                 (date, sleep, study, steps, saving, work_hours, work_status, school_status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
              (date_str, sleep, study, steps, saving, work_hours, work_status, school_status))
    conn.commit()
    st.success(f"✅ {date_str} 전적이 성공적으로 기록되었습니다!")
    st.rerun()

# 5. 전적 분석 시각화
st.divider()
all_stats = pd.read_sql_query("SELECT * FROM stats_v3 ORDER BY date ASC", conn)

if not all_stats.empty:
    # 랭킹 점수 산출 공식 (경영학적 가중치 반영)
    def calc_rpg_score(row):
        # 기본 스탯 점수
        score = (row['sleep'] * 5) + (row['study'] * 15) + (row['steps'] / 200) + (row['saving'] * 0.3)
        # 알바/학교 근태 보너스 및 페널티
        score += row['work_hours'] * 10
        if row['work_status'] == "정시 출근": score += 30
        elif row['work_status'] == "지각": score -= 50
        if row['school_status'] == "출석": score += 20
        elif row['school_status'] == "결석": score -= 100
        return score

    all_stats['total_score'] = all_stats.apply(calc_rpg_score, axis=1)
    
    # 그래프 출력
    st.subheader("📊 나의 성장 곡선")
    fig = px.line(all_stats, x='date', y='total_score', title='일별 종합 전적 점수', markers=True)
    st.plotly_chart(fig)
    
    # 로그 요약
    st.subheader("📑 최근 로그")
    st.dataframe(all_stats[['date', 'work_status', 'school_status', 'total_score']].tail(7))
else:
    st.info("데이터를 입력하면 여기에 전적 그래프가 나타납니다.")

conn.close()
