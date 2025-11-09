# 🏠 Real Estate Property Valuation Assistant

An AI-powered system that analyzes comparable sales and market data to provide accurate property valuations using LLM intelligence.

## ✨ Features

- 🔍 **Intelligent Search**: Searches for comparable properties using DuckDuckGo
- 🤖 **AI Data Extraction**: Uses LLM to intelligently extract property data from search results
- 📊 **Market Analysis**: Analyzes comparable sales and market trends
- 💰 **Price Estimation**: Provides estimated price range with confidence levels
- 🎯 **Valuation Verdict**: Determines if property is underpriced, fair, or overpriced
- 🔗 **Source Links**: Shows all search results with direct links for verification
- 📈 **Comet ML Logging**: Tracks all LLM calls, searches, and workflow steps
- 🎨 **Beautiful UI**: Clean Streamlit interface with progress indicators and detailed insights

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

Create `.env` file:
```
GROQ_API_KEY=your_groq_api_key
COMET_API_KEY=your_comet_api_key (optional)
COMET_PROJECT_NAME=realestate-valuation
COMET_WORKSPACE=default
```

### Run

```bash
# Streamlit Web UI
streamlit run streamlit_app.py

# Access at: http://localhost:8501
```

## 📊 How It Works

```
1. Property Input → Enter address, size, bedrooms, asking price
2. Search Planning → Generate 8 optimized search queries
3. Web Search → Search for comparable properties
4. LLM Extraction → Intelligently extract property data
5. Data Filtering → Validate and filter extracted data
6. Valuation → Calculate estimates and generate verdict
7. Results → Display estimates, comparables, and recommendations
8. Logging → All steps logged to Comet ML for monitoring
```

## 🎯 Valuation Logic

- Searches for recent comparable sales
- Extracts: price, sqft, bedrooms, bathrooms, date
- Filters by quality (proximity, property similarity)
- Calculates weighted average price/sqft
- Applies market adjustments
- Generates low/mid/high estimates
- Determines: UNDERPRICED, FAIR, or OVERPRICED

## 📈 What Gets Logged to Comet ML

- Each node's start/completion
- All search queries executed
- LLM API calls (prompt, response, tokens)
- Data extraction results
- Final valuation and verdict
- Any errors or issues

## 📁 Project Structure

```
agents/           # AI agents (search planning, extraction, valuation)
scrapers/         # Web scraping utilities
prompts/          # LLM prompt templates
graph.py          # Workflow orchestration
streamlit_app.py  # Web interface
logger_comet.py   # Comet ML integration
```

## 🔧 Technologies Used

- **LangGraph**: Workflow orchestration
- **Groq API**: LLM (llama-3.3-70b-versatile)
- **LangChain**: LLM framework
- **DuckDuckGo**: Web search
- **Streamlit**: Web UI
- **Comet ML**: Experiment tracking and logging
- **Pandas**: Data analysis

## 💡 Example

**Input:**
- Address: 123 Main Street, Austin, TX 78701
- Size: 1,800 sqft
- Beds: 3, Baths: 2
- Asking Price: $450,000

**Output:**
```
Estimated Value: $768,996
Difference: +$318,996 (+70.9%)
Verdict: UNDERPRICED ✓

Comparable Found: $769,000 (1,800 sqft)
Market Avg: $427.22/sqft
Confidence: MEDIUM
```

## 📚 Detailed Setup Guide

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for comprehensive documentation.

## 🐛 Troubleshooting

**No comparables found?**
- Normal for some addresses; depends on available real estate data
- Try with addresses in major metros (Austin, NYC, LA, etc.)

**DuckDuckGo warnings in logs?**
- These are INFO messages, not errors
- System automatically falls back to other search engines

**Missing API key?**
- Add GROQ_API_KEY to .env
- Comet ML is optional (add COMET_API_KEY to enable)

## 📝 Notes

- Real-time searches using DuckDuckGo
- LLM temperature set to 0.1 for consistency
- Max 2,000 tokens per LLM call
- All processing is local (no data storage)

## 🔐 Security & Privacy

- API keys stored in .env (not committed)
- No personal data storage
- External services: Groq, DuckDuckGo, Comet ML
- Results are estimates based on available data

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
