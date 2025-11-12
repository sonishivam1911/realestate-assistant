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
  ├─ Selects 10 most relevant ZIPs by proximity
  └─ Limits processing for efficiency
  ↓
🕷️ NODE 3: Zillow Scraping
  ├─ Parallel scraping of up to 10 ZIP codes (8 concurrent workers)
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
📍 ZIP Discovery     ✅ Found 8 nearby ZIP codes (10-mile radius, affluent tier)
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

---

## 🎯 VALUATION METHODOLOGY - 5 Complete Examples

### How the System Works

1. **Input**: Property details (beds, baths, sqft, location, condition)
2. **ZIP Discovery**: Find 2-5 nearby ZIPs within 10-mile radius ✅ **10 MILES NOW** (updated)
3. **Affluence Filtering**: Keep ONLY same economic tier ✅ **NEW** (no Princeton + Trenton mixing)
4. **Scraping**: Collect 15-25 comparable properties from affluent neighborhoods
5. **Ranking**: Sort by similarity score (0.0-1.0) to target property
6. **Price Analysis**: Calculate weighted average $/sqft from top 10 comparables
7. **Adjustments**: Apply location, condition, age, market trend adjustments
8. **Valuation**: Generate low/mid/high estimates with confidence score

---

### Example 1: Princeton, NJ - $750K Colonial (3BR/2BA)

**Property:**
- 42 Witherspoon Street, Princeton, NJ 08540
- Type: Single-family colonial | 2,200 sqft | 0.5 acres
- Built: 1985 (renovated 2015) | Condition: Excellent

**Step 1: ZIP Discovery (10-mile radius, affluent tier only)**
```
Search query: "ZIP codes near Princeton NJ affluent neighborhoods"
Found ZIPs: 08540, 08542, 08544, 08546, 08550
Rejected: 08501 (Trenton - lower income), 08511 (Hightstown - different tier)
```

**Step 2: Comparable Properties Found (Top 10 Ranked)**
```
#1  127 Nassau Street, Princeton  | $745K | 2,180 sqft | $342/sqft | 3BR/2BA | Sold 2mo ago | Similarity: 0.97
#2  5 Prospect Ave, Princeton      | $780K | 2,250 sqft | $347/sqft | 3BR/2.5BA | Sold 3mo ago | Similarity: 0.95
#3  84 Alexander Street, Princeton | $695K | 2,100 sqft | $331/sqft | 3BR/2BA | Sold 4mo ago | Similarity: 0.93
#4  22 Faculty Road, Princeton     | $825K | 2,350 sqft | $351/sqft | 3BR/2.5BA | Sold 2mo ago | Similarity: 0.88
#5  Princeton Twp - Winding Road   | $740K | 2,190 sqft | $338/sqft | 3BR/2BA | Sold 1mo ago | Similarity: 0.86
#6  18 Mountain Avenue             | $760K | 2,280 sqft | $333/sqft | 4BR/2BA | Sold 5mo ago | Similarity: 0.82
#7  Skillman - Deer Run            | $715K | 2,050 sqft | $349/sqft | 3BR/2BA | Sold 2mo ago | Similarity: 0.80
#8  31 Birch Lane, Princeton       | $855K | 2,400 sqft | $356/sqft | 3BR/2.5BA | Active 42d | Similarity: 0.79
#9  Rocky Hill - Cottage Lane      | $725K | 2,100 sqft | $345/sqft | 3BR/2BA | Sold 3mo ago | Similarity: 0.77
#10 15 Boudinot Street             | $770K | 2,200 sqft | $350/sqft | 3BR/2.5BA | Sold 1mo ago | Similarity: 0.76
```

**Step 3: Price Analysis**
```
Average $/SqFt from top 10:  $342/sqft
Target Property SqFt:        2,200
Base Valuation:              $342 × 2,200 = $752,400
```

**Step 4: Adjustments Applied**
```
Base Price:                  $752,400
+ Superior location/lot:     +$15,000
+ Recent renovation (2015):  +$8,000
+ Excellent condition:       +$5,000
+ Hot market trend (+3%):    +$22,572
──────────────────────────
Adjusted Value:              $802,972
```

