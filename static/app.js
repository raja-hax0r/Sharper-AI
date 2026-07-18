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
    currentChart: null,
    
    // Timer state
    solveTimerInterval: null,
    solveSecondsElapsed: 0
};

// SELECT ELEMENTS
const el = {
    headerGems: document.getElementById('header-gems'),
    musicBtn: document.getElementById('music-btn'),
    meinschaftSpeech: document.getElementById('meinschaft-speech'),
    liveClock: document.getElementById('live-clock'),
    
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
    shaftsModal: document.getElementById('shafts-modal'),
    
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
    btnSubmitAnswer: document.getElementById('btn-submit-answer'),
    solveAttempts: document.getElementById('solve-attempts'),
    btnResetCollapsed: document.getElementById('btn-reset-collapsed'),
    solveUnsolvedSection: document.getElementById('solve-unsolved-section'),
    solveSolvedSection: document.getElementById('solve-solved-section'),
    solveGemsRewarded: document.getElementById('solve-gems-rewarded'),
    solveTimeTaken: document.getElementById('solve-time-taken'),
    solveExplanation: document.getElementById('solve-explanation'),
    solveScratchpadInput: document.getElementById('solve-scratchpad-input'),
    scratchpadSavedBadge: document.getElementById('scratchpad-saved-badge'),
    solveTimer: document.getElementById('solve-timer'),
    hintsRevealedList: document.getElementById('hints-revealed-list'),
    btnBuyHint: document.getElementById('btn-buy-hint'),
    hintsCardSection: document.getElementById('hints-card-section'),
    
    // Drillin Floating Console
    drillinFloatPanel: document.getElementById('drillin-float-panel'),
    drillinStatusTag: document.getElementById('drillin-status-tag'),
    drillinChatLog: document.getElementById('drillin-chat-log'),
    drillinBuyBox: document.getElementById('drillin-buy-box'),
    drillinInputBox: document.getElementById('drillin-input-box'),
    drillinMessageInput: document.getElementById('drillin-message-input'),
    
    // Archive Scorecard
    scorecardSolvedCount: document.getElementById('scorecard-solved-count'),
    scorecardDepth: document.getElementById('scorecard-depth'),
    scorecardGems: document.getElementById('scorecard-gems'),
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
    
    // Autoplay policy hook
    document.body.addEventListener('click', () => {
        if (!bgmInitialized) {
            bgmInitialized = true;
            if (localStorage.getItem('bgm_enabled') === 'true') {
                bgm.play().then(() => {
                    el.musicBtn.classList.remove('text-red');
                    el.musicBtn.classList.add('text-green');
                    el.musicBtn.innerText = "🎵 ON";
                }).catch(err => console.log("Audio blocked: ", err));
            }
        }
    }, { once: true });
});

