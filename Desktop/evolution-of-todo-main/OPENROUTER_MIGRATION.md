# OpenRouter API Integration Guide

## Overview

The Phase III AI Chatbot now uses **OpenRouter API** instead of direct OpenAI API access. OpenRouter provides:
- Access to multiple LLM providers (OpenAI, Anthropic, Google, Meta, etc.)
- OpenAI-compatible API (no code changes needed)
- Competitive pricing and pay-per-use model
- Unified interface for different models

## Configuration Changes

### Environment Variables

**Old (OpenAI Direct):**
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

**New (OpenRouter):**
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4
```

### Files Modified

1. **backend/src/config.py**
   - Added `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`
   - Updated validation to check for OpenRouter API key
   - Removed OpenAI-specific configuration

2. **backend/src/ai/agent.py**
   - Updated to use OpenRouter configuration from settings
   - Modified OpenAI client initialization with custom base_url
   - Improved error messages with OpenRouter key instructions

3. **backend/.env**
   - Replaced OpenAI configuration with OpenRouter
   - Added model selection guide with popular options

4. **backend/.env.example**
   - Updated template with OpenRouter configuration

## Getting Started

### 1. Get Your OpenRouter API Key

1. Visit [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `sk-or-v1-...`)

### 2. Configure Your Environment

Edit `backend/.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=openai/gpt-4
```

### 3. Choose Your Model

OpenRouter uses the format: `provider/model-name`

#### Popular Models

**OpenAI Models:**
- `openai/gpt-4` - Most capable, best for complex tasks
- `openai/gpt-3.5-turbo` - Fast and cost-effective
- `openai/gpt-4-turbo` - Latest GPT-4 with improved performance

**Anthropic Claude:**
- `anthropic/claude-3-opus` - Most capable Claude model
- `anthropic/claude-3-sonnet` - Balanced performance and cost
- `anthropic/claude-3-haiku` - Fastest and most affordable

**Google Gemini:**
- `google/gemini-pro` - Google's flagship model
- `google/gemini-pro-vision` - Multimodal capabilities

**Meta Llama:**
- `meta-llama/llama-3-70b-instruct` - Open-source, powerful
- `meta-llama/llama-3-8b-instruct` - Smaller, faster

**Full Model List:** [https://openrouter.ai/models](https://openrouter.ai/models)

## Model Selection Guide

### For Production (Recommended)
```bash
OPENROUTER_MODEL=openai/gpt-4
```
- Best quality responses
- Excellent tool calling support
- Reliable for task management

### For Development/Testing
```bash
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```
- Much cheaper (~10x less expensive)
- Fast responses
- Good enough for testing

### For Cost Optimization
```bash
OPENROUTER_MODEL=anthropic/claude-3-haiku
```
- Very affordable
- Fast responses
- Good quality for simple tasks

### For Open Source
```bash
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct
```
- No vendor lock-in
- Competitive performance
- Cost-effective

## Technical Details

### How It Works

The OpenAI Python SDK is used with a custom `base_url` parameter:

```python
from openai import OpenAI

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL  # Points to OpenRouter
)

# All OpenAI SDK methods work as normal
response = client.chat.completions.create(
    model=settings.OPENROUTER_MODEL,
    messages=[...],
    tools=[...]
)
```

### API Compatibility

OpenRouter implements the OpenAI API specification, so:
- ✅ Chat completions work identically
- ✅ Tool/function calling supported
- ✅ Streaming responses supported
- ✅ All OpenAI SDK features available

### Error Handling

If the API key is missing, the backend will:
1. Raise a clear error message on startup
2. Provide instructions to get an OpenRouter key
3. Prevent the application from starting (fail-fast)

```python
ValueError: OPENROUTER_API_KEY not set in environment.
Please add OPENROUTER_API_KEY to your .env file.
Get your key at: https://openrouter.ai/keys
```

## Testing

### 1. Verify Configuration

```bash
cd backend
python -c "from src.config import settings; print(f'Model: {settings.OPENROUTER_MODEL}')"
```

Expected output:
```
Model: openai/gpt-4
```

### 2. Test AI Agent

```bash
cd backend
python -c "from src.ai.agent import get_agent; agent = get_agent(); print('Agent initialized successfully')"
```

Expected output:
```
AI Agent initialized with OpenRouter
Model: openai/gpt-4
Base URL: https://openrouter.ai/api/v1
Agent initialized successfully
```

### 3. Test Chat Endpoint

Start the backend:
```bash
cd backend
python -m uvicorn src.main:app --reload --port 8000
```

Send a test request:
```bash
curl -X POST http://localhost:8000/api/{user_id}/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {your_token}" \
  -d '{"message": "Create a task to test OpenRouter integration"}'
