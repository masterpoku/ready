import os
import subprocess
import time
import requests
import sys
import random

# ================= KONFIGURASI =================
OPENVPN_PATH = r"C:\Program Files\OpenVPN\bin\openvpn.exe"
FOLDER_VPN = "OpenVPN256"
FILE_PASS = os.path.join(FOLDER_VPN, "pass.txt")
FILE_TRIGGER = "trigger.txt"
FILE_USED_IP = "used_ip.txt"
# ===============================================


# ================= SYSTEM =================
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
    subprocess.run(
        ["taskkill", "/f", "/im", "openvpn.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def reset_trigger():
    with open(FILE_TRIGGER, "w") as f:
        f.write("0")


def check_trigger():
    if not os.path.exists(FILE_TRIGGER):
        reset_trigger()
        return False

    with open(FILE_TRIGGER, "r") as f:
        return f.read().strip() == "1"


# ================= IP STORAGE =================
def load_used_ips():
    if not os.path.exists(FILE_USED_IP):
        return set()

    with open(FILE_USED_IP, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_used_ip(ip):
    with open(FILE_USED_IP, "a") as f:
        f.write(ip + "\n")


# ================= VPN ROTATION =================
def connect_random_vpn():
    used_ips = load_used_ips()

    ovpn_files = [f for f in os.listdir(FOLDER_VPN) if f.endswith('.ovpn')]
    if not ovpn_files:
        print("? Folder .ovpn kosong!")
        return False

    random.shuffle(ovpn_files)

    for selected in ovpn_files:
        config_path = os.path.join(FOLDER_VPN, selected)

        print(f"\n?? Coba Rotasi ke: {selected}")
        kill_ovpn()
        time.sleep(3)

        command = [
            OPENVPN_PATH,
            "--config", config_path,
            "--auth-user-pass", FILE_PASS,
            "--redirect-gateway", "def1",
            "--route-delay", "5",
            "--verb", "1"
        ]

        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )

        print("? Menunggu koneksi stabil (12 detik)...")
        time.sleep(12)

        current_ip = get_current_ip()
        print(f"?? IP Didapat: {current_ip}")

        if (
            current_ip not in used_ips
            and "Koneksi" not in current_ip
            and current_ip != ""
        ):
            print("? IP BARU! Disimpan & digunakan.")
            save_used_ip(current_ip)
            return True
        else:
            print("?? IP sudah pernah dipakai. Rotasi lagi...")

    print("? Semua config menghasilkan IP duplikat.")
    return False


# ================= MAIN =================
def main():
    if not is_admin():
        print("? Jalankan sebagai ADMINISTRATOR!")
        return

    print("??? BOT VPN TRIGGER AKTIF")
    print(f"Monitor file: {FILE_TRIGGER}")
    print("Isi 1 ? Rotasi IP")
    print("IP hanya dipakai 1x\n")

    reset_trigger()

    # Koneksi awal
    connect_random_vpn()

    try:
        while True:
            if check_trigger():
                print("\n?? Trigger terdeteksi! Rotasi dimulai...")
                reset_trigger()

                success = connect_random_vpn()
                if not success:
                    print("?? Tidak ada IP baru tersedia.")

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n?? Memutus koneksi...")
        kill_ovpn()


if __name__ == "__main__":
    main()
