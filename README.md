# 🏠 Real Estate Property Valuation Assistant

An AI-powered multi-agent system that analyzes comparable sales and market data to provide accurate property valuations using LangGraph and LLM intelligence.

## ✨ Features

- 🔍 **Multi-Agent Architecture**: 5 specialized agents (Query Analysis, ZIP Discovery, Scraping, Preprocessing, Valuation)
- 📍 **Smart ZIP Discovery**: Uses DuckDuckGo to find nearby ZIP codes for market analysis
- 🕷️ **Parallel Zillow Scraping**: Concurrent scraping with 8 parallel workers for fast data collection
- 🤖 **LLM-Powered Valuation**: Uses Groq's Llama model for intelligent analysis
- 📊 **Comprehensive Market Analysis**: Analyzes comparable sales, market trends, and inventory
- 💰 **Price Range Estimation**: Generates low/mid/high estimates with confidence levels
- 🎯 **Smart Verdicts**: Determines if property is UNDERPRICED, FAIR, or OVERPRICED
- � **Real-Time Progress Tracking**: Visual loaders synced with each workflow node
- � **Export Options**: Download detailed reports as JSON or comparable data as CSV
- 🎨 **Beautiful UI**: Clean Streamlit interface with metrics, cards, and detailed insights
- 🔒 **Production-Ready**: Dockerized deployment with proper error handling

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment
- API Keys: Groq, Comet ML (optional)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd realestate-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file in the project root:
```bash
# Required - Get from https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# Optional - For LangSmith tracing and monitoring
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=realestate-valuation
```

### Run Locally

```bash
# Using the startup script
./start.sh

# Or manually
source venv/bin/activate
streamlit run streamlit_app.py

# Access at: http://localhost:8501
```

### Run with Docker

```bash
# Build image
docker build -t realestate-assistant .

# Run container
docker run -p 8501:8501 \
  -e GROQ_API_KEY=your_key_here \
  realestate-assistant streamlit run streamlit_app.py
```

## 📊 How It Works

The system uses a 5-node LangGraph pipeline for property valuation:

```
START
  ↓
🔍 NODE 1: Query Analysis
  ├─ Parses property details
  ├─ Generates search strategy
  └─ Extracts location info
  ↓
📍 NODE 2: ZIP Discovery
  ├─ Searches nearby ZIP codes via DuckDuckGo
  ├─ Identifies primary & nearby areas
  └─ Collects all target ZIPs
  ↓
🕷️ NODE 3: Zillow Scraping
  ├─ Parallel scraping of 8 ZIP codes concurrently
  ├─ Collects sold & for-sale properties
  ├─ Extracts: price, sqft, beds, baths, dates
  └─ Filters by timeframe
  ↓
🔧 NODE 4: Data Preprocessing
  ├─ Validates & filters properties
  ├─ Ranks comparables by similarity
  ├─ Calculates market statistics
  └─ Scores data quality
  ↓
💰 NODE 5: Valuation
  ├─ LLM analyzes comparable data
  ├─ Calculates price estimates (low/mid/high)
  ├─ Determines market verdict
  └─ Generates recommendations
  ↓
END
```

**Real-Time UI**: Each node shows:
- ⏳ **Pending** state (gray) → Processing (yellow) → ✅ **Completed** (green)

## 🎯 Valuation Logic

The LLM analyzes all comparable data to generate estimates:

1. **Data Collection**: Scrapes 50-100+ recent comparable sales
2. **Filtering**: Removes outliers and low-quality data
3. **Analysis**: Groups by similarity metrics (size, beds, baths, location)
4. **Calculation**: 
   - Computes weighted average price/sqft
   - Applies market adjustments
   - Generates low/mid/high estimates
5. **Confidence Scoring**: Based on:
   - Number of comparables used
   - Data quality score (50-100%)
   - Market volatility
   - Price variance
6. **Verdict**:
   - UNDERPRICED: Estimated > Asking + 10%
   - OVERPRICED: Estimated < Asking - 10%
   - FAIR: Within ±10% of estimate

## 📈 What Gets Logged (LangSmith)

When LANGSMITH_API_KEY is configured, the system traces:

- ✅ Each node's execution (input → output)
- 🔍 All DuckDuckGo searches and results
- 💬 LLM prompts and completions
- 📊 Data extracted and filtered
- 💰 Final valuation estimates and verdict
- ⚠️ Any errors or warnings encountered
- ⏱️ Execution times for each node

## 📁 Project Structure

```
realestate-assistant/
├── agents/                 # AI agents for each workflow node
│   ├── query_analyzer.py   # Query Analysis Agent
│   ├── zip_discovery.py    # ZIP Discovery Agent
│   ├── zillow_scraper.py   # Zillow Scraping Agent (parallel)
│   ├── data_preprocessor.py # Data Preprocessing Agent
│   └── valuation_agent.py  # Valuation Judgment Agent
├── scrapers/               # Web scraping utilities
│   ├── duckduckgo_search.py # Parallel DuckDuckGo searcher
│   └── html_parsers.py     # HTML parsing utilities
├── prompts/                # LLM prompt templates
│   ├── queryAnalysisPrompt.py
│   ├── zipExtractionPrompt.py
│   └── valuationJudgmentPrompt.py
├── workflow/               # Workflow orchestration
│   ├── state.py           # State management
│   └── valuation_graph.py # LangGraph pipeline
├── streamlit_app.py       # Web UI
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker deployment
└── .env.example           # Environment template
```

