/**
 * Main Application for TrendSaaS Frontend
 * Orchestrates WebSocket connection, UI updates, and analysis flow
 */

class TrendSaaSApp {
    constructor() {
        this.websocket = null;
        this.ui = null;
        this.isAnalyzing = false;
        this.currentKeyword = '';
        
        this.initialize();
    }

    /**
     * Initialize the application
     */
    initialize() {
        console.log('🚀 Initializing TrendSaaS Frontend...');
        
        // Initialize UI manager
        this.ui = new TrendSaaSUI();
        
        // Initialize WebSocket
        this.websocket = new TrendSaaSWebSocket();
        
        // Setup WebSocket event handlers
        this.setupWebSocketHandlers();
        
        // Setup application event listeners
        this.setupEventListeners();
        
        console.log('✅ TrendSaaS Frontend initialized successfully');
    }

    /**
     * Setup WebSocket event handlers
     */
    setupWebSocketHandlers() {
        // Connection events
        this.websocket.onConnect = () => {
            console.log('✅ WebSocket connected');
            this.ui.hideLoadingOverlay();
            this.ui.updateConnectionStatus('connected');
        };

        this.websocket.onDisconnect = (event) => {
            console.log('🔌 WebSocket disconnected:', event);
            this.ui.updateConnectionStatus('disconnected');
            
            if (this.isAnalyzing) {
                this.ui.showErrorSection('Connection lost during analysis. Please try again.');
                this.isAnalyzing = false;
            }
        };

        // Progress updates
        this.websocket.onProgress = (data) => {
            console.log('📊 Progress update:', data);
            this.handleProgressUpdate(data);
        };

        // Results
        this.websocket.onResult = (data) => {
            console.log('✅ Analysis completed:', data);
            this.handleAnalysisComplete(data);
        };

        // Errors
        this.websocket.onError = (error) => {
            console.error('❌ WebSocket error:', error);
            this.handleError(error);
        };

        // Reconnecting
        this.websocket.onReconnecting = (attempt, maxAttempts) => {
            console.log(`🔄 Reconnecting attempt ${attempt}/${maxAttempts}`);
            this.ui.showReconnectionMessage(attempt, maxAttempts);
        };
    }

    /**
     * Setup application event listeners
     */
    setupEventListeners() {
        // Listen for analysis start events from UI
        document.addEventListener('startAnalysis', (event) => {
            const keyword = event.detail.keyword;
            this.startAnalysis(keyword);
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('📱 Page hidden');
            } else {
                console.log('📱 Page visible');
                // Reconnect if needed
                if (this.isAnalyzing && !this.websocket.isReady()) {
                    this.reconnectWebSocket();
                }
            }
        });