**Step 5: Final Valuation**
```
Conservative (Low):   $785,000  (-2.2%)
Market Value (Mid):   $805,000  ✓ RECOMMENDED PRICE
Optimistic (High):    $825,000  (+2.5%)

Confidence Score: 94% (VERY HIGH)
  ✓ 10 recent sold comparables (2-5 months old)
  ✓ Excellent similarity match (avg 0.86)
  ✓ Same affluent neighborhood tier
  ✓ Hot market with clear pricing trends
  ✓ Recently renovated matches comp profile

Market Snapshot:
  • Similar homes: $745K-$855K
  • $/SqFt range: $331-$356/sqft
  • Days on market: 25-30 days
  • Market trend: UP 3% YoY
```

**Recommendation:** List at $805K for optimal market positioning. Hot market supports this price. Expect sale within 25-30 days.

---

### Example 2: Austin, TX - $550K Luxury Condo (2BR/2BA)

**Property:**
- 601 W 6th Street #308, Austin, TX 78703
- Type: High-rise luxury condo | 1,400 sqft
- Year Built: 2012 | Condition: Excellent
- Amenities: Gym, pool, concierge, valet parking

**ZIP Discovery (10 miles, luxury tier only)**
```
Searched ZIPs: 78701, 78702, 78703, 78704, 78705 (all luxury)
Rejected: 78721 (East Riverside - different tier), 78702-mixed areas
```

**Top 10 Comparables**
```
Avg $/SqFt: $387/sqft

#1  360 Nueces St #2501       | $520K | 1,380 sqft | $377/sqft | Sold 1mo | Sim: 0.98
#2  77 San Jacinto #602       | $565K | 1,425 sqft | $397/sqft | Sold 2mo | Sim: 0.96
#3  The Austonian #2806       | $545K | 1,410 sqft | $386/sqft | Sold 3mo | Sim: 0.94
#4  222 Barton Springs #806   | $580K | 1,450 sqft | $400/sqft | Sold 2mo | Sim: 0.91
#5  Brazos Lofts #608         | $510K | 1,350 sqft | $378/sqft | Sold 2mo | Sim: 0.88
(+ 5 more similar properties)
```

**Valuation Calculation**
```
Base: 1,400 sqft × $387 = $541,800

Adjustments:
+ Premium building:     +$8,000
+ Full amenities:       +$5,000
+ Excellent condition:  +$3,000
+ Strong market (+2.5%): +$13,545
─────────────────
Final: $571,345 → $570,000
```

**Final Estimate**
```
Low:  $545,000
Mid:  $570,000 ✓ RECOMMENDED
High: $595,000

Confidence: 91% (EXCELLENT)
Days on market: 20-25 days (hot market)
```

---

### Example 3: San Francisco, CA - $1.8M Victorian (4BR/3BA)

**Property:**
- 1234 Alamo Square, San Francisco, CA 94117
- Type: Victorian single-family | 3,200 sqft | 0.25 acres
- Built: 1892 (restored) | Condition: Excellent

**Analysis**
```
Affluent ZIPs searched: 94117, 94121, 94118, 94108
Comparable count: 22 sold + 8 for-sale

Average $/SqFt: $612/sqft (ultra-premium SF)
Base: 3,200 × $612 = $1,958,400

Adjustments:
+ Historic Victorian charm:    +$50,000
+ Alamo Square premium location: +$100,000
+ Full restoration:            +$40,000
- Market decline (-0.5%):      -$9,792
─────────────────────
Final: $1,775,000
```

**Valuation**
```
Low:  $1,720,000
Mid:  $1,775,000 ✓ MARKET VALUE
High: $1,830,000

Confidence: 85% (GOOD)
Note: Fewer ultra-luxury comps available, but market data strong
```

---

### Example 4: Miami, FL - $425K Waterfront Condo (2BR/2BA)

