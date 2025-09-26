import logging
import random
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import wikipedia
from wikipedia.exceptions import DisambiguationError, PageError, HTTPTimeoutError, RedirectError, WikipediaException


logger = logging.getLogger(__name__)


@dataclass
class WikiPage:
    title: str
    summary: str
    url: str
    content: Optional[str] = None


class WikipediaClient:
    def __init__(self, language_code: str = "en", request_timeout_seconds: int = 10, max_retries: int = 3, retry_backoff_seconds: float = 0.5):
        self.language_code = language_code
        self.request_timeout_seconds = request_timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        wikipedia.set_lang(self.language_code)
        wikipedia.set_rate_limiting(True)

    def set_language(self, language_code: str) -> None:
        self.language_code = language_code
        wikipedia.set_lang(language_code)
        logger.info("Language set to %s", language_code)

    def _with_retries(self, fn, *args, **kwargs):
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except (HTTPTimeoutError, WikipediaException) as exc:  # network or API errors
                last_exc = exc
                sleep_for = self.retry_backoff_seconds * (2 ** (attempt - 1)) + random.uniform(0, 0.2)
                logger.warning("Attempt %d/%d failed: %s. Retrying in %.2fs", attempt, self.max_retries, exc, sleep_for)
                time.sleep(sleep_for)
        assert last_exc is not None
        raise last_exc

    def get_random_page(self) -> WikiPage:
        def _get():
            title = wikipedia.random(1)
            if isinstance(title, list):
                title = title[0]
            # Disable preload to avoid triggering buggy references/extlinks fetch
            page = wikipedia.page(title, auto_suggest=False, preload=False, redirect=True)
            return page

        try:
            page = self._with_retries(_get)
        except DisambiguationError as e:
            # Pick the first option deterministically for simplicity
            option = e.options[0] if e.options else None
            if option is None:
                raise
            logger.info("Disambiguation encountered for '%s', selecting '%s'", e.title, option)
            page = self._with_retries(lambda: wikipedia.page(option, auto_suggest=False, preload=False, redirect=True))
        except (PageError, RedirectError) as e:
            logger.error("Random page retrieval failed: %s", e)
            raise

        return WikiPage(title=page.title, summary=page.summary, url=page.url, content=page.content)

    def search(self, query: str, max_results: int = 10) -> List[str]:
        results = self._with_retries(lambda: wikipedia.search(query, results=max_results, suggestion=False))
        return results

    def get_page(self, title: str) -> WikiPage:
        def _get():
            # Disable preload to avoid triggering buggy references/extlinks fetch
            return wikipedia.page(title, auto_suggest=False, preload=False, redirect=True)

        try:
            page = self._with_retries(_get)
        except DisambiguationError as e:
            option = e.options[0] if e.options else None
            if option is None:
                raise
            logger.info("Disambiguation encountered for '%s', selecting '%s'", e.title, option)
            page = self._with_retries(lambda: wikipedia.page(option, auto_suggest=False, preload=False, redirect=True))
        except (PageError, RedirectError) as e:
            logger.error("Fetching page '%s' failed: %s", title, e)
            raise

        return WikiPage(title=page.title, summary=page.summary, url=page.url, content=page.content)

    @staticmethod
    def limit_text(text: str, max_chars: Optional[int] = None, max_paragraphs: Optional[int] = None) -> str:
        if text is None:
            return ""
        limited = text
        if max_paragraphs is not None and max_paragraphs > 0:
            paragraphs = [p for p in text.split('\n') if p.strip()]
            limited = '\n\n'.join(paragraphs[:max_paragraphs])
        if max_chars is not None and max_chars > 0 and len(limited) > max_chars:
            limited = limited[:max_chars].rstrip() + '…'
        return limited


