"""Seed content calendar for a fictional dev-tools startup, 'Acme'.

The data deliberately tells a story so the agent has something to learn:
  - Tutorials on vector search/RAG consistently outperform everything else.
  - Brand voice drifts from formal (Jun-Jul) to casual and punchy (Sep-Oct).
  - Nothing has been published on security, pricing/cost, or case studies (gaps).
  - LinkedIn opinion pieces underperform; short videos perform well.
"""

# (date, format, title, topic, voice, views, shares)
POSTS = [
    ("2026-06-02", "blog", "Introduction to Vector Databases", "vector search", "formal, technical", 2100, 40),
    ("2026-06-16", "blog", "Enterprise Guidelines for Data Governance", "governance", "formal, corporate", 600, 6),
    ("2026-06-30", "linkedin", "Announcing Our Platform Architecture", "product news", "formal, corporate", 450, 5),
    ("2026-07-07", "blog", "A Formal Overview of RAG Pipelines", "RAG", "formal, technical", 2600, 55),
    ("2026-07-21", "whitepaper", "Operational Excellence in AI Deployment", "operations", "formal, corporate", 300, 3),
    ("2026-08-04", "blog", "Build a RAG Chatbot in 30 Minutes", "RAG", "friendly, tutorial", 5200, 140),
    ("2026-08-11", "video", "60-Second Vector Search Explainer", "vector search", "casual, punchy", 7800, 210),
    ("2026-08-18", "linkedin", "Why We Think AI Strategy Matters", "opinion", "formal, opinion", 380, 4),
    ("2026-08-25", "blog", "Hybrid Search: BM25 + Embeddings Step by Step", "vector search", "friendly, tutorial", 4800, 120),
    ("2026-09-01", "twitter", "Hot take: most RAG demos are toy demos", "RAG", "casual, punchy", 3100, 95),
    ("2026-09-08", "video", "RAG Mistakes in 90 Seconds", "RAG", "casual, punchy", 8400, 260),
    ("2026-09-15", "linkedin", "Why we left microservices", "opinion", "casual, opinionated", 700, 9),
    ("2026-09-22", "blog", "Chunking Strategies That Actually Work", "RAG", "casual, tutorial", 6100, 175),
    ("2026-09-29", "video", "Embeddings Explained With Pizza", "vector search", "casual, humorous", 9200, 300),
    ("2026-10-06", "twitter", "Thread: 5 evals every RAG app needs", "evaluation", "casual, punchy", 3600, 110),
    ("2026-10-13", "blog", "Reranking: The Cheapest Accuracy Win", "RAG", "casual, tutorial", 5900, 160),
    ("2026-10-20", "linkedin", "Our take on the future of agents", "opinion", "casual, opinionated", 650, 8),
    ("2026-10-27", "video", "Cross-Encoders in 2 Minutes", "RAG", "casual, punchy", 8800, 270),
]

# Posts we add live in the demo to show the agent updating its beliefs.
NEW_POST = (
    "2026-11-03", "blog", "Securing Your RAG Pipeline: Prompt Injection 101",
    "security", "casual, tutorial", 9800, 320,
)


def to_text(p):
    date, fmt, title, topic, voice, views, shares = p
    return (
        f"Published {fmt} '{title}' on {date}. Topic: {topic}. Brand voice: {voice}. "
        f"Performance: {views} views, {shares} shares."
    )