## 🔧 Technologies Used

- **LangGraph**: Multi-agent workflow orchestration
- **Groq API**: Fast LLM inference (llama-3.1-8b-instant)
- **LangChain**: LLM framework & utilities
- **Streamlit**: Interactive web UI
- **DuckDuckGo**: Web search (parallel, 5 workers)
- **Zillow Scraper**: Property data (parallel, 8 workers)
- **LangSmith**: LLM tracing & monitoring (optional)
- **Pandas**: Data analysis & CSV export
- **Geopy**: Geocoding & location validation
- **Docker**: Containerization & deployment

## 💡 Example

**Input:**
- Address: 123 Main Street, Austin, TX 78701
- Size: 1,800 sqft
- Beds: 3, Baths: 2
- Asking Price: $450,000

**Workflow Execution:**
```
🔍 Query Analysis    ✅ Parsed address and requirements
📍 ZIP Discovery     ✅ Found 8 nearby ZIP codes
🕷️ Zillow Scraping   ✅ Scraped 67 comparable properties (8 parallel workers)
🔧 Preprocessing     ✅ Filtered to 45 high-quality comparables
💰 Valuation         ✅ Generated valuation report
```

**Output:**
```
VALUATION VERDICT: UNDERPRICED 📈

Asking Price:        $450,000
Estimated Value:     $580,000
Difference:          +$130,000 (+28.9%)

Price Range:
  Low:   $520,000
  Mid:   $580,000
  High:  $640,000

Confidence: HIGH (92.3%)
Data Quality: 94%
Comparables Used: 45

Market Analysis:
  Trend: Appreciating
  Inventory: Low
  Price/sqft: $322.22
```

## 📚 Detailed Setup Guide

### System Requirements
- Python 3.8 or higher
- 2GB RAM minimum
- Internet connection (for searches and API calls)

### Step-by-Step Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/sonishivam1911/realestate-assistant.git
   cd realestate-assistant
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get API key from Groq**
   - Visit https://console.groq.com
   - Create account and API key
   - Copy the key

5. **Create .env file**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

6. **Run application**
   ```bash
   ./start.sh
   # Or: streamlit run streamlit_app.py
   ```

7. **Open in browser**
   - Navigate to http://localhost:8501

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY not found` | Add key to `.env` file and restart app |
| No comparables found | Normal for some addresses; try major metros (Austin, NYC, LA, SF) |
| "Unsupported format string" error | Update to latest version; all None values now handled |
| Slow scraping | This is normal; parallel workers optimize speed (8 concurrent ZIPs) |
| DuckDuckGo warnings | These are INFO messages; system continues normally |
| Out of memory | Try with smaller timeframes or reduce comparable count |
| Streamlit connection error | Ensure port 8501 is not in use; try `streamlit run --port 8502` |

### Debug Mode

```bash
# Run with verbose logging
STREAMLIT_LOGGER_LEVEL=debug streamlit run streamlit_app.py

# Check API connectivity
python -c "from agents.query_analyzer import QueryAnalysisAgent; print('✅ Imports OK')"
```

## 📝 Notes

- **Parallel Processing**: 
  - ZIP scraping: 8 concurrent workers
  - DuckDuckGo searches: 5 concurrent workers
  - Estimated 3-4x speedup vs sequential execution

- **LLM Configuration**:
  - Temperature: 0.1 (for consistency)
  - Model: llama-3.1-8b-instant
  - Max tokens: 1000 per call

- **Data Processing**:
  - All processing is local
  - No data storage or persistence
  - Results cleared on app restart

- **Search Scope**:
  - Searches recent sales (configurable timeframe)
  - Focuses on similar properties (beds, baths, sqft)
  - Applies geographic filtering

## 🔐 Security & Privacy

- **API Keys**: Stored in `.env` file (never committed to git)
- **Data**: No personal information is stored or logged
- **Processing**: All data handling is in-memory only
- **External Services**: 
  - Groq (LLM inference)
  - DuckDuckGo (search results)
  - Zillow (public property data)
  - LangSmith (optional tracing)
- **Results**: Estimates based on available market data
- **Limitations**: Results are not professional appraisals

### Best Practices
```bash
# Never commit .env file
echo ".env" >> .gitignore

# Keep API key secret
# Rotate periodically
# Use different keys per environment (dev/prod)
```

## 📜 License

MIT

## 🙋 Support

For issues:
1. Check SETUP_GUIDE.md
2. Review Comet ML experiment logs
3. Check console output for error messages

---

**Created with ❤️ for real estate professionals**

🏠 **Happy Valuating!**
