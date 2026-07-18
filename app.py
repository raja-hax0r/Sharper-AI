import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import db
import generator

app = Flask(__name__)
# Load secret key from environment or default
app.secret_key = os.getenv("SECRET_KEY", "mineshaft-secret-key-1337")

# Initialize DB tables on startup
db.init_db()

def get_max_attempts(puzzle_type):
    # Easy (shaft_1) = 9 attempts
    # Iron (shaft_2) = 8 attempts
    # Gold (shaft_3) = 7 attempts
    # Ruby (shaft_4) = 6 attempts
    # Diamond (shaft_5) = 5 attempts
    # Default (daily, weekly) = 8 attempts
    attempts_map = {
        "shaft_1": 9,
        "shaft_2": 8,
        "shaft_3": 7,
        "shaft_4": 6,
        "shaft_5": 5,
        "daily": 8,
        "weekly": 8
    }
    return attempts_map.get(puzzle_type, 8)

# Login Wall Middleware
@app.before_request
def require_login():
    exempt_paths = [
        '/login',
        '/api/auth/login',
        '/api/auth/register',
        '/api/auth/logout'
    ]
    if request.path.startswith('/static') or request.path in exempt_paths:
        return
    if 'user_id' not in session:
        if request.path.startswith('/api/'):
            return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for('login_view'))

# View Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_view():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

# Authentication API
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.json or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        if len(username) < 3 or len(password) < 4:
            return jsonify({"error": "Username must be at least 3 characters, password at least 4 characters"}), 400
            
        user_id = db.register_user_db(username, password)
        if not user_id:
            return jsonify({"error": "Username is already taken"}), 400
            
        session['user_id'] = user_id
        session.permanent = True
        return jsonify({"status": "success", "username": username})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.json or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
            
        user_id = db.authenticate_user_db(username, password)
        if not user_id:
            return jsonify({"error": "Invalid username or password"}), 400
            
        session['user_id'] = user_id
        session.permanent = True
        return jsonify({"status": "success", "username": username})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    return jsonify({"status": "success"})