```

## Cost Comparison

OpenRouter pricing is typically competitive or better than direct API access:

| Model | OpenRouter | Direct API |
|-------|-----------|------------|
| GPT-4 | $0.03/1K tokens | $0.03/1K tokens |
| GPT-3.5 Turbo | $0.0015/1K tokens | $0.0015/1K tokens |
| Claude 3 Opus | $0.015/1K tokens | $0.015/1K tokens |
| Claude 3 Haiku | $0.00025/1K tokens | $0.00025/1K tokens |

**Benefits:**
- Single API key for all models
- No need for multiple provider accounts
- Unified billing
- Easy model switching

## Benefits of OpenRouter

### 1. Multi-Provider Access
Switch between OpenAI, Anthropic, Google, Meta without code changes:
```bash
# Just change the model in .env
OPENROUTER_MODEL=anthropic/claude-3-opus
```

### 2. Cost Optimization
Test with cheaper models, deploy with premium:
```bash
# Development
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Production
OPENROUTER_MODEL=openai/gpt-4
```

### 3. Fallback Options
If one provider has issues, switch to another instantly.

### 4. No Vendor Lock-in
Not tied to a single LLM provider.

### 5. Unified Billing
One invoice for all LLM usage across providers.

## Troubleshooting

### Error: "OPENROUTER_API_KEY not set"

**Solution:** Add your API key to `backend/.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Error: "Invalid API key"

**Solution:**
1. Verify your key at [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Ensure the key starts with `sk-or-v1-`
3. Check for extra spaces or quotes in .env file

### Error: "Model not found"

**Solution:**
1. Check model name format: `provider/model-name`
2. Verify model exists: [https://openrouter.ai/models](https://openrouter.ai/models)
3. Common mistake: `gpt-4` should be `openai/gpt-4`

### Slow Responses

**Solution:**
1. Try a faster model: `openai/gpt-3.5-turbo` or `anthropic/claude-3-haiku`
2. Check OpenRouter status: [https://status.openrouter.ai](https://status.openrouter.ai)
3. Consider geographic latency

## Migration Checklist

- [x] Update config.py with OpenRouter settings
- [x] Update AI agent to use OpenRouter
- [x] Update .env with OpenRouter API key
- [x] Update .env.example template
- [ ] Get OpenRouter API key from https://openrouter.ai/keys
- [ ] Add API key to backend/.env
- [ ] Choose model (default: openai/gpt-4)
- [ ] Test backend startup
- [ ] Test chat endpoint
- [ ] Verify task creation works

## Security Notes

### API Key Security

1. **Never commit .env files** - Already in .gitignore
2. **Use environment variables in production** - Not hardcoded
3. **Rotate keys regularly** - OpenRouter allows multiple keys
4. **Monitor usage** - Check OpenRouter dashboard

### Rate Limiting

Current configuration:
```bash
CHAT_RATE_LIMIT=60  # 60 requests per minute per user
```

Adjust based on your OpenRouter plan and expected usage.

## Support

- **OpenRouter Documentation:** [https://openrouter.ai/docs](https://openrouter.ai/docs)
- **OpenRouter Discord:** [https://discord.gg/openrouter](https://discord.gg/openrouter)
- **Model Pricing:** [https://openrouter.ai/models](https://openrouter.ai/models)
- **API Status:** [https://status.openrouter.ai](https://status.openrouter.ai)

## Rollback (If Needed)

To revert to direct OpenAI API:

1. Update `backend/src/config.py`:
   ```python
   OPENAI_API_KEY: Optional[str] = None
   OPENAI_MODEL: str = "gpt-4"
   ```

2. Update `backend/src/ai/agent.py`:
   ```python
   self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
   ```

3. Update `backend/.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4
   ```

---

**Status:** OpenRouter integration complete and ready for testing.
**Next Step:** Get your API key and configure backend/.env
