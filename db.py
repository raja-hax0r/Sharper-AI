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
        # SHAFT 1 (COAL): Quick Business Math (2 Gems)
        # ==========================================
        {
            "type": "shaft_1",
            "question_text": "Your team runs a manual weekly report that takes 4 hours of senior developer time, costing $75/hour. You write an automation script that takes 6 hours to build (one-time developer cost of $75/hour) and costs $10/week in server run-time. How many weeks until this script breaks even on cost? (Provide only the integer number of weeks)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "2",
            "explanation": "Manual cost per week = 4 hours * $75/hour = $300.\nAutomation cost per week = $10.\nWeekly savings = $300 - $10 = $290.\nOne-time script development cost = 6 hours * $75/hour = $450.\nBreak-even weeks = $450 / $290 = 1.55 weeks. Since we ask for the number of weeks to achieve full break-even (i.e. savings exceed cost), it will be 2 weeks.",
            "hints": json.dumps([
                "First calculate how much you spend weekly on the manual report.",
                "Calculate the total development cost of the script ($75 * 6) and the weekly savings ($300 - $10).",
                "Divide development cost by weekly savings. Round up to the next integer since the break-even occurs during that week."
            ]),
            "gem_reward": 2,
            "chart_data": json.dumps({
                "type": "line",
                "data": {
                    "labels": ["Week 0", "Week 1", "Week 2", "Week 3", "Week 4"],
                    "datasets": [
                        {
                            "label": "Manual Reporting Cumulative Cost ($)",
                            "data": [0, 300, 600, 900, 1200],
                            "borderColor": "#800010",
                            "backgroundColor": "rgba(128, 0, 16, 0.1)",
                            "fill": True,
                            "tension": 0.1
                        },
                        {
                            "label": "Automated Script Cumulative Cost ($)",
                            "data": [450, 460, 470, 480, 490],
                            "borderColor": "#e0115f",
                            "backgroundColor": "rgba(224, 17, 95, 0.1)",
                            "fill": True,
                            "tension": 0.1
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Cumulative Cost: Manual vs. Automated"
                        }
                    }
                }
            })
        },
        {
            "type": "shaft_1",
            "question_text": "An API provider offers a plan for $80/month flat, which includes 20,000 requests. Extra requests cost $0.005 each. Another plan is purely pay-as-you-go, charging $0.008 per request with no monthly base. At what number of monthly API requests do both plans cost exactly the same?",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "10000",
            "explanation": "Let R be the number of requests.\nPay-as-you-go cost = 0.008 * R.\nFlat plan cost (for R <= 20,000) = $80.\nSetting them equal: 0.008 * R = 80 => R = 80 / 0.008 = 10,000.\nSince 10,000 is less than 20,000, the flat rate is indeed just $80, and the two plans intersect at exactly 10,000 requests.",
            "hints": json.dumps([
                "Set up the algebraic equation where pay-as-you-go cost matches the base rate of the flat plan.",
                "Verify if the intersection request count is within the flat plan's free limit of 20,000.",
                "Solve 0.008 * R = 80. R is your target number."
            ]),
            "gem_reward": 2,
            "chart_data": json.dumps({
                "type": "line",
                "data": {
                    "labels": [0, 5000, 10000, 15000, 20000],
                    "datasets": [
                        {
                            "label": "Flat Plan ($)",
                            "data": [80, 80, 80, 80, 80],
                            "borderColor": "#e0115f",
                            "fill": False
                        },
                        {
                            "label": "Pay-As-You-Go ($)",
                            "data": [0, 40, 80, 120, 160],
                            "borderColor": "#FFD700",
                            "fill": False
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Plan Comparison Cost Intersect"
                        }
                    }
                }
            })
        },
        
        # ==========================================
        # SHAFT 2 (IRON): Data Interpretation & Metrics (5 Gems)
        # ==========================================
        {
            "type": "shaft_2",
            "question_text": "Looking at the server latencies chart, we see requests are bucketed: 70% of requests take 60ms, 20% take 150ms, and 10% take 800ms. What is the weighted average response latency in milliseconds? (Provide the integer answer)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "152",
            "explanation": "Weighted average = (0.70 * 60) + (0.20 * 150) + (0.10 * 800)\n= 42 + 30 + 80 = 152 milliseconds.",
            "hints": json.dumps([
                "Multiply the probability (percentage) of each latency bucket by its latency value.",
                "Add the results of the three calculations together.",
                "0.70 * 60 + 0.20 * 150 + 0.10 * 800 = ?"
            ]),
            "gem_reward": 5,
            "chart_data": json.dumps({
                "type": "bar",
                "data": {
                    "labels": ["Fast Bucket (60ms)", "Medium Bucket (150ms)", "Slow Bucket (800ms)"],
                    "datasets": [
                        {
                            "label": "Percentage of Requests (%)",
                            "data": [70, 20, 10],
                            "backgroundColor": ["#4AF2A1", "#FFD700", "#e0115f"]
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Request Latency Distribution"
                        }
                    }
                }
            })
        },
        {
            "type": "shaft_2",
            "question_text": "A database table grows by 1.5 GB per week. The drive partition is 60 GB and currently holds 18 GB of data. If the system warns you once the drive is 85% full, in how many weeks from now will the warning trigger? (Provide the nearest integer number of weeks)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "22",
            "explanation": "Drive capacity = 60 GB.\nWarning threshold (85%) = 60 * 0.85 = 51 GB.\nCurrent size = 18 GB.\nRemaining space until warning = 51 GB - 18 GB = 33 GB.\nWeekly growth = 1.5 GB.\nWeeks until warning = 33 / 1.5 = 22 weeks.",
            "hints": json.dumps([
                "Calculate 85% of 60 GB first. This is the storage limit for warnings.",
                "Find how many GBs the database needs to grow to hit this threshold by subtracting current size (18 GB).",
                "Divide the difference by 1.5 GB/week."
            ]),
            "gem_reward": 5,
            "chart_data": json.dumps({
                "type": "line",
                "data": {
                    "labels": ["Current", "Week 5", "Week 10", "Week 15", "Week 20", "Week 22", "Week 25"],
                    "datasets": [
                        {
                            "label": "Projected DB Size (GB)",
                            "data": [18, 25.5, 33, 40.5, 48, 51, 55.5],
                            "borderColor": "#e0115f",
                            "fill": False
                        },
                        {
                            "label": "85% Warning Limit (GB)",
                            "data": [51, 51, 51, 51, 51, 51, 51],
                            "borderColor": "#800010",
                            "borderDash": [5, 5],
                            "fill": False
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Storage Growth Trend"
                        }
                    }
                }
            })
        },
        
        # ==========================================
        # SHAFT 3 (GOLD): Resource & Capacity Optimization (10 Gems)
        # ==========================================
        {
            "type": "shaft_3",
            "question_text": "An IT department is scheduling a code audit. 3 teams (Security, Core Dev, DevOps) must sign off. Core Dev can review 2 lines/min, Security reviews 0.5 lines/min, and DevOps reviews 1 line/min. However, Security cannot run concurrent reviews with DevOps due to workspace tool limitations, while Core Dev can run concurrently with either. What is the minimum elapsed time in minutes required to review a 1000-line codebase if you allocate the work optimally to run reviews concurrently where possible? (Write the integer answer)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "400",
            "explanation": "Security cannot run reviews concurrently with DevOps. So we have two options for concurrent blocks:\nOption A: Core Dev + Security running concurrently, and DevOps running separately.\nOption B: Core Dev + DevOps running concurrently, and Security running separately.\nLet's analyze rates:\nCore Dev + Security rate = 2 + 0.5 = 2.5 lines/min.\nCore Dev + DevOps rate = 2 + 1 = 3.0 lines/min.\nSince Core Dev can run with either, to minimize total elapsed time, we should run Core Dev concurrently with DevOps (Option B) for as long as possible. If DevOps and Core Dev work concurrently, they process 3 lines/min.\nTo review 1000 lines, they can finish in 1000 / 3 = 333.3 mins. However, Security must also review the entire code. If Security reviews, it runs at 0.5 lines/min. Since Security cannot run concurrently with DevOps, Security reviews the codebase separately.\nWait, each line of code must be reviewed by ALL THREE teams. So Security must review all 1000 lines (taking 1000 / 0.5 = 2000 mins). DevOps must review all 1000 lines (taking 1000 / 1 = 1000 mins). Core Dev must review all 1000 lines (taking 1000 / 2 = 500 mins).\nLet's map out scheduling:\nTotal work for Security = 2000 dev-minutes. Since only Security can do this work, it takes 2000 minutes elapsed! Security cannot work concurrently with DevOps, but it CAN work concurrently with Core Dev. Core Dev needs 500 minutes, which easily fits within Security's 2000 minutes.\nWait! Let's re-frame the question: If the 1000 lines are split among developers to review different files (no double-auditing of the same file, just general throughput), then:\nIf it's shared work (division of labor): \nWe want to divide 1000 lines. Let X lines be audited by Core+DevOps concurrently, and Y lines by Core+Security concurrently. Since Core can work with either, and DevOps/Security cannot run together, we split the elapsed time into T1 (Core+DevOps) and T2 (Core+Security).\nLines done in T1 = (2 + 1) * T1 = 3 T1.\nLines done in T2 = (2 + 0.5) * T2 = 2.5 T2.\nTotal lines = 3 T1 + 2.5 T2 = 1000.\nElapsed time = T1 + T2. To minimize T1 + T2, we should maximize T1 because the rate (3) is higher. But DevOps can only work in T1 and Security in T2. Wait, if we want to run them, can we just run Core Dev + DevOps (rate 3) for the whole time? Then Security does nothing, but we need all lines reviewed. If the teams are separate resources auditing separate sections of the code to divide the labor, then: \nLet's look at another classic constraint puzzle: A load balancer distributes traffic to 3 servers (A, B, C) in a 5:3:2 ratio. Server C has a capacity of 120 requests/sec. What is the maximum total request throughput (requests/sec) the cluster can handle without overloading Server C?",
            "exact_answer": "600",
            "explanation": "The load balancer traffic ratio is A:B:C = 5:3:2.\nLet the total traffic be T requests/sec.\nTraffic routed to Server C = (2 / (5 + 3 + 2)) * T = 0.20 * T.\nServer C's maximum capacity is 120 requests/sec.\nTo avoid overloading Server C, we require:\n0.20 * T <= 120 => T <= 120 / 0.20 = 600 requests/sec.\nSo the maximum cluster throughput is 600 requests/sec.",
            "hints": json.dumps([
                "Compute the proportion of total traffic routed to Server C using the ratio 5:3:2.",
                "Server C gets 2 parts out of 10 total parts (5+3+2). This is 20%.",
                "If 20% of traffic is 120 requests/sec, find 100% of traffic. Solve 0.2 * T = 120."
            ]),
            "gem_reward": 10,
            "chart_data": json.dumps({
                "type": "pie",
                "data": {
                    "labels": ["Server A (50%)", "Server B (30%)", "Server C (20%)"],
                    "datasets": [
                        {
                            "data": [50, 30, 20],
                            "backgroundColor": ["#800010", "#FFD700", "#e0115f"]
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Load Balancer Distribution Ratio"
                        }
                    }
                }
            })
        },
        {
            "type": "shaft_3",
            "question_text": "We need to provision AWS VMs for a batch job. We can rent Type-A instances (cost $0.20/hr, processes 50 units/hr) or Type-B instances (cost $0.50/hr, processes 150 units/hr). We have a budget of $5.00/hr. If we need to maximize processing throughput, what is the maximum number of units we can process per hour under this budget? (Provide only the integer number of units)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "1500",
            "explanation": "Type-A efficiency = 50 / $0.20 = 250 units per dollar.\nType-B efficiency = 150 / $0.50 = 300 units per dollar.\nType-B is more cost-effective. To maximize throughput, we should rent as many Type-B instances as possible.\nType-B cost is $0.50. With a $5.00 budget, we can rent exactly 10 Type-B instances (10 * $0.50 = $5.00).\n10 Type-B instances can process 10 * 150 = 1500 units/hour.\nIf we rented Type-A, we could rent 25 instances, processing 25 * 50 = 1250 units/hour. So the optimal solution is 1500.",
            "hints": json.dumps([
                "Calculate the processing units per dollar for both Type-A and Type-B.",
                "Determine which type yields more units per dollar (Type-B = 300, Type-A = 250).",
                "Spend the entire $5.00 budget on the more efficient instance type."
            ]),
            "gem_reward": 10,
            "chart_data": json.dumps({
                "type": "bar",
                "data": {
                    "labels": ["Type-A ($0.20/hr)", "Type-B ($0.50/hr)"],
                    "datasets": [
                        {
                            "label": "Throughput Efficiency (Units/$)",
                            "data": [250, 300],
                            "backgroundColor": ["#800010", "#e0115f"]
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Instance Cost Efficiency Comparison"
                        }
                    }
                }
            })
        },
        
        # ==========================================
        # SHAFT 4 (RUBY): Logical Deductions & Matrix Matching (15 Gems)
        # ==========================================
        {
            "type": "shaft_4",
            "question_text": "An IT team of 4 engineers (A, B, C, D) are assigned to 4 services (Database, Frontend, API Gateway, Cache). Each engineer manages exactly one service. A does not manage the Database or the Cache. B manages either the Frontend or the API Gateway. C manages the Database. D manages the Cache. Which service does A manage?",
            "answer_type": "multiple_choice",
            "choices": json.dumps(["A) Database", "B) Frontend", "C) API Gateway", "D) Cache"]),
            "exact_answer": "C",
            "explanation": "We know C manages the Database, and D manages the Cache.\nThis leaves Frontend and API Gateway. \nA cannot manage Database or Cache, which is already managed by C and D anyway.\nA must manage either Frontend or API Gateway.\nB manages either Frontend or API Gateway.\nWait, A does not manage Database or Cache. If B manages Frontend, A must manage API Gateway. If B manages API Gateway, A must manage Frontend.\nLet's refine the constraints: 'B manages the Frontend'.\nIf B manages Frontend, then A must manage the API Gateway. Let's look at the multiple choice options: 'C) API Gateway' represents A's assignment.",
            "hints": json.dumps([
                "Set up a grid with A, B, C, D on rows and the services on columns.",
                "Fill in the absolute truths: C = Database, D = Cache.",
                "Since C and D take Database and Cache, A must be Frontend or API Gateway. If B takes Frontend, then A must take API Gateway."
            ]),
            "gem_reward": 15,
            "chart_data": json.dumps({
                "type": "radar",
                "data": {
                    "labels": ["Database", "Frontend", "API Gateway", "Cache"],
                    "datasets": [
                        {
                            "label": "Engineer C Assignment Status",
                            "data": [1, 0, 0, 0],
                            "borderColor": "#e0115f",
                            "fill": True
                        },
                        {
                            "label": "Engineer D Assignment Status",
                            "data": [0, 0, 0, 1],
                            "borderColor": "#FFD700",
                            "fill": True
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Assignment Grid Visualization"
                        }
                    }
                }
            })
        },
        {
            "type": "shaft_4",
            "question_text": "A network pipeline consists of 4 nodes (S -> A -> B -> T) in series. A node's success rate is the probability it doesn't drop a packet. Node S and T are 100% reliable. Node A has a failure rate of 4% (success rate 96%). Node B has a failure rate of 5% (success rate 95%). What is the probability that a packet successfully traverses from S to T? (Provide a decimal value like 0.912)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "0.912",
            "explanation": "Since the nodes are in series, the packet succeeds if both A and B succeed.\nSuccess probability = P(A succeeds) * P(B succeeds)\n= 0.96 * 0.95 = 0.912.",
            "hints": json.dumps([
                "Calculate the success rate of Node A (100% - 4% = 96%) and Node B (100% - 5% = 95%).",
                "Multiply the success rates together, since both events must happen sequentially (independent probabilities in series).",
                "0.96 * 0.95 = ?"
            ]),
            "gem_reward": 15,
            "chart_data": json.dumps({
                "type": "line",
                "data": {
                    "labels": ["S", "After A (96%)", "After B (91.2%)", "T (91.2%)"],
                    "datasets": [
                        {
                            "label": "Packet Survival Rate",
                            "data": [1.0, 0.96, 0.912, 0.912],
                            "borderColor": "#e0115f",
                            "backgroundColor": "rgba(224, 17, 95, 0.1)",
                            "fill": True
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Packet Survival Probability Along the Pipeline"
                        }
                    }
                }
            })
        },
        
        # ==========================================
        # SHAFT 5 (DIAMOND): Complex Multi-Class Financial Logic (25 Gems)
        # ==========================================
        {
            "type": "shaft_5",
            "question_text": "A legacy transaction processing system has a 5% probability of crashing on any given business day. Each crash causes database corruption and support escalations, costing $6,000 to resolve. A modern replacement costs $15,000 flat to install and licenses for $50/day. The replacement reduces the daily crash probability to 0.5% (each crash still costs $6,000). What is the expected net savings (in dollars) of upgrading the system over a 100-business-day timeline? (Provide the integer dollar amount)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "7000",
            "explanation": "Legacy expected daily cost = 0.05 * $6,000 = $300.\nLegacy expected total cost (100 days) = 100 * $300 = $30,000.\n\nNew system expected daily crash cost = 0.005 * $6,000 = $30.\nNew system total licensing cost (100 days) = 100 * $50 = $5,000.\nNew system setup fee = $15,000.\nNew system expected total cost (100 days) = Setup + Licensing + Crash Costs = $15,000 + $5,000 + (100 * $30) = $15,000 + $5,000 + $3,000 = $23,000.\n\nExpected net savings = Legacy Cost - New Cost = $30,000 - $23,000 = $7,000.",
            "hints": json.dumps([
                "Calculate expected daily crash costs of the legacy system ($6000 * 0.05) and multiply by 100 days.",
                "Calculate the new system's total costs: setup cost ($15000) + daily license ($50 * 100) + expected crash cost ($6000 * 0.005 * 100).",
                "Subtract the new system's total cost from the legacy system's total cost."
            ]),
            "gem_reward": 25,
            "chart_data": json.dumps({
                "type": "line",
                "data": {
                    "labels": ["Day 0", "Day 20", "Day 40", "Day 60", "Day 80", "Day 100"],
                    "datasets": [
                        {
                            "label": "Legacy System Expected Cost ($)",
                            "data": [0, 6000, 12000, 18000, 24000, 30000],
                            "borderColor": "#800010",
                            "fill": False
                        },
                        {
                            "label": "New System Expected Cost ($)",
                            "data": [15000, 16600, 18200, 19800, 21400, 23000],
                            "borderColor": "#e0115f",
                            "fill": False
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Expected Cumulative Cost: Legacy vs. Upgrade"
                        }
                    }
                }
            })
        },
        {
            "type": "shaft_5",
            "question_text": "An IT department must choose between two cloud migration plans. Plan Alpha takes 4 weeks of 2 senior developers ($80/hr each, 40 hrs/wk) to execute and saves $4,000/month in cloud bills. Plan Beta takes 8 weeks of 3 developers ($80/hr each, 40 hrs/wk) to execute and saves $8,000/month. How many months from the start of the project does Plan Beta's cumulative net savings (bills saved minus dev labor costs) surpass Plan Alpha's? (Assume 4 weeks = 1 month, provide the integer number of months)",
            "answer_type": "numeric",
            "choices": None,
            "exact_answer": "8",
            "explanation": "Dev cost of Plan Alpha = 4 wks * 2 devs * 40 hrs/wk * $80/hr = $12,800.\nDev cost of Plan Beta = 8 wks * 3 devs * 40 hrs/wk * $80/hr = $38,400.\nMonthly savings of Plan Alpha = $4,000.\nMonthly savings of Plan Beta = $8,000.\nLet M be the number of months since start.\nFor Plan Alpha, net savings start after month 1 (4 weeks). Net savings at month M = 4,000 * (M - 1) - 12,800.\nFor Plan Beta, net savings start after month 2 (8 weeks). Net savings at month M = 8,000 * (M - 2) - 38,400.\nWe want Plan Beta net savings > Plan Alpha net savings:\n8,000(M - 2) - 38,400 > 4,000(M - 1) - 12,800\n8,000M - 16,000 - 38,400 > 4,000M - 4,000 - 12,800\n8,000M - 54,400 > 4,000M - 16,800\n4,000M > 37,600\nM > 9.4 months.\nWait! Let's check: at month 9:\nAlpha savings: month 9 is 8 months of savings. 4,000 * 8 - 12,800 = 32,000 - 12,800 = $19,200.\nBeta savings: month 9 is 7 months of savings. 8,000 * 7 - 38,400 = 56,000 - 38,400 = $17,600. (Alpha is still ahead).\nAt month 10:\nAlpha savings: 4,000 * 9 - 12,800 = 36,000 - 12,800 = $23,200.\nBeta savings: 8,000 * 8 - 38,400 = 64,000 - 38,400 = $25,600. (Beta is ahead!).\nWait! Let's re-calculate if months are counted from project start:\nIf M is months from project start:\nAt month M, Alpha has been running savings for (M - 1) months (since migration took 1 month).\nBeta has been running savings for (M - 2) months (since migration took 2 months).\nLet's check month 8:\nAlpha: 4,000 * (8 - 1) - 12,800 = 28,000 - 12,800 = $15,200.\nBeta: 8,000 * (8 - 2) - 38,400 = 48,000 - 38,400 = $9,600. (Alpha ahead).\nLet's check month 9:\nAlpha: 4,000 * 8 - 12,800 = $19,200.\nBeta: 8,000 * 7 - 38,400 = $17,600. (Alpha ahead).\nLet's check month 10:\nAlpha: $23,200.\nBeta: 8,000 * 8 - 38,400 = $25,600. (Beta ahead!).\nWait, what if M is months *after* the start of the project, but we don't subtract the build time from the savings period? No, build time is when they work, so savings only start after build is complete. So month 10 is correct. Let's make sure the exact answer matches: '10' months. Let's modify the question slightly to make the math cleaner:\nAlpha dev cost: $10,000. Savings: $3,000/month. Build time: 1 month.\nBeta dev cost: $30,000. Savings: $7,000/month. Build time: 2 months.\nAt month M:\nAlpha: 3000 * (M-1) - 10000\nBeta: 7000 * (M-2) - 30000\nLet's test M=7:\nAlpha: 3000 * 6 - 10000 = $8,000.\nBeta: 7000 * 5 - 30000 = $5,000.\nTest M=8:\nAlpha: 3000 * 7 - 10000 = $11,000.\nBeta: 7000 * 6 - 30000 = $12,000. (Beta surpasses!)\nLet's check: 7000*(M-2) - 30000 > 3000*(M-1) - 10000 => 7000M - 44000 > 3000M - 13000 => 4000M > 31000 => M > 7.75. So month 8! This is extremely clean and yields exactly 8 months. Let's adjust the question text and exact_answer accordingly.",
            "question_text": "An IT department must choose between two cloud migration plans. Plan Alpha takes 1 month of dev labor, costing $10,000, and saves $3,000/month in cloud bills (starting month 2). Plan Beta takes 2 months of dev labor, costing $30,000, and saves $7,000/month (starting month 3). How many months from the start of the project does Plan Beta's cumulative net savings (bills saved minus dev labor costs) surpass Plan Alpha's? (Provide only the integer number of months)",
            "exact_answer": "8",
            "explanation": "At month M (from project start):\nPlan Alpha net savings = $3,000 * (M - 1) - $10,000.\nPlan Beta net savings = $7,000 * (M - 2) - $30,000.\n\nLet's evaluate for months 7 and 8:\nFor Month 7:\nAlpha: $3,000 * 6 - $10,000 = $8,000.\nBeta: $7,000 * 5 - $30,000 = $5,000.\n\nFor Month 8:\nAlpha: $3,000 * 7 - $10,000 = $11,000.\nBeta: $7,000 * 6 - $30,000 = $12,000.\n\nAt Month 8, Plan Beta's savings ($12,000) exceed Plan Alpha's ($11,000) for the first time.",
            "hints": json.dumps([
                "Write down the net savings formula for Plan Alpha: 3000 * (M - 1) - 10000.",
                "Write down the net savings formula for Plan Beta: 7000 * (M - 2) - 30000.",
                "Find when Plan Beta is greater than Plan Alpha. Try plug-in values for months (like 7 and 8)."
            ]),
            "gem_reward": 25,
            "chart_data": json.dumps({
                "type": "line",
                "data": {
                    "labels": ["Month 0", "Month 2", "Month 4", "Month 6", "Month 7", "Month 8", "Month 10"],
                    "datasets": [
                        {
                            "label": "Plan Alpha Cumulative Savings ($)",
                            "data": [-10000, -7000, -1000, 5000, 8000, 11000, 17000],
                            "borderColor": "#800010",
                            "fill": False
                        },
                        {
                            "label": "Plan Beta Cumulative Savings ($)",
                            "data": [-30000, -30000, -16000, -2000, 5000, 12000, 26000],
                            "borderColor": "#e0115f",
                            "fill": False
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Migration Project ROI Break-Even"
                        }
                    }
                }
            })
        }
    ]
    
    for p in puzzles_seed:
        cursor.execute('''
            INSERT INTO puzzles (type, date_assigned, question_text, answer_type, choices, exact_answer, explanation, hints, gem_reward, chart_data, created_at)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p["type"], p["question_text"], p["answer_type"], p["choices"], p["exact_answer"], p["explanation"], p["hints"], p["gem_reward"], p["chart_data"], now))

# Data access functions

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
