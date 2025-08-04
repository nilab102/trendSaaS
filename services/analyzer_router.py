import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Import the analyzer classes from data_analyzer.py
from .data_analyzer import SaaSOpportunityAnalyzer, TrendsClient

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/analyzer", tags=["analyzer"])

# Pydantic Models for API requests/responses
class AnalysisRequest(BaseModel):
    keyword: str = Field(..., description="Keyword to analyze", min_length=1, max_length=100)
    comparison: bool = Field(False, description="Enable comparison mode")
    include_competitors: bool = Field(True, description="Include competitor analysis")

class AnalysisResponse(BaseModel):
    keyword: str
    analysis_timestamp: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class WebSocketMessage(BaseModel):
    type: str  # "progress", "result", "error"
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

# Initialize connection manager
manager = ConnectionManager()

# Initialize analyzer
analyzer = SaaSOpportunityAnalyzer()

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SaaS Opportunity Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyzer/analyze/{keyword}",
            "websocket": "/analyzer/ws",
            "health": "/analyzer/health"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SaaS Opportunity Analyzer"
    }

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_keyword_sync(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze a keyword for SaaS opportunities (synchronous)
    
    Args:
        request: Analysis request with keyword and options
    
    Returns:
        Analysis results
    """
    try:
        logger.info(f"Starting analysis for keyword: '{request.keyword}'")
        
        # Run the analysis
        results = await analyzer.analyze_keyword(
            request.keyword, 
            request.comparison
        )
        
        return AnalysisResponse(
            keyword=request.keyword,
            analysis_timestamp=datetime.now().isoformat(),
            status="completed",
            message="Analysis completed successfully",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Analysis failed for '{request.keyword}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/analyze/{keyword}", response_model=AnalysisResponse)
async def analyze_keyword_get(
    keyword: str = Path(..., description="Keyword to analyze", min_length=1, max_length=100),
    comparison: bool = Query(False, description="Enable comparison mode"),
    include_competitors: bool = Query(True, description="Include competitor analysis")
) -> AnalysisResponse:
    """
    Analyze a keyword for SaaS opportunities (GET endpoint)
    
    Args:
        keyword: The search term to analyze
        comparison: Whether to enable comparison mode
        include_competitors: Whether to include competitor analysis
    
    Returns:
        Analysis results
    """
    try:
        logger.info(f"Starting analysis for keyword: '{keyword}'")
        
        # Run the analysis
        results = await analyzer.analyze_keyword(keyword, comparison)
        
        return AnalysisResponse(
            keyword=keyword,
            analysis_timestamp=datetime.now().isoformat(),
            status="completed",
            message="Analysis completed successfully",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Analysis failed for '{keyword}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time analysis updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            
            try:
                # Parse the message
                message_data = json.loads(data)
                message_type = message_data.get("type", "analyze")
                
                if message_type == "analyze":
                    # Handle analysis request
                    keyword = message_data.get("keyword", "")
                    comparison = message_data.get("comparison", False)
                    
                    if not keyword:
                        await manager.send_personal_message(
                            json.dumps(WebSocketMessage(
                                type="error",
                                message="Keyword is required",
                                timestamp=datetime.now().isoformat()
                            ).dict()),
                            websocket
                        )
                        continue
                    
                    # Start analysis with progress updates
                    await run_analysis_with_progress(websocket, keyword, comparison)
                
                elif message_type == "ping":
                    # Handle ping message
                    await manager.send_personal_message(
                        json.dumps(WebSocketMessage(
                            type="pong",
                            message="pong",
                            timestamp=datetime.now().isoformat()
                        ).dict()),
                        websocket
                    )
                
                else:
                    await manager.send_personal_message(
                        json.dumps(WebSocketMessage(
                            type="error",
                            message=f"Unknown message type: {message_type}",
                            timestamp=datetime.now().isoformat()
                        ).dict()),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps(WebSocketMessage(
                        type="error",
                        message="Invalid JSON format",
                        timestamp=datetime.now().isoformat()
                    ).dict()),
                    websocket
                )
            except Exception as e:
                await manager.send_personal_message(
                    json.dumps(WebSocketMessage(
                        type="error",
                        message=f"Error processing message: {str(e)}",
                        timestamp=datetime.now().isoformat()
                    ).dict()),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def run_analysis_with_progress(websocket: WebSocket, keyword: str, comparison: bool):
    """Run analysis with real-time progress updates via WebSocket"""
    try:
        # Send start message
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Starting analysis...",
                data={"step": "start", "keyword": keyword},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        # Step 0: Fetch trends data
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Fetching Google Trends data...",
                data={"step": "fetching_trends", "progress": 10},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        trends_client = TrendsClient()
        trends_data = await trends_client.get_trends_data(keyword, comparison)
        
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Trends data fetched successfully",
                data={"step": "trends_fetched", "progress": 20},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        # Step 1: Extract problems
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Extracting user problems...",
                data={"step": "extracting_problems", "progress": 30},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        problems = await analyzer.pipeline.step_1_extract_problems(trends_data)
        
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message=f"Problems extracted: {len(problems.problems)} problems identified",
                data={"step": "problems_extracted", "progress": 40, "problems_count": len(problems.problems)},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        # Step 2: Analyze market maturity
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Analyzing market maturity...",
                data={"step": "analyzing_market", "progress": 50},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        market_maturity = await analyzer.pipeline.step_2_analyze_market_maturity(trends_data)
        
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message=f"Market maturity analyzed: {market_maturity.stage} stage",
                data={"step": "market_analyzed", "progress": 60, "market_stage": market_maturity.stage},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        # Step 3a: Extract goals
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Extracting solution goals...",
                data={"step": "extracting_goals", "progress": 70},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        goals = await analyzer.pipeline.step_3a_extract_goals(problems)
        
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message=f"Goals extracted: {len(goals.goals)} goals defined",
                data={"step": "goals_extracted", "progress": 80, "goals_count": len(goals.goals)},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        # Step 3b: Suggest feature categories
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Suggesting SaaS solution categories...",
                data={"step": "suggesting_categories", "progress": 85},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        feature_suggestions = await analyzer.pipeline.step_3b_suggest_feature_categories(goals, market_maturity)
        
        # Step 3c: Generate innovative features
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message="Generating innovative SaaS features...",
                data={"step": "generating_features", "progress": 90},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        innovative_features = await analyzer.pipeline.step_3c_generate_features(
            feature_suggestions, goals, keyword, trends_data
        )
        
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="progress",
                message=f"Features generated: {len(innovative_features.features)} features created",
                data={"step": "features_generated", "progress": 95, "features_count": len(innovative_features.features)},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
        # Step 4: Analyze competitors (if enabled)
        if hasattr(analyzer.pipeline, 'competitor_fetcher') and analyzer.pipeline.competitor_fetcher:
            await manager.send_personal_message(
                json.dumps(WebSocketMessage(
                    type="progress",
                    message="Analyzing competitors...",
                    data={"step": "analyzing_competitors", "progress": 97},
                    timestamp=datetime.now().isoformat()
                ).dict()),
                websocket
            )
            
            competitor_analysis = await analyzer.pipeline.step_4_analyze_competitors(keyword, innovative_features)
            
            # Step 5: Enhance features
            await manager.send_personal_message(
                json.dumps(WebSocketMessage(
                    type="progress",
                    message="Enhancing features based on competitor analysis...",
                    data={"step": "enhancing_features", "progress": 98},
                    timestamp=datetime.now().isoformat()
                ).dict()),
                websocket
            )
            
            enhanced_features = await analyzer.pipeline.step_5_enhance_features(competitor_analysis, innovative_features, keyword)
            
            # Compile final results
            result = {
                "keyword": keyword,
                "analysis_timestamp": datetime.now().isoformat(),
                "trends_metadata": trends_data.get('metadata', {}),
                "identified_problems": problems.model_dump() if problems else {},
                "market_maturity": market_maturity.model_dump() if market_maturity else {},
                "solution_goals": goals.model_dump() if goals else {},
                "saas_opportunities": feature_suggestions.model_dump() if feature_suggestions else {},
                "innovative_features": innovative_features.model_dump() if innovative_features else {},
                "competitor_analysis": competitor_analysis.model_dump() if competitor_analysis else {},
                "enhanced_features": enhanced_features.model_dump() if enhanced_features else {}
            }
        else:
            # Compile results without competitor analysis
            result = {
                "keyword": keyword,
                "analysis_timestamp": datetime.now().isoformat(),
                "trends_metadata": trends_data.get('metadata', {}),
                "identified_problems": problems.model_dump() if problems else {},
                "market_maturity": market_maturity.model_dump() if market_maturity else {},
                "solution_goals": goals.model_dump() if goals else {},
                "saas_opportunities": feature_suggestions.model_dump() if feature_suggestions else {},
                "innovative_features": innovative_features.model_dump() if innovative_features else {}
            }
        
        # Add enhanced insights
        enhanced_result = analyzer._add_enhanced_insights(result, trends_data)
        
        # Send final result
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="result",
                message="Analysis completed successfully!",
                data={"step": "completed", "progress": 100, "result": enhanced_result},
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        await manager.send_personal_message(
            json.dumps(WebSocketMessage(
                type="error",
                message=f"Analysis failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()),
            websocket
        )

@router.get("/status")
async def get_analysis_status():
    """Get current analysis status and active connections"""
    return {
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat(),
        "status": "running"
    } 