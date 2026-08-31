import time
import requests
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from backend.adapters.base import BaseAdapter


class SearchAdapter(BaseAdapter):
    """Real Search & Web Research Adapter using DuckDuckGo Search and Web Scraper."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=api_key, config=config)

    def authenticate(self) -> bool:
        # DuckDuckGo search is public/free, always available
        return True

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        query = input_data.get("query") or input_data.get("topic")
        return bool(query and isinstance(query, str))

    def estimate_cost(self, input_data: Dict[str, Any]) -> float:
        return 0.0  # Free search integration

    def estimate_time(self, input_data: Dict[str, Any]) -> int:
        return 2500  # ~2.5s for web search + extraction

    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        return bool(output_data and output_data.get("results"))

    def execute(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {
                "success": False,
                "output": None,
                "execution_time_ms": 0,
                "estimated_cost": 0.0,
                "error": "Invalid search query input."
            }

        query = input_data.get("query") or input_data.get("topic")
        max_results = input_data.get("max_results", 5)
        scrape_webpages = input_data.get("scrape_webpages", True)

        start_time = time.time()

        try:
            results = []
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
                for item in ddg_results:
                    results.append({
                        "title": item.get("title"),
                        "snippet": item.get("body"),
                        "url": item.get("href")
                    })

            detailed_facts = []
            # Scrape content from top result if requested
            if scrape_webpages and results:
                top_url = results[0]["url"]
                try:
                    res = requests.get(top_url, headers={"User-Agent": "LiteMind-ResearchBot/1.0"}, timeout=5)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 40]
                        web_text = " ".join(paragraphs[:8])
                        detailed_facts.append({"url": top_url, "extracted_text": web_text[:2000]})
                except Exception:
                    pass  # Non-fatal if specific scrape fails

            elapsed_ms = int((time.time() - start_time) * 1000)

            summary_content = f"Search Query: {query}\nFound {len(results)} source results.\n\n"
            for idx, r in enumerate(results, 1):
                summary_content += f"{idx}. {r['title']}\n   URL: {r['url']}\n   Snippet: {r['snippet']}\n\n"

            return {
                "success": True,
                "output": {
                    "content": summary_content,
                    "results": results,
                    "detailed_facts": detailed_facts
                },
                "execution_time_ms": elapsed_ms,
                "estimated_cost": 0.0,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "output": None,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "estimated_cost": 0.0,
                "error": f"Search execution failed: {str(e)}"
            }
