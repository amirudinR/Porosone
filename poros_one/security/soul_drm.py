import os
import uuid
import json
import zipfile
import shutil
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

def get_hardware_id() -> str:
    """
    Menghasilkan Hardware ID unik berdasarkan UUID node mesin lokal.
    (Bisa dikembangkan lebih lanjut membaca MAC address secara spesifik).
    """
    # Menggunakan node UUID (yang merepresentasikan MAC address dari network interface)
    return str(uuid.getnode())

def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Menurunkan kunci enkripsi AES-256 dari passphrase menggunakan PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32, # AES-256 membutuhkan kunci 32 bytes
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(passphrase.encode())

def encrypt_file(input_file: str, output_file: str, passphrase: str, hardware_id: str):
    """
    Mengenkripsi file zip dan menyisipkan metadata (termasuk hardware ID yang diizinkan) ke dalam header terenkripsi.
    """
    salt = os.urandom(16)
    iv = os.urandom(16)
    key = _derive_key(passphrase, salt)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Metadata untuk validasi (Hardware Binding)
    metadata = {
        "allowed_hardware_id": hardware_id
    }
    metadata_bytes = json.dumps(metadata).encode('utf-8')

    # Panjang metadata disimpan dalam 4 bytes pertama setelah plain data
    metadata_len = len(metadata_bytes).to_bytes(4, byteorder='big')

    with open(input_file, 'rb') as f:
        data = f.read()

    # Gabungkan metadata_len + metadata + raw zip data
    payload = metadata_len + metadata_bytes + data

    # Padding PKCS7
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(payload) + padder.finalize()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Format file keluaran: [Salt (16 bytes)] + [IV (16 bytes)] + [Encrypted Payload]
    with open(output_file, 'wb') as f:
        f.write(salt)
        f.write(iv)
        f.write(encrypted_data)

def decrypt_file(input_file: str, output_file: str, passphrase: str) -> str:
    """
    Mendekripsi file .poros dan memverifikasi Hardware ID.
    Mengembalikan Hardware ID yang diizinkan jika sukses, raise Exception jika gagal.
    """
    with open(input_file, 'rb') as f:
        salt = f.read(16)
        iv = f.read(16)
        encrypted_data = f.read()

    key = _derive_key(passphrase, salt)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    try:
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        payload = unpadder.update(padded_data) + unpadder.finalize()
    except Exception as e:
        raise ValueError("Passphrase salah atau file rusak (gagal dekripsi/unpad).")

    metadata_len = int.from_bytes(payload[:4], byteorder='big')
    metadata_bytes = payload[4:4+metadata_len]
    zip_data = payload[4+metadata_len:]

    try:
        metadata = json.loads(metadata_bytes.decode('utf-8'))
    except Exception as e:
        raise ValueError("Gagal membaca metadata dari file yang didekripsi.")

    # Verifikasi Hardware ID (Hardware Binding Anti-Maling)
    current_hw_id = get_hardware_id()
    allowed_hw_id = metadata.get("allowed_hardware_id")

    if current_hw_id != allowed_hw_id:
        raise PermissionError(f"AKSES DITOLAK: Hardware ID tidak cocok. (Allowed: {allowed_hw_id}, Current: {current_hw_id})")

    with open(output_file, 'wb') as f:
        f.write(zip_data)

    return allowed_hw_id

def export_soul(db_path: str, output_path: str, passphrase: str, target_hardware_id: Optional[str] = None):
    """
    Mengekspor "Nyawa" (direktori memori/ChromaDB dan config) ke file .poros terenkripsi.
    File .env akan diabaikan secara ketat.

    Args:
        db_path: Path menuju direktori penyimpanan nyawa.
        output_path: Path file .poros keluaran.
        passphrase: Kata sandi utama untuk AES-256.
        target_hardware_id: ID hardware yang diizinkan memuat nyawa ini. Jika None, gunakan ID mesin ini.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Direktori database tidak ditemukan: {db_path}")

    hw_id = target_hardware_id if target_hardware_id else get_hardware_id()
    temp_zip = f"{output_path}.temp.zip"

    try:
        # 1. Archive ke zip sementara, DILARANG KERAS memasukkan .env
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(db_path):
                for file in files:
                    if file == ".env" or file.endswith(".env"):
                        print(f"Skipping file kredensial: {file}")
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=db_path)
                    zipf.write(file_path, arcname)

        # 2. Enkripsi zip tersebut menjadi .poros dan sisipkan Hardware ID
        encrypt_file(temp_zip, output_path, passphrase, hw_id)
        print(f"Berhasil mengekspor nyawa ke: {output_path} (Bound to HW_ID: {hw_id})")

    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)

def import_soul(poros_file_path: str, extract_to_path: str, passphrase: str):
    """
    Memuat dan mengimpor file .poros ke dalam sistem.
    Mendekripsi, memverifikasi Hardware ID, lalu mengekstrak ke direktori target.

    Args:
        poros_file_path: Path file .poros yang akan diimpor.
        extract_to_path: Path direktori untuk menyimpan hasil ekstrak (ChromaDB).
        passphrase: Kata sandi utama.
    """
    if not os.path.exists(poros_file_path):
        raise FileNotFoundError(f"File nyawa tidak ditemukan: {poros_file_path}")

    temp_zip = f"{poros_file_path}.temp.zip"

    try:
        # 1. Dekripsi dan Verifikasi Hardware ID
        print("Mendekripsi dan memverifikasi Hardware ID...")
        decrypt_file(poros_file_path, temp_zip, passphrase)

        # 2. Bersihkan direktori tujuan jika ada
        if os.path.exists(extract_to_path):
            shutil.rmtree(extract_to_path)
        os.makedirs(extract_to_path, exist_ok=True)

        # 3. Ekstrak zip sementara ke direktori target
        with zipfile.ZipFile(temp_zip, 'r') as zipf:
            zipf.extractall(extract_to_path)

        print(f"Berhasil mengimpor nyawa ke: {extract_to_path}")

    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
