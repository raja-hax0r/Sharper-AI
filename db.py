import sqlite3
import json
import os
from datetime import datetime

DB_PATH = 'mineshaft.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. User Profile table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            depth_meters INTEGER DEFAULT 0,
            gems INTEGER DEFAULT 17,
            last_active TEXT
        )
    ''')
    
    # 2. Puzzles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puzzles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, -- 'daily', 'weekly', 'shaft_1', 'shaft_2', 'shaft_3', 'shaft_4', 'shaft_5'
            date_assigned TEXT, -- 'YYYY-MM-DD' for daily, 'YYYY-Www' for weekly, NULL for shaft
            question_text TEXT,
            answer_type TEXT, -- 'numeric', 'multiple_choice', 'short_text'
            choices TEXT, -- JSON string list of choices or NULL
            exact_answer TEXT,
            explanation TEXT,
            hints TEXT, -- JSON string list of 3 hints
            gem_reward INTEGER,
            chart_data TEXT, -- JSON string representing Chart.js configs
            created_at TEXT
        )
    ''')
    
    # 3. User Puzzle Status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_puzzle_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id INTEGER,
            status TEXT DEFAULT 'unsolved', -- 'unsolved', 'solved'
            hints_revealed INTEGER DEFAULT 0, -- 0 to 3
            drillin_active INTEGER DEFAULT 0, -- 0 or 1
            user_answer TEXT,
            user_notes TEXT,
            solved_at TEXT,
            attempts INTEGER DEFAULT 0,
            FOREIGN KEY(puzzle_id) REFERENCES puzzles(id)
        )
    ''')

    # 4. Drillin Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drillin_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id INTEGER,
            sender TEXT, -- 'user', 'drillin'
            message TEXT,
            created_at TEXT,
            FOREIGN KEY(puzzle_id) REFERENCES puzzles(id)
        )
    ''')
    
    # Check if user profile is seeded
    cursor.execute('SELECT COUNT(*) FROM user_profile')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO user_profile (id, depth_meters, gems, last_active) VALUES (1, 0, 17, NULL)')
    
    # Check if puzzles table is seeded
    cursor.execute('SELECT COUNT(*) FROM puzzles WHERE type LIKE "shaft_%"')
    if cursor.fetchone()[0] == 0:
        seed_puzzles(cursor)
        
    conn.commit()
    conn.close()

