---
title: VedaBot Chatbot
emoji: "🌿"
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: "1.32.0"
python_version: "3.10"
app_file: app.py
pinned: false
---

# VedaBot - Your Personalized Ayurveda Advisor

VedaBot is an intelligent Ayurveda Advisor chatbot designed to assist users with Ayurvedic solutions, remedies, and general health-related queries. Powered by retrieval and LLM inference, it provides context-aware responses.

## Features

- Context-aware conversations with per-user history
- Ayurveda-focused response style and precautions
- FAISS-based retrieval for relevant context
- Streamlit interface for web embedding

## Local Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Add environment variable in `.env`:

```env
HUGGINGFACEHUB_ACCESS_TOKEN="your_token_here"
```

5. Run:

```bash
streamlit run app.py
```

## Notes

- This app intentionally expects `?userId=<id>` in the URL query params.
- On Hugging Face Spaces, set `HUGGINGFACEHUB_ACCESS_TOKEN` in **Settings -> Variables and secrets**.
