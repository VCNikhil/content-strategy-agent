# Content Strategy Agent (Hindsight)

An agent that remembers every piece of content a team publishes, with its topic, voice
and performance, and uses Hindsight memory to find coverage gaps, track brand voice
evolution and recommend what to publish next.

## Why memory matters
A stateless LLM can't tell you that tutorials beat opinion pieces, or that your voice
shifted from formal to casual in August. Hindsight retains each post, consolidates
observations over time, and `reflect` reasons across the whole history.

## Setup
```bash
pip install -r requirements.txt

# Option A: Docker server
export OPENAI_API_KEY=sk-xxx
docker run -d --name hindsight -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -v hindsight-data:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest

# Option B: embedded (no Docker)
pip install hindsight-all
export USE_EMBEDDED=1 OPENAI_API_KEY=sk-xxx

streamlit run app.py
```

## Demo script (2 minutes)
1. Click **Load 18 past posts**.
2. Tab **Coverage gaps**: the agent notes security, pricing and case studies are missing.
3. Tab **Brand voice evolution**: formal in Jun-Jul, casual and punchy by Sep-Oct.
4. In the sidebar, publish the security post (9.8k views).
5. Re-run **Coverage gaps** and **What to publish next**. The answers change because the
   agent learned security content performs well.

## Hindsight operations used
- `retain` with `context` and `timestamp` for every post
- `recall` for factual questions
- `reflect` for gap analysis, voice evolution and recommendations

## Stack
Python, Streamlit, Hindsight (hindsight-client / hindsight-all)
