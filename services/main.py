import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pytrends.request import TrendReq
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class TrendDataPoint(BaseModel):
    date: str
    interest: int = Field(..., ge=0, le=100)

class RelatedQuery(BaseModel):
    query: str
    value: int

class RisingQuery(BaseModel):
    query: str
    value: str  # Can be "Breakout" or percentage

class TrendsResponse(BaseModel):
    keyword: str
    comparison_enabled: bool
    interest_over_time: List[TrendDataPoint]
    related_queries: Dict[str, List[RelatedQuery]]
    rising_searches: Dict[str, List[RisingQuery]]
    metadata: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str

# Trends Service Class
class TrendsService:
    def __init__(self):
        self.pytrends = None
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum seconds between requests
        self._initialize_pytrends()
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _initialize_pytrends(self):
        """Initialize pytrends with retry logic"""
        try:
            # Initialize with minimal parameters to avoid urllib3 compatibility issues
            self.pytrends = TrendReq(
                hl='en-US', 
                tz=360,
                timeout=(10, 25)
            )
            logger.info("PyTrends initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyTrends: {e}")
            # Try fallback initialization
            try:
                self.pytrends = TrendReq()
                logger.info("PyTrends initialized with fallback settings")
            except Exception as fallback_error:
                logger.error(f"Fallback initialization also failed: {fallback_error}")
                raise HTTPException(status_code=503, detail="Trends service unavailable")
    
    async def get_trends_data(self, keyword: str, comparison: bool = False) -> Dict[str, Any]:
        """
        Fetch comprehensive trends data for a keyword
        """
        try:
            # Reinitialize pytrends if needed
            if self.pytrends is None:
                self._initialize_pytrends()
            
            # Rate limiting
            self._wait_for_rate_limit()
            
            # Build payload
            kw_list = [keyword]
            if comparison:
                # Add a comparison term (you can modify this logic)
                kw_list.append(f"{keyword} alternative")
            
            # Set timeframe (last 12 months)
            timeframe = 'today 12-m'
            
            # Build payload with error handling and retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await asyncio.to_thread(
                        self.pytrends.build_payload,
                        kw_list, 
                        cat=0, 
                        timeframe=timeframe, 
                        geo='', 
                        gprop=''
                    )
                    break
                except Exception as payload_error:
                    logger.warning(f"Payload attempt {attempt + 1} failed: {payload_error}")
                    if attempt == max_retries - 1:
                        # Last attempt with simplified payload
                        await asyncio.to_thread(
                            self.pytrends.build_payload,
                            [keyword], 
                            timeframe=timeframe
                        )
                    else:
                        # Wait before retry
                        await asyncio.sleep(1)
            
            # Fetch interest over time
            interest_data = None
            try:
                interest_data = await asyncio.to_thread(self.pytrends.interest_over_time)
            except Exception as iot_error:
                logger.error(f"Error fetching interest over time: {iot_error}")
                # Create empty DataFrame as fallback
                interest_data = pd.DataFrame()
            
            # Fetch related queries with error handling
            related_queries = {}
            try:
                related_queries = await asyncio.to_thread(self.pytrends.related_queries)
                if related_queries is None:
                    related_queries = {}
            except Exception as rq_error:
                logger.warning(f"Could not fetch related queries: {rq_error}")
                related_queries = {}
            
            # Fetch related topics with error handling
            related_topics = {}
            try:
                related_topics = await asyncio.to_thread(self.pytrends.related_topics)
                if related_topics is None:
                    related_topics = {}
            except Exception as rt_error:
                logger.warning(f"Could not fetch related topics: {rt_error}")
                related_topics = {}
            
            return {
                'interest_over_time': interest_data,
                'related_queries': related_queries,
                'related_topics': related_topics,
                'keyword': keyword,
                'comparison_enabled': comparison
            }
            
        except Exception as e:
            logger.error(f"Error fetching trends data for '{keyword}': {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch trends data. This might be due to rate limiting or network issues. Please try again in a moment."
            )
    
    def _process_interest_over_time(self, data: pd.DataFrame, keyword: str) -> List[TrendDataPoint]:
        """Process interest over time data"""
        if data is None or data.empty:
            return []
        
        result = []
        for date, row in data.iterrows():
            if keyword in row:
                result.append(TrendDataPoint(
                    date=date.strftime('%Y-%m-%d'),
                    interest=int(row[keyword]) if pd.notna(row[keyword]) else 0
                ))
        
        return result
    
    def _process_related_queries(self, data: Dict) -> Dict[str, List[RelatedQuery]]:
        """Process related queries data"""
        result = {'top': [], 'rising': []}
        
        if not data:
            return result
        
        # Get the first keyword's data
        keyword_data = list(data.values())[0] if data else {}
        
        # Process top queries
        if 'top' in keyword_data and keyword_data['top'] is not None:
            for _, row in keyword_data['top'].iterrows():
                result['top'].append(RelatedQuery(
                    query=row['query'],
                    value=int(row['value'])
                ))
        
        # Process rising queries - convert to RelatedQuery format
        if 'rising' in keyword_data and keyword_data['rising'] is not None:
            for _, row in keyword_data['rising'].iterrows():
                value = row['value']
                # Handle "Breakout" values and convert to integer
                if isinstance(value, str) and value == 'Breakout':
                    # Use a high number for breakout queries
                    numeric_value = 10000
                else:
                    try:
                        # Extract numeric value from percentage strings
                        if isinstance(value, str) and '%' in str(value):
                            numeric_value = int(str(value).replace('%', '').replace('+', ''))
                        else:
                            numeric_value = int(value) if pd.notna(value) else 0
                    except (ValueError, TypeError):
                        numeric_value = 0
                
                result['rising'].append(RelatedQuery(
                    query=row['query'],
                    value=numeric_value
                ))
        
        return result
    
    def _process_rising_searches(self, data: Dict) -> Dict[str, List[RisingQuery]]:
        """Process rising searches from related topics"""
        result = {'top': [], 'rising': []}
        
        if not data:
            return result
        
        # Get the first keyword's data
        keyword_data = list(data.values())[0] if data else {}
        
        # Process top topics as rising searches
        if 'top' in keyword_data and keyword_data['top'] is not None:
            try:
                for _, row in keyword_data['top'].iterrows():
                    # Handle both topic_title and title columns
                    title = row.get('topic_title', row.get('title', 'Unknown'))
                    value = row.get('value', 0)
                    
                    value_str = f"{value}%" if pd.notna(value) else "N/A"
                    
                    result['top'].append(RisingQuery(
                        query=str(title),
                        value=value_str
                    ))
            except Exception as e:
                logger.warning(f"Error processing top topics: {e}")
        
        # Process rising topics
        if 'rising' in keyword_data and keyword_data['rising'] is not None:
            try:
                for _, row in keyword_data['rising'].iterrows():
                    # Handle both topic_title and title columns
                    title = row.get('topic_title', row.get('title', 'Unknown'))
                    value = row.get('value', 0)
                    
                    if isinstance(value, str) and value == 'Breakout':
                        value_str = 'Breakout'
                    else:
                        value_str = f"+{value}%" if pd.notna(value) else "N/A"
                    
                    result['rising'].append(RisingQuery(
                        query=str(title),
                        value=value_str
                    ))
            except Exception as e:
                logger.warning(f"Error processing rising topics: {e}")
        
        return result

