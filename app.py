from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from langchain_ollama import OllamaLLM  # 업데이트된 패키지 및 클래스 사용
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Flask 애플리케이션 생성
app = Flask(__name__)

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 데이터베이스 초기화 함수
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            daily_record TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 홈 페이지
@app.route('/')
def index():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM records').fetchall()
    conn.close()
    return render_template('index.html', records=records)

# 학습 기록 추가
@app.route('/add_record', methods=['POST'])
def add_record():
    goal = request.form['goal']
    daily_record = request.form['daily_record']
    conn = get_db_connection()
    conn.execute('INSERT INTO records (goal, daily_record) VALUES (?, ?)', (goal, daily_record))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# 학습 기록 초기화
@app.route('/reset', methods=['POST'])
def reset_records():
    conn = get_db_connection()
    conn.execute('DROP TABLE IF EXISTS records')
    conn.commit()
    init_db()
    return redirect(url_for('index'))

# Ollama 모델을 사용한 주간 리포트 생성
@app.route('/generate_report', methods=['GET'])
def generate_report():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM records').fetchall()
    conn.close()

    if not records:
        return render_template('report.html', report="No learning records to analyze.")

    # OllamaLLM 모델 초기화
    llm = OllamaLLM(model="llama3")

    # 미리 설정된 프롬프트
    prompt = "사용자의 학습 기록을 바탕으로 간단하고 짧은 리포트 하나를 한국어로만 생성해줘."

    # 학습 기록을 텍스트로 변환
    records_text = "\n".join([f"Goal: {record['goal']}, Daily Record: {record['daily_record']}" for record in records])
    full_prompt = f"{prompt}\n{records_text}"

    try:
        # OllamaLLM 모델 호출
        response = llm.invoke(full_prompt)  # 모델을 invoke 메서드로 호출
        report = response.strip()  # 텍스트 앞뒤의 공백 제거
        return render_template('report.html', report=report)
    except Exception as e:
        return render_template('report.html', report=f"Error generating report: {e}")

# 애플리케이션 실행
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