**Property:**
- 1000 Brickell Ave #2505, Miami, FL 33131
- Type: Luxury waterfront condo | 1,200 sqft
- View: Ocean/bay | Full amenities

**Analysis**
```
Affluent ZIPs: 33131, 33139, 33141, 33142
Rejected: 33010, 33013 (lower income areas)

Comparable count: 16 sold + 10 for-sale
Quality score: 0.81 (good, but seasonal variation in Miami)

Avg $/SqFt: $356/sqft
Base: 1,200 × $356 = $427,200

Adjustments:
+ Ocean view:          +$15,000
+ Waterfront location: +$12,000
+ Luxury amenities:    +$8,000
+ Good condition:      +$3,000
+ Hot market (+4%):    +$17,088
─────────────────
Final: $480,000
```

**Valuation**
```
Low:  $465,000
Mid:  $480,000 ✓ MARKET VALUE
High: $495,000

Confidence: 78% (MODERATE)
Note: Miami market has seasonal fluctuations and international buyer influence
```

---

### Example 5: Denver, CO - $650K Modern Home (3BR/2.5BA)

**Property:**
- 2250 S Columbine, Denver, CO 80210
- Type: Modern architectural | 2,400 sqft | 0.35 acres
- Year Built: 2018 (like new) | Condition: Excellent
- Location: Affluent Mayfair neighborhood

**Analysis**
```
Affluent ZIPs: 80210, 80209, 80211, 80218
Rejected: 80011, 80246 (different tiers)

Comparable count: 20 sold + 12 for-sale
Quality score: 0.87 (good)

Avg $/SqFt: $271/sqft
Base: 2,400 × $271 = $650,400

Adjustments:
+ Modern/new construction:    +$25,000
+ Excellent condition:        +$15,000
+ Affluent Mayfair location:  +$12,000
+ Fast-growing market (+6%):  +$39,024
──────────────────
Final: $741,424
```

**Valuation**
```
Low:  $715,000
Mid:  $740,000 ✓ MARKET VALUE
High: $765,000

Confidence: 90% (VERY GOOD)
Days on market: 15-20 days (hot market)
Note: Denver market very strong with robust buyer demand
```

---

### � Comparison Across Examples

| Market | Property Type | Price | Confidence | Days/Market | Trend | Economic Tier |
|--------|---------------|-------|-----------|------------|-------|---------------|
| Princeton, NJ | Colonial | $805K | 94% | 25-30 | Hot (+3%) | Affluent ✓ |
| Austin, TX | Luxury Condo | $570K | 91% | 20-25 | Hot (+2.5%) | Luxury ✓ |
| San Francisco, CA | Victorian | $1.78M | 85% | 25-35 | Stable | Ultra-Luxury ✓ |
| Miami, FL | Waterfront | $480K | 78% | 30-40 | Moderate | High-End ✓ |
| Denver, CO | Modern | $740K | 90% | 15-20 | Hot (+6%) | Affluent ✓ |

**Key Updates Shown in Examples:**
- ✅ **10-mile radius** used in all ZIP searches (increased from 5-6)
- ✅ **Affluent tier only** - no cross-economic comparisons (Princeton ≠ Trenton)
- ✅ **Same state only** - all comparables in same state
- ✅ **2-5 quality ZIPs** - flexible selection based on data quality
- ✅ **Confidence transparency** - confidence scores based on comparable quality
- ✅ **Economic tier matching** - Princeton comps from affluent neighborhoods only

---

### More Examples

See **[EXAMPLES.md](EXAMPLES.md)** for comprehensive examples across multiple markets:

- **New York**: Manhattan luxury, Upper West Side, Queens condos
- **New Jersey**: Jersey City, Princeton, Newark
- **Connecticut**: Greenwich luxury homes
- **Pennsylvania**: Philadelphia lofts, Main Line estates
- **Massachusetts**: Boston Back Bay townhouses

Each example includes:
- ✅ Property details and specifications
- ✅ Complete valuation results with price ranges
- ✅ Market analysis and insights
- ✅ Confidence scores and comparable counts

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
