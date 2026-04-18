def build_react_prompt(user_prompt: str, memory_context: str, error_context: str = "") -> str:
    """Membangun prompt untuk siklus ReAct, termasuk konteks error jika ada."""

    reflection_block = ""
    if error_context:
        reflection_block = f"""
[PERINGATAN REFLEKSI]
Tindakan sebelumnya gagal dengan error:
{error_context}
Evaluasi kenapa ini terjadi, buat rencana perbaikan, dan coba eksekusi tindakan alternatif atau perbaiki parameter Anda.
"""

    prompt = f"""
Anda adalah Poros One, agen AI yang mandiri (The God Mode).
Ingatan relevan Anda:
{memory_context}

Tugas Pengguna: {user_prompt}
{reflection_block}

Pilih SATU tindakan yang paling sesuai dari daftar alat berikut:
1. read_file (details: filepath)
2. create_file (details: format json {{"filepath": "...", "content": "..."}})
3. delete_file (details: filepath)
4. search_text (details: query pencarian web pasif)
5. interact_web (details: format json {{"url": "...", "action_type": "click/fill", "selector": "...", "input_text": "opsional"}})
6. run_code (details: kode python untuk dieksekusi di sandbox)
7. send_message (details: pesan teks telegram)
8. ask_user_help (details: pertanyaan atau permintaan bantuan ke pengguna)

Berikan output murni dalam format JSON:
{{"action": "nama_tindakan", "details": "detail_tindakan_sesuai_format"}}
"""
    return prompt
