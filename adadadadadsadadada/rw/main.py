import logging
import os
import argparse

from cache import LRUCache
from ui import ConsoleUI
from wikipedia_client import WikipediaClient
from gui import WikipediaGUI


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    log_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    root = logging.getLogger()
    root.addHandler(file_handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Wikipedia console app")
    parser.add_argument("--demo-random", action="store_true", help="Run non-interactive: fetch one random article and exit")
    parser.add_argument("--lang", type=str, default=None, help="Language code, e.g., en, ru, de")
    parser.add_argument("--max-chars", type=int, default=None, help="Limit content by characters in demo mode")
    parser.add_argument("--max-paragraphs", type=int, default=None, help="Limit content by paragraphs in demo mode")
    parser.add_argument("--search", type=str, default=None, help="Non-interactive search query")
    parser.add_argument("--result-index", type=int, default=1, help="Which search result to open (1-based)")
    parser.add_argument("--gui", action="store_true", help="Launch Tkinter GUI")
    args = parser.parse_args()

    setup_logging()
    client = WikipediaClient(language_code=args.lang or "en")
    cache = LRUCache(capacity=20)

    if args.gui:
        app = WikipediaGUI(client, cache)
        app.mainloop()
        return

    if args.demo_random:
        try:
            print("Fetching random article...")
            page = client.get_random_page()
            print(f"Title: {page.title}")
            print(f"URL: {page.url}")
            print("\nSummary:")
            print(page.summary or "(no summary)")
            if page.content:
                limited = WikipediaClient.limit_text(page.content, max_chars=args.max_chars, max_paragraphs=args.max_paragraphs)
                if limited:
                    print("\nContent:")
                    print(limited)
        except Exception as e:
            logging.getLogger(__name__).exception("Demo mode failed")
            print(f"Demo failed: {e}")
        return

    if args.search:
        try:
            print(f"Searching for: {args.search}")
            results = client.search(args.search, max_results=20)
            if not results:
                print("No results found.")
                return
            for idx, title in enumerate(results, start=1):
                print(f"{idx}. {title}")
            pick = args.result_index if args.result_index and args.result_index > 0 else 1
            if pick > len(results):
                pick = len(results)
            title = results[pick - 1]
            print(f"\nOpening result #{pick}: {title}")
            page = client.get_page(title)
            print(f"Title: {page.title}")
            print(f"URL: {page.url}")
            print("\nSummary:")
            print(page.summary or "(no summary)")
            if page.content:
                limited = WikipediaClient.limit_text(page.content, max_chars=args.max_chars, max_paragraphs=args.max_paragraphs)
                if limited:
                    print("\nContent:")
                    print(limited)
        except Exception as e:
            logging.getLogger(__name__).exception("Search demo failed")
            print(f"Search demo failed: {e}")
        return

    ui = ConsoleUI(client, cache)
    ui.run()


if __name__ == "__main__":
    main()


