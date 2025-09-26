## Wikipedia Random and Search Console App

A Python 3 console application that uses the `wikipedia` library (Wikipedia API) to:

- Fetch random articles with title, summary, and URL
- Choose Wikipedia language (e.g., ru, en, de)
- View full article text with optional length limits
- Search articles by keywords and open a selected result
- Cache recently viewed articles for fast re-access
- Log requests and errors with robust error handling and retries

### Requirements

- Python 3.8+

### Installation

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Usage

Follow the on-screen menu to:

1. Get a random article
2. Search by keywords and select an article
3. View cached articles
4. Change language (default: `en`)
5. Exit

When viewing an article, you can choose to show the full content and optionally limit by characters or paragraphs.

### Configuration

- Logs are written to `logs/app.log` and also printed to the console.
- The cache holds the most recent 20 articles by default.

### Notes

- Uses the `wikipedia` library which wraps the Wikipedia API.
- Handles disambiguation, missing pages, invalid language codes, and network errors with retries.


