import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import db

load_dotenv()

# Check for API key
api_key = os.getenv("OPENAI_API_KEY")

def get_openai_client():
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set!")
    return OpenAI(api_key=api_key)

def generate_puzzle(puzzle_type, date_assigned=None):
    """
    Generates a new puzzle of a specific type (shaft_1..5, daily, weekly)
    using OpenAI API and saves it to the database.
    """
    client = get_openai_client()
    
    # Map type to difficulty description
    difficulty_map = {
        "shaft_1": "Level 1: Coal Mine. Very Easy. Simple math, quick logic, basic margins, hourly savings.",
        "shaft_2": "Level 2: Iron Mine. Easy. Data interpretation, averages, percentages, database size warning thresholds.",
        "shaft_3": "Level 3: Gold Mine. Medium. Optimization, resource allocation, cloud instance costs, flow networks, load balancer ratios.",
        "shaft_4": "Level 4: Ruby Mine. Hard. Matrix matching, logical deductions, scheduling overlaps, server path reliability.",
        "shaft_5": "Level 5: Diamond Mine. Insane. Complex multi-class business scenarios combining probability, cost-benefit trade-offs, and scheduling.",
        "daily": "Medium. Engaging corporate IT logical or quick math puzzle suitable for a daily challenge.",
        "weekly": "Hard/Insane. Comprehensive multi-class logical puzzle with multiple constraints, scheduling, and calculations."
    }
    
    difficulty_info = difficulty_map.get(puzzle_type, "Medium difficulty logic/math puzzle.")
    
    # We want to give the model context about what has already been generated so it doesn't repeat.
    # Let's pull the last 5 questions of this type to pass as negative examples.
    existing_questions = []
    try:
        conn = db.get_db()
        rows = conn.execute('SELECT question_text FROM puzzles WHERE type = ? ORDER BY id DESC LIMIT 5', (puzzle_type,)).fetchall()
        existing_questions = [r['question_text'] for r in rows]
        conn.close()
    except Exception:
        pass
        
    avoid_instruction = ""
    if existing_questions:
        avoid_instruction = "\nAVOID repeating or mirroring the structures of these past questions:\n" + "\n".join([f"- {q[:120]}..." for q in existing_questions])

    system_prompt = f"""You are the Master Builder of Pariah's Mineshaft, a cognitive gym web application.
Your task is to generate a high-quality, logically rigorous logical reasoning or quantitative reasoning puzzle.

CRITICAL RULES:
1. THEME: The puzzle MUST be set in a corporate IT context (e.g. software migrations, Jira boards, SLA compliance, AWS budgets, server path reliability, database clusters, Scrum scheduling overlaps, load balancer distribution, or team allocations).
2. STYLE & RIGOR: Focus on CAT DILR (Data Interpretation and Logical Reasoning) style questions. Puzzles must involve:
   - Matrix matching / Grid scheduling (assigning developers, services, or servers with overlapping rules).
   - Network flows or routing (moving data packets, server paths, or ticket transfers under latency/capacity bounds).
   - Statistics tables (deducing values from medians, averages, or ranges with missing data bounds).
   - Games, tournaments, or transactions (betting logs, scores, ratings, or rank tracking).
   - Set theory or Venn diagrams (services using combinations of languages or databases).
   IGNORE VARC style questions. The puzzle must be solvable with 100% mathematical certainty. All parameters must be tight so there are no contradictions, ambiguities, or 50/50 guesses.
3. SINGLE EXACT ANSWER: The question must have a single, definitive, short answer.
   - For 'numeric' type, it must be a single clean integer or decimal (e.g., '14' or '0.6' or '45').
   - For 'multiple_choice' type, it must be the option letter ('A', 'B', 'C', or 'D').
   - For 'short_text' type, a single short word or name.
4. VISUAL GRAPH: Generate structured 'chart_data' ONLY if the question is based on reading data from a graph. If the question is purely logical matching or text-based scheduling, set 'chart_data' to null. Do NOT leak or highlight the final answer in the chart datasets.
5. HINTS: Provide 3 progressive hints. Hint 1 is a subtle guide. Hint 2 explains the logic/equations setup. Hint 3 gives direct mathematical steps without revealing the final exact answer.
6. FORMAT: Return ONLY a valid JSON object matching the schema below. No markdown wrappers (like ```json), no extra text.

JSON Schema:
{{
    "question_text": "Detailed story, table/matrix setup, and the question.",
    "answer_type": "numeric" | "multiple_choice" | "short_text",
    "choices": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"] or null (if numeric/text),
    "exact_answer": "the exact string of the answer (e.g. '14' or 'C')",
    "explanation": "Detailed step-by-step logical breakdown showing how to derive the correct answer with absolute certainty.",
    "hints": ["Hint 1", "Hint 2", "Hint 3"],
    "gem_reward": number (2 for Coal/shaft_1, 5 for Iron/shaft_2/daily, 10 for Gold/shaft_3, 15 for Ruby/shaft_4/weekly, 25 for Diamond/shaft_5),
    "chart_data": {{
        "type": "line" | "bar" | "pie" | "radar",
        "data": {{
            "labels": ["Label1", "Label2", ...],
            "datasets": [
                {{
                    "label": "Dataset Title",
                    "data": [value1, value2, ...]
                }}
            ]
        }},
        "options": {{
            "responsive": true,
            "plugins": {{
                "title": {{
                    "display": true,
                    "text": "Chart title"
                }}
            }}
        }}
    }} or null
}}
"""

    user_prompt = f"Generate a puzzle of type: {puzzle_type}. Difficulty Level: {difficulty_info}.{avoid_instruction}"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini", # Standard mini model for fast structured generation
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.8
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Save to database
    gem_reward = result.get("gem_reward", 5)
    # Ensure correct reward mapping
    reward_map = {"shaft_1": 2, "shaft_2": 5, "shaft_3": 10, "shaft_4": 15, "shaft_5": 25, "daily": 5, "weekly": 15}
    gem_reward = reward_map.get(puzzle_type, gem_reward)
    
    choices_str = json.dumps(result.get("choices")) if result.get("choices") else None
    hints_str = json.dumps(result.get("hints"))
    chart_data_str = json.dumps(result.get("chart_data")) if result.get("chart_data") else None
    
    puzzle_id = db.save_new_puzzle(
        puzzle_type=puzzle_type,
        question_text=result["question_text"],
        answer_type=result["answer_type"],
        choices=choices_str,
        exact_answer=str(result["exact_answer"]),
        explanation=result["explanation"],
        hints=hints_str,
        gem_reward=gem_reward,
        chart_data=chart_data_str,
        date_assigned=date_assigned
    )
    
    return puzzle_id

