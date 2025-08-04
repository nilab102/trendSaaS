import os
import asyncio
import httpx
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from datetime import datetime
import json
import re
from collections import Counter
import statistics

# Load environment variables
load_dotenv(override=True)

# Environment variables
TRENDS_API_BASE_URL = os.getenv("TRENDS_API_BASE_URL", "http://localhost:8000")
GEMINI_API_KEY = os.getenv("google_api_key")
GEMINI_MODEL_NAME = os.getenv("google_gemini_name", "gemini-1.5-pro")
GEMINI_MODEL_LIGHT = os.getenv("google_gemini_name_light", "gemini-1.5-flash")

# Enhanced Data Processing Classes
class TrendsDataProcessor:
    """Advanced data processing and enrichment for trends data"""
    
    def __init__(self):
        self.problem_keywords = {
            'pain_points': ['problem', 'issue', 'error', 'bug', 'fail', 'broken', 'difficult', 'hard', 'complex'],
            'solution_seeking': ['how to', 'how do i', 'solution', 'fix', 'repair', 'resolve', 'tutorial', 'guide'],
            'comparison': ['vs', 'versus', 'alternative', 'better', 'best', 'compare', 'difference'],
            'negative': ['not working', 'doesn\'t work', 'bad', 'terrible', 'awful', 'hate', 'dislike']
        }
        
        self.trend_patterns = {
            'seasonal': ['christmas', 'holiday', 'summer', 'winter', 'spring', 'fall'],
            'trending': ['new', 'latest', '2024', '2023', 'trending', 'viral'],
            'technical': ['api', 'integration', 'automation', 'ai', 'machine learning', 'cloud']
        }
    
    def clean_and_validate_data(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate trends data"""
        cleaned_data = trends_data.copy()
        
        # Clean related queries
        if 'related_queries' in cleaned_data:
            cleaned_data['related_queries'] = self._clean_queries(cleaned_data['related_queries'])
        
        # Clean rising searches
        if 'rising_searches' in cleaned_data:
            cleaned_data['rising_searches'] = self._clean_queries(cleaned_data['rising_searches'])
        
        # Clean interest over time
        if 'interest_over_time' in cleaned_data:
            cleaned_data['interest_over_time'] = self._clean_interest_data(cleaned_data['interest_over_time'])
        
        return cleaned_data
    
    def _clean_queries(self, queries_data: Dict[str, List]) -> Dict[str, List]:
        """Clean and filter query data"""
        cleaned = {'top': [], 'rising': []}
        
        for category in ['top', 'rising']:
            if category in queries_data:
                queries = queries_data[category]
                cleaned_queries = []
                
                for query in queries:
                    if isinstance(query, dict):
                        query_text = query.get('query', str(query))
                        value = query.get('value', 0)
                    else:
                        query_text = str(query)
                        value = 0
                    
                    # Clean query text
                    cleaned_text = self._clean_query_text(query_text)
                    
                    if cleaned_text and len(cleaned_text) > 2:  # Filter out very short queries
                        cleaned_queries.append({
                            'query': cleaned_text,
                            'value': value,
                            'category': category
                        })
                
                # Sort by value and limit to top results
                cleaned_queries.sort(key=lambda x: x['value'], reverse=True)
                cleaned[category] = cleaned_queries[:10]  # Limit to top 10
        
        return cleaned
    
    def _clean_query_text(self, text: str) -> str:
        """Clean individual query text"""
        if not text:
            return ""
        
        # Remove special characters but keep spaces and basic punctuation
        cleaned = re.sub(r'[^\w\s\-\.]', '', text.lower())
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _clean_interest_data(self, interest_data: List[Dict]) -> List[Dict]:
        """Clean interest over time data"""
        cleaned = []
        
        for point in interest_data:
            if isinstance(point, dict):
                date = point.get('date', '')
                interest = point.get('interest', 0)
            else:
                # Handle object attributes
                date = getattr(point, 'date', '')
                interest = getattr(point, 'interest', 0)
            
            # Validate interest value
            try:
                interest = int(interest) if interest is not None else 0
                interest = max(0, min(100, interest))  # Clamp to 0-100
            except (ValueError, TypeError):
                interest = 0
            
            if date:  # Only include points with valid dates
                cleaned.append({
                    'date': str(date),
                    'interest': interest
                })
        
        return cleaned
    
    def enrich_trends_data(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich trends data with additional insights"""
        enriched = trends_data.copy()
        
        # Add problem analysis
        enriched['problem_analysis'] = self._analyze_problems(trends_data)
        
        # Add trend patterns
        enriched['trend_patterns'] = self._analyze_trend_patterns(trends_data)
        
        # Add statistical insights
        enriched['statistical_insights'] = self._calculate_statistics(trends_data)
        
        # Add keyword clustering
        enriched['keyword_clusters'] = self._cluster_keywords(trends_data)
        
        return enriched
    
    def _analyze_problems(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze queries for problem indicators"""
        all_queries = []
        
        # Collect all queries
        for category in ['related_queries', 'rising_searches']:
            if category in trends_data:
                for subcategory in ['top', 'rising']:
                    queries = trends_data[category].get(subcategory, [])
                    for query in queries:
                        if isinstance(query, dict):
                            all_queries.append(query.get('query', ''))
                        else:
                            all_queries.append(str(query))
        
        # Analyze problem indicators
        problem_scores = {}
        for category, keywords in self.problem_keywords.items():
            score = 0
            for query in all_queries:
                query_lower = query.lower()
                for keyword in keywords:
                    if keyword in query_lower:
                        score += 1
            problem_scores[category] = score
        
        return {
            'problem_indicators': problem_scores,
            'total_queries_analyzed': len(all_queries),
            'problem_density': sum(problem_scores.values()) / max(len(all_queries), 1)
        }
    
    def _analyze_trend_patterns(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trend patterns in queries"""
        all_queries = []
        
        # Collect all queries
        for category in ['related_queries', 'rising_searches']:
            if category in trends_data:
                for subcategory in ['top', 'rising']:
                    queries = trends_data[category].get(subcategory, [])
                    for query in queries:
                        if isinstance(query, dict):
                            all_queries.append(query.get('query', ''))
                        else:
                            all_queries.append(str(query))
        
        pattern_analysis = {}
        for pattern_type, keywords in self.trend_patterns.items():
            matches = []
            for query in all_queries:
                query_lower = query.lower()
                for keyword in keywords:
                    if keyword in query_lower:
                        matches.append(query)
                        break
            pattern_analysis[pattern_type] = {
                'matches': matches,
                'count': len(matches)
            }
        
        return pattern_analysis
    
    def _calculate_statistics(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical insights from trends data"""
        stats = {}
        
        # Interest over time statistics
        if 'interest_over_time' in trends_data:
            interest_values = []
            for point in trends_data['interest_over_time']:
                if isinstance(point, dict):
                    interest_values.append(point.get('interest', 0))
                else:
                    interest_values.append(getattr(point, 'interest', 0))
            
            if interest_values:
                stats['interest_stats'] = {
                    'mean': statistics.mean(interest_values),
                    'median': statistics.median(interest_values),
                    'max': max(interest_values),
                    'min': min(interest_values),
                    'trend_direction': self._calculate_trend_direction(interest_values),
                    'volatility': statistics.stdev(interest_values) if len(interest_values) > 1 else 0
                }
        
        # Query value statistics
        all_values = []
        for category in ['related_queries', 'rising_searches']:
            if category in trends_data:
                for subcategory in ['top', 'rising']:
                    queries = trends_data[category].get(subcategory, [])
                    for query in queries:
                        if isinstance(query, dict):
                            all_values.append(query.get('value', 0))
                        else:
                            all_values.append(0)
        
        if all_values:
            stats['query_value_stats'] = {
                'mean_value': statistics.mean(all_values),
                'max_value': max(all_values),
                'total_queries': len(all_values)
            }
        
        return stats
    
    def _calculate_trend_direction(self, values: List[int]) -> str:
        """Calculate trend direction from interest values"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg * 1.1:
            return "rising"
        elif second_avg < first_avg * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _cluster_keywords(self, trends_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Cluster keywords by similarity"""
        all_queries = []
        
        # Collect all queries
        for category in ['related_queries', 'rising_searches']:
            if category in trends_data:
                for subcategory in ['top', 'rising']:
                    queries = trends_data[category].get(subcategory, [])
                    for query in queries:
                        if isinstance(query, dict):
                            all_queries.append(query.get('query', ''))
                        else:
                            all_queries.append(str(query))
        
        # Simple clustering by common words
        word_freq = Counter()
        for query in all_queries:
            words = query.lower().split()
            word_freq.update(words)
        
        # Find common themes
        common_words = [word for word, count in word_freq.most_common(10) if count > 1]
        
        clusters = {}
        for word in common_words:
            cluster_queries = [query for query in all_queries if word in query.lower()]
            if len(cluster_queries) > 1:
                clusters[word] = cluster_queries[:5]  # Limit to 5 per cluster
        
        return clusters

class TokenOptimizer:
    """Optimize data for LLM token efficiency"""
    
    def __init__(self, max_tokens_per_section: int = 1000):
        self.max_tokens_per_section = max_tokens_per_section
    
    def optimize_for_llm(self, data: Dict[str, Any], context_type: str) -> Dict[str, Any]:
        """Optimize data structure for LLM consumption"""
        if context_type == "problem_extraction":
            return self._optimize_for_problem_extraction(data)
        elif context_type == "market_maturity":
            return self._optimize_for_market_maturity(data)
        elif context_type == "feature_generation":
            return self._optimize_for_feature_generation(data)
        else:
            return self._optimize_generic(data)
    
    def _optimize_for_problem_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data specifically for problem extraction"""
        optimized = {}
        
        # Focus on queries that indicate problems
        problem_queries = self._extract_problem_queries(data)
        optimized['problem_indicators'] = problem_queries
        
        # Include rising searches (often indicate emerging problems)
        rising_searches = data.get('rising_searches', {}).get('rising', [])
        optimized['rising_problems'] = rising_searches[:5]  # Top 5
        
        # Include top related queries for context
        related_top = data.get('related_queries', {}).get('top', [])
        optimized['context_queries'] = related_top[:3]  # Top 3
        
        return optimized
    
    def _optimize_for_market_maturity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data specifically for market maturity analysis"""
        optimized = {}
        
        # Focus on interest over time data
        interest_data = data.get('interest_over_time', [])
        if interest_data:
            # Sample data points to reduce tokens while maintaining trend visibility
            sample_size = min(12, len(interest_data))  # Monthly samples
            step = len(interest_data) // sample_size
            sampled_data = interest_data[::step][:sample_size]
            optimized['interest_trend'] = sampled_data
        
        # Include key statistics
        if 'statistical_insights' in data:
            stats = data['statistical_insights']
            optimized['key_stats'] = {
                'trend_direction': stats.get('interest_stats', {}).get('trend_direction', 'unknown'),
                'volatility': round(stats.get('interest_stats', {}).get('volatility', 0), 2),
                'avg_interest': round(stats.get('interest_stats', {}).get('mean', 0), 1)
            }
        
        return optimized
    
    def _optimize_for_feature_generation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data specifically for feature generation"""
        optimized = {}
        
        # Focus on emerging trends and user needs
        if 'trend_patterns' in data:
            patterns = data['trend_patterns']
            optimized['emerging_trends'] = {
                'trending_topics': patterns.get('trending', {}).get('matches', [])[:5],
                'technical_interest': patterns.get('technical', {}).get('matches', [])[:5]
            }
        
        # Include problem analysis
        if 'problem_analysis' in data:
            problems = data['problem_analysis']
            optimized['user_problems'] = {
                'pain_points': problems.get('problem_indicators', {}).get('pain_points', 0),
                'solution_seeking': problems.get('problem_indicators', {}).get('solution_seeking', 0),
                'problem_density': round(problems.get('problem_density', 0), 2)
            }
        
        # Include keyword clusters for feature inspiration
        if 'keyword_clusters' in data:
            clusters = data['keyword_clusters']
            optimized['feature_themes'] = list(clusters.keys())[:3]  # Top 3 themes
        
        return optimized
    
    def _optimize_generic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic optimization for any context"""
        optimized = {}
        
        # Include essential data only
        if 'related_queries' in data:
            optimized['top_queries'] = data['related_queries'].get('top', [])[:5]
            optimized['rising_queries'] = data['related_queries'].get('rising', [])[:5]
        
        if 'rising_searches' in data:
            optimized['rising_searches'] = data['rising_searches'].get('rising', [])[:5]
        
        return optimized
    
    def _extract_problem_queries(self, data: Dict[str, Any]) -> List[str]:
        """Extract queries that likely indicate problems"""
        problem_queries = []
        problem_indicators = ['problem', 'issue', 'error', 'fix', 'how to', 'tutorial', 'help']
        
        for category in ['related_queries', 'rising_searches']:
            if category in data:
                for subcategory in ['top', 'rising']:
                    queries = data[category].get(subcategory, [])
                    for query in queries:
                        if isinstance(query, dict):
                            query_text = query.get('query', '')
                        else:
                            query_text = str(query)
                        
                        query_lower = query_text.lower()
                        if any(indicator in query_lower for indicator in problem_indicators):
                            problem_queries.append(query_text)
        
        return problem_queries[:10]  # Limit to top 10

class ContextBuilder:
    """Build rich contextual information for LLM prompts"""
    
    def __init__(self):
        self.processor = TrendsDataProcessor()
        self.optimizer = TokenOptimizer()
    
    def build_context(self, trends_data: Dict[str, Any], context_type: str) -> Dict[str, Any]:
        """Build comprehensive context for LLM analysis"""
        # First, clean and enrich the data
        cleaned_data = self.processor.clean_and_validate_data(trends_data)
        enriched_data = self.processor.enrich_trends_data(cleaned_data)
        
        # Then optimize for the specific context
        optimized_data = self.optimizer.optimize_for_llm(enriched_data, context_type)
        
        # Build final context
        context = {
            'keyword': trends_data.get('keyword', ''),
            'timestamp': datetime.now().isoformat(),
            'data_quality': self._assess_data_quality(trends_data),
            'optimized_data': optimized_data,
            'summary_insights': self._create_summary_insights(enriched_data)
        }
        
        return context
    
    def _assess_data_quality(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality and completeness of trends data"""
        quality_metrics = {
            'has_interest_data': len(trends_data.get('interest_over_time', [])) > 0,
            'has_related_queries': len(trends_data.get('related_queries', {}).get('top', [])) > 0,
            'has_rising_searches': len(trends_data.get('rising_searches', {}).get('rising', [])) > 0,
            'data_completeness': 0.0
        }
        
        # Calculate completeness score
        total_expected = 3  # interest, related, rising
        total_present = sum([
            quality_metrics['has_interest_data'],
            quality_metrics['has_related_queries'],
            quality_metrics['has_rising_searches']
        ])
        
        quality_metrics['data_completeness'] = total_present / total_expected
        
        return quality_metrics
    
    def _create_summary_insights(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary insights from enriched data"""
        insights = {}
        
        # Market maturity insights
        if 'statistical_insights' in enriched_data:
            stats = enriched_data['statistical_insights']
            if 'interest_stats' in stats:
                interest_stats = stats['interest_stats']
                insights['market_trend'] = {
                    'direction': interest_stats.get('trend_direction', 'unknown'),
                    'volatility': 'high' if interest_stats.get('volatility', 0) > 15 else 'low',
                    'interest_level': 'high' if interest_stats.get('mean', 0) > 50 else 'low'
                }
        
        # Problem insights
        if 'problem_analysis' in enriched_data:
            problems = enriched_data['problem_analysis']
            insights['problem_landscape'] = {
                'has_pain_points': problems.get('problem_indicators', {}).get('pain_points', 0) > 0,
                'solution_seeking': problems.get('problem_indicators', {}).get('solution_seeking', 0) > 0,
                'problem_density': problems.get('problem_density', 0)
            }
        
        # Trend insights
        if 'trend_patterns' in enriched_data:
            patterns = enriched_data['trend_patterns']
            insights['trend_characteristics'] = {
                'is_seasonal': patterns.get('seasonal', {}).get('count', 0) > 0,
                'is_trending': patterns.get('trending', {}).get('count', 0) > 0,
                'is_technical': patterns.get('technical', {}).get('count', 0) > 0
            }
        
        return insights

# Pydantic Models for LLM Outputs
class UserProblem(BaseModel):
    problem: str = Field(description="A clear description of the user problem")
    evidence: str = Field(description="Evidence from trends data supporting this problem")
    severity: int = Field(description="Problem severity score from 1-10", ge=1, le=10)

class ProblemsExtractorOutput(BaseModel):
    problems: List[UserProblem] = Field(description="Top 3 user problems identified from trends")
    analysis_summary: str = Field(description="Brief summary of the analysis")

class MarketMaturity(BaseModel):
    stage: str = Field(description="Market stage: early, mid, or saturated")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)
    reasoning: str = Field(description="Explanation of the market stage assessment")
    trend_direction: str = Field(description="Trend direction: rising, stable, or declining")

class SolutionGoal(BaseModel):
    goal: str = Field(description="Clear goal statement for solving the problem")
    target_audience: str = Field(description="Primary target audience")
    value_proposition: str = Field(description="Core value proposition")

class GoalExtractorOutput(BaseModel):
    goals: List[SolutionGoal] = Field(description="Goals for each identified problem")

class FeatureCategory(BaseModel):
    category: str = Field(description="SaaS solution category name")
    description: str = Field(description="Detailed description of the category")
    key_features: List[str] = Field(description="2-3 key features for this category")
    market_fit_score: int = Field(description="Market fit score 1-10", ge=1, le=10)

class FeatureSuggestionOutput(BaseModel):
    categories: List[FeatureCategory] = Field(description="2-3 SaaS solution categories")
    recommended_category: str = Field(description="Most recommended category and why")

class InnovativeFeature(BaseModel):
    name: str = Field(description="Feature name")
    description: str = Field(description="Detailed feature description")
    innovation_level: int = Field(description="Innovation level 1-10", ge=1, le=10)
    implementation_complexity: str = Field(description="Complexity: low, medium, high")
    tags: List[str] = Field(description="Feature tags (e.g., AI, automation, analytics)")
    user_value: str = Field(description="Primary value this feature provides to users")
    competitive_advantage: str = Field(description="How this feature differentiates from competitors")

class FeatureGeneratorOutput(BaseModel):
    features: List[InnovativeFeature] = Field(description="5-7 innovative SaaS features")
    feature_priority_ranking: List[str] = Field(description="Feature names ranked by priority")
    mvp_features: List[str] = Field(description="3-4 features recommended for MVP")
    advanced_features: List[str] = Field(description="Features for later versions")
    technical_considerations: str = Field(description="Key technical considerations for implementation")

class TrendsClient:
    """Client for interacting with the Trends API"""
    
    def __init__(self, base_url: str = TRENDS_API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        
    async def get_trends_data(self, keyword: str, comparison: bool = False) -> Dict[str, Any]:
        """Fetch trends data from the API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/analyze/{keyword}",
                    params={"cmp": comparison}
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                raise Exception(f"Error connecting to trends API: {e}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"Trends API returned error {e.response.status_code}: {e.response.text}")

class LLMPipeline:
    """Multi-step LLM pipeline for SaaS opportunity analysis with enhanced data processing"""
    
    def __init__(self):
        self.heavy_llm = self._initialize_llm(model=GEMINI_MODEL_NAME)
        self.light_llm = self._initialize_llm(model=GEMINI_MODEL_LIGHT)
        self.trends_client = TrendsClient()
        self.context_builder = ContextBuilder()
    
    def _initialize_llm(self, model: str, temperature: float = 0.1) -> ChatGoogleGenerativeAI:
        """Initialize Gemini LLM"""
        if not GEMINI_API_KEY:
            raise ValueError("Google API key not found in environment variables")
        
        return ChatGoogleGenerativeAI(
            model=model, 
            temperature=temperature, 
            google_api_key=GEMINI_API_KEY
        )
    
    async def _safe_llm_call(self, chain, inputs: Dict[str, Any], step_name: str, max_retries: int = 2):
        """Safely execute LLM chain with error handling and retries"""
        
        for attempt in range(max_retries + 1):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries + 1} for {step_name}...")
                result = await chain.ainvoke(inputs)
                
                if result is None:
                    raise Exception(f"LLM returned None for {step_name}")
                
                print(f"  ✓ {step_name} successful")
                return result
                
            except Exception as e:
                print(f"  ⚠️ Attempt {attempt + 1} failed for {step_name}: {e}")
                
                if attempt == max_retries:
                    # Final attempt failed, create fallback response
                    print(f"  Creating fallback response for {step_name}")
                    return self._create_fallback_response(step_name, inputs)
                
                # Wait before retry
                await asyncio.sleep(1)
    
    def _create_fallback_response(self, step_name: str, inputs: Dict[str, Any]):
        """Create fallback responses when LLM calls fail"""
        
        if step_name == "Problem Extraction":
            return ProblemsExtractorOutput(
                problems=[
                    UserProblem(
                        problem="Unable to extract specific problems due to API error",
                        evidence="Analysis incomplete - please retry",
                        severity=5
                    )
                ],
                analysis_summary="Analysis failed - fallback response generated"
            )
        
        elif step_name == "Market Maturity":
            return MarketMaturity(
                stage="mid",
                confidence=0.5,
                reasoning="Unable to complete analysis due to API error",
                trend_direction="stable"
            )
        
        elif step_name == "Goal Extraction":
            return GoalExtractorOutput(
                goals=[
                    SolutionGoal(
                        goal="Solve user problems efficiently",
                        target_audience="General users",
                        value_proposition="Improved user experience"
                    )
                ]
            )
        
        elif step_name == "Feature Categories":
            return FeatureSuggestionOutput(
                categories=[
                    FeatureCategory(
                        category="General SaaS Solution",
                        description="Standard SaaS application with basic features",
                        key_features=["Basic functionality", "User management", "Data storage"],
                        market_fit_score=5
                    )
                ],
                recommended_category="General SaaS Solution - API analysis incomplete"
            )
        
        elif step_name == "Feature Generation":
            return FeatureGeneratorOutput(
                features=[
                    InnovativeFeature(
                        name="Basic Feature Set",
                        description="Standard functionality for the application",
                        innovation_level=3,
                        implementation_complexity="medium",
                        tags=["basic", "standard"],
                        user_value="Provides essential functionality",
                        competitive_advantage="Reliable basic features"
                    )
                ],
                feature_priority_ranking=["Basic Feature Set"],
                mvp_features=["Basic Feature Set"],
                advanced_features=[],
                technical_considerations="Standard implementation required"
            )
        
        else:
            raise Exception(f"No fallback available for {step_name}")
    
    async def step_1_extract_problems(self, trends_data: Dict[str, Any]) -> ProblemsExtractorOutput:
        """LLM 1: Extract top 3 user problems from related queries and rising searches with enhanced data processing"""
        
        parser = PydanticOutputParser(pydantic_object=ProblemsExtractorOutput)
        
        # Build enhanced context for problem extraction
        context = self.context_builder.build_context(trends_data, "problem_extraction")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert market analyst specializing in identifying user problems from search trends data.
            Your task is to analyze Google Trends data and identify the top 3 user problems.
            
            Focus on:
            - Pain points users are actively searching for solutions to
            - Problems indicated by "how to", "why", "problem with", "fix", "solution" type queries
            - Rising searches that suggest unmet needs
            - Frequency and intensity of problem-related searches
            - Emerging trends that indicate new problems
            
            Use the enriched data context to identify problems with strong business potential.
            
            {format_instructions}"""),
            ("user", """Analyze this enhanced Google Trends data and identify the top 3 user problems:

KEYWORD: {keyword}

DATA QUALITY: {data_quality}

PROBLEM INDICATORS:
{problem_indicators}

RISING PROBLEMS:
{rising_problems}

CONTEXT QUERIES:
{context_queries}

SUMMARY INSIGHTS:
{summary_insights}

USER PROBLEM LANDSCAPE:
{problem_landscape}

Identify problems that represent genuine user pain points with strong business potential. Use the enriched context to provide more accurate and actionable problem identification.""")
        ])
        
        chain = prompt | self.heavy_llm | parser
        
        # Prepare optimized inputs
        optimized_data = context['optimized_data']
        
        inputs = {
            "keyword": context['keyword'],
            "data_quality": json.dumps(context['data_quality'], indent=2),
            "problem_indicators": json.dumps(optimized_data.get('problem_indicators', []), indent=2),
            "rising_problems": json.dumps(optimized_data.get('rising_problems', []), indent=2),
            "context_queries": json.dumps(optimized_data.get('context_queries', []), indent=2),
            "summary_insights": json.dumps(context['summary_insights'], indent=2),
            "problem_landscape": json.dumps(context['summary_insights'].get('problem_landscape', {}), indent=2),
            "format_instructions": parser.get_format_instructions()
        }
        
        return await self._safe_llm_call(chain, inputs, "Problem Extraction")
    
    async def step_3c_generate_features(self, categories: FeatureSuggestionOutput, goals: GoalExtractorOutput, keyword: str, trends_context: Dict[str, Any]) -> FeatureGeneratorOutput:
        """LLM 3c: Generate innovative SaaS features with enhanced trends context"""
        
        parser = PydanticOutputParser(pydantic_object=FeatureGeneratorOutput)
        
        # Build enhanced context for feature generation
        context = self.context_builder.build_context(trends_context, "feature_generation")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an innovative SaaS product designer and feature architect. Your task is to generate cutting-edge, innovative SaaS features that solve real user problems.

Focus on creating features that are:
- INNOVATIVE: Novel approaches, not just copies of existing solutions
- USER-CENTRIC: Directly address identified user problems and goals
- TECHNICALLY FEASIBLE: Realistic to implement with current technology
- BUSINESS VIABLE: Clear value proposition and monetization potential
- DIFFERENTIATED: Provide competitive advantages

Consider modern trends like:
- AI/ML integration and automation
- Real-time collaboration and communication
- Advanced analytics and insights
- Personalization and adaptive interfaces
- Integration capabilities and APIs
- Mobile-first and cross-platform design
- Privacy and security features
- Workflow automation and productivity enhancements

Use the enriched trends data to identify emerging opportunities and user needs.

Tag features appropriately with relevant technology/concept tags.

{format_instructions}"""),
            ("user", """Generate innovative SaaS features for this enhanced context:

KEYWORD CONTEXT: {keyword}
This keyword represents the market/domain we're targeting.

DATA QUALITY: {data_quality}

RECOMMENDED SAAS CATEGORY:
{recommended_category}

ALL CATEGORIES CONSIDERED:
{all_categories}

SOLUTION GOALS:
{goals}

EMERGING TRENDS:
{emerging_trends}

USER PROBLEMS ANALYSIS:
{user_problems}

FEATURE THEMES:
{feature_themes}

TREND CHARACTERISTICS:
{trend_characteristics}

SUMMARY INSIGHTS:
{summary_insights}

Generate 5-7 innovative features that would make this SaaS solution stand out in the market. Use the enriched trends data to identify emerging opportunities and create features that address both current and future user needs. Consider both MVP features and advanced capabilities.""")
        ])
        
        chain = prompt | self.heavy_llm | parser
        
        # Prepare optimized inputs
        optimized_data = context['optimized_data']
        
        inputs = {
            "keyword": keyword,
            "data_quality": json.dumps(context['data_quality'], indent=2),
            "recommended_category": categories.recommended_category,
            "all_categories": categories.model_dump_json(indent=2),
            "goals": goals.model_dump_json(indent=2),
            "emerging_trends": json.dumps(optimized_data.get('emerging_trends', {}), indent=2),
            "user_problems": json.dumps(optimized_data.get('user_problems', {}), indent=2),
            "feature_themes": json.dumps(optimized_data.get('feature_themes', []), indent=2),
            "trend_characteristics": json.dumps(context['summary_insights'].get('trend_characteristics', {}), indent=2),
            "summary_insights": json.dumps(context['summary_insights'], indent=2),
            "format_instructions": parser.get_format_instructions()
        }
        
        return await self._safe_llm_call(chain, inputs, "Feature Generation")
    
    def _create_trends_summary(self, trends_data: Dict[str, Any]) -> str:
        """Create a summary of trends data for context"""
        summary_parts = []
        
        # Add related queries context
        related_queries = trends_data.get('related_queries', {})
        if related_queries.get('top'):
            top_queries = [q.get('query', str(q)) if isinstance(q, dict) else str(q) for q in related_queries['top'][:5]]
            summary_parts.append(f"Top related searches: {', '.join(top_queries)}")
        
        if related_queries.get('rising'):
            rising_queries = [q.get('query', str(q)) if isinstance(q, dict) else str(q) for q in related_queries['rising'][:5]]
            summary_parts.append(f"Rising related searches: {', '.join(rising_queries)}")
        
        # Add rising searches context
        rising_searches = trends_data.get('rising_searches', {})
        if rising_searches.get('rising'):
            rising_topics = [q.get('query', str(q)) if isinstance(q, dict) else str(q) for q in rising_searches['rising'][:5]]
            summary_parts.append(f"Rising topics: {', '.join(rising_topics)}")
        
        return ". ".join(summary_parts) if summary_parts else "Limited trends context available"
    
    async def step_2_analyze_market_maturity(self, trends_data: Dict[str, Any]) -> MarketMaturity:
        """LLM 2: Analyze market maturity from interest over time data with enhanced processing"""
        
        parser = PydanticOutputParser(pydantic_object=MarketMaturity)
        
        # Build enhanced context for market maturity analysis
        context = self.context_builder.build_context(trends_data, "market_maturity")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a market maturity expert. Analyze Google Trends interest over time data to determine market stage.

Market Stages:
- EARLY: Low but growing interest, volatility, emerging market
- MID: Moderate interest, steady growth, established but growing market  
- SATURATED: High interest with plateau/decline, mature market with high competition

Consider:
- Overall trend direction and pattern
- Interest level consistency
- Growth rate and volatility
- Seasonal patterns
- Statistical insights and data quality

Use the enriched statistical data to provide more accurate market stage assessment.

{format_instructions}"""),
            ("user", """Analyze this enhanced interest over time data to determine market maturity:

KEYWORD: {keyword}
TIME PERIOD: Last 12 months

DATA QUALITY: {data_quality}

INTEREST TREND DATA:
{interest_trend}

KEY STATISTICS:
{key_stats}

MARKET TREND INSIGHTS:
{market_trend}

SUMMARY INSIGHTS:
{summary_insights}

Determine the market stage and provide detailed reasoning based on the enhanced statistical analysis.""")
        ])
        
        chain = prompt | self.light_llm | parser
        
        # Prepare optimized inputs
        optimized_data = context['optimized_data']
        
        inputs = {
            "keyword": context['keyword'],
            "data_quality": json.dumps(context['data_quality'], indent=2),
            "interest_trend": json.dumps(optimized_data.get('interest_trend', []), indent=2),
            "key_stats": json.dumps(optimized_data.get('key_stats', {}), indent=2),
            "market_trend": json.dumps(context['summary_insights'].get('market_trend', {}), indent=2),
            "summary_insights": json.dumps(context['summary_insights'], indent=2),
            "format_instructions": parser.get_format_instructions()
        }
        
        return await self._safe_llm_call(chain, inputs, "Market Maturity")
    
    async def step_3a_extract_goals(self, problems: ProblemsExtractorOutput) -> GoalExtractorOutput:
        """LLM 3a: Extract goals for each identified problem"""
        
        parser = PydanticOutputParser(pydantic_object=GoalExtractorOutput)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product strategy expert. For each user problem, define a clear solution goal.

A good goal should be:
- Specific and actionable
- Address the root cause of the problem
- Have clear success metrics
- Be technically feasible
- Have commercial potential

{format_instructions}"""),
            ("user", """Define solution goals for these identified user problems:

PROBLEMS ANALYSIS:
{problems_data}

For each problem, create a solution goal that addresses the core user need and has strong business potential.""")
        ])
        
        chain = prompt | self.heavy_llm | parser
        
        inputs = {
            "problems_data": problems.model_dump_json(indent=2),
            "format_instructions": parser.get_format_instructions()
        }
        
        return await self._safe_llm_call(chain, inputs, "Goal Extraction")
    
    async def step_3b_suggest_feature_categories(self, goals: GoalExtractorOutput, market_maturity: MarketMaturity) -> FeatureSuggestionOutput:
        """LLM 3b: Suggest 2-3 SaaS solution categories for each goal"""
        
        parser = PydanticOutputParser(pydantic_object=FeatureSuggestionOutput)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SaaS product expert. Based on solution goals and market maturity, suggest 2-3 SaaS solution categories.

