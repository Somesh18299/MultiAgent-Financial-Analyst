# Financial Analysis AI 📈

A comprehensive AI-powered financial analysis system that combines web search capabilities with intelligent retry mechanisms to provide detailed financial insights and analysis.

## 🌟 Features

- **AI-Powered Analysis**: Uses Groq's LLaMA 3 model for intelligent financial analysis
- **Web Search Integration**: Leverages Tavily Search API for real-time financial data
- **Intelligent Retry System**: Automatically retries with different strategies when initial analysis quality is below threshold
- **Multi-Source Data Aggregation**: Combines information from multiple sources for comprehensive analysis
- **Quality Assessment**: Built-in critic system that evaluates analysis quality and triggers retries when needed
- **Modern Web Interface**: Clean Streamlit frontend with real-time progress tracking
- **RESTful API**: FastAPI backend with comprehensive documentation


## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- GROQ API Key ([Get it here](https://console.groq.com))
- Tavily API Key ([Get it here](https://tavily.com))

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd financial-analysis-ai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

   This will start both the backend and frontend servers automatically and open your browser.

### Manual Setup (Alternative)

If you prefer to run services separately:

1. **Start the backend:**
   ```bash
   uvicorn backend:app --host localhost --port 8000 --reload
   ```

2. **Start the frontend (in another terminal):**
   ```bash
   streamlit run frontend.py --server.port 8501
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key for LLM access | Yes |
| `TAVILY_API_KEY` | Your Tavily API key for web search | Yes |

### System Parameters

The system uses fixed parameters for consistent performance:
- **Target Score**: 5 (minimum quality score for analysis)
- **Max Retries**: 5 (maximum retry attempts)
- **Search Results**: 3 per query
- **Timeout**: 300 seconds (5 minutes)

## 💡 Usage Examples

### Web Interface

1. Open http://localhost:8501 in your browser
2. Enter your financial question, such as:
   - "How is Apple performing in Q4 2024?"
   - "What are Tesla's key financial metrics this quarter?"
   - "Analyze Microsoft's recent earnings report"
3. Click "🚀 Analyze" and wait for results

### API Usage

```python
import requests

# Analyze a financial query
response = requests.post("http://localhost:8000/analyze", json={
    "query": "How is Apple stock performing in 2024?",
    "purpose": "financial analysis"
})

result = response.json()
print(result["final_answer"])
```

```bash
# Using curl
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Tesla Q4 2024 earnings analysis",
       "purpose": "financial analysis"
     }'
```

## 🔄 How It Works

### Analysis Workflow

1. **Planning**: AI breaks down your question into 3 focused sub-questions
2. **Retrieval**: Concurrent web searches gather relevant financial data
3. **Summarization**: AI analyzes and summarizes findings for each sub-question
4. **Quality Assessment**: Critic evaluates analysis completeness and accuracy
5. **Retry Logic**: If quality is below threshold, system retries with enhanced strategies
6. **Synthesis**: Creates comprehensive final analysis combining all findings

### Retry Strategies

- **Attempts 1-3**: Refine sub-questions for more specific searches
- **Attempts 4-6**: Modify search terms with financial synonyms
- **Attempts 7+**: Broaden search scope for general information

## 📊 API Endpoints

### POST /analyze
Analyze a financial query with AI agents.

**Request:**
```json
{
  "query": "Your financial question",
  "purpose": "financial analysis"
}
```

**Response:**
```json
{
  "final_answer": "Comprehensive analysis...",
  "critic_score": 8,
  "retry_count": 2,
  "processing_time": {
    "planning": 1.2,
    "retrieval": 3.4,
    "summarization": 2.1,
    "critic": 0.8,
    "synthesis": 1.5
  },
  "max_retries_reached": false,
  "error": false
}
```

### GET /health
Check API health status.

### GET /docs
Interactive API documentation (Swagger UI).

## 🎯 Best Practices

### For Better Results

1. **Be Specific**: Include company names, time periods, and specific metrics
2. **Use Financial Terms**: Incorporate terms like "earnings," "revenue," "P/E ratio"
3. **Recent Data**: Ask about recent quarters or current year for best data availability
4. **Multiple Aspects**: Questions covering different angles get more comprehensive analysis

### Example Good Queries

- ✅ "Apple's Q4 2024 revenue growth and profit margins compared to Q3"
- ✅ "Tesla's production numbers and delivery targets for 2024"
- ✅ "Microsoft Azure revenue growth and market share in cloud computing"

### Example Poor Queries

- ❌ "Tell me about Apple" (too vague)
- ❌ "Stock market" (too broad)
- ❌ "Best investment" (subjective)

## 🔍 Troubleshooting

### Common Issues

1. **API Keys Not Working**
   - Verify keys are correctly set in `.env` file
   - Check for extra spaces or quotes around keys
   - Ensure keys have sufficient credits/quota

2. **Backend Connection Failed**
   - Check if backend is running on port 8000
   - Verify no firewall blocking localhost connections
   - Try restarting with `python main.py`

3. **Search Results Empty**
   - Some queries may not have recent web data
   - Try rephrasing with more specific terms
   - Check Tavily API quota and status

4. **Analysis Takes Too Long**
   - Complex queries may take 2-3 minutes
   - Check network connectivity
   - Monitor API rate limits

### Logs and Debugging

The system provides detailed logging. Check console output for:
- API connection status
- Search query results
- Retry attempt information
- Processing time breakdowns

## 🛠️ Development

### Project Structure

```
financial-analysis-ai/
├── main.py              # Application launcher
├── backend.py           # FastAPI backend server
├── frontend.py          # Streamlit frontend
├── graph.py             # LangGraph workflow definition
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
└── README.md            # This file
```

### Adding New Features

1. **New Analysis Types**: Extend the `purpose` parameter in requests
2. **Additional Data Sources**: Add new search tools in `graph.py`
3. **Custom Retry Strategies**: Modify retry functions in the workflow
4. **UI Enhancements**: Update `frontend.py` with new Streamlit components

### Testing

```bash
# Test backend health
curl http://localhost:8000/health

# Test analysis endpoint
curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"query": "test query"}'
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Check the API documentation at http://localhost:8000/docs
- Review logs for error details

## 🎉 Acknowledgments

- **Groq** for fast LLM inference
- **Tavily** for web search capabilities  
- **LangChain** for AI agent framework
- **Streamlit** for rapid frontend development
- **FastAPI** for high-performance backend

---

Built with ❤️ for financial analysis and AI automation.