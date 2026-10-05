# MarketMate Shopping Agent

A simple Streamlit shopping assistant powered by Groq and LangChain. Search the local product catalog, compare review ratings, find products from an uploaded image, and place an order after confirmation.

## Features

- Natural-language product search
- Maximum price and organic-product filters
- Product review ratings
- Image-based product search
- Explicit checkout confirmation
- Local SQLite catalog and order history
- Dark Streamlit chat interface

## Requirements

- Python 3.10+
- A Groq API key

## Setup

1. Clone the repository and open its folder:

   ```bash
   git clone <your-repository-url>
   cd shopping-agent-project
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install streamlit python-dotenv langchain langchain-core langchain-groq
   ```

4. Create your local environment file:

   ```bash
   copy .env.sample .env
   ```

   Replace `your_groq_api_key_here` in `.env` with your real Groq API key.

5. Start the app:

   ```bash
   streamlit run app.py
   ```

The included `store.db` file contains the product catalog, reviews, and order tables. Orders created through the app are saved to that local database.

## Image search

Use **Find products from an image** in the sidebar, upload a JPG, JPEG, PNG, or WEBP image, and select **Search this image**. The image is sent to the configured vision-capable Groq model for product identification before matching products are searched in SQLite.

## Project files

- `app.py` - Streamlit user interface
- `shopping_agent.py` - LangChain agent and shopping tools
- `reviews_api.py` - SQLite review aggregation helpers
- `store.db` - Local product and order database
- `.env.sample` - Safe environment variable template

