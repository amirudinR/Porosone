from playwright.sync_api import sync_playwright
from poros_one.security.hitl_gateway import ActionGateway

class WebBrowser:
    """
    Tool untuk mengakses internet secara headless.
    """

    @staticmethod
    def search_and_summarize(query: str) -> str:
        """
        Mencari informasi di web dan mengambil ringkasan teks dasar (Level 1).
        """
        try:
            ActionGateway.check_action("search_text", f"Mencari web untuk query: {query}")

            with sync_playwright() as p:
                # Menggunakan chromium dengan mode headless
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Menggunakan DuckDuckGo untuk pencarian sederhana tanpa blokir agresif
                search_url = f"https://html.duckduckgo.com/html/?q={query}"
                page.goto(search_url)

                # Mengambil cuplikan teks hasil pencarian (snippet)
                # DuckDuckGo HTML layout menggunakan class 'result__snippet'
                snippets = page.locator('.result__snippet').all_inner_texts()

                browser.close()

                if snippets:
                    # Menggabungkan 3 hasil teratas
                    summary = "\\n".join(snippets[:3])
                    return f"Hasil Pencarian untuk '{query}':\\n{summary}"
                else:
                    return f"Tidak ditemukan hasil yang jelas untuk '{query}'."

        except Exception as e:
            return f"Gagal melakukan pencarian web: {e}"