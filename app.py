from flask import Flask, jsonify, request, render_template
import os
import db
import generator
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize DB on startup
db.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        profile = db.get_user_profile()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
            
        # Check daily and weekly puzzles
        today_str = datetime.now().strftime('%Y-%m-%d')
        week_str = datetime.now().strftime('%Y-W%U')
        
        conn = db.get_db()
        
        # Daily
        daily_row = conn.execute('SELECT id FROM puzzles WHERE type = "daily" AND date_assigned = ?', (today_str,)).fetchone()
        if daily_row:
            daily_id = daily_row['id']
        else:
            # Generate new daily puzzle
            try:
                daily_id = generator.generate_puzzle('daily', today_str)
            except Exception as e:
                print(f"Error generating daily puzzle: {e}")
                # Fallback to last daily puzzle or a random one
                fallback = conn.execute('SELECT id FROM puzzles WHERE type = "daily" ORDER BY id DESC LIMIT 1').fetchone()
                daily_id = fallback['id'] if fallback else 1
                
        # Weekly
        weekly_row = conn.execute('SELECT id FROM puzzles WHERE type = "weekly" AND date_assigned = ?', (week_str,)).fetchone()
        if weekly_row:
            weekly_id = weekly_row['id']
        else:
            # Generate new weekly puzzle
            try:
                weekly_id = generator.generate_puzzle('weekly', week_str)
            except Exception as e:
                print(f"Error generating weekly puzzle: {e}")
                fallback = conn.execute('SELECT id FROM puzzles WHERE type = "weekly" ORDER BY id DESC LIMIT 1').fetchone()
                weekly_id = fallback['id'] if fallback else 2

        # Check solved status
        daily_status = conn.execute('SELECT status FROM user_puzzle_status WHERE puzzle_id = ?', (daily_id,)).fetchone()
        weekly_status = conn.execute('SELECT status FROM user_puzzle_status WHERE puzzle_id = ?', (weekly_id,)).fetchone()
        
        # Get count of solved puzzles
        solved_count = conn.execute('SELECT COUNT(*) FROM user_puzzle_status WHERE status = "solved"').fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "depth_meters": profile["depth_meters"],
            "gems": profile["gems"],
            "daily_puzzle_id": daily_id,
            "daily_solved": (daily_status['status'] == 'solved') if daily_status else False,
            "weekly_puzzle_id": weekly_id,
            "weekly_solved": (weekly_status['status'] == 'solved') if weekly_status else False,
            "solved_count": solved_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shaft/<shaft_type>', methods=['GET'])
