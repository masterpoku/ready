import os
import subprocess
import time
import requests
import random

# ================= KONFIGURASI =================
OPENVPN_PATH = r"C:\Program Files\OpenVPN\bin\openvpn.exe"
FOLDER_VPN = "cinta"
FILE_PASS = os.path.join(FOLDER_VPN, "pass.txt")
FILE_USED_IP = "used_ip.txt"
INTERVAL_DETIK = 30 * 60  # 30 menit
# ===============================================

def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def get_current_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=8).text.strip()
    except:
        return "Koneksi Bermasalah"

def kill_ovpn():
    subprocess.run(["taskkill", "/f", "/im", "openvpn.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def clear_used_ip():
    """Menghapus isi file used_ip.txt saat program mulai"""
    with open(FILE_USED_IP, "w") as f:
        f.truncate()
    print("🧹 File used_ip.txt telah dibersihkan.")

def load_used_ips():
    if not os.path.exists(FILE_USED_IP):
        return set()
    with open(FILE_USED_IP, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_used_ip(ip):
    with open(FILE_USED_IP, "a") as f:
        f.write(ip + "\n")

def connect_random_vpn():
    used_ips = load_used_ips()
    ovpn_files = [f for f in os.listdir(FOLDER_VPN) if f.endswith('.ovpn')]
    
    if not ovpn_files:
        print("❌ Folder .ovpn kosong!")
        return False

    random.shuffle(ovpn_files)

    for selected in ovpn_files:
        config_path = os.path.join(FOLDER_VPN, selected)
        print(f"\n🔄 Mencoba koneksi: {selected}")
        kill_ovpn()
        time.sleep(3)

        command = [
            OPENVPN_PATH, "--config", config_path,
            "--auth-user-pass", FILE_PASS,
            "--redirect-gateway", "def1",
            "--route-delay", "5", "--verb", "1"
        ]

        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print("⏳ Menunggu koneksi (12 detik)...")
        time.sleep(12)

        current_ip = get_current_ip()
        print(f"📍 IP Saat ini: {current_ip}")

        if current_ip not in used_ips and "Koneksi" not in current_ip and current_ip != "":
            print("✅ IP Baru didapat dan disimpan.")
            save_used_ip(current_ip)
            return True
        else:
            print("⚠️ IP duplikat atau koneksi gagal, mencoba config lain...")

    print("❌ Semua config sudah terpakai.")
    return False

def main():
    if not is_admin():
        print("❌ Jalankan sebagai ADMINISTRATOR!")
        return

    print("🚀 BOT AUTO ROTATE IP AKTIF (Interval 30 Menit)")
    
    # 1. Clear file saat awal running
    clear_used_ip()

    # 2. Koneksi awal
    connect_random_vpn()

    last_rotation_time = time.time()

    try:
        while True:
            # Hitung selisih waktu
            current_time = time.time()
            if current_time - last_rotation_time >= INTERVAL_DETIK:
                print("\n🔔 Waktu 30 menit tercapai. Memulai rotasi otomatis...")
                if connect_random_vpn():
                    last_rotation_time = time.time()
            
            time.sleep(10) # Cek setiap 10 detik

    except KeyboardInterrupt:
        print("\n🛑 Memutus koneksi...")
        kill_ovpn()

if __name__ == "__main__":
    main()