Consider:
- Market maturity and competition level
- Technical feasibility and complexity
- Monetization potential
- Differentiation opportunities
- Time to market

SaaS Categories might include: Analytics, Automation, Communication, Productivity, Security, Integration, AI/ML, etc.

{format_instructions}"""),
            ("user", """Suggest SaaS solution categories based on these goals and market conditions:

SOLUTION GOALS:
{goals_data}

MARKET MATURITY:
{market_data}

Provide 2-3 distinct SaaS categories with specific features that would address the identified goals while considering the market maturity.""")
        ])
        
        chain = prompt | self.heavy_llm | parser
        
        inputs = {
            "goals_data": goals.model_dump_json(indent=2),
            "market_data": market_maturity.model_dump_json(indent=2),
            "format_instructions": parser.get_format_instructions()
        }
        
        return await self._safe_llm_call(chain, inputs, "Feature Categories")

class SaaSOpportunityAnalyzer:
    """Main analyzer class that orchestrates the entire pipeline with enhanced data processing"""
    
    def __init__(self):
        self.pipeline = LLMPipeline()
        self.context_builder = ContextBuilder()
        self._analysis_cache = {}  # Simple in-memory cache for analysis results
    
    async def analyze_keyword(self, keyword: str, comparison: bool = False) -> Dict[str, Any]:
        """Run the complete analysis pipeline for a keyword"""
        
        print(f"🔍 Starting SaaS opportunity analysis for: '{keyword}'")
        
        try:
            # Step 0: Fetch trends data
            print("📊 Fetching Google Trends data...")
            trends_data = await self.pipeline.trends_client.get_trends_data(keyword, comparison)
            print(f"✓ Trends data fetched successfully")
            
            # Step 1: Extract problems
            print("🧠 Extracting user problems...")
            problems = await self.pipeline.step_1_extract_problems(trends_data)
            if problems is None:
                raise Exception("Problem extraction returned None - check LLM response parsing")
            print(f"✓ Problems extracted: {len(problems.problems)} problems identified")
            
            # Step 2: Analyze market maturity
            print("📈 Analyzing market maturity...")
            market_maturity = await self.pipeline.step_2_analyze_market_maturity(trends_data)
            if market_maturity is None:
                raise Exception("Market maturity analysis returned None - check LLM response parsing")
            print(f"✓ Market maturity analyzed: {market_maturity.stage} stage")
            
            # Step 3a: Extract goals
            print("🎯 Extracting solution goals...")
            goals = await self.pipeline.step_3a_extract_goals(problems)
            if goals is None:
                raise Exception("Goal extraction returned None - check LLM response parsing")
            print(f"✓ Goals extracted: {len(goals.goals)} goals defined")
            
            # Step 3b: Suggest feature categories
            print("💡 Suggesting SaaS solution categories...")
            feature_suggestions = await self.pipeline.step_3b_suggest_feature_categories(goals, market_maturity)
            if feature_suggestions is None:
                raise Exception("Feature suggestions returned None - check LLM response parsing")
            print(f"✓ Categories suggested: {len(feature_suggestions.categories)} categories")
            
            # Step 3c: Generate innovative features
            print("🚀 Generating innovative SaaS features...")
            innovative_features = await self.pipeline.step_3c_generate_features(
                feature_suggestions, goals, keyword, trends_data
            )
            if innovative_features is None:
                raise Exception("Feature generation returned None - check LLM response parsing")
            print(f"✓ Features generated: {len(innovative_features.features)} features created")
            
            # Compile final results with safe model dumping
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
            
                    print("✅ Analysis complete!")
        
        # Add enhanced data insights to the result
        enhanced_result = self._add_enhanced_insights(result, trends_data)
        
        return enhanced_result
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

# Usage Example
async def main():
    """Example usage of the SaaS Opportunity Analyzer"""
    
    # Check environment variables first
    if not GEMINI_API_KEY:
        print("❌ Error: Google API key not found!")
        print("Please set 'google_api_key' in your .env file")
        return
    
    if not TRENDS_API_BASE_URL:
        print("❌ Error: Trends API base URL not configured!")
        print("Please set 'TRENDS_API_BASE_URL' in your .env file")
        return
    
    print(f"🔧 Configuration:")
    print(f"   Trends API: {TRENDS_API_BASE_URL}")
    print(f"   Gemini Model: {GEMINI_MODEL_NAME}")
    print(f"   Light Model: {GEMINI_MODEL_LIGHT}")
    print(f"   API Key: {'✓ Set' if GEMINI_API_KEY else '❌ Missing'}")
    
    analyzer = SaaSOpportunityAnalyzer()
    
    # Test with a simple keyword first
    keyword = "productivity tools"  # Change this to your target keyword
    
    try:
        print(f"\n{'='*80}")
        print(f"🚀 Starting analysis...")
        print(f"{'='*80}")
        
        results = await analyzer.analyze_keyword(keyword)
        
        print("\n" + "="*80)
        print(f"SAAS OPPORTUNITY ANALYSIS RESULTS FOR: {keyword.upper()}")
        print("="*80)
        
        # Display problems
        print("\n🔍 IDENTIFIED USER PROBLEMS:")
        problems = results.get("identified_problems", {}).get("problems", [])
        if problems:
            for i, problem in enumerate(problems, 1):
                print(f"\n{i}. {problem.get('problem', 'N/A')}")
                print(f"   Evidence: {problem.get('evidence', 'N/A')}")
                print(f"   Severity: {problem.get('severity', 'N/A')}/10")
        else:
            print("   No problems identified")
        
        # Display market maturity
        market = results.get("market_maturity", {})
        if market:
            print(f"\n📊 MARKET MATURITY:")
            print(f"   Stage: {market.get('stage', 'N/A').upper()}")
            print(f"   Trend: {market.get('trend_direction', 'N/A')}")
            print(f"   Confidence: {market.get('confidence', 0):.1%}")
            print(f"   Reasoning: {market.get('reasoning', 'N/A')}")
        
        # Display SaaS opportunities
        saas_opps = results.get("saas_opportunities", {})
        categories = saas_opps.get("categories", [])
        if categories:
            print(f"\n💡 SAAS SOLUTION OPPORTUNITIES:")
            for i, category in enumerate(categories, 1):
                print(f"\n{i}. {category.get('category', 'N/A')}")
                print(f"   Description: {category.get('description', 'N/A')}")
                print(f"   Market Fit Score: {category.get('market_fit_score', 'N/A')}/10")
                print(f"   Key Features: {', '.join(category.get('key_features', []))}")
        
        recommended = saas_opps.get("recommended_category", "N/A")
        print(f"\n🏆 RECOMMENDED: {recommended}")
        
        # Display innovative features
        features_data = results.get("innovative_features", {})
        if features_data:
            print(f"\n🚀 INNOVATIVE FEATURES:")
            
            mvp_features = features_data.get("mvp_features", [])
            if mvp_features:
                print(f"\n   MVP FEATURES (Priority):")
                all_features = features_data.get("features", [])
                for i, feature_name in enumerate(mvp_features, 1):
                    feature_details = next((f for f in all_features if f.get("name") == feature_name), None)
                    if feature_details:
                        print(f"   {i}. {feature_details.get('name', 'N/A')}")
                        print(f"      {feature_details.get('description', 'N/A')}")
                        print(f"      Tags: {', '.join(feature_details.get('tags', []))}")
                        print(f"      Innovation Level: {feature_details.get('innovation_level', 'N/A')}/10")
                        print(f"      Complexity: {feature_details.get('implementation_complexity', 'N/A')}")
            
            advanced_features = features_data.get("advanced_features", [])
            if advanced_features:
                print(f"\n   ADVANCED FEATURES (Future):")
                all_features = features_data.get("features", [])
                for i, feature_name in enumerate(advanced_features, 1):
                    feature_details = next((f for f in all_features if f.get("name") == feature_name), None)
                    if feature_details:
                        print(f"   {i}. {feature_details.get('name', 'N/A')}")
                        print(f"      {feature_details.get('description', 'N/A')}")
                        print(f"      Tags: {', '.join(feature_details.get('tags', []))}")
            
            tech_considerations = features_data.get("technical_considerations", "N/A")
            print(f"\n🔧 TECHNICAL CONSIDERATIONS:")
            print(f"   {tech_considerations}")
        
        print(f"\n{'='*80}")
        print("✅ Analysis completed successfully!")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide debugging suggestions
        print(f"\n🔧 Debugging suggestions:")
        print(f"1. Check if your Trends API is running at {TRENDS_API_BASE_URL}")
        print(f"2. Verify your Google API key is valid")
        print(f"3. Try with a simpler keyword")
        print(f"4. Check your internet connection")
        
        import traceback
        print(f"\nFull traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())