const app = {
    init() {
        // Load configurations
        const musicEnabled = localStorage.getItem('bgm_enabled') !== 'false';
        localStorage.setItem('bgm_enabled', musicEnabled);
        
        const volume = localStorage.getItem('bgm_volume') || '0.5';
        bgm.volume = parseFloat(volume);
        el.volumeSlider.value = volume;

        if (musicEnabled) {
            el.musicBtn.classList.remove('text-red');
            el.musicBtn.classList.add('text-green');
            el.musicBtn.innerText = "🎵 ON";
        } else {
            el.musicBtn.classList.remove('text-green');
            el.musicBtn.classList.add('text-red');
            el.musicBtn.innerText = "🎵 OFF";
            bgm.pause();
        }

        // Start Live Clock
        this.startClock();

        // Fetch User Status
        this.loadStatus();
    },

    // CLOCK TIMERS
    startClock() {
        const updateClock = () => {
            const now = new Date();
            const pad = num => String(num).padStart(2, '0');
            const dateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
            const timeStr = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
            el.liveClock.innerText = `${dateStr} ${timeStr}`;
        };
        updateClock();
        setInterval(updateClock, 1000);
    },

    startSolveTimer() {
        this.stopSolveTimer();
        state.solveSecondsElapsed = 0;
        el.solveTimer.innerText = "TIME: 00:00";
        
        state.solveTimerInterval = setInterval(() => {
            state.solveSecondsElapsed++;
            const minutes = Math.floor(state.solveSecondsElapsed / 60);
            const seconds = state.solveSecondsElapsed % 60;
            const pad = num => String(num).padStart(2, '0');
            el.solveTimer.innerText = `TIME: ${pad(minutes)}:${pad(seconds)}`;
        }, 1000);
    },

    stopSolveTimer() {
        if (state.solveTimerInterval) {
            clearInterval(state.solveTimerInterval);
            state.solveTimerInterval = null;
        }
    },

    formatTimeElapsed(secondsTotal) {
        const minutes = Math.floor(secondsTotal / 60);
        const seconds = secondsTotal % 60;
        if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        }
        return `${seconds}s`;
    },

    // NAVIGATION
    showView(viewName) {
        el.viewHome.classList.remove('active');
        el.viewShaft.classList.remove('active');
        el.viewSolve.classList.remove('active');
        el.viewArchive.classList.remove('active');
        el.viewSettings.classList.remove('active');
        
        // Modal safety
        this.toggleShaftsModal(false);
        
        // Clear Drillin chat pooling if leaving solve view
        if (viewName !== 'solve' && state.drillinChatInterval) {
            clearInterval(state.drillinChatInterval);
            state.drillinChatInterval = null;
            this.toggleDrillinConsole(false); // Collapsed by default on exit
        }
        
        // Stop timer if leaving solve view
        if (viewName !== 'solve') {
            this.stopSolveTimer();
        }

        if (viewName === 'home') {
            el.viewHome.classList.add('active');
            document.body.classList.add('home-active');
        } else {
            document.body.classList.remove('home-active');
        }
        if (viewName === 'shaft') el.viewShaft.classList.add('active');
        if (viewName === 'solve') el.viewSolve.classList.add('active');
        if (viewName === 'archive') el.viewArchive.classList.add('active');
        if (viewName === 'settings') el.viewSettings.classList.add('active');
        
        document.querySelector('.app-main').scrollTop = 0;
    },

    showHome() {
        this.loadStatus();
        this.showView('home');
    },

    toggleShaftsModal(show) {
        if (show) {
            el.shaftsModal.classList.remove('hidden');
        } else {
            el.shaftsModal.classList.add('hidden');
        }
    },

    // DRILLIN AI FLOAT PANEL CONTROLS
    toggleDrillinConsole(show = null) {
        if (show === true) {
            el.drillinFloatPanel.classList.remove('hidden');
        } else if (show === false) {
            el.drillinFloatPanel.classList.add('hidden');
        } else {
            // Toggle
            el.drillinFloatPanel.classList.toggle('hidden');
        }
        
        // Scroll chat log if revealed
        if (!el.drillinFloatPanel.classList.contains('hidden')) {
            el.drillinChatLog.scrollTop = el.drillinChatLog.scrollHeight;
        }
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
            
            this.updateSpeechBubble();
        } catch (err) {
            console.error("Error loading status:", err);
        }
    },

    updateSpeechBubble() {
        let msg = "";
        if (state.dailySolved && state.weeklySolved) {
            msg = `"Unbelievable, Herr Pariah. Today's daily ore is loaded and the weekly metrics are verified. Your boss will fall in the line of questioning."`;
        } else if (state.dailySolved) {
            msg = `"Today's vein is dry. Daily challenge successfully completed, but the weekly deep logic expedition remains. Ready to extract?"`;
        } else if (state.gems < 3) {
            msg = `"Resource balance depleted, Pariah. Less than 3 gems! You are unable to extract hints. Go to Shaft I to mine gems immediately."`;
        } else {
            msg = `"Welcome back, Pariah. Select a mineshaft from the menu, or begin the daily challenge. Keep your logic pickaxe sharp!"`;
        }
        el.meinschaftSpeech.innerText = msg;
    },

    // MINESHAFT BANK
    async enterShaft(shaftType) {
        state.activeShaft = shaftType;
        this.toggleShaftsModal(false);
        
        const shaftNames = {
            "shaft_1": "SHAFT I: COAL MINE (MATH)",
            "shaft_2": "SHAFT II: IRON MINE (METRICS)",
            "shaft_3": "SHAFT III: GOLD MINE (OPTIMIZE)",
            "shaft_4": "SHAFT IV: RUBY MINE (LOGIC)",
            "shaft_5": "SHAFT V: DIAMOND MINE (FINANCIALS)"
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
            this.enterShaft(state.activeShaft);
        } catch (err) {
            alert("Error generating new puzzle: " + err.message);
        } finally {
            el.btnDigDeeper.disabled = false;
            el.btnDigDeeper.innerText = "⛏️ DIG DEEPER (NEW PUZZLE)";
        }
    },

    // SOLVE VIEW
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
        
        // Reset inputs and buttons
        el.userAnswerInput.value = '';
        el.btnSubmitAnswer.disabled = false;
        el.btnSubmitAnswer.innerText = "SUBMIT ANSWER";
        el.userAnswerInput.disabled = false;
        el.btnResetCollapsed.classList.add('hidden');
        
        el.solveUnsolvedSection.classList.remove('hidden');
        el.solveSolvedSection.classList.add('hidden');
        el.multipleChoiceContainer.classList.add('hidden');
        el.textInputContainer.classList.add('hidden');
        el.hintsRevealedList.innerHTML = '';
        el.btnBuyHint.disabled = false;
        el.btnBuyHint.innerText = "🔓 EXTRACT HINT (COSTS 💎 3)";
        el.hintsCardSection.classList.remove('hidden');
        
        el.puzzleQuestion.innerHTML = `<div class="text-muted font-xs">Reading drill cores...</div>`;
        
        try {
            const res = await fetch(`/api/puzzle/${puzzleId}`);
            if (!res.ok) throw new Error(await res.text());
            const q = await res.json();
            state.activePuzzle = q;
            
            // Set details
            el.solveTitle.innerText = q.type.replace('_', ' ').toUpperCase() + ` EXTRACTION`;
            el.puzzleDifficultyTag.innerText = `DIFFICULTY: ${q.type.replace('_', ' ').toUpperCase()}`;
            el.puzzleRewardTag.innerText = `💎 ${q.gem_reward} Gems`;
            el.puzzleQuestion.innerText = q.question_text;
            
            const maxAtt = q.max_attempts;
            const currentAttempts = q.status_info.attempts || 0;
            
            el.solveAttempts.innerText = `Attempts: ${currentAttempts} / ${maxAtt}`;
            
            // Set Scratchpad workspace draft notes
            el.solveScratchpadInput.value = q.status_info.user_notes || '';
            el.scratchpadSavedBadge.classList.add('hidden');
            
            // Start timer
            this.startSolveTimer();

            // Check attempts and status
            if (q.status_info.status === 'solved') {
                this.showSolvedState(q);
            } else if (currentAttempts >= maxAtt) {
                // Collapsed due to max attempts
                this.showCollapsedState(q);
            } else {
                // Setup Input Panel
                if (q.answer_type === 'multiple_choice' && q.choices) {
                    el.multipleChoiceContainer.classList.remove('hidden');
                    el.multipleChoiceContainer.innerHTML = '';
                    const choices = typeof q.choices === 'string' ? JSON.parse(q.choices) : q.choices;
                    choices.forEach(c => {
                        const optLetter = c.charAt(0); // 'A', 'B' etc
                        const btn = document.createElement('button');
                        btn.className = 'pixel-btn red-glow';
                        btn.innerText = c;
                        btn.onclick = () => this.submitAnswer(optLetter);
                        el.multipleChoiceContainer.appendChild(btn);
                    });
                } else {
                    el.textInputContainer.classList.remove('hidden');
                }
                
                // Show hints
                this.renderHints(q.hints, q.status_info.hints_revealed);
            }
            
            // Render Chart
            this.renderChart(q.chart_data);
            
            // Drillin Terminal connection check
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
            
            // Overriding chart configuration for high legibility on white background!
            const distinctColors = ['#007bff', '#28a745', '#fd7e14', '#6f42c1', '#dc3545', '#17a2b8'];
            const distinctBacks = [
                'rgba(0, 123, 255, 0.25)', 
                'rgba(40, 167, 69, 0.25)', 
                'rgba(253, 126, 20, 0.25)', 
                'rgba(111, 66, 193, 0.25)', 
                'rgba(220, 53, 69, 0.25)', 
                'rgba(23, 162, 184, 0.25)'
            ];

            if (config.data && config.data.datasets) {
                config.data.datasets.forEach((ds, idx) => {
                    ds.borderWidth = 3.5;
                    
                    if (config.type === 'pie' || config.type === 'doughnut') {
                        // Apply separate vibrant contrasting colors to each slice
                        ds.borderColor = '#ffffff';
                        ds.borderWidth = 2;
                        ds.backgroundColor = distinctColors.slice(0, ds.data.length);
                    } else {
                        // Line/Bar charts
                        const colorIdx = idx % distinctColors.length;
                        ds.borderColor = distinctColors[colorIdx];
                        ds.backgroundColor = distinctBacks[colorIdx];
                    }
                });
            }
            
            // Adjust options for white canvas container styling
            if (!config.options) config.options = {};
            
            const fontConfig = {
                family: 'VT323',
                size: 16
            };
            
            // Configure Scales
            if (config.type !== 'pie' && config.type !== 'doughnut') {
                config.options.scales = config.options.scales || {};
                ['x', 'y'].forEach(axis => {
                    config.options.scales[axis] = config.options.scales[axis] || {};
                    config.options.scales[axis].ticks = config.options.scales[axis].ticks || {};
                    config.options.scales[axis].ticks.font = fontConfig;
                    config.options.scales[axis].ticks.color = '#333333'; // Dark ticks on white
                    config.options.scales[axis].grid = {
                        color: '#e2e8f0' // Soft light gray grids on white
                    };
                });
            }
            
            // Chart legends/titles text readability
            if (!config.options.plugins) config.options.plugins = {};
            config.options.plugins.legend = config.options.plugins.legend || {};
            config.options.plugins.legend.labels = {
                color: '#333333', // Dark charcoal text
                font: { family: 'VT323', size: 16 }
            };
            
            config.options.plugins.title = config.options.plugins.title || {};
            config.options.plugins.title.color = '#111111'; // Dark title on white
            config.options.plugins.title.font = { family: 'VT323', size: 20 };

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
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Server error");
            }
            const data = await res.json();
            
            state.gems = data.gems;
            el.headerGems.innerText = `💎 ${state.gems}`;
            
            // Re-render
            state.activePuzzle.status_info.hints_revealed = data.hints_revealed;
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
            
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Server error");
            }
            
            const data = await res.json();
            
            // Stop Timer
            this.stopSolveTimer();
            const timeFormatted = this.formatTimeElapsed(state.solveSecondsElapsed);

            if (data.correct) {
                state.gems = data.gems;
                state.depth = data.depth_meters;
                
                el.headerGems.innerText = `💎 ${state.gems}`;
                
                state.activePuzzle.status_info.status = 'solved';
                state.activePuzzle.explanation = data.explanation;
                state.activePuzzle.status_info.user_answer = answer;
                
                // Show Solved UI
                el.solveUnsolvedSection.classList.add('hidden');
                el.solveSolvedSection.classList.remove('hidden');
                el.hintsCardSection.classList.add('hidden');
                
                el.solveGemsRewarded.innerText = `+${state.activePuzzle.gem_reward} Gems`;
                el.solveTimeTaken.innerText = `Solved in ${timeFormatted}`;
                el.solveExplanation.innerText = data.explanation;
                
                el.meinschaftSpeech.innerText = `"Elegantly extracted in ${timeFormatted}! Your logic pickaxe is lethal. Save your final scratchpad notes now!"`;
                
                // Save scratchpad notes
                this.saveScratchpadDraft(true);
                
                if (state.activePuzzle.status_info.drillin_active === 1) {
                    this.updateDrillinConsole(1);
                    this.sendDrillinSystemMessage(`*** SYSTEM: User solved the puzzle successfully in ${timeFormatted}. Drillin review requested. ***`);
                }
                
                this.loadStatus();
            } else {
                // Screen shake
                const ws = document.querySelector('.solve-workspace-full');
                ws.classList.add('shake-screen');
                setTimeout(() => ws.classList.remove('shake-screen'), 300);
                
                // Update attempts
                const currentAttempts = (state.activePuzzle.status_info.attempts || 0) + 1;
                state.activePuzzle.status_info.attempts = currentAttempts;
                const maxAtt = state.activePuzzle.max_attempts;
                
                el.solveAttempts.innerText = `Attempts: ${currentAttempts} / ${maxAtt}`;
                
                if (currentAttempts >= maxAtt) {
                    this.showCollapsedState(state.activePuzzle);
                } else {
                    el.meinschaftSpeech.innerText = `"Ah! A structural collapse of logic! Attempts remaining: ${maxAtt - currentAttempts}."`;
                }
            }
        } catch (err) {
            alert("Submission error: " + err.message);
        }
    },

    showSolvedState(q) {
        el.solveUnsolvedSection.classList.add('hidden');
        el.solveSolvedSection.classList.remove('hidden');
        el.hintsCardSection.classList.add('hidden');
        
        el.solveGemsRewarded.innerText = `+${q.gem_reward} Gems`;
        el.solveTimeTaken.innerText = `Status: Solved`;
        el.solveExplanation.innerText = q.explanation;
        
        el.meinschaftSpeech.innerText = `"Site completed. Your analytical reflections are documented in the archive."`;
        
        if (q.status_info.drillin_active === 1) {
            this.updateDrillinConsole(1);
        }
    },

    showCollapsedState(q) {
        el.solveUnsolvedSection.classList.remove('hidden');
        el.solveSolvedSection.classList.add('hidden');
        
        // Disable inputs
        el.btnSubmitAnswer.disabled = true;
        el.btnSubmitAnswer.innerText = "MINESHAFT COLLAPSED";
        el.userAnswerInput.disabled = true;
        el.multipleChoiceContainer.classList.add('hidden');
        
        el.solveAttempts.innerHTML = `<span class="text-red">Attempts: ${q.status_info.attempts} / ${q.max_attempts} (COLLAPSED!)</span>`;
        el.meinschaftSpeech.innerText = `"Mineshaft collapsed! Max attempts reached. You must abandon this shift."`;
        
        // Show restore button (costs 5 gems)
        el.btnResetCollapsed.classList.remove('hidden');
    },

    async resetCollapsedSite() {
        if (state.gems < 5) {
            alert("Not enough gems! Cost to restore collapsed mineshaft is 5 gems.");
            return;
        }
        
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/reset-attempts`, { method: 'POST' });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Server error");
            }
            const data = await res.json();
            
            // Deduct gems
            state.gems = data.gems;
            el.headerGems.innerText = `💎 ${state.gems}`;
            
            alert("Mineshaft stabilized! Resetting attempts back to 0.");
            
            // Reload puzzle
            this.loadPuzzle(state.activePuzzle.id);
        } catch (err) {
            alert("Error restoring mineshaft: " + err.message);
        }
    },

    // WORKSPACE notes draft save
    async saveScratchpadDraft(silent = false) {
        const text = el.solveScratchpadInput.value.trim();
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: text })
            });
            if (res.ok) {
                if (!silent) {
                    el.scratchpadSavedBadge.classList.remove('hidden');
                    setTimeout(() => {
                        el.scratchpadSavedBadge.classList.add('hidden');
                    }, 1500);
                }
                state.activePuzzle.status_info.user_notes = text;
            }
        } catch (err) {
            console.error("Error saving scratchpad draft: ", err);
        }
    },

    // DRILLIN TERMINAL CHATBOT
    updateDrillinConsole(active) {
        if (active === 1) {
            el.drillinStatusTag.innerText = "ONLINE";
            el.drillinStatusTag.className = "blink text-green";
            el.drillinBuyBox.classList.add('hidden');
            el.drillinInputBox.classList.remove('hidden');
            
            this.loadDrillinMessages();
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
        
        // Typing bubble
        const typingBubble = document.createElement('div');
        typingBubble.className = 'drillin-chat-bubble';
        typingBubble.innerHTML = `<strong>Drillin:</strong> <em>Extracting response...</em>`;
        el.drillinChatLog.appendChild(typingBubble);
        el.drillinChatLog.scrollTop = el.drillinChatLog.scrollHeight;
        
        try {
            const res = await fetch(`/api/puzzle/${state.activePuzzle.id}/drillin/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            
            const reply = await res.json();
            
            typingBubble.innerHTML = `<strong>Drillin:</strong> ${reply.message}`;
            el.drillinChatLog.scrollTop = el.drillinChatLog.scrollHeight;
            
        } catch (err) {
            typingBubble.innerHTML = `<span class="text-red">Connection timed out.</span>`;
        }
    },

    async sendDrillinSystemMessage(sysMsg) {
        try {
            await fetch(`/api/puzzle/${state.activePuzzle.id}/drillin/chat`, {
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
            
            // Depth map for analytics: Coal=2m, Iron/Daily=5m, Gold=10m, Ruby/Weekly=15m, Diamond=25m
            let totalDepth = 0;
            const depthMap = {"shaft_1": 2, "shaft_2": 5, "daily": 5, "shaft_3": 10, "shaft_4": 15, "weekly": 15, "shaft_5": 25};
            
            data.forEach(item => {
                totalDepth += depthMap[item.type] || 5;
            });
            
            // Update Scorecard HTML
            el.scorecardSolvedCount.innerText = data.length;
            el.scorecardDepth.innerText = `${totalDepth}m`;
            el.scorecardGems.innerText = state.gems;
            
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
            localStorage.setItem('bgm_enabled', 'false');
            bgm.pause();
            el.musicBtn.classList.remove('text-green');
            el.musicBtn.classList.add('text-red');
            el.musicBtn.innerText = "🎵 OFF";
        } else {
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

    async resetProgress() {
        if (!confirm("Are you absolutely sure you want to trigger a cave-in? This resets all solved puzzle counts, depth records, custom notes, and resets gems to 0. This cannot be undone!")) {
            return;
        }
        
        try {
            const res = await fetch('/api/settings/reset', { method: 'POST' });
            const data = await res.json();
            
            state.depth = data.depth_meters;
            state.gems = data.gems;
            
            el.headerGems.innerText = `💎 ${state.gems}`;
            
            alert("Progress reset completed. The mineshafts have collapsed and gems are reset to 0.");
            this.showHome();
        } catch (err) {
            alert("Error resetting progress: " + err.message);
        }
    }
};
