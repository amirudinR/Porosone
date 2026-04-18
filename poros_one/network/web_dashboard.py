import os
import json
import uvicorn
import asyncio
import webbrowser
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from threading import Thread

# Import Core Agent
from poros_one.core.agent_loop import PorosAgent
from poros_one.memory.soul_manager import SoulManager

class WebDashboardServer:
    """
    Localhost Web Server untuk mengontrol Poros One via Browser UI.
    Menghubungkan FastAPI WebSocket dengan backend sinkron PorosAgent.
    """

    def __init__(self, agent: PorosAgent):
        self.app = FastAPI(title="Poros One Local Dashboard")
        self.agent = agent

        # Simpan referensi ke koneksi WS aktif
        self.active_websocket: WebSocket = None

        # Event lock sinkron untuk menjembatani FastAPI (Async) dan Agent Loop (Sync)
        # Khusus untuk sistem persetujuan Human-in-the-Loop
        self.hitl_event = None
        self.hitl_response_status = None
        self.main_loop = None

        # Mount static directory for JS and CSS
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        web_dir = os.path.join(base_dir, "web")
        self.app.mount("/static", StaticFiles(directory=web_dir), name="static")

        self._setup_routes()

    def _setup_routes(self):

        @self.app.get("/", response_class=HTMLResponse)
        async def get_index():
            """Melayani UI utama dari index.html"""
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            index_path = os.path.join(base_dir, "web", "index.html")

            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>Error 404</h1><p>File web/index.html tidak ditemukan.</p>"

        @self.app.websocket("/ws/chat")
        async def websocket_endpoint(websocket: WebSocket):
            """Menerima dan memproses pesan dari UI Chat"""
            await websocket.accept()
            self.active_websocket = websocket

            # Ambil event loop aktif agar thread sinkron bisa mengirim request kembali ke Async context
            self.main_loop = asyncio.get_running_loop()
            if self.hitl_event is None:
                self.hitl_event = asyncio.Event()

            print("\\n[WEB] Klien terhubung ke Dashboard.")

            try:
                while True:
                    data = await websocket.receive_text()
                    payload = json.loads(data)
                    msg_type = payload.get("type")

                    if msg_type == "user_prompt":
                        # Jika user mengirimkan prompt, jalankan loop ReAct di background
                        user_message = payload.get("message")

                        # Kirim status system
                        await self._send_ws({"type": "system", "message": f"Menjalankan Tugas: {user_message}"})

                        # Eksekusi agen dalam thread terpisah agar tidak memblokir event loop WebSocket
                        Thread(target=self._run_agent_task_sync, args=(user_message,)).start()

                    elif msg_type == "hitl_response":
                        # User merespon popup otorisasi (Y/N)
                        self.hitl_response_status = payload.get("status") # "approved" atau "rejected"
                        # Lepaskan lock yang menunggu di Agent Loop
                        if self.hitl_event:
                            self.hitl_event.set()

            except WebSocketDisconnect:
                print("\\n[WEB] Klien terputus dari Dashboard.")
                self.active_websocket = None
            except Exception as e:
                print(f"\\n[WEB ERROR] WebSocket bermasalah: {e}")
                self.active_websocket = None

    def _run_agent_task_sync(self, prompt: str):
        """Membungkus Agent.run_task ke dalam lingkungan sinkron untuk dipanggil oleh Thread"""
        try:
            self.agent.run_task(prompt)
            # Beritahu UI jika tugas selesai
            self._send_ws_sync({"type": "system", "message": "Tugas Selesai"})
        except Exception as e:
            self._send_ws_sync({"type": "agent_message", "message": f"Terjadi kesalahan fatal: {str(e)}"})

    async def _send_ws(self, payload: dict):
        """Mengirim payload JSON ke WebSocket yang aktif (Async)"""
        if self.active_websocket:
            try:
                await self.active_websocket.send_text(json.dumps(payload))
            except Exception as e:
                print(f"[WEB] Gagal mengirim pesan ke WS: {e}")

    def _send_ws_sync(self, payload: dict):
        """Membantu mengirim WS dari thread sinkron (Agent Loop) ke event loop Async"""
        if self.main_loop and self.main_loop.is_running():
            asyncio.run_coroutine_threadsafe(self._send_ws(payload), self.main_loop)

    def trigger_hitl_approval_sync(self, action_name: str, action_details: str) -> bool:
        """
        Didaftarkan sebagai callback ke ActionGateway.
        Menghentikan eksekusi agen, memunculkan popup di UI, lalu menunggu balasan.
        Berjalan secara sinkron memblokir thread Agen.
        """
        if not self.main_loop or not self.hitl_event:
            return False

        # 1. Reset event lock dengan me-lempar task ke event loop utama untuk menghindari RuntimeError "Event loop is closed"
        def clear_event():
            self.hitl_event.clear()

        # Panggil clear_event di dalam event loop utama
        self.main_loop.call_soon_threadsafe(clear_event)
        self.hitl_response_status = None

        # 2. Kirim pesan HitL ke UI
        msg = f"Menunggu otorisasi untuk: {action_name}\\nDetail: {action_details}"
        self._send_ws_sync({"type": "hitl_request", "message": msg})

        # 3. Tunggu hingga user mengklik Y/N di UI
        # Karena kita berada di worker thread, kita minta event loop utama untuk memantau asyncio.Event
        # dan memblokir worker thread secara aman lewat future.result()
        future = asyncio.run_coroutine_threadsafe(self.hitl_event.wait(), self.main_loop)
        try:
            future.result() # Memblokir thread agen (sinkron) sampai future terpenuhi (UI merespon)
        except Exception:
            return False

        # 4. Cek hasil
        if self.hitl_response_status == "approved":
            return True
        return False

    def stream_log_sync(self, text: str):
        """Meneruskan pesan log (Thought/Action) ke UI Web."""
        self._send_ws_sync({"type": "agent_log", "message": text})

    def start(self, port: int = 8000):
        """Menjalankan Uvicorn Server dan membuka browser secara otomatis"""
        print(f"\\n==================================================")
        print(f"   POROS ONE WEB DASHBOARD AKTIF di Port {port}")
        print(f"   Akses di: http://localhost:{port}")
        print(f"==================================================\\n")

        # Buka peramban OS default
        webbrowser.open(f"http://localhost:{port}")

        # Jalankan server FastAPI
        uvicorn.run(self.app, host="127.0.0.1", port=port, log_level="error")