def seed_puzzles(cursor):
    now = datetime.utcnow().isoformat()
    
    puzzles_seed = [
        # ==========================================
        # SHAFT 1 (COAL): CAT QUANT PUZZLES
        # ==========================================
        {
            "type": "shaft_1",
            "question_text": "Jayant bought a certain number of white shirts at the rate of Rs. 1000 per piece and a certain number of blue shirts at the rate of Rs. 1125 per piece. For each shirt, he then set a fixed market price which was 25% higher than the average cost of all the shirts. He sold all the shirts at a discount of 10% and made a total profit of Rs. 51000. If he bought both colors of shirts, what is the maximum possible total number of shirts that he could have bought? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "407",
            "explanation": "Let white shirts = x, blue shirts = y. Total Cost Price (CP) = 1000x + 1125y.\nTotal Market Price (MP) = 1.25 * (1000x + 1125y).\nTotal Selling Price (SP) = 0.9 * MP = 1.125 * (1000x + 1125y).\nProfit = SP - CP = 0.125 * (1000x + 1125y) = 51000.\nSo 1000x + 1125y = 408000 -> 8x + 9y = 3264.\ny = 8 * (408 - x) / 9. y must be a multiple of 8.\nTo maximize total shirts (x + y), we want to minimize individual shirt prices. 4a (average cost) must be minimized. From constraints, we get n < 408, so maximum possible total shirts n = 407.",
            "hints": json.dumps([
                "Express average cost and profit in terms of white shirts x and blue shirts y.",
                "Simplify the profit equation to get a linear relationship: 8x + 9y = 3264.",
                "Since x and y must be positive integers, find the boundary limits that maximize the sum x + y. This yields a maximum of 407."
            ]),
            "gem_reward": 2,
            "chart_data": None
        },
        {
            "type": "shaft_1",
            "question_text": "Let n and m be two positive integers such that there are exactly 41 integers greater than 8^m and less than 8^n, which can be expressed as powers of 2. Then, what is the smallest possible value of n + m? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "16",
            "explanation": "8^m = 2^(3m) and 8^n = 2^(3n).\nPowers of 2 between them are 2^(3m+1), 2^(3m+2), ..., 2^(3n-1).\nThe number of powers is (3n - 1) - (3m + 1) + 1 = 3n - 3m - 1.\nWe are given 3n - 3m - 1 = 41 -> 3(n - m) = 42 -> n - m = 14.\nSince m and n are positive integers, the smallest values are m = 1 and n = 15.\nHence, the smallest value of n + m = 1 + 15 = 16.",
            "hints": json.dumps([
                "Rewrite 8^m and 8^n as base-2 powers, which are 2^(3m) and 2^(3n).",
                "Formulate the number of integers that are powers of 2 strictly between 2^(3m) and 2^(3n). That is: 3n - 3m - 1 = 41.",
                "Solve for n - m = 14. Since they must be positive integers, set m = 1 and n = 15 to minimize n + m."
            ]),
            "gem_reward": 2,
            "chart_data": None
        },
        {
            "type": "shaft_1",
            "question_text": "Suppose f(x, y) is a real valued function such that f(3x + 2y, 2x - 5y) = 19x, for all real numbers x and y. What is the value of x for which f(x, 2x) = 27? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "3",
            "explanation": "We need to express f(A, B) = 19x in terms of A and B.\nLet A = 3x + 2y and B = 2x - 5y.\nMultiplying A by 5: 5A = 15x + 10y.\nMultiplying B by 2: 2B = 4x - 10y.\nAdding them: 5A + 2B = 19x.\nThus f(A, B) = 5A + 2B.\nNow, we need f(x, 2x) = 27.\nHere, A = x and B = 2x.\nSo f(x, 2x) = 5(x) + 2(2x) = 9x = 27.\nThus x = 3.",
            "hints": json.dumps([
                "Eliminate y by combining the two variables A = 3x + 2y and B = 2x - 5y.",
                "See how 5A + 2B relates directly to 19x.",
                "Substitute A = x and B = 2x into the function rule 5A + 2B = 27, and solve for x."
            ]),
            "gem_reward": 2,
            "chart_data": None
        },
        # ==========================================
        # SHAFT 2 (IRON): CAT DILR SET 1 (AC SALES)
        # ==========================================
        {
            "type": "shaft_2",
            "question_text": "An air conditioner (AC) company has four dealers - D1, D2, D3 and D4 in a city. It sells two variants of ACs - Window and Split. Both can be Inverter or Non-inverter. 25% of total ACs sold were Window variant, and the rest were Split. Among Inverter ACs sold, 20% were Window. Known facts:\n1. Every dealer sold at least two window ACs.\n2. D1 sold 13 inverter ACs, while D3 sold 5 Non-inverter ACs.\n3. A total of 6 Window Non-inverter ACs and 36 Split Inverter ACs were sold in the city.\n4. The number of Split ACs sold by D1 was twice the number of Window ACs sold by it.\n5. D3 and D4 sold an equal number of Window ACs, which was 1/3 of the number of Window ACs sold by D2.\n6. D2 and D3 were the only ones who sold Window Non-inverter ACs. D2's count was twice D3's.\n7. D3 and D4 sold equal Split Inverters, which was half D2's.\nHow many Split Inverter ACs did D2 sell? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "14",
            "explanation": "Let total ACs = A, Window = A/4, Split = 3A/4.\nLet total Inverters = B. Window Inverter = B/5, Split Inverter = 4B/5.\nFrom Condition 3, Split Inverter = 36 -> 4B/5 = 36 -> B = 45. Thus Window Inverter = 9.\nFrom Condition 3, Window Non-inverter = 6.\nTotal Window ACs = Window Inverter (9) + Window Non-inverter (6) = 15.\nSince Window = 15, total ACs A = 60. Split ACs = 45.\nFrom Condition 6, D2 & D3 sold Window Non-inverters in 2:1 ratio, totaling 6. Thus D2 sold 4, D3 sold 2. D1 and D4 sold 0.\nUsing the remaining constraints, we solve the system of equations. Solving gives z (Split Inverters sold by D3 and D4) = 7. D2 sold 2z = 14.",
            "hints": json.dumps([
                "Find total Window ACs using the sum of Window Inverters and Window Non-inverters.",
                "Window Non-inverters = 6 (given). B/5 + 4B/5 relationship tells us total Inverter ACs = 45, making Window Inverters = 9.",
                "This means total Window ACs = 15, making total ACs = 60. Set up a grid for D1-D4 and solve the remaining conditions to find D2's Split Inverters = 14."
            ]),
            "gem_reward": 5,
            "chart_data": None
        },
        {
            "type": "shaft_2",
            "question_text": "Based on the air conditioner sales data (Dealers D1-D4), what percentage of the total ACs sold in the city were of the Non-Inverter type? (Provide only the integer value, e.g. 25)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "25",
            "explanation": "From the solved system: Total ACs sold in the city = 60.\nTotal Inverter ACs sold = 45 (B = 45).\nTherefore, total Non-Inverter ACs sold = 60 - 45 = 15.\nPercentage of Non-Inverter ACs = (15 / 60) * 100 = 25%.",
            "hints": json.dumps([
                "Recall the total number of ACs sold in the city is 60.",
                "Recall the total number of Inverter ACs sold in the city is 45.",
                "Find the ratio of Non-Inverters (15) to total ACs (60)."
            ]),
            "gem_reward": 5,
            "chart_data": None
        },
        {
            "type": "shaft_2",
            "question_text": "Based on the air conditioner sales data (Dealers D1-D4), what was the total number of ACs (of all variants) sold by dealers D2 and D4 combined? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "33",
            "explanation": "By completing the matrix table for the dealers:\n- D1 total ACs = 15\n- D2 total ACs = 21\n- D3 total ACs = 12\n- D4 total ACs = 12\nTotal sold by D2 and D4 combined = 21 + 12 = 33.",
            "hints": json.dumps([
                "Complete the grid of sales values for each dealer.",
                "Total ACs sold by D2 = 21. Total ACs sold by D4 = 12.",
                "Add D2 and D4 sales values together."
            ]),
            "gem_reward": 5,
            "chart_data": None
        },
        # ==========================================
        # SHAFT 3 (GOLD): CAT DILR SET 2 (STUDENTS & WEIGHTS)
        # ==========================================
        {
            "type": "shaft_3",
            "question_text": "Three female students (Amala, Koli, Rini) and three male students (Biman, Mathew, Shyamal) take a course graded on a project and a test. The aggregate score is a weighted average of both components (weights positive and sum to 1). Projects are in groups of one female and one male, sharing the same project score. Facts:\n1. Minimum, maximum, and average of both project and test scores were 40, 80, and 60 respectively.\n2. Test scores were multiples of 10; 4 distinct and 2 equal to the average (60).\n3. Amala's project score was double Koli's, but Koli scored 20 more than Amala in the test. Amala had the highest aggregate.\n4. Shyamal scored second highest in the test. He scored 2 more than Koli, but 2 less than Amala in the aggregate.\n5. Biman scored second lowest in the test and lowest in the aggregate.\n6. Mathew scored more than Rini in the project, but less than her in the test.\nWhat was Rini's score in the project? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "60",
            "explanation": "Project scores must be 40, 60, and 80 (since average is 60 and min/max are 40/80).\nFrom Fact 3, Amala's project score is double Koli's, so Amala's project score = 80, and Koli's project score = 40.\nThis leaves Rini's project score = 60.",
            "hints": json.dumps([
                "Determine the three possible project scores from the min (40), max (80), and average (60).",
                "Look at Fact 3: Amala's project score is twice Koli's.",
                "The only possible project scores that fit are 80 for Amala and 40 for Koli, leaving Rini's score."
            ]),
            "gem_reward": 10,
            "chart_data": None
        },
        {
            "type": "shaft_3",
            "question_text": "Based on the student project and test score data, what was the weight of the test component in the aggregate score calculation? (Provide the decimal value, e.g. 0.6)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "0.6",
            "explanation": "Let weight of project = x, weight of test = 1 - x.\nFrom the constraints, the test scores are distinct multiples of 10 between 40 and 80. The sorted test scores are 40, 50, 60, 60, 70, 80.\nFrom Fact 3 and 4, we establish the aggregate equations.\nCase study yields that Test weight is 0.6 and Project weight is 0.4. This satisfies the constraint that Shyamal's aggregate is 2 less than Amala's.",
            "hints": json.dumps([
                "Let Project weight = x and Test weight = 1 - x.",
                "Determine the distinct test scores from the constraints (40, 50, 60, 60, 70, 80).",
                "Solve the linear equation matching Shyamal's and Amala's aggregate scores to find x."
            ]),
            "gem_reward": 10,
            "chart_data": None
        },
        {
            "type": "shaft_3",
            "question_text": "Based on the student project and test score data, what was the maximum aggregate score obtained among all the students? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "68",
            "explanation": "Amala had the highest aggregate score.\nAmala's test score = 60, project score = 80.\nAggregate = (Test Score * 0.6) + (Project Score * 0.4) = (60 * 0.6) + (80 * 0.4) = 36 + 32 = 68.",
            "hints": json.dumps([
                "Amala scored the highest aggregate score.",
                "Amala's project score is 80, and her test score is 60.",
                "Apply the weights (40% project, 60% test) to calculate Amala's score."
            ]),
            "gem_reward": 10,
            "chart_data": None
        },
        # ==========================================
        # SHAFT 4 (RUBY): CAT DILR SET 3 (ODSVILLE ELEVATION)
        # ==========================================
        {
            "type": "shaft_4",
            "question_text": "Odsville has five firms - Alfloo, Bzygoo, Czechy, Drjbna and Elavalaki. Each firm was founded in some year and closed down a few years later. Each raised Rs 1 crore in its first and last year. The amount raised increased every year to a max, and then decreased. No firm raised the same amount in two consecutive years. Annual changes were either +/- 1 or +/- 2 crores. Partial info:\n- Alfloo: Existed 2009-2016, Total 21 crores\n- Bzygoo: Existed 2012-2015\n- Czechy: Founded 2013, Total 9 crores\n- Drjbna: Existed 2011-2015, Total 10 crores\n- Elavalaki: Founded 2010, Total 13 crores\nWhat is the largest possible total amount of money (in Rs. crores) that could have been raised in 2013? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "17",
            "explanation": "By setting up the possible trajectory paths for each company:\n- Alfloo in 2013: Max possible is 5 crores.\n- Bzygoo in 2013: Max possible is 3 crores.\n- Czechy in 2013: It was founded in 2013, so it raised 1 crore.\n- Drjbna in 2013: From its constraints (2011-2015, total 10), its only possible trajectory is 1, 2, 4, 2, 1, so it raised 4 crores.\n- Elavalaki in 2013: Max possible is 4 crores.\nSumming these up: 5 + 3 + 1 + 4 + 4 = 17 crores.",
            "hints": json.dumps([
                "Determine the maximum possible amount raised by each firm individually in the year 2013.",
                "For Czechy, 2013 is the founding year, so it must be 1. For Drjbna, the only valid sequence totaling 10 is 1, 2, 4, 2, 1, so it must be 4.",
                "Analyze the boundaries for Alfloo (max 5), Bzygoo (max 3), and Elavalaki (max 4) in 2013 and sum them."
            ]),
            "gem_reward": 15,
            "chart_data": None
        },
        {
            "type": "shaft_4",
            "question_text": "Based on the Odsville firms funding records, for which firm(s) can the annual amounts raised by them be concluded with absolute certainty in each year of their existence?",
            "answer_type": "multiple_choice",
            "choices": [
                "A) Only Drjbna",
                "B) Only Czechy",
                "C) Only Czechy and Drjbna",
                "D) Only Bzygoo, Czechy and Drjbna"
            ],
            "exact_answer": "C",
            "explanation": "Analyzing the constraints:\n- Drjbna exists 2011-2015 (5 years), total 10. The only valid single-peaked sequence starts and ends at 1 and has no consecutive duplicates is 1, 2, 4, 2, 1. So it is certain.\n- Czechy total is 9, starting 2013. The only single-peaked sequence is 1, 2, 3, 2, 1 (exiting 2017). So it is certain.\n- Others have multiple possible pathways.\nHence, only Czechy and Drjbna are certain.",
            "hints": json.dumps([
                "Write down the single-peaked sequence rules (start/end with 1, no adjacent duplicates, steps of +/-1 or +/-2).",
                "Test Drjbna: 5 years, sum 10. The only sequence is 1, 2, 4, 2, 1.",
                "Test Czechy: sum 9. The only sequence is 1, 2, 3, 2, 1. Both are uniquely determined."
            ]),
            "gem_reward": 15,
            "chart_data": None
        },
        {
            "type": "shaft_4",
            "question_text": "Based on the Odsville firms funding records, what best can be concluded about the total amount of money raised by all 5 companies combined in the year 2015?",
            "answer_type": "multiple_choice",
            "choices": [
                "A) It is either Rs. 8 crores or Rs. 9 crores",
                "B) It is exactly Rs. 8 crores",
                "C) It is either Rs. 7 crores or Rs. 8 crores or Rs. 9 crores",
                "D) It is either Rs. 7 crores or Rs. 8 crores"
            ],
            "exact_answer": "D",
            "explanation": "Evaluating the year 2015 for each firm:\n- Alfloo: raised 2 crores\n- Bzygoo: raised 1 crore (last year)\n- Czechy: raised 3 crores\n- Drjbna: raised 1 crore (last year)\n- Elavalaki: could be 0 (if closed 2014) or 1 crore (if closed 2015).\nSum of first four = 2 + 1 + 3 + 1 = 7.\nWith Elavalaki, the sum is either 7 crores or 8 crores.",
            "hints": json.dumps([
                "Find the exact amounts raised in 2015 by Alfloo, Bzygoo, Czechy, and Drjbna.",
                "Check Elavalaki: its trajectory could exit in 2014 (raising 0 in 2015) or exit in 2015 (raising 1 in 2015).",
                "Add these possibilities to get the final range."
            ]),
            "gem_reward": 15,
            "chart_data": None
        },
        # ==========================================
        # SHAFT 5 (DIAMOND): CAT DILR SET 4 (RANDOM DRAW)
        # ==========================================
        {
            "type": "shaft_5",
            "question_text": "Three participants - Akhil, Bimal, and Chatur participate in a random draw for five days, scoring between 1 and 9 daily. The 2-day average (except Day 1) is the average of the total scores of that day and the previous day. The 2-day averages are: Day 2: 15, Day 3: 15.5, Day 4: 16, Day 5: 17.\nRanks (1 = highest score) table:\n- Akhil: Day 1: 1, Day 2: 2, Day 3: 2, Day 4: 3, Day 5: 3\n- Bimal: Day 1: 2, Day 2: 3, Day 3: 2, Day 4: 1, Day 5: 1\n- Chatur: Day 1: 3, Day 2: 1, Day 3: 1, Day 4: 2, Day 5: 2\nFacts:\n1. Chatur always scores in multiples of 3. His Day 2 score is the unique highest in the competition. His minimum is only on Day 1, matching Akhil's score on Day 4.\n2. Total score on Day 3 equals Day 4.\n3. Bimal's scores are the same on Day 1 and Day 3.\nWhat is Akhil's score on Day 1? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "7",
            "explanation": "Let daily total scores be T1, T2, T3, T4, T5.\n(T1+T2)/2 = 15 -> T1+T2 = 30.\n(T2+T3)/2 = 15.5 -> T2+T3 = 31.\n(T3+T4)/2 = 16 -> T3+T4 = 32.\n(T4+T5)/2 = 17 -> T4+T5 = 34.\nFrom Fact 2, T3 = T4 -> 2 * T3 = 32 -> T3 = 16, T4 = 16. Thus T2 = 31 - 16 = 15. T1 = 30 - 15 = 15. T5 = 34 - 16 = 18.\nUsing these daily sums and rank conditions: on Day 1, Akhil (Rank 1), Bimal (Rank 2), Chatur (Rank 3) sum to 15. Chatur's score is a multiple of 3. Solving the constraints yields Akhil's score = 7, Bimal = 5, Chatur = 3.",
            "hints": json.dumps([
                "Calculate the total scores for each day using the 2-day averages (T1+T2=30, T2+T3=31, T3+T4=32, T4+T5=34).",
                "Since T3 = T4, solve for T3 = 16 and T4 = 16, which gives the daily sums: T1=15, T2=15, T3=16, T4=16, T5=18.",
                "On Day 1, the scores sum to 15. Ranks are Akhil > Bimal > Chatur, and Chatur's score is a multiple of 3. Dedicate the scores to find Akhil = 7."
            ]),
            "gem_reward": 25,
            "chart_data": None
        },
        {
            "type": "shaft_5",
            "question_text": "Based on the random draw competition data (Akhil, Bimal, Chatur), what was the minimum possible total score of Bimal across all 5 days? (Provide only the integer value)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "25",
            "explanation": "Solving the full grid yields the minimum daily scores for Bimal:\n- Day 1: 5\n- Day 2: 1 or 2\n- Day 3: 5\n- Day 4: 7\n- Day 5: 7 or 8\nSumming the minimum values: 5 + 1 + 5 + 7 + 7 = 25.",
            "hints": json.dumps([
                "Write down Bimal's scores for each day based on the rank constraints.",
                "Bimal's scores on Day 1 and Day 3 are both 5. On Day 4, Bimal ranks 1st in a total of 16, which requires a score of 7.",
                "Sum Bimal's lowest possible daily scores across all five days."
            ]),
            "gem_reward": 25,
            "chart_data": None
        },
        {
            "type": "shaft_5",
            "question_text": "Based on the random draw competition data, who is definitely the participant that achieved the highest aggregate score across the five days?",
            "answer_type": "multiple_choice",
            "choices": [
                "A) Akhil",
                "B) Cannot be determined",
                "C) Bimal",
                "D) Chatur"
            ],
            "exact_answer": "D",
            "explanation": "Let's calculate the total scores for each participant:\n- Akhil totals 23, 24, or 25.\n- Bimal totals 25, 26, or 27.\n- Chatur totals exactly 30 (Day 1: 3, Day 2: 9, Day 3: 6, Day 4: 6, Day 5: 6).\nHence, Chatur definitely has the highest aggregate score.",
            "hints": json.dumps([
                "Evaluate the daily scores for Chatur, who always scores in multiples of 3.",
                "Chatur's daily scores are: Day 1: 3, Day 2: 9, Day 3: 6, Day 4: 6, Day 5: 6. Total = 30.",
                "Compare Chatur's total (30) with the maximum possible totals for Akhil (25) and Bimal (27)."
            ]),
            "gem_reward": 25,
            "chart_data": None
        }
    ]
    
    for p in puzzles_seed:
        choices_str = json.dumps(p["choices"]) if p["choices"] else None
        cursor.execute('''
            INSERT INTO puzzles (type, date_assigned, question_text, answer_type, choices, exact_answer, explanation, hints, gem_reward, chart_data, created_at)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p["type"], p["question_text"], p["answer_type"], choices_str, p["exact_answer"], p["explanation"], p["hints"], p["gem_reward"], p["chart_data"], now))

def get_user_profile():
    conn = get_db()
    profile = conn.execute('SELECT * FROM user_profile WHERE id = 1').fetchone()
    conn.close()
    return dict(profile) if profile else None

def update_gems(amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE user_profile SET gems = gems + ? WHERE id = 1', (amount,))
    cursor.execute('SELECT gems FROM user_profile WHERE id = 1')
    new_gems = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_gems

def add_depth(meters):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE user_profile SET depth_meters = depth_meters + ? WHERE id = 1', (meters,))
    cursor.execute('SELECT depth_meters FROM user_profile WHERE id = 1')
    new_depth = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_depth

def get_puzzles_by_shaft(shaft_type):
    conn = get_db()
    query = '''
        SELECT p.id, p.type, p.question_text, p.answer_type, p.choices, p.gem_reward, p.chart_data,
               COALESCE(ups.status, 'unsolved') as status,
               COALESCE(ups.hints_revealed, 0) as hints_revealed,
               COALESCE(ups.drillin_active, 0) as drillin_active,
               ups.user_notes, ups.attempts
         FROM puzzles p
         LEFT JOIN user_puzzle_status ups ON p.id = ups.puzzle_id
         WHERE p.type = ?
    '''
    rows = conn.execute(query, (shaft_type,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_puzzle_detail(puzzle_id):
    conn = get_db()
    # Get basic detail
    puzzle = conn.execute('SELECT * FROM puzzles WHERE id = ?', (puzzle_id,)).fetchone()
    if not puzzle:
        conn.close()
        return None
    
    puzzle_dict = dict(puzzle)
    
    # Get user status
    status = conn.execute('SELECT * FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
    status_dict = dict(status) if status else {"status": "unsolved", "hints_revealed": 0, "drillin_active": 0, "user_answer": None, "user_notes": None, "attempts": 0}
    
    # Hide solution fields if unsolved
    if status_dict["status"] != "solved":
        puzzle_dict.pop("exact_answer", None)
        puzzle_dict.pop("explanation", None)
        
        # Only show hints that have been unlocked
        all_hints = json.loads(puzzle_dict["hints"])
        revealed_count = status_dict["hints_revealed"]
        puzzle_dict["hints"] = all_hints[:revealed_count]
    else:
        # If solved, show all hints
        puzzle_dict["hints"] = json.loads(puzzle_dict["hints"])
        
    puzzle_dict["status_info"] = status_dict
    conn.close()
    return puzzle_dict

def get_puzzle_raw(puzzle_id):
    conn = get_db()
    puzzle = conn.execute('SELECT * FROM puzzles WHERE id = ?', (puzzle_id,)).fetchone()
    conn.close()
    return dict(puzzle) if puzzle else None

def unlock_hint_db(puzzle_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check current status
    status = cursor.execute('SELECT * FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
    
    if not status:
        cursor.execute('INSERT INTO user_puzzle_status (puzzle_id, status, hints_revealed) VALUES (?, "unsolved", 1)', (puzzle_id,))
        hints_revealed = 1
    else:
        status_dict = dict(status)
        hints_revealed = status_dict["hints_revealed"]
        if hints_revealed < 3:
            hints_revealed += 1
            cursor.execute('UPDATE user_puzzle_status SET hints_revealed = ? WHERE puzzle_id = ?', (hints_revealed, puzzle_id))
            
    # Deduct gems
    cursor.execute('UPDATE user_profile SET gems = gems - 3 WHERE id = 1')
    
    conn.commit()
    conn.close()
    
    return hints_revealed

def activate_drillin_db(puzzle_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check status
    status = cursor.execute('SELECT * FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
    if not status:
        cursor.execute('INSERT INTO user_puzzle_status (puzzle_id, status, drillin_active) VALUES (?, "unsolved", 1)', (puzzle_id,))
    else:
        cursor.execute('UPDATE user_puzzle_status SET drillin_active = 1 WHERE puzzle_id = ?', (puzzle_id,))
        
    # Deduct 2 gems
    cursor.execute('UPDATE user_profile SET gems = gems - 2 WHERE id = 1')
    
    # Record trigger message in drillin_messages
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO drillin_messages (puzzle_id, sender, message, created_at)
        VALUES (?, "drillin", "Drillin console active. Connection established. Ask me to clarify parameters or details of this mine problem, user. Note: I will not give you clues or answers.", ?)
    ''', (puzzle_id, now))
    
    conn.commit()
    conn.close()
    return True

