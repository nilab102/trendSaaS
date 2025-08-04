# TrendSaaS - AI-Powered SaaS Opportunity Analyzer

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**TrendSaaS** is an intelligent platform that analyzes Google Trends data to identify profitable SaaS opportunities. It combines advanced AI analysis with real-time market data to help entrepreneurs and product managers discover untapped market potential.

## 🚀 Features

### Core Capabilities
- **Google Trends Analysis**: Real-time analysis of search trends and interest patterns
- **AI-Powered Problem Extraction**: Identifies user pain points and unmet needs
- **Market Maturity Assessment**: Determines market stage (early, mid, saturated)
- **SaaS Opportunity Identification**: Suggests viable SaaS solution categories
- **Innovative Feature Generation**: Creates cutting-edge feature ideas with competitive advantages
- **Competitor Analysis**: Analyzes existing solutions and identifies market gaps
- **Real-time WebSocket Updates**: Live progress tracking during analysis

### Technical Features
- **Multi-step LLM Pipeline**: Advanced AI analysis using Google Gemini models
- **Enhanced Data Processing**: Sophisticated data cleaning and enrichment
- **Token Optimization**: Efficient LLM context management
- **Competitor Intelligence**: SERP API integration for market research
- **Responsive Web Interface**: Modern, intuitive user experience
- **Robust Error Handling**: Graceful failure recovery and user feedback

## 🏗️ Architecture

### Backend (Python/FastAPI)
```
trendSaaS/
├── main.py                 # FastAPI application entry point
├── start.py               # Development server launcher
├── requirements.txt       # Python dependencies
├── services/
│   ├── trends_router.py   # Google Trends API integration
│   ├── analyzer_router.py # AI analysis endpoints & WebSocket
│   └── data_analyzer.py   # Core AI analysis pipeline
```

### Frontend (HTML/CSS/JavaScript)
```
frontend/
├── index.html            # Main application interface
├── styles/
│   └── main.css         # Modern responsive styling
└── scripts/
    ├── app.js           # Main application logic
    ├── ui.js            # User interface management
    └── websocket.js     # Real-time communication
```

## 📋 Prerequisites

- **Python 3.10** (required)
- **Google API Key** (for Gemini AI models)
- **SERP API Key** (optional, for competitor analysis)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd trendSaaS
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root:
```env
# Required: Google API Key for Gemini AI
google_api_key=your_google_api_key_here

# Optional: SERP API Key for competitor analysis
serp_api_key=your_serp_api_key_here

# Optional: Custom configuration
google_gemini_name=gemini-1.5-pro
google_gemini_name_light=gemini-1.5-flash
TRENDS_API_BASE_URL=http://localhost:8000
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

### 4. Get API Keys

#### Google API Key (Required)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

#### SERP API Key (Optional)
1. Visit [SERP API](https://serpapi.com/)
2. Sign up for a free account
3. Get your API key and add it to `.env`

## 🚀 Quick Start

### Option 1: Single Command Launch
```bash
python start.py
```

This will automatically start both backend and frontend servers.

### Option 2: Manual Launch

#### Start Backend Server
```bash
python main.py
```
Backend will be available at: http://localhost:8000

#### Start Frontend Server
```bash
cd frontend
python -m http.server 3000
```
Frontend will be available at: http://localhost:3000

## 🌐 Access the Application

After installation, the frontend will be available at:
**http://localhost:3000**

## 📊 API Documentation

### Backend API Endpoints

#### Health Check
- `GET /health` - Service health status
- `GET /api/v1/trends/health` - Trends service health
- `GET /api/v1/analyzer/health` - Analyzer service health

#### Trends Analysis
- `GET /api/v1/trends/analyze/{keyword}` - Analyze Google Trends data
- `GET /api/v1/trends/analyze/{keyword}?cmp=true` - With comparison mode

#### AI Analysis
- `POST /api/v1/analyzer/analyze` - Synchronous analysis
- `GET /api/v1/analyzer/analyze/{keyword}` - GET-based analysis
- `WebSocket /api/v1/analyzer/ws` - Real-time analysis with progress updates

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 How It Works

### 1. Data Collection
The system fetches comprehensive Google Trends data including:
- Interest over time (12-month history)
- Related queries (top and rising)
- Rising searches and topics
- Regional and demographic insights

### 2. AI Analysis Pipeline
The multi-step AI pipeline performs:

#### Step 1: Problem Extraction
- Analyzes search queries for pain points
- Identifies user problems and unmet needs
- Assesses problem severity and frequency

#### Step 2: Market Maturity Analysis
- Evaluates interest trends and patterns
- Determines market stage (early/mid/saturated)
- Assesses growth potential and competition level

#### Step 3: Solution Development
- **3a**: Extract solution goals for each problem
- **3b**: Suggest SaaS solution categories
- **3c**: Generate innovative features with competitive advantages

#### Step 4: Competitor Analysis (Optional)
- Identifies existing market players
- Analyzes competitor strengths and weaknesses
- Identifies market gaps and opportunities

#### Step 5: Feature Enhancement
- Enhances features based on competitor analysis
- Creates competitive differentiators
- Prioritizes implementation roadmap

### 3. Real-time Updates
- WebSocket connection provides live progress updates
- Users see analysis progress in real-time
- Immediate results display upon completion

## 🎯 Usage Examples

### Basic Analysis
1. Open http://localhost:3000
2. Enter a keyword (e.g., "productivity tools")
3. Click "Start Analysis"
4. Watch real-time progress updates
5. Review comprehensive results

### Advanced Analysis
- Use comparison mode for competitive analysis
- Analyze emerging trends and seasonal patterns
- Identify market gaps and opportunities
- Generate feature roadmaps for MVP and future versions

## 📈 Sample Results

### Market Analysis
```
Keyword: "project management tools"
Market Stage: Mid-stage
Trend Direction: Rising
Confidence: 85%
```

### Identified Problems
1. **Complex onboarding** (Severity: 8/10)
2. **Team collaboration issues** (Severity: 7/10)
3. **Integration difficulties** (Severity: 6/10)

### SaaS Opportunities
- **Collaborative Project Management Platform**
- **AI-Powered Workflow Automation**
- **Integration Hub for Team Tools**

### Innovative Features
- **Smart Task Prioritization AI**
- **Real-time Team Pulse Analytics**
- **Automated Workflow Templates**
- **Cross-platform Integration Engine**

## 🔧 Configuration Options

### Environment Variables
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `google_api_key` | Google Gemini API key | - | Yes |
| `serp_api_key` | SERP API key for competitor analysis | - | No |
| `google_gemini_name` | Primary Gemini model | gemini-1.5-pro | No |
| `google_gemini_name_light` | Light Gemini model | gemini-1.5-flash | No |
| `TRENDS_API_BASE_URL` | Trends API base URL | http://localhost:8000 | No |
| `HOST` | Server host | 0.0.0.0 | No |
| `PORT` | Server port | 8000 | No |
| `RELOAD` | Auto-reload for development | true | No |

### Customization
- Modify analysis prompts in `services/data_analyzer.py`
- Adjust UI styling in `frontend/styles/main.css`
- Configure WebSocket behavior in `frontend/scripts/websocket.js`

## 🐛 Troubleshooting

### Common Issues

#### 1. API Key Errors
```
Error: Google API key not found
```
**Solution**: Ensure your `.env` file contains a valid `google_api_key`

#### 2. Connection Issues
```
WebSocket connection failed
```
**Solution**: 
- Check if backend is running on port 8000
- Verify firewall settings
- Ensure no other services are using the ports

#### 3. Analysis Failures
```
Analysis failed: Trends API error
```
**Solution**:
- Check internet connection
- Verify Google Trends API availability
- Try with a different keyword

#### 4. Memory Issues
```
Out of memory during analysis
```
**Solution**:
- Close other applications
- Restart the application
- Use simpler keywords for testing

### Debug Commands
Open browser console and use:
```javascript
// Check application status
trendSaaSDebug.getStatus()

