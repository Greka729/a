import logging
from typing import Optional

from wikipedia.exceptions import DisambiguationError, PageError, WikipediaException

from cache import LRUCache
from wikipedia_client import WikipediaClient


logger = logging.getLogger(__name__)


class ConsoleUI:
    def __init__(self, client: WikipediaClient, cache: LRUCache):
        self.client = client
        self.cache = cache

    def run(self) -> None:
        while True:
            self._print_menu()
            choice = input("Select an option: ").strip()
            if choice == "1":
                self._action_random()
            elif choice == "2":
                self._action_search()
            elif choice == "3":
                self._action_cached()
            elif choice == "4":
                self._action_language()
            elif choice == "5":
                print("Bye!")
                return
            else:
                print("Unknown option. Please try again.")

    def _print_menu(self) -> None:
        print("\n=== Wikipedia Console ===")
        print("1. Get random article")
        print("2. Search articles by keywords")
        print("3. View cached articles")
        print("4. Change language")
        print("5. Exit")

    def _display_article(self, title: str, summary: str, url: str, content: Optional[str]) -> None:
        print(f"\nTitle: {title}")
        print(f"URL: {url}")
        if summary:
            print("\nSummary:")
            print(summary)

        show_full = input("\nShow full article? (y/N): ").strip().lower() == "y"
        if show_full and content:
            limit_chars = self._ask_int("Limit by characters (empty to skip): ")
            limit_pars = self._ask_int("Limit by paragraphs (empty to skip): ")
            limited = WikipediaClient.limit_text(content, max_chars=limit_chars, max_paragraphs=limit_pars)
            print("\nContent:")
            print(limited)

    def _ask_int(self, prompt: str) -> Optional[int]:
        raw = input(prompt).strip()
        if not raw:
            return None
        try:
            v = int(raw)
            if v <= 0:
                return None
            return v
        except ValueError:
            print("Invalid number. Ignoring.")
            return None

    def _action_random(self) -> None:
        try:
            page = self.client.get_random_page()
            self.cache.put(page.title, (page.summary, page.url, page.content or ""))
            self._display_article(page.title, page.summary, page.url, page.content)
        except (PageError, DisambiguationError) as e:
            print(f"Page error: {e}")
        except WikipediaException as e:
            print(f"Wikipedia error: {e}")
        except Exception as e:
            logger.exception("Unexpected error while fetching random page")
            print(f"Unexpected error: {e}")

    def _action_search(self) -> None:
        query = input("Enter keywords: ").strip()
        if not query:
            print("Empty query.")
            return
        try:
            results = self.client.search(query, max_results=20)
            if not results:
                print("No results found.")
                return
            for idx, title in enumerate(results, start=1):
                print(f"{idx}. {title}")
            choice = self._ask_int("Select a result number (empty to cancel): ")
            if choice is None or choice < 1 or choice > len(results):
                print("Cancelled.")
                return
            title = results[choice - 1]
            page = self.client.get_page(title)
            self.cache.put(page.title, (page.summary, page.url, page.content or ""))
            self._display_article(page.title, page.summary, page.url, page.content)
        except (PageError, DisambiguationError) as e:
            print(f"Page error: {e}")
        except WikipediaException as e:
            print(f"Wikipedia error: {e}")
        except Exception as e:
            logger.exception("Unexpected error during search")
            print(f"Unexpected error: {e}")

    def _action_cached(self) -> None:
        keys = self.cache.keys()
        if not keys:
            print("Cache is empty.")
            return
        for idx, title in enumerate(keys, start=1):
            print(f"{idx}. {title}")
        choice = self._ask_int("Select an article number (empty to cancel): ")
        if choice is None or choice < 1 or choice > len(keys):
            print("Cancelled.")
            return
        title = keys[choice - 1]
        summary, url, content = self.cache.get(title) or ("", "", "")
        self._display_article(title, summary, url, content)

    def _action_language(self) -> None:
        code = input("Enter language code (e.g., en, ru, de): ").strip()
        if not code:
            print("Language unchanged.")
            return
        try:
            self.client.set_language(code)
            print(f"Language set to '{code}'.")
        except Exception as e:
            print(f"Failed to set language: {e}")