def get_shaft_puzzles(shaft_type):
    if shaft_type not in ["shaft_1", "shaft_2", "shaft_3", "shaft_4", "shaft_5"]:
        return jsonify({"error": "Invalid shaft type"}), 400
    try:
        puzzles = db.get_puzzles_by_shaft(shaft_type)
        return jsonify(puzzles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shaft/<shaft_type>/generate', methods=['POST'])
def generate_shaft_puzzle(shaft_type):
    if shaft_type not in ["shaft_1", "shaft_2", "shaft_3", "shaft_4", "shaft_5"]:
        return jsonify({"error": "Invalid shaft type"}), 400
    try:
        puzzle_id = generator.generate_puzzle(shaft_type)
        puzzle = db.get_puzzle_detail(puzzle_id)
        return jsonify(puzzle)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>', methods=['GET'])
def get_puzzle(puzzle_id):
    try:
        puzzle = db.get_puzzle_detail(puzzle_id)
        if not puzzle:
            return jsonify({"error": "Puzzle not found"}), 404
        return jsonify(puzzle)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/hint', methods=['POST'])
def unlock_hint(puzzle_id):
    try:
        profile = db.get_user_profile()
        if profile["gems"] < 3:
            return jsonify({"error": "Not enough gems!"}), 400
            
        status = db.get_user_puzzle_status(puzzle_id) if hasattr(db, 'get_user_puzzle_status') else None
        # Let's check status directly in DB or via function
        conn = db.get_db()
        status_row = conn.execute('SELECT hints_revealed, status FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
        conn.close()
        
        hints_revealed = status_row['hints_revealed'] if status_row else 0
        status_val = status_row['status'] if status_row else 'unsolved'
        
        if status_val == 'solved':
            return jsonify({"error": "Puzzle already solved! Hints are fully unlocked."}), 400
            
        if hints_revealed >= 3:
            return jsonify({"error": "All hints already unlocked!"}), 400
            
        new_hints_count = db.unlock_hint_db(puzzle_id)
        
        # Get raw puzzle hints to return the newly unlocked ones
        puzzle = db.get_puzzle_raw(puzzle_id)
        all_hints = json.loads(puzzle["hints"])
        revealed_hints = all_hints[:new_hints_count]
        
        new_profile = db.get_user_profile()
        
        return jsonify({
            "hints_revealed": new_hints_count,
            "hints": revealed_hints,
            "gems": new_profile["gems"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/drillin/activate', methods=['POST'])
def activate_drillin(puzzle_id):
    try:
        profile = db.get_user_profile()
        if profile["gems"] < 2:
            return jsonify({"error": "Not enough gems!"}), 400
            
        # Check if already active
        conn = db.get_db()
        status_row = conn.execute('SELECT drillin_active FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
        conn.close()
        
        if status_row and status_row['drillin_active'] == 1:
            return jsonify({"error": "Drillin is already active for this puzzle!"}), 400
            
        db.activate_drillin_db(puzzle_id)
        new_profile = db.get_user_profile()
        
        return jsonify({
            "drillin_active": 1,
            "gems": new_profile["gems"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/drillin/chat', methods=['GET', 'POST'])
def drillin_chat(puzzle_id):
    try:
        # Verify Drillin is active
        conn = db.get_db()
        status_row = conn.execute('SELECT drillin_active FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
        conn.close()
        
        if not status_row or status_row['drillin_active'] != 1:
            return jsonify({"error": "Drillin is not active. Invoke him first!"}), 403
            
        if request.method == 'GET':
            history = db.get_drillin_chat_db(puzzle_id)
            return jsonify(history)
            
        # POST
        data = request.json
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
            
        # Save user message
        db.add_drillin_message_db(puzzle_id, 'user', user_message)
        
        # Get conversation history
        history = db.get_drillin_chat_db(puzzle_id)
        
        # Generate and save Drillin reply
        drillin_reply = generator.drillin_respond(puzzle_id, history)
        db.add_drillin_message_db(puzzle_id, 'drillin', drillin_reply)
        
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
        data = request.json
        user_answer = data.get("answer", "")
        if not user_answer:
            return jsonify({"error": "Answer cannot be empty"}), 400
            
        res = db.submit_answer_db(puzzle_id, user_answer)
        profile = db.get_user_profile()
        res["gems"] = profile["gems"]
        res["depth_meters"] = profile["depth_meters"]
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzle/<int:puzzle_id>/notes', methods=['POST'])
def save_notes(puzzle_id):
    try:
        data = request.json
        notes = data.get("notes", "")
        db.save_puzzle_notes_db(puzzle_id, notes)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/archive', methods=['GET'])
def get_archive():
    try:
        archive = db.get_archive_db()
        return jsonify(archive)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/reset', methods=['POST'])
def reset_progress():
    try:
        conn = db.get_db()
        cursor = conn.cursor()
        # Reset profile
        cursor.execute('UPDATE user_profile SET gems = 17, depth_meters = 0, last_active = NULL WHERE id = 1')
        # Clear status & chat tables
        cursor.execute('DELETE FROM user_puzzle_status')
        cursor.execute('DELETE FROM drillin_messages')
        conn.commit()
        conn.close()
        
        # Regenerate daily/weekly
        today_str = datetime.now().strftime('%Y-%m-%d')
        week_str = datetime.now().strftime('%Y-W%U')
        
        try:
            generator.generate_puzzle('daily', today_str)
            generator.generate_puzzle('weekly', week_str)
        except Exception:
            pass
            
        return jsonify({"status": "success", "gems": 17, "depth_meters": 0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Listen on all interfaces (for Tailscale remote access) on port 8003
    app.run(host='0.0.0.0', port=8003, debug=True)
