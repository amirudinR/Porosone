import os
import requests
import uvicorn
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.responses import FileResponse
from datetime import datetime
from pydantic import BaseModel

from poros_one.security.soul_drm import import_soul, export_soul

class SoulSyncProtocol:
    """
    Protokol sinkronisasi nyawa antara Node PC dan Node Android.
    Menggunakan FastAPI untuk server lokal yang ringan.
    """

    def __init__(self, memory_dir: str = "./poros_memory"):
        self.memory_dir = memory_dir
        self.app = FastAPI(title="Poros One Sync Server")
        self.master_passphrase = None
        # Rute akan diatur saat start_sync_server agar passphrase bisa dikenali

    def _setup_routes(self):
        """Mendefinisikan endpoint REST API untuk sinkronisasi."""

        @self.app.post("/sync/push")
        async def receive_soul(
            file: UploadFile = File(...),
            x_passphrase: str = Header(..., description="Master Passphrase untuk otentikasi"),
            x_timestamp: str = Header(..., description="Timestamp file nyawa pengirim (ISO format)")
        ):
            """Menerima file .poros dari node lain dan melakukan pengecekan versi."""
            if not self.master_passphrase or x_passphrase != self.master_passphrase:
                raise HTTPException(status_code=401, detail="Otentikasi Gagal: Passphrase tidak valid.")

            temp_path = f"./temp_received_{datetime.now().strftime('%Y%m%d%H%M%S')}.poros"

            try:
                # Simpan file yang diupload
                with open(temp_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)

                # Logika Versioning Sederhana
                # Cek apakah memori lokal ada. Jika tidak, anggap waktu lokal adalah epoch 0.
                local_time = 0.0
                if os.path.exists(self.memory_dir):
                    # Kita gunakan waktu modifikasi direktori memory sbg versi lokal
                    local_time = os.path.getmtime(self.memory_dir)

                incoming_time = datetime.fromisoformat(x_timestamp).timestamp()

                if incoming_time > local_time:
                    print(f"\\n[SYNC] Memori baru terdeteksi! Memulai import...")
                    import_soul(temp_path, self.memory_dir, x_passphrase)
                    return {"status": "success", "message": "Memori berhasil disinkronkan dan diimpor."}
                else:
                    print(f"\\n[SYNC] Memori yang diterima lebih lama atau sama dengan memori lokal. Diabaikan.")
                    return {"status": "ignored", "message": "Memori lokal sudah yang terbaru."}

            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=401, detail="Passphrase salah atau file korup.")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Gagal memproses file: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        @self.app.get("/sync/pull")
        async def send_soul(
            x_passphrase: str = Header(..., description="Master Passphrase untuk otentikasi"),
            x_target_hwid: str = Header(None, description="Hardware ID node peminta untuk enkripsi DRM")
        ):
            """Mengekspor dan mengirimkan file .poros memori saat ini."""
            if not self.master_passphrase or x_passphrase != self.master_passphrase:
                raise HTTPException(status_code=401, detail="Otentikasi Gagal: Passphrase tidak valid.")

            export_path = f"./temp_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.poros"

            try:
                # Ekspor memori saat ini, re-enkripsi dengan target HWID peminta
                export_soul(self.memory_dir, export_path, x_passphrase, target_hardware_id=x_target_hwid)

                # Mengirim file sebagai response
                return FileResponse(
                    path=export_path,
                    filename="latest_soul.poros",
                    media_type="application/octet-stream"
                )
            except Exception as e:
                if os.path.exists(export_path):
                    os.remove(export_path)
                raise HTTPException(status_code=500, detail=str(e))

    def start_sync_server(self, port: int, master_passphrase: str, host: str = "0.0.0.0"):
        """Menjalankan server FastAPI menggunakan uvicorn dan mengkonfigurasi otentikasi."""
        self.master_passphrase = master_passphrase
        self._setup_routes()
        print(f"\\n[SYNC SERVER] Memulai server sinkronisasi di {host}:{port}...")
        uvicorn.run(self.app, host=host, port=port, log_level="error")

    @staticmethod
    def push_soul(target_ip: str, port: int, poros_filepath: str, master_passphrase: str):
        """Mengirim file .poros ke node lain (Sebagai Klien)."""
        url = f"http://{target_ip}:{port}/sync/push"

        if not os.path.exists(poros_filepath):
            print(f"Error: File {poros_filepath} tidak ditemukan.")
            return False

        # Ambil timestamp modifikasi file untuk versioning
        file_mtime = os.path.getmtime(poros_filepath)
        timestamp_iso = datetime.fromtimestamp(file_mtime).isoformat()

        headers = {
            "x-passphrase": master_passphrase,
            "x-timestamp": timestamp_iso
        }

        print(f"[SYNC CLIENT] Mendorong memori ke {url}...")
        try:
            with open(poros_filepath, 'rb') as f:
                files = {'file': ('soul.poros', f, 'application/octet-stream')}
                response = requests.post(url, headers=headers, files=files, timeout=30)

            if response.status_code == 200:
                print(f"Sukses: {response.json().get('message')}")
                return True
            else:
                print(f"Gagal mengirim. Status: {response.status_code}, Detail: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error koneksi jaringan: {e}")
            return False

    @staticmethod
    def pull_soul(target_ip: str, port: int, master_passphrase: str, save_path: str, target_hwid: str):
        """Mengunduh file .poros dari node lain (Sebagai Klien)."""
        url = f"http://{target_ip}:{port}/sync/pull"

        headers = {
            "x-passphrase": master_passphrase,
            "x-target-hwid": target_hwid
        }

        print(f"[SYNC CLIENT] Menarik memori dari {url}...")
        try:
            # Gunakan stream=True untuk file besar
            with requests.get(url, headers=headers, stream=True, timeout=30) as response:
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Sukses mengunduh memori ke {save_path}")
                    return True
                else:
                    print(f"Gagal mengunduh. Status: {response.status_code}, Detail: {response.text}")
                    return False

        except requests.exceptions.RequestException as e:
            print(f"Error koneksi jaringan: {e}")
            return False