def submit_answer_db(puzzle_id, user_answer):
    conn = get_db()
    cursor = conn.cursor()
    
    puzzle = cursor.execute('SELECT * FROM puzzles WHERE id = ?', (puzzle_id,)).fetchone()
    if not puzzle:
        conn.close()
        return {"error": "Puzzle not found"}
        
    puzzle_dict = dict(puzzle)
    exact_ans = puzzle_dict["exact_answer"].strip().lower()
    user_ans_clean = user_answer.strip().lower()
    
    # Exact check
    is_correct = (user_ans_clean == exact_ans)
    
    # Also support loose check for numerical values if formatting differs (e.g. "$1,500" vs "1500")
    if not is_correct and puzzle_dict["answer_type"] == "numeric":
        def sanitize_num(s):
            # Keep digits and periods
            return "".join(c for c in s if c.isdigit() or c == '.')
        try:
            is_correct = (float(sanitize_num(user_ans_clean)) == float(sanitize_num(exact_ans)))
        except ValueError:
            pass
            
    # Check current status
    status = cursor.execute('SELECT * FROM user_puzzle_status WHERE puzzle_id = ?', (puzzle_id,)).fetchone()
    
    now = datetime.utcnow().isoformat()
    if not status:
        cursor.execute('''
            INSERT INTO user_puzzle_status (puzzle_id, status, user_answer, solved_at, attempts)
            VALUES (?, ?, ?, ?, 1)
        ''', (puzzle_id, 'solved' if is_correct else 'unsolved', user_answer, now if is_correct else None))
    else:
        status_dict = dict(status)
        if status_dict["status"] == "solved":
            # Already solved
            conn.close()
            return {"correct": True, "already_solved": True, "explanation": puzzle_dict["explanation"]}
            
        cursor.execute('''
            UPDATE user_puzzle_status
            SET status = ?, user_answer = ?, solved_at = ?, attempts = attempts + 1
            WHERE puzzle_id = ?
        ''', ('solved' if is_correct else 'unsolved', user_answer, now if is_correct else None, puzzle_id))
        
    if is_correct:
        # Award gems and depth
        reward_gems = puzzle_dict["gem_reward"]
        cursor.execute('UPDATE user_profile SET gems = gems + ? WHERE id = 1', (reward_gems,))
        
        # Calculate depth reward
        # Coal=2m, Iron=5m, Gold=10m, Ruby=15m, Diamond=25m
        depth_map = {"shaft_1": 2, "shaft_2": 5, "shaft_3": 10, "shaft_4": 15, "shaft_5": 25, "daily": 5, "weekly": 15}
        depth_reward = depth_map.get(puzzle_dict["type"], 5)
        cursor.execute('UPDATE user_profile SET depth_meters = depth_meters + ? WHERE id = 1', (depth_reward,))
        
    conn.commit()
    conn.close()
    
    return {
        "correct": is_correct,
        "explanation": puzzle_dict["explanation"] if is_correct else None,
        "gem_reward": puzzle_dict["gem_reward"] if is_correct else 0
    }