# Initialize FastAPI app
app = FastAPI(
    title="Google Trends API",
    description="A FastAPI service for analyzing Google Trends data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize trends service
trends_service = TrendsService()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Google Trends API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze/{keyword}?cmp=true",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Google Trends API"
    }

@app.get("/analyze/{keyword}", response_model=TrendsResponse)
async def analyze_keyword(
    keyword: str = Path(..., description="Keyword to analyze", min_length=1, max_length=100),
    cmp: bool = Query(False, description="Enable comparison mode")
) -> TrendsResponse:
    """
    Analyze Google Trends data for a given keyword
    
    Args:
        keyword: The search term to analyze
        cmp: Whether to enable comparison mode
    
    Returns:
        Comprehensive trends data including interest over time, related queries, and rising searches
    """
    
    try:
        # Validate keyword
        if not keyword.strip():
            raise HTTPException(status_code=400, detail="Keyword cannot be empty")
        
        # Clean keyword
        clean_keyword = keyword.strip().lower()
        
        logger.info(f"Analyzing keyword: '{clean_keyword}' with comparison: {cmp}")
        
        # Fetch trends data
        raw_data = await trends_service.get_trends_data(clean_keyword, cmp)
        
        # Process the data with error handling
        try:
            interest_over_time = trends_service._process_interest_over_time(
                raw_data['interest_over_time'], 
                clean_keyword
            )
        except Exception as e:
            logger.warning(f"Error processing interest over time: {e}")
            interest_over_time = []
        
        try:
            related_queries = trends_service._process_related_queries(
                raw_data['related_queries']
            )
        except Exception as e:
            logger.warning(f"Error processing related queries: {e}")
            related_queries = {'top': [], 'rising': []}
        
        try:
            rising_searches = trends_service._process_rising_searches(
                raw_data['related_topics']
            )
        except Exception as e:
            logger.warning(f"Error processing rising searches: {e}")
            rising_searches = {'top': [], 'rising': []}
        
        # Build metadata
        metadata = {
            "fetch_timestamp": datetime.now().isoformat(),
            "timeframe": "last_12_months",
            "region": "worldwide",
            "data_points": len(interest_over_time),
            "has_related_queries": len(related_queries.get('top', [])) > 0 or len(related_queries.get('rising', [])) > 0,
            "has_rising_searches": len(rising_searches.get('top', [])) > 0 or len(rising_searches.get('rising', [])) > 0
        }
        
        # Create response with validation
        try:
            response = TrendsResponse(
                keyword=clean_keyword,
                comparison_enabled=cmp,
                interest_over_time=interest_over_time,
                related_queries=related_queries,
                rising_searches=rising_searches,
                metadata=metadata
            )
            
            logger.info(f"Successfully analyzed '{clean_keyword}' - {len(interest_over_time)} data points")
            return response
            
        except Exception as validation_error:
            logger.error(f"Validation error for response: {validation_error}")
            # Return a minimal response if validation fails
            return TrendsResponse(
                keyword=clean_keyword,
                comparison_enabled=cmp,
                interest_over_time=interest_over_time,
                related_queries={'top': [], 'rising': []},
                rising_searches={'top': [], 'rising': []},
                metadata=metadata
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing '{keyword}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=f"Request failed with status {exc.status_code}",
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )