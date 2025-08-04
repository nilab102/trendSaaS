/**
 * UI Manager for TrendSaaS Frontend
 * Handles all visual updates, progress tracking, and results display
 */

class TrendSaaSUI {
    constructor() {
        this.currentKeyword = '';
        this.initializeElements();
        this.setupEventListeners();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        // Sections
        this.inputSection = document.getElementById('input-section');
        this.progressSection = document.getElementById('progress-section');
        this.resultsSection = document.getElementById('results-section');
        this.errorSection = document.getElementById('error-section');
        this.loadingOverlay = document.getElementById('loading-overlay');

        // Input elements
        this.analysisForm = document.getElementById('analysis-form');
        this.keywordInput = document.getElementById('keyword-input');
        this.analyzeBtn = document.getElementById('analyze-btn');

        // Progress elements
        this.progressMessage = document.getElementById('progress-message');
        this.progressFill = document.getElementById('progress-fill');
        this.progressPercentage = document.getElementById('progress-percentage');
        this.progressSteps = document.getElementById('progress-steps');

        // Results elements
        this.resultsContent = document.getElementById('results-content');
        this.newAnalysisBtn = document.getElementById('new-analysis-btn');

        // Error elements
        this.errorMessage = document.getElementById('error-message');
        this.retryBtn = document.getElementById('retry-btn');

        // Progress elements
        this.stopAnalysisBtn = document.getElementById('stop-analysis-btn');

        // Connection status elements
        this.connectionStatus = document.getElementById('connection-status');
        this.statusIndicator = this.connectionStatus?.querySelector('.status-indicator');
        this.statusText = this.connectionStatus?.querySelector('.status-text');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Form submission
        this.analysisForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmission();
        });

        // New analysis button
        this.newAnalysisBtn.addEventListener('click', () => {
            this.resetToInput();
        });

        // Retry button
        this.retryBtn.addEventListener('click', () => {
            this.resetToInput();
        });

        // New analysis button (also resets connection)
        this.newAnalysisBtn.addEventListener('click', () => {
            this.resetToInput();
        });

        // Stop analysis button
        this.stopAnalysisBtn.addEventListener('click', () => {
            this.stopAnalysis();
        });

        // Input validation
        this.keywordInput.addEventListener('input', () => {
            this.validateInput();
        });
    }

    /**
     * Handle form submission
     */
    handleFormSubmission() {
        const keyword = this.keywordInput.value.trim();
        
        if (!this.validateKeyword(keyword)) {
            return;
        }

        this.currentKeyword = keyword;
        this.startAnalysis(keyword);
    }

    /**
     * Validate keyword input
     */
    validateKeyword(keyword) {
        if (!keyword) {
            this.showInputError('Please enter a keyword to analyze');
            return false;
        }

        if (keyword.length < 2) {
            this.showInputError('Keyword must be at least 2 characters long');
            return false;
        }

        if (keyword.length > 100) {
            this.showInputError('Keyword must be less than 100 characters');
            return false;
        }

        return true;
    }

    /**
     * Show input validation error
     */
    showInputError(message) {
        // Remove existing error
        const existingError = this.keywordInput.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        // Add new error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = '#dc3545';
        errorDiv.style.fontSize = '0.9rem';
        errorDiv.style.marginTop = '0.5rem';
        errorDiv.textContent = message;

        this.keywordInput.parentNode.appendChild(errorDiv);

        // Remove error after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    /**
     * Validate input in real-time
     */
    validateInput() {
        const keyword = this.keywordInput.value.trim();
        
        // Remove existing error
        const existingError = this.keywordInput.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        // Update button state
        this.analyzeBtn.disabled = !keyword || keyword.length < 2;
    }

    /**
     * Start analysis process
     */
    startAnalysis(keyword) {
        this.showProgressSection();
        this.updateProgress(0, 'Initializing analysis...');
        this.clearProgressSteps();
        
        // Emit custom event for app.js to handle
        const event = new CustomEvent('startAnalysis', {
            detail: { keyword: keyword }
        });
        document.dispatchEvent(event);
    }

    /**
     * Show progress section
     */
    showProgressSection() {
        this.hideAllSections();
        this.progressSection.classList.remove('hidden');
        this.progressSection.classList.add('fade-in');
        
        // Show stop button
        this.stopAnalysisBtn.classList.remove('hidden');
    }

    /**
     * Update progress display
     */
    updateProgress(percentage, message) {
        // Update progress bar
        this.progressFill.style.width = `${percentage}%`;
        this.progressPercentage.textContent = `${percentage}%`;

        // Update message
        if (message) {
            this.progressMessage.textContent = message;
        }

        // Add step to progress steps
        if (message && percentage > 0) {
            this.addProgressStep(message, percentage);
        }
    }

    /**
     * Add a progress step
     */
    addProgressStep(message, percentage) {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step-item';
        
        const stepName = this.getStepName(message);
        const stepDescription = this.getStepDescription(message);
        
        stepDiv.innerHTML = `
            <h4>${stepName}</h4>
            <p>${stepDescription}</p>
        `;

        // Add active class to current step
        const existingSteps = this.progressSteps.querySelectorAll('.step-item');
        existingSteps.forEach(step => step.classList.remove('active'));
        stepDiv.classList.add('active');

        // Mark previous steps as completed
        existingSteps.forEach(step => step.classList.add('completed'));

        this.progressSteps.appendChild(stepDiv);
    }

    /**
     * Get step name from message
     */
    getStepName(message) {
        const stepMap = {
            'Starting analysis': 'Initialization',
            'Fetching Google Trends data': 'Trends Data',
            'Trends data fetched successfully': 'Data Retrieved',
            'Extracting user problems': 'Problem Analysis',
            'Analyzing market maturity': 'Market Analysis',
            'Extracting solution goals': 'Goal Extraction',
            'Suggesting SaaS solution categories': 'Category Analysis',
            'Generating innovative SaaS features': 'Feature Generation',
            'Analyzing competitors': 'Competitor Analysis',
            'Enhancing features based on competitor analysis': 'Feature Enhancement'
        };

        for (const [key, value] of Object.entries(stepMap)) {
            if (message.includes(key)) {
                return value;
            }
        }

        return 'Processing';
    }

    /**
     * Get step description from message
     */
    getStepDescription(message) {
        // Extract additional info from message
        if (message.includes('problems identified')) {
            const match = message.match(/(\d+) problems identified/);
            if (match) {
                return `${match[1]} problems found`;
            }
        }

        if (message.includes('goals defined')) {
            const match = message.match(/(\d+) goals defined/);
            if (match) {
                return `${match[1]} goals created`;
            }
        }

        if (message.includes('features created')) {
            const match = message.match(/(\d+) features created/);
            if (match) {
                return `${match[1]} features generated`;
            }
        }

        if (message.includes('stage')) {
            const match = message.match(/(\w+) stage/);
            if (match) {
                return `Market: ${match[1]} stage`;
            }
        }

        return message;
    }

    /**
     * Clear progress steps
     */
    clearProgressSteps() {
        this.progressSteps.innerHTML = '';
    }

    /**
     * Show results section
     */
    showResultsSection() {
        this.hideAllSections();
        this.resultsSection.classList.remove('hidden');
        this.resultsSection.classList.add('fade-in');
        
        // Hide stop button
        this.stopAnalysisBtn.classList.add('hidden');
    }

    /**
     * Display comprehensive results
     */
    displayResults(resultData) {
        this.resultsContent.innerHTML = '';
        
        // Create results grid
        const resultsHTML = this.generateResultsHTML(resultData);
        this.resultsContent.innerHTML = resultsHTML;
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Generate HTML for results display
     */
    generateResultsHTML(resultData) {
        let html = '';

        // 1. Identified Problems
        html += this.generateProblemsHTML(resultData);

        // 2. Market Maturity
        html += this.generateMarketHTML(resultData);

        // 3. Solution Goals
        html += this.generateGoalsHTML(resultData);

        // 4. SaaS Opportunities
        html += this.generateOpportunitiesHTML(resultData);

        // 5. Innovative Features
        html += this.generateFeaturesHTML(resultData);

        // 6. Competitor Analysis
        html += this.generateCompetitorsHTML(resultData);

        // 7. Enhanced Features
        html += this.generateEnhancedFeaturesHTML(resultData);

        // 8. Data Quality
        html += this.generateDataQualityHTML(resultData);

        return html;
    }

    /**
     * Generate problems section HTML
     */
    generateProblemsHTML(resultData) {
        const problems = resultData.identified_problems?.problems || [];
        
        if (problems.length === 0) {
            return '';
        }

        let html = `
            <div class="result-card">
                <h3><i class="fas fa-exclamation-triangle"></i> Identified User Problems</h3>
        `;

        problems.forEach((problem, index) => {
            html += `
                <div class="result-item">
                    <h4>Problem ${index + 1}</h4>
                    <p><strong>Issue:</strong> ${problem.problem || 'N/A'}</p>
                    <p><strong>Evidence:</strong> ${problem.evidence || 'N/A'}</p>
                    <div class="meta">
                        <span class="meta-item">Severity: ${problem.severity || 'N/A'}/10</span>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    /**
     * Generate market maturity section HTML
     */
    generateMarketHTML(resultData) {
        const market = resultData.market_maturity;
        
        if (!market) {
            return '';
        }

        return `
            <div class="result-card">
                <h3><i class="fas fa-chart-line"></i> Market Maturity Analysis</h3>
                <div class="result-item">
                    <h4>Market Assessment</h4>
                    <p><strong>Stage:</strong> ${market.stage?.toUpperCase() || 'N/A'}</p>
                    <p><strong>Trend Direction:</strong> ${market.trend_direction || 'N/A'}</p>
                    <p><strong>Confidence:</strong> ${market.confidence ? `${(market.confidence * 100).toFixed(1)}%` : 'N/A'}</p>
                    <p><strong>Reasoning:</strong> ${market.reasoning || 'N/A'}</p>
                </div>
            </div>
        `;
    }

    /**
     * Generate goals section HTML
     */
    generateGoalsHTML(resultData) {
        const goals = resultData.solution_goals?.goals || [];
        
        if (goals.length === 0) {
            return '';
        }

        let html = `
            <div class="result-card">
                <h3><i class="fas fa-bullseye"></i> Solution Goals</h3>
        `;

        goals.forEach((goal, index) => {
            html += `
                <div class="result-item">
                    <h4>Goal ${index + 1}</h4>
                    <p><strong>Objective:</strong> ${goal.goal || 'N/A'}</p>
                    <p><strong>Target Audience:</strong> ${goal.target_audience || 'N/A'}</p>
                    <p><strong>Value Proposition:</strong> ${goal.value_proposition || 'N/A'}</p>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    /**
     * Generate opportunities section HTML
     */
    generateOpportunitiesHTML(resultData) {
        const saasOpps = resultData.saas_opportunities;
        const categories = saasOpps?.categories || [];
        
        if (categories.length === 0) {
            return '';
        }

        let html = `
            <div class="result-card">
                <h3><i class="fas fa-lightbulb"></i> SaaS Solution Opportunities</h3>
        `;

        categories.forEach((category, index) => {
            html += `
                <div class="result-item">
                    <h4>${category.category || 'N/A'}</h4>
                    <p><strong>Description:</strong> ${category.description || 'N/A'}</p>
                    <p><strong>Market Fit Score:</strong> ${category.market_fit_score || 'N/A'}/10</p>
                    <p><strong>Key Features:</strong></p>
                    <ul class="feature-list">
                        ${(category.key_features || []).map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                </div>
            `;
        });

        if (saasOpps.recommended_category) {
            html += `
                <div class="result-item" style="background: rgba(102, 126, 234, 0.1); border-left-color: #667eea;">
                    <h4>🏆 Recommended Category</h4>
                    <p><strong>${saasOpps.recommended_category}</strong></p>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    /**
     * Generate features section HTML
     */
    generateFeaturesHTML(resultData) {
        const featuresData = resultData.innovative_features;
        const features = featuresData?.features || [];
        
        if (features.length === 0) {
            return '';
        }

        let html = `
            <div class="result-card">
                <h3><i class="fas fa-rocket"></i> Innovative Features</h3>
        `;

        // MVP Features
        const mvpFeatures = featuresData.mvp_features || [];
        if (mvpFeatures.length > 0) {
            html += '<h4 style="margin: 1rem 0 0.5rem 0; color: #667eea;">🎯 MVP Features (Priority)</h4>';
            mvpFeatures.forEach(featureName => {
                const feature = features.find(f => f.name === featureName);
                if (feature) {
                    html += this.generateFeatureItemHTML(feature, 'mvp');
                }
            });
        }

        // Advanced Features
        const advancedFeatures = featuresData.advanced_features || [];
        if (advancedFeatures.length > 0) {
            html += '<h4 style="margin: 1rem 0 0.5rem 0; color: #667eea;">🔮 Advanced Features (Future)</h4>';
            advancedFeatures.forEach(featureName => {
                const feature = features.find(f => f.name === featureName);
                if (feature) {
                    html += this.generateFeatureItemHTML(feature, 'advanced');
                }
            });
        }

        // Technical Considerations
        if (featuresData.technical_considerations) {
            html += `
                <div class="result-item">
                    <h4>🔧 Technical Considerations</h4>
                    <p>${featuresData.technical_considerations}</p>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    /**
     * Generate feature item HTML
     */
    generateFeatureItemHTML(feature, type) {
        const typeClass = type === 'mvp' ? 'mvp-feature' : 'advanced-feature';
        
        return `
            <div class="result-item ${typeClass}">
                <h4>${feature.name || 'N/A'}</h4>
                <p><strong>Description:</strong> ${feature.description || 'N/A'}</p>
                <p><strong>User Value:</strong> ${feature.user_value || 'N/A'}</p>
                <p><strong>Competitive Advantage:</strong> ${feature.competitive_advantage || 'N/A'}</p>
                <div class="meta">
                    <span class="meta-item">Innovation: ${feature.innovation_level || 'N/A'}/10</span>
                    <span class="meta-item">Complexity: ${feature.implementation_complexity || 'N/A'}</span>
                    ${(feature.tags || []).map(tag => `<span class="meta-item">${tag}</span>`).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Generate competitors section HTML
     */
    generateCompetitorsHTML(resultData) {
        const competitorData = resultData.competitor_analysis;
        const competitors = competitorData?.competitors || [];
        
        if (competitors.length === 0) {
            return '';
        }

        let html = `
            <div class="result-card">
                <h3><i class="fas fa-users"></i> Competitor Analysis</h3>
        `;

        competitors.forEach((competitor, index) => {
            html += `
                <div class="result-item">
                    <h4>${competitor.name || 'N/A'}</h4>
                    <p><strong>Website:</strong> <a href="${competitor.website || '#'}" target="_blank">${competitor.website || 'N/A'}</a></p>
                    <p><strong>Description:</strong> ${competitor.description || 'N/A'}</p>
                    <p><strong>Market Position:</strong> ${competitor.market_position || 'N/A'}</p>
                    ${competitor.features?.length > 0 ? `<p><strong>Features:</strong> ${competitor.features.slice(0, 3).join(', ')}${competitor.features.length > 3 ? '...' : ''}</p>` : ''}
                    ${competitor.strengths?.length > 0 ? `<p><strong>Strengths:</strong> ${competitor.strengths.slice(0, 2).join(', ')}${competitor.strengths.length > 2 ? '...' : ''}</p>` : ''}
                    ${competitor.weaknesses?.length > 0 ? `<p><strong>Weaknesses:</strong> ${competitor.weaknesses.slice(0, 2).join(', ')}${competitor.weaknesses.length > 2 ? '...' : ''}</p>` : ''}
                </div>
            `;
        });

        // Market gaps and opportunities
        const marketGaps = competitorData.market_gaps || [];
        const missingFeatures = competitorData.missing_features || [];
        const competitiveAdvantages = competitorData.competitive_advantages || [];

        if (marketGaps.length > 0) {
            html += `
                <div class="result-item">
                    <h4>📈 Market Gaps</h4>
                    <ul class="feature-list">
                        ${marketGaps.slice(0, 5).map(gap => `<li>${gap}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (missingFeatures.length > 0) {
            html += `
                <div class="result-item">
                    <h4>❌ Missing Features</h4>
                    <ul class="feature-list">
                        ${missingFeatures.slice(0, 5).map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (competitiveAdvantages.length > 0) {
            html += `
                <div class="result-item">
                    <h4>🏆 Competitive Advantages</h4>
                    <ul class="feature-list">
                        ${competitiveAdvantages.slice(0, 5).map(advantage => `<li>${advantage}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    /**
     * Generate enhanced features section HTML
     */
    generateEnhancedFeaturesHTML(resultData) {
        const enhancedData = resultData.enhanced_features;
        const enhancedFeatures = enhancedData?.enhanced_features || [];
        
        if (enhancedFeatures.length === 0) {
            return '';
        }

        let html = `
            <div class="result-card">
                <h3><i class="fas fa-star"></i> Enhanced Features (Post-Competitor Analysis)</h3>
        `;

        enhancedFeatures.slice(0, 5).forEach((feature, index) => {
            html += `
                <div class="result-item">
                    <h4>${feature.name || 'N/A'}</h4>
                    <p><strong>Description:</strong> ${feature.description || 'N/A'}</p>
                    <p><strong>Competitive Advantage:</strong> ${feature.competitive_advantage || 'N/A'}</p>
                    <div class="meta">
                        <span class="meta-item">Innovation: ${feature.innovation_level || 'N/A'}/10</span>
                        ${(feature.tags || []).map(tag => `<span class="meta-item">${tag}</span>`).join('')}
                    </div>
                </div>
            `;
        });

        if (enhancedData.competitive_strategy) {
            html += `
                <div class="result-item">
                    <h4>🎯 Competitive Strategy</h4>
                    <p>${enhancedData.competitive_strategy}</p>
                </div>
            `;
        }

        const implementationPriorities = enhancedData.implementation_priorities || [];
        if (implementationPriorities.length > 0) {
            html += `
                <div class="result-item">
                    <h4>📋 Implementation Priorities</h4>
                    <ul class="feature-list">
                        ${implementationPriorities.slice(0, 5).map(priority => `<li>${priority}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    /**
     * Generate data quality section HTML
     */
    generateDataQualityHTML(resultData) {
        const qualityData = resultData.data_quality_assessment;
        
        if (!qualityData) {
            return '';
        }

        const qualityMetrics = qualityData.quality_metrics || {};
        const recommendations = qualityData.recommendations || [];

        return `
            <div class="result-card">
                <h3><i class="fas fa-chart-bar"></i> Data Quality Assessment</h3>
                <div class="result-item">
                    <h4>Quality Metrics</h4>
                    <p><strong>Completeness Score:</strong> ${qualityData.data_completeness_score ? `${(qualityData.data_completeness_score * 100).toFixed(1)}%` : 'N/A'}</p>
                    <p><strong>Has Interest Data:</strong> ${qualityMetrics.has_interest_data ? '✅ Yes' : '❌ No'}</p>
                    <p><strong>Has Related Queries:</strong> ${qualityMetrics.has_related_queries ? '✅ Yes' : '❌ No'}</p>
                    <p><strong>Has Rising Searches:</strong> ${qualityMetrics.has_rising_searches ? '✅ Yes' : '❌ No'}</p>
                    ${recommendations.length > 0 ? `
                        <p><strong>Recommendations:</strong></p>
                        <ul class="feature-list">
                            ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Show error section
     */
    showErrorSection(message) {
        this.hideAllSections();
        this.errorMessage.textContent = message;
        this.errorSection.classList.remove('hidden');
        this.errorSection.classList.add('fade-in');
        
        // Hide stop button
        this.stopAnalysisBtn.classList.add('hidden');
    }

    /**
     * Show loading overlay
     */
    showLoadingOverlay() {
        this.loadingOverlay.classList.remove('hidden');
    }

    /**
     * Hide loading overlay
     */
    hideLoadingOverlay() {
        this.loadingOverlay.classList.add('hidden');
    }

    /**
     * Hide all sections
     */
    hideAllSections() {
        this.inputSection.classList.add('hidden');
        this.progressSection.classList.add('hidden');
        this.resultsSection.classList.add('hidden');
        this.errorSection.classList.add('hidden');
    }

    /**
     * Reset to input section
     */
    resetToInput() {
        console.log('🔄 Resetting to input section');
        
        // Hide all sections
        this.hideAllSections();
        
        // Show input section
        this.inputSection.classList.remove('hidden');
        
        // Clear form
        this.analysisForm.reset();
        this.keywordInput.value = '';
        
        // Reset button state
        this.analyzeBtn.disabled = false;
        
        // Clear any error messages
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(msg => msg.remove());
        
        // Only disconnect if we're not in the middle of analysis
        if (window.trendSaaSApp && window.trendSaaSApp.websocket) {
            const isAnalyzing = window.trendSaaSApp.isAnalyzing;
            const hasActiveAnalysis = window.trendSaaSApp.websocket.currentAnalysis && 
                                    window.trendSaaSApp.websocket.currentAnalysis.progress < 100;
            
            if (!isAnalyzing && !hasActiveAnalysis) {
                console.log('🔄 No active analysis, disconnecting WebSocket');
                window.trendSaaSApp.websocket.disconnect();
            } else {
                console.log('⚠️ Active analysis in progress, keeping WebSocket connection');
            }
        }
        
        // Hide stop button
        this.stopAnalysisBtn.classList.add('hidden');
        
        // Update connection status
        this.updateConnectionStatus('disconnected');
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * Stop analysis
     */
    stopAnalysis() {
        if (confirm('Are you sure you want to stop the analysis? This action cannot be undone.')) {
            console.log('🛑 User requested to stop analysis');
            
            // Force disconnect WebSocket only if user explicitly wants to stop
            if (window.trendSaaSApp && window.trendSaaSApp.websocket) {
                window.trendSaaSApp.websocket.forceDisconnect();
            }
            
            // Reset to input
            this.resetToInput();
            
            // Show message
            alert('Analysis stopped. You can start a new analysis when ready.');
        }
    }

    /**
     * Get current keyword
     */
    getCurrentKeyword() {
        return this.currentKeyword;
    }

    /**
     * Update connection status
     */
    updateConnectionStatus(status, details = '') {
        if (!this.connectionStatus || !this.statusIndicator || !this.statusText) {
            return;
        }

        // Remove all status classes
        this.statusIndicator.classList.remove('connected', 'connecting', 'disconnected', 'reconnecting');
        
        switch (status) {
            case 'connected':
                this.statusIndicator.classList.add('connected');
                this.statusText.textContent = 'Connected';
                break;
            case 'connecting':
                this.statusIndicator.classList.add('connecting');
                this.statusText.textContent = 'Connecting...';
                break;
            case 'reconnecting':
                this.statusIndicator.classList.add('reconnecting');
                this.statusText.textContent = `Reconnecting... (${details})`;
                break;
            case 'disconnected':
                this.statusIndicator.classList.add('disconnected');
                this.statusText.textContent = 'Disconnected';
                break;
            default:
                this.statusIndicator.classList.add('disconnected');
                this.statusText.textContent = 'Unknown';
        }
    }

    /**
     * Show reconnection message
     */
    showReconnectionMessage(attempt, maxAttempts) {
        const message = `Connection lost during analysis. Reconnecting... (${attempt}/${maxAttempts})`;
        
        // Update progress message
        if (this.progressMessage) {
            this.progressMessage.textContent = message;
        }
        
        // Update connection status
        this.updateConnectionStatus('reconnecting', `${attempt}/${maxAttempts}`);
    }
}

// Export for use in other scripts
window.TrendSaaSUI = TrendSaaSUI; 