def save_puzzle_notes_db(puzzle_id, notes):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE user_puzzle_status SET user_notes = ? WHERE puzzle_id = ?', (notes, puzzle_id))
    conn.commit()
    conn.close()
    return True

def get_archive_db():
    conn = get_db()
    query = '''
        SELECT p.id, p.type, p.question_text, p.answer_type, p.choices, p.gem_reward, p.chart_data, p.explanation, p.exact_answer,
               ups.user_notes, ups.solved_at, ups.user_answer
        FROM puzzles p
        JOIN user_puzzle_status ups ON p.id = ups.puzzle_id
        WHERE ups.status = 'solved'
        ORDER BY ups.solved_at DESC
    '''
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_drillin_chat_db(puzzle_id):
    conn = get_db()
    rows = conn.execute('SELECT * FROM drillin_messages WHERE puzzle_id = ? ORDER BY id ASC', (puzzle_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_drillin_message_db(puzzle_id, sender, message):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO drillin_messages (puzzle_id, sender, message, created_at) VALUES (?, ?, ?, ?)', (puzzle_id, sender, message, now))
    conn.commit()
    conn.close()
    return True

def save_new_puzzle(puzzle_type, question_text, answer_type, choices, exact_answer, explanation, hints, gem_reward, chart_data=None, date_assigned=None):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO puzzles (type, date_assigned, question_text, answer_type, choices, exact_answer, explanation, hints, gem_reward, chart_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (puzzle_type, date_assigned, question_text, answer_type, choices, exact_answer, explanation, hints, gem_reward, chart_data, now))
    puzzle_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return puzzle_id
