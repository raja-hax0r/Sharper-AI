// APP STATE
const state = {
    depth: 0,
    gems: 17,
    dailyPuzzleId: null,
    weeklyPuzzleId: null,
    dailySolved: false,
    weeklySolved: false,
    activePuzzle: null,
    activeShaft: null,
    drillinChatInterval: null,
    currentChart: null
};

// SELECT ELEMENTS
const el = {
    headerDepth: document.getElementById('header-depth'),
    headerGems: document.getElementById('header-gems'),
    musicBtn: document.getElementById('music-btn'),
    meinschaftSpeech: document.getElementById('meinschaft-speech'),
    
    // Views
    viewHome: document.getElementById('view-home'),
    viewShaft: document.getElementById('view-shaft'),
    viewSolve: document.getElementById('view-solve'),
    viewArchive: document.getElementById('view-archive'),
    viewSettings: document.getElementById('view-settings'),
    
    // Shaft view
    shaftTitle: document.getElementById('shaft-title'),
    shaftDescription: document.getElementById('shaft-description'),
    shaftQuestions: document.getElementById('shaft-questions'),
    btnDigDeeper: document.getElementById('btn-dig-deeper'),
    
    // Solve view
    solveTitle: document.getElementById('solve-title'),
    puzzleDifficultyTag: document.getElementById('puzzle-difficulty-tag'),
    puzzleRewardTag: document.getElementById('puzzle-reward-tag'),
    puzzleQuestion: document.getElementById('puzzle-question'),
    puzzleVisualCard: document.getElementById('puzzle-visual-card'),
    puzzleChart: document.getElementById('puzzle-chart'),
    multipleChoiceContainer: document.getElementById('multiple-choice-container'),
    textInputContainer: document.getElementById('text-input-container'),
    userAnswerInput: document.getElementById('user-answer-input'),
    solveAttempts: document.getElementById('solve-attempts'),
    solveUnsolvedSection: document.getElementById('solve-unsolved-section'),
    solveSolvedSection: document.getElementById('solve-solved-section'),
    solveGemsRewarded: document.getElementById('solve-gems-rewarded'),
    solveExplanation: document.getElementById('solve-explanation'),
    solveUserNotes: document.getElementById('solve-user-notes'),
    hintsRevealedList: document.getElementById('hints-revealed-list'),
    btnBuyHint: document.getElementById('btn-buy-hint'),
    hintsCardSection: document.getElementById('hints-card-section'),
    
    // Drillin Chat
    drillinStatusTag: document.getElementById('drillin-status-tag'),
    drillinChatLog: document.getElementById('drillin-chat-log'),
    drillinBuyBox: document.getElementById('drillin-buy-box'),
    drillinInputBox: document.getElementById('drillin-input-box'),
    drillinMessageInput: document.getElementById('drillin-message-input'),
    
    // Archive
    archiveListContainer: document.getElementById('archive-list-container'),
    
    // Settings
    volumeSlider: document.getElementById('volume-slider')
};

// AUDIO BGM
const bgm = document.getElementById('bgm');
let bgmInitialized = false;

// INITIALIZE APP
document.addEventListener('DOMContentLoaded', () => {
    app.init();
    
    // Initialize audio play on first click (browser autoplay policy)
    document.body.addEventListener('click', () => {
        if (!bgmInitialized) {
            bgmInitialized = true;
            // Play if it is toggled on (by default let's start it muted/off as per user setting)
            if (localStorage.getItem('bgm_enabled') === 'true') {
                bgm.play().then(() => {
                    el.musicBtn.classList.remove('text-red');
                    el.musicBtn.classList.add('text-green');
                    el.musicBtn.innerText = "🎵 ON";
                }).catch(err => console.log("Audio play blocked: ", err));
            }
        }
    }, { once: true });
});

