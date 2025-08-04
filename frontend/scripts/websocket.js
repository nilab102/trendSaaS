/**
 * WebSocket Handler for TrendSaaS API
 * Manages WebSocket connection and communication with the backend
 */

class TrendSaaSWebSocket {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5; // Increased max attempts
        this.reconnectDelay = 2000; // Increased delay for stability
        this.serverUrl = this.getServerUrl();
        
        // Analysis state
        this.currentAnalysis = null;
        this.lastProgress = 0;
        this.analysisStartTime = null;
        
        // Connection health
        this.lastPongTime = null;
        this.heartbeatInterval = null;
        this.connectionHealthCheck = null;
        this.connectionStable = false;
        
        // Event callbacks
        this.onProgress = null;
        this.onResult = null;
        this.onError = null;
        this.onConnect = null;
        this.onDisconnect = null;
        this.onReconnecting = null;
    }

    /**
     * Get the WebSocket server URL
     */
    getServerUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        // Always use port 8000 for backend API, regardless of frontend port
        const port = '8000';
        return `${protocol}//${host}:${port}/api/v1/analyzer/ws`;
    }

    /**
     * Connect to the WebSocket server
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                console.log('Connecting to WebSocket:', this.serverUrl);
                
                this.websocket = new WebSocket(this.serverUrl);
                
                this.websocket.onopen = () => {
                    console.log('✅ WebSocket connected successfully');
                    this.isConnected = true;
                    this.connectionStable = true;
                    this.reconnectAttempts = 0;
                    this.lastPongTime = Date.now();
                    
                    // Start heartbeat with delay to ensure connection is stable
                    setTimeout(() => {
                        this.startHeartbeat();
                    }, 2000);
                    
                    // Resume analysis if we have one in progress
                    this.resumeAnalysisIfNeeded();
                    
                    if (this.onConnect) {
                        this.onConnect();
                    }
                    
                    resolve();
                };
                
                this.websocket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    } catch (error) {
                        console.error('❌ Error parsing WebSocket message:', error);
                        if (this.onError) {
                            this.onError('Invalid message format received from server');
                        }
                    }
                };
                
                this.websocket.onclose = (event) => {
                    console.log('🔌 WebSocket connection closed:', event.code, event.reason);
                    this.isConnected = false;
                    this.connectionStable = false;
                    
                    // Stop heartbeat
                    this.stopHeartbeat();
                    
                    if (this.onDisconnect) {
                        this.onDisconnect(event);
                    }
                    
                    // Only attempt reconnect for unexpected closures or during active analysis
                    if (event.code !== 1000) {
                        if (this.currentAnalysis && this.currentAnalysis.progress < 100 && this.reconnectAttempts < this.maxReconnectAttempts) {
                            console.log('🔄 Connection lost during analysis, attempting to reconnect...');
                            this.attemptReconnect();
                        } else if (this.reconnectAttempts < this.maxReconnectAttempts) {
                            console.log('🔄 Attempting to reconnect due to unexpected closure...');
                            this.attemptReconnect();
                        } else {
                            console.log('❌ Max reconnection attempts reached');
                        }
                    } else {
                        console.log('✅ WebSocket closed normally');
                    }
                };
                
                this.websocket.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    this.isConnected = false;
                    this.connectionStable = false;
                    reject(new Error('Failed to connect to WebSocket server'));
                };
                
            } catch (error) {
                console.error('❌ Error creating WebSocket connection:', error);
                reject(error);
            }
        });
    }

    /**
     * Attempt to reconnect to the WebSocket server
     */
    attemptReconnect() {
        this.reconnectAttempts++;
        console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        
        // Notify UI about reconnection attempt
        if (this.onReconnecting) {
            this.onReconnecting(this.reconnectAttempts, this.maxReconnectAttempts);
        }
        
        setTimeout(() => {
            this.connect().catch(error => {
                console.error('❌ Reconnection failed:', error);
                if (this.onError) {
                    this.onError('Failed to reconnect to server');
                }
            });
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    /**
     * Start heartbeat mechanism
     */
    startHeartbeat() {
        // Clear existing heartbeat
        this.stopHeartbeat();
        
        // Send heartbeat every 15 seconds (increased from 10)
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected && this.websocket && this.connectionStable) {
                try {
                    this.websocket.send(JSON.stringify({ type: 'ping' }));
                    console.log('🏓 Heartbeat ping sent');
                } catch (error) {
                    console.warn('⚠️ Failed to send heartbeat:', error);
                    // Don't immediately disconnect, just log the warning
                }
            }
        }, 15000); // 15 seconds
        
        // Check connection health every 60 seconds (increased from 30)
        this.connectionHealthCheck = setInterval(() => {
            this.checkConnectionHealth();
        }, 60000); // 60 seconds
    }

    /**
     * Stop heartbeat mechanism
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        if (this.connectionHealthCheck) {
            clearInterval(this.connectionHealthCheck);
            this.connectionHealthCheck = null;
        }
    }

    /**
     * Check connection health
     */
    checkConnectionHealth() {
        if (!this.lastPongTime) return;
        
        const timeSinceLastPong = Date.now() - this.lastPongTime;
        const maxTimeWithoutPong = 120000; // 120 seconds (increased from 60)
        
        if (timeSinceLastPong > maxTimeWithoutPong) {
            console.warn('⚠️ No pong received for too long, connection may be stale');
            // Only handle connection issue if we're not in the middle of analysis
            if (!this.currentAnalysis || this.currentAnalysis.progress >= 100) {
                this.handleConnectionIssue();
            }
        }
    }

    /**
     * Handle connection issues
     */
    handleConnectionIssue() {
        if (this.isConnected && this.websocket && this.connectionStable) {
            console.log('🔧 Handling connection issue, closing and reconnecting...');
            this.connectionStable = false;
            this.websocket.close(1000, 'Connection health check failed');
        }
    }

    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.websocket) {
            // Only disconnect if we're not in the middle of an analysis
            if (!this.currentAnalysis || this.currentAnalysis.progress >= 100) {
                this.websocket.close(1000, 'Client disconnecting');
                this.websocket = null;
                this.isConnected = false;
                this.connectionStable = false;
                this.stopHeartbeat();
                this.clearAnalysisState();
                console.log('🔌 WebSocket disconnected by client');
            } else {
                console.log('⚠️ Preventing disconnection during active analysis');
            }
        }
    }

    /**
     * Force disconnect (used when user explicitly wants to stop)
     */
    forceDisconnect() {
        if (this.websocket) {
            this.websocket.close(1000, 'Client force disconnecting');
            this.websocket = null;
            this.isConnected = false;
            this.connectionStable = false;
            this.stopHeartbeat();
            this.clearAnalysisState();
            console.log('🔌 WebSocket force disconnected by client');
        }
    }

    /**
     * Send a message to the WebSocket server
     */
    sendMessage(message) {
        if (!this.isConnected || !this.websocket) {
            throw new Error('WebSocket is not connected');
        }
        
        try {
            const messageStr = JSON.stringify(message);
            this.websocket.send(messageStr);
            console.log('📤 Sent message:', message);
            return true;
        } catch (error) {
            console.error('❌ Error sending message:', error);
            throw error;
        }
    }

    /**
     * Start analysis for a keyword
     */
    startAnalysis(keyword) {
        // Store analysis state
        this.currentAnalysis = {
            keyword: keyword,
            startTime: Date.now(),
            progress: 0,
            step: 'start'
        };
        
        // Save to localStorage for persistence
        this.saveAnalysisState();
        
        const message = {
            type: 'analyze',
            keyword: keyword,
            comparison: true // Always enabled as per requirements
        };
        
        return this.sendMessage(message);
    }

    /**
     * Save analysis state to localStorage
     */
    saveAnalysisState() {
        if (this.currentAnalysis) {
            const state = {
                ...this.currentAnalysis,
                timestamp: Date.now()
            };
            localStorage.setItem('trendSaaS_analysis_state', JSON.stringify(state));
        }
    }

    /**
     * Load analysis state from localStorage
     */
    loadAnalysisState() {
        try {
            const stateStr = localStorage.getItem('trendSaaS_analysis_state');
            if (stateStr) {
                const state = JSON.parse(stateStr);
                const maxAge = 30 * 60 * 1000; // 30 minutes
                
                if (Date.now() - state.timestamp < maxAge) {
                    this.currentAnalysis = state;
                    return true;
                } else {
                    // Clear old state
                    localStorage.removeItem('trendSaaS_analysis_state');
                }
            }
        } catch (error) {
            console.warn('Failed to load analysis state:', error);
        }
        return false;
    }

    /**
     * Clear analysis state
     */
    clearAnalysisState() {
        this.currentAnalysis = null;
        this.lastProgress = 0;
        this.analysisStartTime = null;
        localStorage.removeItem('trendSaaS_analysis_state');
    }

    /**
     * Resume analysis if needed
     */
    resumeAnalysisIfNeeded() {
        if (this.loadAnalysisState() && this.currentAnalysis) {
            console.log('🔄 Resuming analysis for:', this.currentAnalysis.keyword);
            
            // Check if analysis is still in progress (less than 10 minutes old)
            const analysisAge = Date.now() - this.currentAnalysis.startTime;
            const maxAnalysisAge = 10 * 60 * 1000; // 10 minutes
            
            if (analysisAge < maxAnalysisAge && this.currentAnalysis.progress < 100) {
                console.log(`📊 Resuming at ${this.currentAnalysis.progress}% progress`);
                
                // Resume the analysis
                const message = {
                    type: 'analyze',
                    keyword: this.currentAnalysis.keyword,
                    comparison: true,
                    resume: true,
                    lastProgress: this.currentAnalysis.progress
                };
                
                this.sendMessage(message);
                return true;
            } else {
                console.log('Analysis too old or completed, clearing state');
                this.clearAnalysisState();
            }
        }
        return false;
    }

    /**
     * Send ping message to keep connection alive
     */
    ping() {
        const message = { type: 'ping' };
        return this.sendMessage(message);
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(data) {
        const messageType = data.type;
        const messageText = data.message || '';
        const timestamp = data.timestamp || new Date().toISOString();
        
        console.log(`📨 Received ${messageType} message:`, data);
        
        switch (messageType) {
            case 'progress':
                this.handleProgressMessage(data);
                break;
                
            case 'result':
                this.handleResultMessage(data);
                break;
                
            case 'error':
                this.handleErrorMessage(data);
                break;
                
            case 'pong':
                console.log('🏓 Pong received');
                this.lastPongTime = Date.now();
                break;
                
            default:
                console.warn('⚠️ Unknown message type:', messageType);
                break;
        }
    }

    /**
     * Handle progress update messages
     */
    handleProgressMessage(data) {
        const progressData = data.data || {};
        const step = progressData.step || 'unknown';
        const progress = progressData.progress || 0;
        const message = data.message || '';
        
        // Update analysis state
        if (this.currentAnalysis) {
            this.currentAnalysis.progress = progress;
            this.currentAnalysis.step = step;
            this.lastProgress = progress;
            this.saveAnalysisState();
        }
        
        if (this.onProgress) {
            this.onProgress({
                step: step,
                progress: progress,
                message: message,
                data: progressData,
                timestamp: data.timestamp
            });
        }
    }

    /**
     * Handle result messages
     */
    handleResultMessage(data) {
        const resultData = data.data?.result || {};
        
        // Clear analysis state on completion
        this.clearAnalysisState();
        
        if (this.onResult) {
            this.onResult({
                result: resultData,
                message: data.message || '',
                timestamp: data.timestamp
            });
        }
    }

    /**
     * Handle error messages
     */
    handleErrorMessage(data) {
        const errorMessage = data.message || 'An unknown error occurred';
        
        console.error('❌ Server error:', errorMessage);
        
        if (this.onError) {
            this.onError(errorMessage);
        }
    }

    /**
     * Check if WebSocket is connected (fixed naming conflict)
     */
    getConnectionStatus() {
        if (!this.websocket) {
            return 'disconnected';
        }
        
        switch (this.websocket.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return this.isConnected ? 'connected' : 'disconnected';
            case WebSocket.CLOSING:
                return 'closing';
            case WebSocket.CLOSED:
                return 'disconnected';
            default:
                return 'unknown';
        }
    }

    /**
     * Check if WebSocket is ready for communication
     */
    isReady() {
        return this.isConnected && this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }
}

// Export for use in other scripts
window.TrendSaaSWebSocket = TrendSaaSWebSocket; 