# Profile & Progress API
@app.route('/api/status')
def get_status():
    try:
        user_id = session['user_id']
        profile = db.get_user_profile(user_id)
        if not profile:
            session.pop('user_id', None)
            return jsonify({"error": "User session invalid"}), 401
            
        today_str = datetime.now().strftime('%Y-%m-%d')
        week_str = datetime.now().strftime('%Y-W%U')
        
        # Check if daily/weekly puzzles exist
        conn = db.get_db()
        
        # Daily
        daily_row = conn.execute('SELECT id FROM puzzles WHERE type = "daily" AND date_assigned = ?', (today_str,)).fetchone()
        if daily_row:
            daily_id = daily_row['id']
        else:
            try:
                daily_id = generator.generate_puzzle('daily', today_str)
            except Exception as e:
                print(f"Error generating daily puzzle: {e}")
                fallback = conn.execute('SELECT id FROM puzzles WHERE type = "daily" ORDER BY id DESC LIMIT 1').fetchone()
                daily_id = fallback['id'] if fallback else 1
                
        # Weekly
        weekly_row = conn.execute('SELECT id FROM puzzles WHERE type = "weekly" AND date_assigned = ?', (week_str,)).fetchone()
        if weekly_row:
            weekly_id = weekly_row['id']
        else:
            try:
                weekly_id = generator.generate_puzzle('weekly', week_str)
            except Exception as e:
                print(f"Error generating weekly puzzle: {e}")
                fallback = conn.execute('SELECT id FROM puzzles WHERE type = "weekly" ORDER BY id DESC LIMIT 1').fetchone()
                weekly_id = fallback['id'] if fallback else 2
                
        conn.close()
        
        daily_solved = False
        weekly_solved = False
        
        # Check user solved status
        conn = db.get_db()
        daily_status = conn.execute('SELECT status FROM user_puzzle_status WHERE puzzle_id = ? AND user_id = ?', (daily_id, user_id)).fetchone()
        daily_solved = (daily_status and daily_status['status'] == 'solved')
        
        weekly_status = conn.execute('SELECT status FROM user_puzzle_status WHERE puzzle_id = ? AND user_id = ?', (weekly_id, user_id)).fetchone()
        weekly_solved = (weekly_status and weekly_status['status'] == 'solved')
        conn.close()
            
        return jsonify({
            "depth_meters": profile["depth_meters"],
            "gems": profile["gems"],
            "username": profile["username"],
            "daily_puzzle_id": daily_id,
            "weekly_puzzle_id": weekly_id,
            "daily_solved": daily_solved,
            "weekly_solved": weekly_solved
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Shaft & Puzzle Actions API
@app.route('/api/shaft/<shaft_type>')
def get_shaft(shaft_type):
    try:
        user_id = session['user_id']
        puzzles = db.get_puzzles_by_shaft(user_id, shaft_type)
        for p in puzzles:
            p["max_attempts"] = get_max_attempts(p["type"])
        return jsonify(puzzles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shaft/<shaft_type>/generate', methods=['POST'])
def generate_shaft_puzzle(shaft_type):
    try:
        user_id = session['user_id']
        profile = db.get_user_profile(user_id)
        
        # Generator logic check: Digging cost
        # Coal (shaft_1)=Free, Iron=3gems, Gold=5gems, Ruby=8gems, Diamond=12gems
        cost_map = {"shaft_1": 0, "shaft_2": 3, "shaft_3": 5, "shaft_4": 8, "shaft_5": 12}
        cost = cost_map.get(shaft_type, 0)
        
        if profile["gems"] < cost:
            return jsonify({"error": f"Insufficient gems. Digging in {shaft_type} costs {cost} gems."}), 400
            
        # Deduct cost
        if cost > 0:
            db.update_gems(user_id, -cost)
            
        # Generate new puzzle using OpenAI
        generator.generate_puzzle(shaft_type)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>')
def get_puzzle(puzzle_id):
    try:
        user_id = session['user_id']
        puzzle = db.get_puzzle_detail(user_id, puzzle_id)
        if not puzzle:
            return jsonify({"error": "Puzzle not found"}), 404
        puzzle["max_attempts"] = get_max_attempts(puzzle["type"])
        return jsonify(puzzle)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/hint', methods=['POST'])
@app.route('/api/puzzle/<int:puzzle_id>/hint/unlock', methods=['POST'])
def unlock_hint(puzzle_id):
    try:
        user_id = session['user_id']
        profile = db.get_user_profile(user_id)
        if profile["gems"] < 3:
            return jsonify({"error": "Not enough gems! Cost is 3 gems."}), 400
            
        revealed = db.unlock_hint_db(user_id, puzzle_id)
        puzzle_raw = db.get_puzzle_raw(puzzle_id)
        all_hints = json.loads(puzzle_raw["hints"])
        unlocked_hints = all_hints[:revealed]
        
        new_profile = db.get_user_profile(user_id)
        return jsonify({
            "hints_revealed": revealed,
            "hints": unlocked_hints,
            "gems": new_profile["gems"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/drillin/activate', methods=['POST'])
def activate_drillin(puzzle_id):
    try:
        user_id = session['user_id']
        profile = db.get_user_profile(user_id)
        if profile["gems"] < 2:
            return jsonify({"error": "Not enough gems! Cost is 2 gems."}), 400
            
        db.activate_drillin_db(user_id, puzzle_id)
        new_profile = db.get_user_profile(user_id)
        
        return jsonify({
            "drillin_active": 1,
            "gems": new_profile["gems"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/drillin/chat', methods=['GET', 'POST'])
def drillin_chat(puzzle_id):
    try:
        user_id = session['user_id']
        conn = db.get_db()
        status_row = conn.execute('SELECT drillin_active FROM user_puzzle_status WHERE puzzle_id = ? AND user_id = ?', (puzzle_id, user_id)).fetchone()
        conn.close()
        
        if not status_row or status_row['drillin_active'] != 1:
            return jsonify({"error": "Drillin is not active. Invoke him first!"}), 403
            
        if request.method == 'GET':
            history = db.get_drillin_chat_db(user_id, puzzle_id)
            return jsonify(history)
            
        # POST
        data = request.json or {}
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
            
        db.add_drillin_message_db(user_id, puzzle_id, 'user', user_message)
        history = db.get_drillin_chat_db(user_id, puzzle_id)
        
        drillin_reply = generator.drillin_respond(puzzle_id, history)
        db.add_drillin_message_db(user_id, puzzle_id, 'drillin', drillin_reply)
        
        return jsonify({
            "sender": "drillin",
            "message": drillin_reply,
            "created_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/submit', methods=['POST'])
def submit_answer(puzzle_id):
    try:
        user_id = session['user_id']
        data = request.json or {}
        user_answer = data.get("answer", "")
        if not user_answer:
            return jsonify({"error": "Answer cannot be empty"}), 400
            
        conn = db.get_db()
        status_row = conn.execute('SELECT attempts, status FROM user_puzzle_status WHERE puzzle_id = ? AND user_id = ?', (puzzle_id, user_id)).fetchone()
        puzzle_row = conn.execute('SELECT type FROM puzzles WHERE id = ?', (puzzle_id,)).fetchone()
        conn.close()
        
        if puzzle_row:
            max_att = get_max_attempts(puzzle_row['type'])
            if status_row:
                if status_row['status'] == 'solved':
                    return jsonify({"error": "This puzzle is already solved!"}), 400
                if status_row['attempts'] >= max_att:
                    return jsonify({"error": f"Max attempts ({max_att}) reached! This site has collapsed."}), 400
            
        res = db.submit_answer_db(user_id, puzzle_id, user_answer)
        profile = db.get_user_profile(user_id)
        res["gems"] = profile["gems"]
        res["depth_meters"] = profile["depth_meters"]
        
        if puzzle_row:
            res["max_attempts"] = get_max_attempts(puzzle_row['type'])
            
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/notes', methods=['POST'])
def save_notes(puzzle_id):
    try:
        user_id = session['user_id']
        data = request.json or {}
        notes = data.get("notes", "")
        db.save_puzzle_notes_db(user_id, puzzle_id, notes)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/archive', methods=['GET'])
def get_archive():
    try:
        user_id = session['user_id']
        archive = db.get_archive_db(user_id)
        return jsonify(archive)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/reset', methods=['POST'])
def reset_progress():
    try:
        user_id = session['user_id']
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET gems = 0, depth_meters = 0, last_active = NULL WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM user_puzzle_status WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM drillin_messages WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        week_str = datetime.now().strftime('%Y-W%U')
        try:
            generator.generate_puzzle('daily', today_str)
            generator.generate_puzzle('weekly', week_str)
        except Exception:
            pass
            
        return jsonify({"status": "success", "gems": 0, "depth_meters": 0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/reset-attempts', methods=['POST'])
def reset_puzzle_attempts(puzzle_id):
    try:
        user_id = session['user_id']
        profile = db.get_user_profile(user_id)
        if profile["gems"] < 5:
            return jsonify({"error": "Not enough gems! Cost is 5 gems."}), 400
            
        conn = db.get_db()
        status_row = conn.execute('SELECT attempts, status FROM user_puzzle_status WHERE puzzle_id = ? AND user_id = ?', (puzzle_id, user_id)).fetchone()
        puzzle_row = conn.execute('SELECT type FROM puzzles WHERE id = ?', (puzzle_id,)).fetchone()
        
        if not status_row or not puzzle_row:
            conn.close()
            return jsonify({"error": "Puzzle status not found."}), 400
            
        max_att = get_max_attempts(puzzle_row['type'])
        if status_row['attempts'] < max_att:
            conn.close()
            return jsonify({"error": "Mineshaft is not collapsed!"}), 400
            
        cursor = conn.cursor()
        cursor.execute('UPDATE user_puzzle_status SET attempts = 0 WHERE puzzle_id = ? AND user_id = ?', (puzzle_id, user_id))
        cursor.execute('UPDATE users SET gems = gems - 5 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        new_profile = db.get_user_profile(user_id)
        return jsonify({
            "status": "success",
            "gems": new_profile["gems"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)
