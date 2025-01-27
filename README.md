# Executive Orders Bot

A bot that fetches and summarizes executive orders and important government announcements using the Federal Register API. The bot uses langraph for orchestration and implements a RAG (Retrieval Augmented Generation) approach for generating summaries.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the bot:
```bash
python main.py
```

## Features

- Fetches executive orders from the Federal Register API
- Stores documents in a vector database (ChromaDB)
- Generates summaries using OpenAI's GPT models
- Uses langraph for workflow orchestration 