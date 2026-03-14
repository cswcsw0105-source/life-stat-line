import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px

# 1. 데이터베이스 설정 (SQLite)
conn = sqlite3.connect('life_rpg.db', check_same_thread=False)
c = conn.cursor()

# 테이블 생성 (최초 1회)
c.execute('''CREATE TABLE IF NOT EXISTS stats 
             (date TEXT PRIMARY KEY, sleep REAL, study REAL, steps INTEGER, saving INTEGER)''')
conn.commit()

# 2. 페이지 설정
st.set_page_config(page_title="Life Stat-Line DB", page_icon="💾")
st.title("🎮 인생 전적 관리 시스템")

# 3. 날짜 선택 및 설정
st.sidebar.header("📅 날짜 선택")
target_date = st.sidebar.date_input("데이터를 입력/확인할 날짜", date.today())
date_str = target_date.strftime('%Y-%m-%d')

# 개발 모드 설정 (수정 가능 여부 제어)
is_dev_mode = st.sidebar.checkbox("개발자 모드 (과거 데이터 수정 허용)", value=True)

# 4. 기존 데이터 불러오기
c.execute("SELECT * FROM stats WHERE date=?", (date_str,))
existing_data = c.fetchone()

# 5. 입력 폼
st.subheader(f"📊 {date_str}의 스탯")

# 만약 오늘이 아니거나 개발모드가 꺼져있으면 입력을 막는 로직
can_edit = is_dev_mode or target_date == date.today()

if not can_edit:
    st.warning("⚠️ 오늘이 지난 데이터는 수정할 수 없습니다. (개발자 모드를 켜면 수정 가능)")

# 기존 데이터가 있으면 기본값으로 세팅, 없으면 기본값 0
default_sleep = existing_data[1] if existing_data else 7.0
default_study = existing_data[2] if existing_data else 0.0
default_steps = existing_data[3] if existing_data else 5000
default_saving = existing_data[4] if existing_data else 50

with st.form("stat_form"):
    col1, col2 = st.columns(2)
    with col1:
        sleep = st.slider("수면 시간", 0.0, 12.0, default_sleep, disabled=not can_edit)
        study = st.slider("자기계발 시간", 0.0, 15.0, default_study, disabled=not can_edit)
    with col2:
        steps = st.number_input("걸음 수", 0, 30000, default_steps, disabled=not can_edit)
        saving = st.slider("절약률 (%)", 0, 100, default_saving, disabled=not can_edit)
    
    submitted = st.form_submit_button("전적 저장하기", disabled=not can_edit)

if submitted and can_edit:
    c.execute('''INSERT OR REPLACE INTO stats (date, sleep, study, steps, saving) 
                 VALUES (?, ?, ?, ?, ?)''', (date_str, sleep, study, steps, saving))
    conn.commit()
    st.success(f"✅ {date_str} 전적 저장 완료!")
    st.rerun()

# 6. 통계 및 그래프 분석
st.divider()
st.subheader("📈 전체 전적 추이")

# DB의 모든 데이터 불러와서 차트 그리기
all_stats = pd.read_sql_query("SELECT * FROM stats ORDER BY date ASC", conn)

if not all_stats.empty:
    # 점수 계산 (선웅이의 공식)
    all_stats['total_score'] = (all_stats['sleep'] * 10) + (all_stats['study'] * 20) + (all_stats['steps'] / 100) + (all_stats['saving'] * 0.5)
    
    # 꺾은선 그래프
    fig = px.line(all_stats, x='date', y='total_score', title='내 인생 점수 변화', markers=True)
    st.plotly_chart(fig)
    
    # 최근 데이터 표로 보여주기
    st.dataframe(all_stats.tail(10))
else:
    st.info("아직 저장된 전적이 없습니다. 첫 데이터를 입력해보세요!")

conn.close()