const app = {
    init() {
        // Load settings from local storage
        const musicEnabled = localStorage.getItem('bgm_enabled') !== 'false'; // default true
        localStorage.setItem('bgm_enabled', musicEnabled);
        
        const crtEnabled = localStorage.getItem('crt_enabled') !== 'false'; // default true
        localStorage.setItem('crt_enabled', crtEnabled);
        
        if (!crtEnabled) {
            document.querySelector('.scanlines').classList.add('hidden');
            document.querySelector('.crt-overlay').classList.add('hidden');
        }
        
        const volume = localStorage.getItem('bgm_volume') || '0.5';
        bgm.volume = parseFloat(volume);
        el.volumeSlider.value = volume;

        if (musicEnabled) {
            el.musicBtn.classList.remove('text-red');
            el.musicBtn.classList.add('text-green');
            el.musicBtn.innerText = "🎵 ON";
            // Browser autoplay might block it on first load, handled by body click listener
        } else {
            el.musicBtn.classList.remove('text-green');
            el.musicBtn.classList.add('text-red');
            el.musicBtn.innerText = "🎵 OFF";
            bgm.pause();
        }

        // Fetch User Status
        this.loadStatus();
    },

    // NAVIGATION
    showView(viewName) {
        // Hide all views
        el.viewHome.classList.remove('active');
        el.viewShaft.classList.remove('active');
        el.viewSolve.classList.remove('active');
        el.viewArchive.classList.remove('active');
        el.viewSettings.classList.remove('active');
        
        // Clear drillin chat interval if moving away from solve
        if (viewName !== 'solve' && state.drillinChatInterval) {
            clearInterval(state.drillinChatInterval);
            state.drillinChatInterval = null;
        }

        // Show targets
        if (viewName === 'home') el.viewHome.classList.add('active');
        if (viewName === 'shaft') el.viewShaft.classList.add('active');
        if (viewName === 'solve') el.viewSolve.classList.add('active');
        if (viewName === 'archive') el.viewArchive.classList.add('active');
        if (viewName === 'settings') el.viewSettings.classList.add('active');
        
        // Scroll to top
        document.querySelector('.app-main').scrollTop = 0;
    },

    showHome() {
        this.loadStatus();
        this.showView('home');
    },

    // LOAD PROFILE STATS
    async loadStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            state.depth = data.depth_meters;
            state.gems = data.gems;
            state.dailyPuzzleId = data.daily_puzzle_id;
            state.weeklyPuzzleId = data.weekly_puzzle_id;
            state.dailySolved = data.daily_solved;
            state.weeklySolved = data.weekly_solved;
            
            // Update UI Gauges
            el.headerDepth.innerText = `${state.depth}m`;
            el.headerGems.innerText = `💎 ${state.gems}`;
            
            // Update Badges
            const dailyBadge = document.getElementById('daily-solved-badge');
            if (state.dailySolved) {
                dailyBadge.className = "badge badge-solved";
                dailyBadge.innerText = "SOLVED";
            } else {
                dailyBadge.className = "badge badge-unsolved";
                dailyBadge.innerText = "UNSOLVED";
            }
            
            const weeklyBadge = document.getElementById('weekly-solved-badge');
            if (state.weeklySolved) {
                weeklyBadge.className = "badge badge-solved";
                weeklyBadge.innerText = "SOLVED";
            } else {
                weeklyBadge.className = "badge badge-unsolved";
                weeklyBadge.innerText = "UNSOLVED";
            }
            
            // Character reaction
            this.updateSpeechBubble();
        } catch (err) {
            console.error("Error loading status:", err);
        }
    },

    updateSpeechBubble() {
        let msg = "";
        if (state.dailySolved && state.weeklySolved) {
            msg = `"Unbelievable, Herr Pariah. The daily quota is extracted and the weekly haul is locked. Your boss won't know what hit him in the board room."`;
        } else if (state.dailySolved) {
            msg = `"Today's vein is dry. You've dug out your daily ore, but the weekly deep expedition remains waiting. Grab your pick."`;
        } else if (state.gems < 5) {
            msg = `"Resource levels are dangerously thin, Pariah. Less than 5 gems! Enter Shaft I or II to extract easy gems, or face logic bankruptcy."`;
        } else if (state.depth > 100) {
            msg = `"Over 100 meters deep! That is some serious structural thinking. Let's keep digging before the mental gears freeze up."`;
        } else {
            msg = `"Ah, another shift in the mindshaft, Herr Pariah. Let's sharpen the mental pickaxe. Pick a shaft or start the daily challenge!"`;
        }
        el.meinschaftSpeech.innerText = msg;
    },

    // MINESHAFT VIEW
    async enterShaft(shaftType) {
        state.activeShaft = shaftType;
        
        const shaftNames = {
            "shaft_1": "SHAFT I: COAL MINE (MATH)",
            "shaft_2": "SHAFT II: IRON MINE (METRICS)",
            "shaft_3": "SHAFT III: GOLD MINE (OPTIMIZATION)",
            "shaft_4": "SHAFT IV: RUBY MINE (LOGIC)",
            "shaft_5": "SHAFT V: DIAMOND MINE (ROI SCENARIOS)"
        };
        
        const shaftDescriptions = {
            "shaft_1": "Quick mental arithmetic, break-even speeds, cost margins. This exercises fast, raw estimates of money and hourly savings.",
            "shaft_2": "Data calculations, average response times, database safety margins. This builds intuitive chart reading capacities.",
            "shaft_3": "Resource allocation, hardware budget bounds, capacity bottlenecks. This sharpens server routing and scheduling logic.",
            "shaft_4": "Multi-variable logical mapping, reliability grids, dependency schedules. This builds structure out of complex constraints.",
            "shaft_5": "Comprehensive multi-domain business evaluations, combining ROI, support estimates, crash rates, and cloud license costs."
        };
        
        el.shaftTitle.innerText = shaftNames[shaftType];
        el.shaftDescription.innerText = shaftDescriptions[shaftType];
        
        // Show loading
        el.shaftQuestions.innerHTML = `<div class="text-muted font-xs">Excavating available sites...</div>`;
        this.showView('shaft');
        
        try {
            const res = await fetch(`/api/shaft/${shaftType}`);
            const data = await res.json();
            this.renderQuestionsList(data);
        } catch (err) {
            el.shaftQuestions.innerHTML = `<div class="text-red font-xs">Error opening shaft: ${err.message}</div>`;
        }
    },

    renderQuestionsList(questions) {
        if (questions.length === 0) {
            el.shaftQuestions.innerHTML = `<div class="text-muted font-sm">No puzzle extractions here yet. Run 'Dig Deeper' to generate one!</div>`;
            return;
        }
        
        el.shaftQuestions.innerHTML = '';
        questions.forEach((q, idx) => {
            const item = document.createElement('div');
            item.className = 'q-item';
            item.onclick = () => this.loadPuzzle(q.id);
            
            const titleText = q.type.replace('_', ' ').toUpperCase() + ` - SITE #${idx + 1}`;
            const snippet = q.question_text.length > 90 ? q.question_text.substring(0, 90) + '...' : q.question_text;
            
            const solvedBadge = q.status === 'solved' 
                ? `<span class="badge badge-solved">SOLVED</span>` 
                : `<span class="badge badge-unsolved">UNSOLVED</span>`;
                
            item.innerHTML = `
                <div>
                    <div class="q-item-title">${titleText} ${solvedBadge}</div>
                    <div class="q-item-text text-muted">${snippet}</div>
                </div>
                <div class="text-green font-retro font-sm">💎 ${q.gem_reward}</div>
            `;
            el.shaftQuestions.appendChild(item);
        });
    },

    async generateNewQuestion() {
        el.btnDigDeeper.disabled = true;
        el.btnDigDeeper.innerText = "DIGGING... PLEASE STAND BY";
        
        try {
            const res = await fetch(`/api/shaft/${state.activeShaft}/generate`, { method: 'POST' });
            if (!res.ok) throw new Error(await res.text());
            
            const data = await res.json();
            // Re-load the shaft list
            this.enterShaft(state.activeShaft);
        } catch (err) {
            alert("Error generating new puzzle: " + err.message);
        } finally {
            el.btnDigDeeper.disabled = false;
            el.btnDigDeeper.innerText = "⛏️ DIG DEEPER (NEW PUZZLE)";
        }
    },

    // SOLVE PUZZLE VIEW
    async loadDailyPuzzle() {
        if (!state.dailyPuzzleId) await this.loadStatus();
        this.loadPuzzle(state.dailyPuzzleId);
    },

    async loadWeeklyPuzzle() {
        if (!state.weeklyPuzzleId) await this.loadStatus();
        this.loadPuzzle(state.weeklyPuzzleId);
    },

    async loadPuzzle(puzzleId) {
        this.showView('solve');
        
        // Reset Inputs
        el.userAnswerInput.value = '';
        el.solveUnsolvedSection.classList.remove('hidden');
        el.solveSolvedSection.classList.add('hidden');
        el.multipleChoiceContainer.classList.add('hidden');
        el.textInputContainer.classList.add('hidden');
        el.hintsRevealedList.innerHTML = '';
        el.btnBuyHint.disabled = false;
        el.btnBuyHint.innerText = "🔓 EXTRACT HINT (COSTS 💎 3)";
        
        el.puzzleQuestion.innerHTML = `<div class="text-muted font-xs">Reading drill cores...</div>`;
        
        try {
            const res = await fetch(`/api/puzzle/${puzzleId}`);
            if (!res.ok) throw new Error(await res.text());
            const q = await res.json();
            state.activePuzzle = q;
            
            // Bind Details
            el.solveTitle.innerText = q.type.replace('_', ' ').toUpperCase() + ` EXTRACTION`;
            el.puzzleDifficultyTag.innerText = `DIFFICULTY: ${q.type.replace('_', ' ').toUpperCase()}`;
            el.puzzleRewardTag.innerText = `💎 ${q.gem_reward} Gems`;
            el.puzzleQuestion.innerText = q.question_text;
            el.solveAttempts.innerText = `Attempts: ${q.status_info.attempts || 0}`;
            
            // Check status (Solved / Unsolved)
            if (q.status_info.status === 'solved') {
                this.showSolvedState(q);
            } else {
                // Setup Input Panel
                if (q.answer_type === 'multiple_choice' && q.choices) {
                    el.multipleChoiceContainer.classList.remove('hidden');
                    el.multipleChoiceContainer.innerHTML = '';
                    const choices = typeof q.choices === 'string' ? JSON.parse(q.choices) : q.choices;
                    choices.forEach(c => {
                        const optLetter = c.charAt(0); // 'A', 'B', 'C', 'D'
                        const btn = document.createElement('button');
                        btn.className = 'pixel-btn red-glow';
                        btn.innerText = c;
                        btn.onclick = () => this.submitAnswer(optLetter);
                        el.multipleChoiceContainer.appendChild(btn);
                    });
                } else {
                    el.textInputContainer.classList.remove('hidden');
                }
                
                // Show unlocked hints
                this.renderHints(q.hints, q.status_info.hints_revealed);
            }
            
            // Draw Chart
            this.renderChart(q.chart_data);
            
            // Drillin Terminal Status
            this.updateDrillinConsole(q.status_info.drillin_active);
            
        } catch (err) {
            el.puzzleQuestion.innerHTML = `<div class="text-red font-xs">Error opening site: ${err.message}</div>`;
        }
    },

    renderChart(chartDataStr) {
        if (state.currentChart) {
            state.currentChart.destroy();
            state.currentChart = null;
        }
        
        if (!chartDataStr) {
            el.puzzleVisualCard.classList.add('hidden');
            return;
        }
        
        el.puzzleVisualCard.classList.remove('hidden');
        
        try {
            const config = typeof chartDataStr === 'string' ? JSON.parse(chartDataStr) : chartDataStr;
            
            // Retro theme injection override
            if (config.data && config.data.datasets) {
                config.data.datasets.forEach(ds => {
                    ds.borderWidth = ds.borderWidth || 3;
                    // Inject pixel style colors if undefined
                    if (!ds.borderColor && !ds.backgroundColor) {
                        ds.borderColor = '#ff2a4b';
                        ds.backgroundColor = 'rgba(128, 0, 16, 0.1)';
                    }
                });
            }
            
            // Set font overrides
            if (!config.options) config.options = {};
            config.options.scales = config.options.scales || {};
            
            const fontConfig = {
                family: 'VT323',
                size: 14
            };
            
            // Configure ticks to look retro
            ['x', 'y'].forEach(axis => {
                if (!config.options.scales[axis]) config.options.scales[axis] = {};
                config.options.scales[axis].ticks = config.options.scales[axis].ticks || {};
                config.options.scales[axis].ticks.font = fontConfig;
                config.options.scales[axis].ticks.color = '#aaaaaa';
                config.options.scales[axis].grid = {
                    color: '#2a0407'
                };
            });
            
            const ctx = el.puzzleChart.getContext('2d');
            state.currentChart = new Chart(ctx, config);
        } catch (e) {
            console.error("Error drawing Chart.js:", e);
            el.puzzleVisualCard.classList.add('hidden');
        }
    },

    renderHints(hintsList, count) {
        el.hintsRevealedList.innerHTML = '';
        if (count === 0) {
            el.hintsRevealedList.innerHTML = `<div class="text-muted font-xs">No hints extracted yet. Costs 3 gems to buy one.</div>`;
        } else {
            hintsList.forEach((hint, idx) => {
                const entry = document.createElement('div');
                entry.className = 'hint-entry';
                entry.innerHTML = `<strong>CLUE #${idx + 1}:</strong> ${hint}`;
                el.hintsRevealedList.appendChild(entry);
            });
        }
        
        if (count >= 3) {
            el.btnBuyHint.disabled = true;
            el.btnBuyHint.innerText = "ALL CLUES EXTRACTED";
        }
    },

    async buyHint() {
        if (state.gems < 3) {
            alert("Insufficient Gems! Solve other puzzles to earn gems.");
            return;
        }
        
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/hint`, { method: 'POST' });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            
            // Update gems
            state.gems = data.gems;
            el.headerGems.innerText = `💎 ${state.gems}`;
            
            // Refresh hints list
            this.renderHints(data.hints, data.hints_revealed);
            
        } catch (err) {
            alert("Error purchasing hint: " + err.message);
        }
    },

    // SUBMIT GRADING
    async submitAnswer(chosenChoice = null) {
        const answer = chosenChoice || el.userAnswerInput.value.trim();
        if (!answer) {
            alert("Please type or select an answer!");
            return;
        }
        
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer: answer })
            });
            
            const data = await res.json();
            
            if (data.correct) {
                // Correct logic!
                state.gems = data.gems;
                state.depth = data.depth_meters;
                
                el.headerGems.innerText = `💎 ${state.gems}`;
                el.headerDepth.innerText = `${state.depth}m`;
                
                // Show Solved State
                state.activePuzzle.status_info.status = 'solved';
                state.activePuzzle.explanation = data.explanation;
                state.activePuzzle.status_info.user_answer = answer;
                
                this.showSolvedState(state.activePuzzle);
                
                // Refresh Status (for streak checks)
                this.loadStatus();
            } else {
                // Wrong answer - Balatro Screen Shake effect!
                const ws = document.querySelector('.solve-workspace');
                ws.classList.add('shake-screen');
                setTimeout(() => ws.classList.remove('shake-screen'), 300);
                
                // Update attempts
                const currentAttempts = (state.activePuzzle.status_info.attempts || 0) + 1;
                state.activePuzzle.status_info.attempts = currentAttempts;
                el.solveAttempts.innerText = `Attempts: ${currentAttempts}`;
                
                // Speech bubble reaction
                el.meinschaftSpeech.innerText = `"Ah! A structural collapse of logic! Re-read the constraints, Pariah, or consult Drillin."`;
            }
        } catch (err) {
            alert("Error submitting answer: " + err.message);
        }
    },

    showSolvedState(q) {
        el.solveUnsolvedSection.classList.add('hidden');
        el.solveSolvedSection.classList.remove('hidden');
        el.hintsCardSection.classList.add('hidden'); // Hide hint section once solved
        
        el.solveGemsRewarded.innerText = `+${q.gem_reward} Gems, Depth Increased`;
        el.solveExplanation.innerText = q.explanation;
        
        // Show saved notes if they exist
        el.solveUserNotes.value = q.status_info.user_notes || '';
        
        el.meinschaftSpeech.innerText = `"Elegantly extracted! Your brain cells are firing. Make sure to record your approach in the archive notes."`;
        
        // If Drillin is active, we can refresh his panel to review notes
        if (q.status_info.drillin_active === 1) {
            this.updateDrillinConsole(1);
        }
    },

    async saveNotes() {
        const notes = el.solveUserNotes.value.trim();
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: notes })
            });
            if (res.ok) {
                alert("Reflection committed to the archive!");
                // If Drillin is connected, prompt him to analyze their notes!
                if (state.activePuzzle.status_info.drillin_active === 1) {
                    this.sendDrillinSystemMessage("*** SYSTEM: User saved new approach notes. Drillin review requested. ***");
                }
            }
        } catch (err) {
            alert("Error saving notes: " + err.message);
        }
    },

    abandonPuzzle() {
        if (state.activeShaft) {
            this.enterShaft(state.activeShaft);
        } else {
            this.showHome();
        }
    },

    // DRILLIN CHATBOT TERMINAL
    updateDrillinConsole(active) {
        if (active === 1) {
            el.drillinStatusTag.innerText = "ONLINE";
            el.drillinStatusTag.className = "blink text-green";
            el.drillinBuyBox.classList.add('hidden');
            el.drillinInputBox.classList.remove('hidden');
            
            // Load messages
            this.loadDrillinMessages();
            
            // Poll for messages if needed (just load once and on sends is usually enough, but let's refresh when we open)
        } else {
            el.drillinStatusTag.innerText = "OFFLINE";
            el.drillinStatusTag.className = "blink text-red";
            el.drillinBuyBox.classList.remove('hidden');
            el.drillinInputBox.classList.add('hidden');
            el.drillinChatLog.innerHTML = `
                <div class="system-msg">
                    *** SYSTEM: DRILLIN INTERNET PROTOCOL DISCONNECTED ***<br>
                    Drillin is an AI support assistant on this site. He does not solve problems or provide direct hints. He only clarifies question parameters before solving, and analyzes your mathematical approach after solving.<br><br>
                    Connection Cost: 💎 2 (Gives access for the entire duration of this problem).
                </div>
            `;
        }
    },

    async activateDrillin() {
        if (state.gems < 2) {
            alert("Insufficient Gems to connect Drillin!");
            return;
        }
        
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/drillin/activate`, { method: 'POST' });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            
            // Deduct gems locally
            state.gems = data.gems;
            el.headerGems.innerText = `💎 ${state.gems}`;
            
            state.activePuzzle.status_info.drillin_active = 1;
            this.updateDrillinConsole(1);
            
        } catch (err) {
            alert("Error activating Drillin: " + err.message);
        }
    },

    async loadDrillinMessages() {
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/drillin/chat`);
            const chat = await res.json();
            
            el.drillinChatLog.innerHTML = '';
            chat.forEach(msg => {
                const bubble = document.createElement('div');
                if (msg.sender === 'user') {
                    bubble.className = 'user-chat-bubble';
                    bubble.innerHTML = msg.message;
                } else if (msg.sender === 'system') {
                    bubble.className = 'system-msg';
                    bubble.innerHTML = msg.message;
                } else {
                    bubble.className = 'drillin-chat-bubble';
                    bubble.innerHTML = `<strong>Drillin:</strong> ${msg.message}`;
                }
                el.drillinChatLog.appendChild(bubble);
            });
            
            // Scroll to bottom
            el.drillinChatLog.scrollTop = el.drillinChatLog.scrollHeight;
        } catch (err) {
            console.error("Error loading chat messages:", err);
        }
    },

    async sendDrillinMessage() {
        const text = el.drillinMessageInput.value.trim();
        if (!text) return;
        
        el.drillinMessageInput.value = '';
        
        // Append user bubble instantly
        const userBubble = document.createElement('div');
        userBubble.className = 'user-chat-bubble';
        userBubble.innerText = text;
        el.drillinChatLog.appendChild(userBubble);
        el.drillinChatLog.scrollTop = el.drillinChatLog.scrollHeight;
        
        // Append pending typing message
        const typingBubble = document.createElement('div');
        typingBubble.className = 'drillin-chat-bubble';
        typingBubble.innerHTML = `<strong>Drillin:</strong> <em>Extracting data...</em>`;
        el.drillinChatLog.appendChild(typingBubble);
        el.drillinChatLog.scrollTop = el.drillinChatLog.scrollHeight;
        
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/drillin/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            
            const reply = await res.json();
            
            // Replace typing bubble with actual reply
            typingBubble.innerHTML = `<strong>Drillin:</strong> ${reply.message}`;
            el.drillinChatLog.scrollTop = el.drillinChatLog.scrollHeight;
            
        } catch (err) {
            typingBubble.innerHTML = `<span class="text-red">Connection error to Drillin node.</span>`;
        }
    },

    async sendDrillinSystemMessage(sysMsg) {
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/drillin/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: sysMsg })
            });
            this.loadDrillinMessages();
        } catch (err) {
            console.error(err);
        }
    },

    // COGNITIVE ARCHIVE VIEW
    async showArchive() {
        this.showView('archive');
        el.archiveListContainer.innerHTML = `<div class="text-muted font-xs">Opening archive doors...</div>`;
        
        try {
            const res = await fetch('/api/archive');
            const data = await res.json();
            
            if (data.length === 0) {
                el.archiveListContainer.innerHTML = `<div class="text-muted font-sm title-center">Archive is currently empty. Extract a site successfully to store records.</div>`;
                return;
            }
            
            el.archiveListContainer.innerHTML = '';
            data.forEach((item, idx) => {
                const card = document.createElement('div');
                card.className = `archive-item card-${item.type.includes('shaft') ? item.type : 'gold'}`;
                
                const titleText = item.type.replace('_', ' ').toUpperCase() + ` - ARCHIVED EXTRACTION #${idx + 1}`;
                
                card.innerHTML = `
                    <div class="archive-item-header">
                        <h3 class="pixel-text font-sm text-red">${titleText}</h3>
                        <span class="text-muted font-xs">${new Date(item.solved_at).toLocaleDateString()}</span>
                    </div>
                    
                    <p class="font-sm mb-1"><strong>Question:</strong> ${item.question_text}</p>
                    <p class="font-sm text-green mb-05"><strong>Correct Answer:</strong> ${item.exact_answer}</p>
                    
                    <div class="explanation-box font-sm mb-1">
                        <strong>Math Pathway:</strong><br>
                        ${item.explanation}
                    </div>
                    
                    <div class="archive-user-notes">
                        <strong>📝 Your Approach Notes:</strong>
                        <textarea id="archive-notes-${item.id}" rows="3" placeholder="No notes captured. Type your approach reflections here to lock them in memory...">${item.user_notes || ''}</textarea>
                        <button class="pixel-btn-sm border-red text-red mt-05" onclick="app.updateArchiveNotes(${item.id})">UPDATE REFLECTION</button>
                    </div>
                `;
                
                el.archiveListContainer.appendChild(card);
            });
        } catch (err) {
            el.archiveListContainer.innerHTML = `<div class="text-red font-xs">Error opening archives: ${err.message}</div>`;
        }
    },

    async updateArchiveNotes(puzzleId) {
        const textEl = document.getElementById(`archive-notes-${puzzleId}`);
        const notes = textEl.value.trim();
        
        try {
            const res = await fetch(`/api/puzzle/${puzzleId}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: notes })
            });
            if (res.ok) {
                alert("Archive notes updated!");
            }
        } catch (err) {
            alert("Error saving notes: " + err.message);
        }
    },

    // SETTINGS VIEW
    showSettings() {
        this.showView('settings');
    },

    toggleMusic() {
        const isMuted = localStorage.getItem('bgm_enabled') === 'true';
        if (isMuted) {
            // Mute it
            localStorage.setItem('bgm_enabled', 'false');
            bgm.pause();
            el.musicBtn.classList.remove('text-green');
            el.musicBtn.classList.add('text-red');
            el.musicBtn.innerText = "🎵 OFF";
        } else {
            // Unmute it
            localStorage.setItem('bgm_enabled', 'true');
            bgm.play().then(() => {
                el.musicBtn.classList.remove('text-red');
                el.musicBtn.classList.add('text-green');
                el.musicBtn.innerText = "🎵 ON";
            }).catch(err => {
                alert("Audio play blocked by browser. Click anywhere on the screen first, then toggle.");
            });
        }
    },

    adjustVolume(val) {
        bgm.volume = parseFloat(val);
        localStorage.setItem('bgm_volume', val);
    },

    toggleCRT() {
        const isCrt = localStorage.getItem('crt_enabled') === 'true';
        if (isCrt) {
            localStorage.setItem('crt_enabled', 'false');
            document.querySelector('.scanlines').classList.add('hidden');
            document.querySelector('.crt-overlay').classList.add('hidden');
        } else {
            localStorage.setItem('crt_enabled', 'true');
            document.querySelector('.scanlines').classList.remove('hidden');
            document.querySelector('.crt-overlay').classList.remove('hidden');
        }
    },

    async resetProgress() {
        if (!confirm("Are you absolutely sure you want to trigger a cave-in? This resets all solved puzzle counts, depth records, custom notes, and returns gems to 17. This cannot be undone!")) {
            return;
        }
        
        try {
            const res = await fetch('/api/settings/reset', { method: 'POST' });
            const data = await res.json();
            
            state.depth = data.depth_meters;
            state.gems = data.gems;
            
            el.headerDepth.innerText = `${state.depth}m`;
            el.headerGems.innerText = `💎 ${state.gems}`;
            
            alert("Progress reset completed. The mineshafts have collapsed and re-seeded.");
            this.showHome();
        } catch (err) {
            alert("Error resetting progress: " + err.message);
        }
    }
};
