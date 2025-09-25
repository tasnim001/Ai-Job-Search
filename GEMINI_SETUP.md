# Gemini Integration Setup Guide

## Overview
Your job search platform is already integrated with Google Gemini in two key areas:
1. **Embeddings**: Using `models/text-embedding-004` for semantic search
2. **Query Parsing**: Using `gemini-2.5-flash` for natural language understanding

## Quick Setup

### 1. Get Your Gemini API Key
1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Click "Get API key" to generate your key
4. Copy your API key

### 2. Configure Your Environment
Create a `.env` file in your project root:

```env
# Gemini Configuration
GOOGLE_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_DIMENSION=768
```

### 3. Install Dependencies (Already Done)
Your `requirements.txt` already includes:
```
google-generativeai==0.8.3
```

## Gemini Models Available

### For Query Parsing (LLM):
- **`gemini-2.5-flash`** (Default) - Fast and cost-effective
- **`gemini-2.5-pro`** - More powerful for complex queries
- **`gemini-1.5-flash`** - Good balance of speed/performance

### For Embeddings:
- **`models/text-embedding-004`** (Default) - Latest embedding model
- **`models/embedding-001`** - Alternative option

## How It Works

### Enhanced Query Parser
Your system now uses Gemini LLM to understand natural language queries like:

**Input**: "Find me remote Python jobs in Dhaka with 50k+ salary"

**Gemini Output**:
```json
{
  "intent": "job_search",
  "keywords": ["remote"],
  "location": "Dhaka",
  "salary_min": 50000,
  "employment_type": "remote",
  "skills": ["Python"],
  "category": "Software Engineering"
}
```

### Fallback System
- If Gemini is unavailable → Falls back to rule-based parsing
- If API key is placeholder → Uses rule-based parsing
- Graceful error handling ensures system always works

## Testing the Integration

Run your job insertion script:
```bash
cd scripts
python insert_jobs.py --sample
```

Test the search API:
```bash
curl "http://localhost:8000/search?q=Python developer jobs in Dhaka with 60k salary"
```

## Cost Optimization Tips

1. **Use Flash models**: `gemini-2.5-flash` is cost-effective for parsing
2. **Cache results**: Consider caching parsed queries for repeated searches
3. **Batch requests**: Process multiple queries together when possible

## API Limits & Best Practices

### Free Tier Limits
- **Rate Limit**: 10 requests per minute per model (Free tier)
- **Daily Limit**: Check your [Google AI Studio](https://ai.google.dev/) dashboard
- **Token Limits**: Flash models handle up to 1M tokens
- **Automatic Fallback**: When limits hit, system uses rule-based parsing

### Rate Limit Handling
Your system automatically handles rate limits:
```
Error: 429 You exceeded your current quota
→ Falls back to rule-based parser
→ Service continues without interruption
→ No user-facing errors
```

### Upgrade Options
For production use, consider:
- **Gemini Pro**: Higher rate limits
- **Pay-as-you-go**: Remove free tier restrictions
- **Enterprise**: Custom quotas and SLAs

## Monitor Usage

Track your API usage at [Google AI Studio](https://ai.google.dev/):
- Monitor daily/monthly usage
- Set up billing alerts if needed
- Review query patterns for optimization

## Next Steps

Your implementation is production-ready! Consider these enhancements:

1. **Query Caching**: Cache parsed queries to reduce API calls
2. **A/B Testing**: Compare Gemini vs rule-based parsing performance
3. **Analytics**: Track which queries benefit most from LLM parsing
4. **Multilingual**: Extend Gemini prompt for non-English queries