// Reset application state
trendSaaSDebug.reset()

// Reconnect WebSocket
trendSaaSDebug.reconnect()
```

## 🧪 Development

### Project Structure
```
trendSaaS/
├── main.py                 # FastAPI application
├── start.py               # Development launcher
├── requirements.txt       # Dependencies
├── services/              # Backend services
│   ├── trends_router.py   # Trends API
│   ├── analyzer_router.py # Analysis API
│   └── data_analyzer.py   # AI pipeline
└── frontend/              # Frontend application
    ├── index.html         # Main page
    ├── styles/            # CSS styles
    └── scripts/           # JavaScript
```

### Adding New Features
1. **Backend**: Add new endpoints in router files
2. **AI Pipeline**: Extend `data_analyzer.py` with new analysis steps
3. **Frontend**: Add UI components in `ui.js` and update `app.js`

### Testing
```bash
# Test backend API
curl http://localhost:8000/health

# Test trends endpoint
curl "http://localhost:8000/api/v1/trends/analyze/productivity"

# Test WebSocket (use a WebSocket client)
ws://localhost:8000/api/v1/analyzer/ws
```

## 📊 Performance

### Optimization Features
- **Token Optimization**: Efficient LLM context management
- **Data Caching**: In-memory analysis result caching
- **Connection Pooling**: Optimized HTTP client usage
- **Progress Streaming**: Real-time updates without blocking

### Scalability
- **Stateless Design**: Easy horizontal scaling
- **Modular Architecture**: Independent service components
- **Resource Management**: Efficient memory and CPU usage

## 🔒 Security

### Best Practices
- **Environment Variables**: Sensitive data stored in `.env`
- **Input Validation**: Comprehensive keyword validation
- **Rate Limiting**: Built-in API rate limiting
- **Error Handling**: Secure error messages without data leakage

### Production Deployment
- Use HTTPS in production
- Configure proper CORS settings
- Implement API authentication
- Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines
- Follow Python PEP 8 style guide
- Use meaningful commit messages
- Add comments for complex logic
- Test thoroughly before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Trends API** for market data
- **Google Gemini** for AI analysis capabilities
- **SERP API** for competitor intelligence
- **FastAPI** for the robust backend framework
- **Font Awesome** for beautiful icons

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

---

**Made with ❤️ for entrepreneurs and product managers**

*Transform market insights into profitable SaaS opportunities*


