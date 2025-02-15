from flask import Flask, render_template, request, redirect, url_for, session, make_response, Response
import mysql.connector
import os
import requests

app = Flask(__name__)

# 세션 설정 (Flask가 로그인 정보를 저장할 수 있도록 함)
app.config['SECRET_KEY'] = 'TestFork8s'
app.config['SESSION_TYPE'] = 'filesystem'

# MySQL DB Connection
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'mysql-service'),
        user=os.getenv('MYSQL_USER', 'admin'),
        password=os.getenv('MYSQL_PASSWORD', 'admin'),
        database=os.getenv('MYSQL_DB', 'user_db')
    )
    return conn

# 로그인 페이지
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('board'))
        else:
            return "로그인 실패. 다시 시도하세요."

    return render_template('login.html')

# 로그인 후 Node.js 서비스로 이동
@app.route('/board')
def board():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    nodejs_url = 'http://nodejs-service.goals.svc.cluster.local:3000/'
    try:
        resp=requests.get(nodejs_url)
    except Exception as e:
        return f"Node.js 서비스 호출 실패: {e}", 500
    
    return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))

@app.route('/add-goal', methods=['POST'])
def add_goal():
    # 요청 데이터를 그대로 Node.js 서비스로 전달
    nodejs_url = 'http://nodejs-service.goals.svc.cluster.local:3000/add-goal'
    try:
        # Node.js 서비스에 POST 요청 보내기 (폼 데이터 전달)
        resp = requests.post(nodejs_url, data=request.form)
    except Exception as e:
        return f"Node.js 서비스 호출 실패: {e}", 500

    # Node.js 서비스의 응답에 따라 리다이렉트하거나 결과 반환
    if resp.status_code == 200:
        return redirect(url_for('board'))
    else:
        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
