#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// Ambil argumen command line dari user (mengabaikan 'node' dan 'poros.js')
const args = process.argv.slice(2);

// Asumsikan struktur folder: <global_node_modules>/poros-one/bin/poros.js
// Kita perlu mencari root path project Python tempat modul 'poros_one' berada
const projectRoot = path.resolve(__dirname, '..');

// Eksekusi engine Python
// Gunakan 'python' secara spesifik agar cross-platform (khususnya untuk Windows)
// 'stdio: inherit' sangat penting agar input/output dari Python (termasuk HitL Y/N prompt)
// tidak terblokir dan langsung masuk ke terminal/CMD/PowerShell yang sedang aktif.
const pythonProcess = spawn('python', ['-m', 'poros_one.cli', ...args], {
    cwd: projectRoot,
    stdio: 'inherit',
    env: process.env // Turunkan environment variable agar token API .env tetap terbaca
});

// Tangani event penutupan
pythonProcess.on('close', (code) => {
    process.exit(code);
});

// Tangani error jika Python tidak terinstall
pythonProcess.on('error', (err) => {
    console.error(`\\n[ERROR] Gagal menjalankan Poros One Engine.`);
    console.error(`Pastikan Python 3 sudah terinstal dan ditambahkan ke PATH Windows/OS Anda.`);
    console.error(`Detail error: ${err.message}\\n`);
    process.exit(1);
});