def drillin_respond(puzzle_id, messages_history):
    """
    Sends the chat history and current puzzle context to OpenAI to get a response from 'Drillin'.
    """
    client = get_openai_client()
    
    # Get puzzle context
    puzzle = db.get_puzzle_raw(puzzle_id)
    if not puzzle:
        return "System error: puzzle context not found."
        
    # Get user solved status
    conn = db.get_db()
    status_row = conn.execute('SELECT status, user_answer, user_notes FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
    conn.close()
    
    status_dict = dict(status_row) if status_row else {"status": "unsolved"}
    is_solved = (status_dict["status"] == "solved")
    
    system_prompt = f"""You are Drillin, a support chatbot console in Pariah's Mineshaft.
You speak in a dry, tech-pessimistic, slightly sarcastic 8-bit miner persona (e.g. using metaphors like digging, pickaxes, bedrock, cave-ins, and deep extraction).
Your color is maroon, and your UI is a retro-terminal terminal.

Here is the puzzle you are attached to:
---
Question: {puzzle["question_text"]}
Type: {puzzle["type"]}
---

Here is the current state of this puzzle:
- Status: {'SOLVED' if is_solved else 'UNSOLVED'}
- User Submitted Correct Answer: {status_dict.get('user_answer')}
- User Solved Notes/Approach: {status_dict.get('user_notes')}
- Correct Solution Explanation: {puzzle["explanation"]}

CRITICAL RULES OF ENGAGEMENT:
1. IF THE STATUS IS UNSOLVED:
   - You MUST NOT reveal the answer under any circumstances.
   - You MUST NOT give clues or walk them through the equations (that's what the 3-gem hints are for).
   - If they ask for hints/answers, say they need to use the mine hints button or adjust their top hat and monocle.
   - You ARE ALLOWED and encouraged to clarify unclear wording in the question, define business acronyms (like SLA, ROI, VMs, CPU), rephrase constraints, or confirm if their understanding of the question premise is correct.
   - Keep them focused on figuring it out themselves.

2. IF THE STATUS IS SOLVED:
   - Celebrate (in your dry miner way).
   - Read their notes/approach (User Solved Notes). Give your feedback on how good it is.
   - Present alternate ways of thinking, optimization shortcuts, or mathematical models. Show the elegance of the math here! Explain the numbers in a way that gives them an intuitive sense of how to present it to senior leadership.
   - Help them remember the logic for their real life.

Keep your response under 120 words. Be concise, punchy, and retro-miner styled.
"""

    api_messages = [{"role": "system", "content": system_prompt}]
    
    # Append recent chat history
    for msg in messages_history[-10:]: # last 10 messages for context
        role = "user" if msg["sender"] == "user" else "assistant"
        api_messages.append({"role": role, "content": msg["message"]})
        
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,
        temperature=0.7,
        max_completion_tokens=250
    )
    
    reply = response.choices[0].message.content.strip()
    return reply
