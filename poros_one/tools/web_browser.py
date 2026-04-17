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

    @staticmethod
    def interact_with_webpage(url: str, action_type: str, selector: str, input_text: str = None) -> str:
        """
        Berinteraksi dengan elemen web secara aktif (click/fill) lalu mengekstrak isi halaman/hasil. (Level 2)

        Args:
            url: URL tujuan.
            action_type: 'click' atau 'fill'.
            selector: CSS atau XPath selector elemen.
            input_text: Teks untuk diketikkan (jika action_type='fill').
        """
        try:
            ActionGateway.check_action("interact_web", f"Aksi '{action_type}' pada {url} selector '{selector}'")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)

                # Tunggu elemen muncul maksimal 5 detik
                page.wait_for_selector(selector, timeout=5000)

                if action_type == "click":
                    page.locator(selector).click()
                elif action_type == "fill":
                    if not input_text:
                        raise ValueError("input_text dibutuhkan untuk aksi 'fill'.")
                    page.locator(selector).fill(input_text)
                else:
                    raise ValueError(f"action_type tidak valid: {action_type}")

                # Tunggu network idle setelah interaksi
                page.wait_for_load_state("networkidle", timeout=5000)

                # Ekstrak seluruh konten HTML agar agen bisa melihat selector yang tersedia
                # (Akan di-parse atau digunakan oleh LLM untuk mencari selector)
                result_html = page.content()
                # Batasi output dengan membuang skrip dan stylesheet, fokus ke body.
                import re
                clean_html = re.sub(r"<(script|style).*?>.*?</\1>", "", result_html, flags=re.DOTALL)
                clean_html = re.sub(r"\\s+", " ", clean_html).strip()
                # Berikan cuplikan HTML yang cukup untuk elemen interaktif selanjutnya
                result_snippet = clean_html[:1500] + "... (terpotong)" if len(clean_html) > 1500 else clean_html

                browser.close()
                return f"Interaksi berhasil. Cuplikan DOM halaman saat ini:\\n{result_snippet}"

        except Exception as e:
            return f"Error saat interaksi web: {e}"