        // Handle page unload - only force disconnect if not analyzing
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                // Only force disconnect if we're not in the middle of analysis
                if (!this.isAnalyzing || (this.websocket.currentAnalysis && this.websocket.currentAnalysis.progress >= 100)) {
                    this.websocket.forceDisconnect();
                } else {
                    console.log('⚠️ Preventing force disconnect during active analysis');
                }
            }
        });

        // Handle page focus to check connection status
        window.addEventListener('focus', () => {
            if (this.isAnalyzing && this.websocket && !this.websocket.isReady()) {
                console.log('🔄 Page focused, checking WebSocket connection...');
                this.reconnectWebSocket();
            }
        });
    }

    /**
     * Start analysis for a keyword
     */
    async startAnalysis(keyword) {
        if (this.isAnalyzing) {
            console.warn('⚠️ Analysis already in progress');
            return;
        }

        this.currentKeyword = keyword;
        this.isAnalyzing = true;

        console.log(`🎯 Starting analysis for: "${keyword}"`);

        try {
            // Show loading overlay
            this.ui.showLoadingOverlay();
            this.ui.updateConnectionStatus('connecting');

            // Connect to WebSocket if not already connected
            if (!this.websocket.isReady()) {
                await this.websocket.connect();
            }

            // Start analysis
            this.websocket.startAnalysis(keyword);

            console.log('📤 Analysis request sent successfully');

        } catch (error) {
            console.error('❌ Failed to start analysis:', error);
            this.handleError(`Failed to start analysis: ${error.message}`);
            this.isAnalyzing = false;
        }
    }

    /**
     * Handle progress updates from WebSocket
     */
    handleProgressUpdate(data) {
        const { progress, message, step, timestamp } = data;
        
        // Update UI progress
        this.ui.updateProgress(progress, message);
        
        // Log progress for debugging
        console.log(`📊 Progress: ${progress}% - ${message}`);
        
        // Handle specific step updates
        this.handleStepUpdate(step, data);
    }

    /**
     * Handle specific step updates
     */
    handleStepUpdate(step, data) {
        switch (step) {
            case 'start':
                console.log('🚀 Analysis started');
                break;
                
            case 'fetching_trends':
                console.log('📊 Fetching trends data...');
                break;
                
            case 'trends_fetched':
                console.log('✅ Trends data fetched successfully');
                break;
                
            case 'extracting_problems':
                console.log('🔍 Extracting user problems...');
                break;
                
            case 'problems_extracted':
                const problemsCount = data.problems_count || 0;
                console.log(`✅ ${problemsCount} problems extracted`);
                break;
                
            case 'analyzing_market':
                console.log('📈 Analyzing market maturity...');
                break;
                
            case 'market_analyzed':
                const marketStage = data.market_stage || 'unknown';
                console.log(`✅ Market analyzed: ${marketStage} stage`);
                break;
                
            case 'extracting_goals':
                console.log('🎯 Extracting solution goals...');
                break;
                
            case 'goals_extracted':
                const goalsCount = data.goals_count || 0;
                console.log(`✅ ${goalsCount} goals extracted`);
                break;
                
            case 'suggesting_categories':
                console.log('💡 Suggesting SaaS categories...');
                break;
                
            case 'generating_features':
                console.log('🚀 Generating innovative features...');
                break;
                
            case 'features_generated':
                const featuresCount = data.features_count || 0;
                console.log(`✅ ${featuresCount} features generated`);
                break;
                
            case 'analyzing_competitors':
                console.log('👥 Analyzing competitors...');
                break;
                
            case 'enhancing_features':
                console.log('⭐ Enhancing features...');
                break;
                
            case 'completed':
                console.log('🎉 Analysis completed!');
                break;
                
            default:
                console.log(`📝 Step: ${step}`);
                break;
        }
    }

    /**
     * Handle analysis completion
     */
    handleAnalysisComplete(data) {
        this.isAnalyzing = false;
        
        try {
            // Show results section
            this.ui.showResultsSection();
            
            // Display comprehensive results
            this.ui.displayResults(data.result);
            
            console.log('✅ Results displayed successfully');
            
            // Mark analysis as completed in WebSocket state
            if (this.websocket && this.websocket.currentAnalysis) {
                this.websocket.currentAnalysis.progress = 100;
                this.websocket.saveAnalysisState();
            }
            
            // Keep WebSocket connection alive for future analyses
            // Only disconnect when user explicitly requests or page is closed
            
        } catch (error) {
            console.error('❌ Error displaying results:', error);
            this.handleError('Failed to display results. Please try again.');
        }
    }

    /**
     * Handle errors
     */
    handleError(error) {
        this.isAnalyzing = false;
        
        console.error('❌ Application error:', error);
        
        // Show error in UI
        this.ui.showErrorSection(error);
        
        // Don't disconnect WebSocket on error - let it handle reconnection
        // Only disconnect if it's a critical error
        if (error.includes('Failed to connect') || error.includes('Invalid message format')) {
            if (this.websocket) {
                this.websocket.disconnect();
            }
        }
    }

    /**
     * Reconnect WebSocket
     */
    async reconnectWebSocket() {
        if (this.isAnalyzing) {
            console.log('🔄 Attempting to reconnect WebSocket...');
            
            try {
                await this.websocket.connect();
                console.log('✅ WebSocket reconnected successfully');
                
                // Restart analysis if needed
                if (this.currentKeyword) {
                    this.websocket.startAnalysis(this.currentKeyword);
                }
                
            } catch (error) {
                console.error('❌ Failed to reconnect:', error);
                this.handleError('Failed to reconnect to server. Please refresh the page.');
            }
        }
    }

    /**
     * Get application status
     */
    getStatus() {
        return {
            isAnalyzing: this.isAnalyzing,
            currentKeyword: this.currentKeyword,
            websocketStatus: this.websocket ? this.websocket.getConnectionStatus() : 'disconnected',
            websocketReady: this.websocket ? this.websocket.isReady() : false,
            uiReady: !!this.ui
        };
    }

    /**
     * Reset application state
     */
    reset() {
        this.isAnalyzing = false;
        this.currentKeyword = '';
        
        if (this.websocket) {
            this.websocket.disconnect();
        }
        
        console.log('🔄 Application state reset');
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM loaded, initializing TrendSaaS application...');
    
    // Create global app instance
    window.trendSaaSApp = new TrendSaaSApp();
    
    // Add some helpful console commands for debugging
    window.trendSaaSDebug = {
        getStatus: () => window.trendSaaSApp.getStatus(),
        reset: () => window.trendSaaSApp.reset(),
        reconnect: () => window.trendSaaSApp.reconnectWebSocket()
    };
    
    console.log('✅ TrendSaaS application ready!');
    console.log('💡 Debug commands available: trendSaaSDebug.getStatus(), trendSaaSDebug.reset(), trendSaaSDebug.reconnect()');
});

// Handle any unhandled errors
window.addEventListener('error', (event) => {
    console.error('❌ Unhandled error:', event.error);
    
    if (window.trendSaaSApp) {
        window.trendSaaSApp.handleError('An unexpected error occurred. Please refresh the page.');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('❌ Unhandled promise rejection:', event.reason);
    
    if (window.trendSaaSApp) {
        window.trendSaaSApp.handleError('A network error occurred. Please check your connection and try again.');
    }
}); 