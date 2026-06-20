import gspread
import ssl
import concurrent.futures
import sys
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
ssl._create_default_https_context = ssl._create_unverified_context
_original_del = uc.Chrome.__del__
def _patched_del(self):
    try:
        _original_del(self)
    except OSError as e:
        if e.winerror == 6:
            pass
        else:
            raise
uc.Chrome.__del__ = _patched_del
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException
from typing import List
import os
import csv
import subprocess
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import random
import platform


def get_chrome_version():
    if platform.system() == "Windows":
        commands = [
            r'powershell -command "(Get-Item \'C:\Program Files\Google\Chrome\Application\chrome.exe\').VersionInfo.ProductVersion"',
            r'powershell -command "(Get-Item \'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe\').VersionInfo.ProductVersion"',
            r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
        ]
        for cmd in commands:
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
                match = re.search(r'(\d+)\.', output)
                if match:
                    return int(match.group(1))
            except:
                continue
        return 142
    else:
        commands = [
            ['google-chrome', '--version'],
            ['google-chrome-stable', '--version'],
            ['chromium', '--version']
        ]
        for cmd in commands:
            try:
                output = subprocess.check_output(cmd).decode('utf-8')
                version = re.search(r'(\d+)\.', output).group(1)
                return int(version)
            except:
                continue
        return 142


def safe_click(driver, element):
    try:
        element.click()
    except (ElementNotInteractableException, ElementClickInterceptedException):
        driver.execute_script("arguments[0].click();", element)


def type_slowly(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(0.03)


def profile_name_from_email(email):
    username = email.split('@')[0]
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', username)
    return f"profile_{safe}"


def dismiss_dialogs(driver):
    try:
        driver.execute_script("""
            document.querySelectorAll('div[role="dialog"], div[role="alertdialog"]').forEach(el => {
                el.querySelectorAll('button, span[role="button"]').forEach(b => {
                    let t = b.innerText.toLowerCase().trim();
                    if (t.includes('skip') || t.includes('no thanks') || t.includes('close') || t.includes('tutup')) {
                        try { b.click(); } catch(e) {}
                    }
                });
                el.remove();
            });
        """)
    except:
        pass


def clear_official_link_cookies(driver):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Membersihkan session official.link...")
        driver.get("https://official.link")
        time.sleep(1)
        cookies = driver.get_cookies()
        removed = 0
        for cookie in cookies:
            domain = cookie.get("domain", "")
            if "official.link" in domain:
                try:
                    driver.delete_cookie(cookie["name"])
                    removed += 1
                except:
                    pass
        driver.execute_script("""
            try {
                localStorage.clear();
                sessionStorage.clear();
            } catch(e){}
        """)
        print(f"[+] {removed} cookies official.link dihapus")
        driver.refresh()
        time.sleep(1)
        return True
    except Exception as e:
        print(f"[!] Error clear cookies: {e}")
        return False


def login_gmail_to_profile(driver, email, password):
    wait = WebDriverWait(driver, 10)
    try:
        driver.get("https://accounts.google.com/signin")
        time.sleep(2)
        dismiss_dialogs(driver)

        try:
            wait.until(EC.presence_of_element_located((
                By.XPATH, "//img[@alt='Google Account'] | //a[contains(@href, 'myaccount')]"
            )))
            print(f"[+] {email} sudah login (session profile dipakai).")
            return True
        except:
            pass

        print(f"{datetime.now().strftime('%H:%M:%S')} Login ke Gmail {email}...")
        email_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='email'] | //input[@name='identifier']")))
        email_input.clear()
        type_slowly(email_input, email)

        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(., 'Berikutnya')] | //span[contains(., 'Next')]")))
        safe_click(driver, next_btn)
        time.sleep(3)

        password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password'] | //input[@name='password']")))
        type_slowly(password_input, password)

        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(., 'Berikutnya')] | //span[contains(., 'Next')]")))
        safe_click(driver, next_btn)
        time.sleep(4)

        try:
            # 1. Cek & Klik Tombol `#confirm` (Jika ada)
            try:
                confirm_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#confirm"))
                )
                safe_click(driver, confirm_btn)
                print("[+] Tombol #confirm berhasil diklik")
                time.sleep(2)
            except:
                pass  # Lewati jika tidak muncul

            # 2. Cek & Klik Tombol "I understand" / "Saya mengerti" (Jika ada)
            try:
                # Menggunakan XPATH yang fleksibel untuk teks bahasa Inggris maupun Indonesia
                understand_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'understand')] | "
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mengerti')] | "
                        "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'understand')] | "
                        "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mengerti')]"
                    ))
                )
                safe_click(driver, understand_btn)
                print("[+] Tombol 'I understand / Mengerti' berhasil diklik")
                time.sleep(2)
            except:
                pass  # Lewati jika tidak muncul

            # 3. Verifikasi Akhir Login Berhasil
            wait.until(EC.presence_of_element_located((
                By.XPATH, "//img[@alt='Google Account'] | //a[contains(@href, 'myaccount')]"
            )))
            print(f"[+] Login {email} berhasil! Session tersimpan.")
            return True
            
        except Exception as e:
            print(f"[!] Login {email} gagal. Error: {e}")
            return False
    except Exception as e:
        print(f"[!] Error login Gmail: {e}")
        return False


def handle_ads_flow(driver):
    print(f"{datetime.now().strftime('%H:%M:%S')} Memeriksa banner cookie...")
    time.sleep(3)

    accept_cookies_js = """
    function acceptAllCookies() {
        let allElements = document.querySelectorAll('button, a, span, div[role="button"]');
        for (let el of allElements) {
            let text = el.innerText.toLowerCase().trim();
            if (text.includes('accept all') || text.includes('accept') ||
                text.includes('allow all') || text.includes('allow') ||
                text.includes('agree') || text.includes('consent') ||
                text.includes('i agree') || text.includes('got it') ||
                text.includes('accepter') || text.includes('aceitar') ||
                text.includes('aceptar') || text.includes('akzeptieren') ||
                text.includes('accetta') || text.includes('accepteer')) {
                try { el.click(); return true; } catch(e) {}
            }
        }
        return false;
    }
    return acceptAllCookies();
    """
    try:
        if driver.execute_script(accept_cookies_js):
            print("[+] Banner Cookie disetujui.")
            time.sleep(1)
    except Exception as e:
        print(f"[!] Gagal eksekusi cookie: {e}")


def request_reset(driver, email):
    url = "https://official.link/lost-password?redirect=dashboard"
    try:
        driver.get(url)
        time.sleep(2)
        handle_ads_flow(driver)

        print(f"{datetime.now().strftime('%H:%M:%S')} Request reset untuk: {email}")
        # Cari input email dengan beberapa fallback selector
        possible_selectors = [
            "#email",
            "input[type='email']",
            "input[name='email']",
            "input[placeholder*='Email']",
            "input[placeholder*='email']",
            "input[autocomplete='email']"
        ]

        email_input = None
        for sel in possible_selectors:
            try:
                email_input = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                if email_input:
                    break
            except Exception:
                continue

        if not email_input:
            print("[!] Tidak menemukan input email pada form reset")
            return False

        try:
            # Fokus & bersihkan, lalu ketik perlahan. Jika tidak berhasil, set value via JS
            try:
                email_input.click()
            except Exception:
                pass
            email_input.clear()
            type_slowly(email_input, email)
            time.sleep(0.5)
            # Jika send_keys gagal (nilai kosong), set lewat JS dan dispatch event
            current_val = (email_input.get_attribute('value') or '').strip()
            if not current_val:
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
                    email_input,
                    email,
                )
                time.sleep(0.3)
        except Exception as e:
            print(f"[!] Gagal mengisi email secara normal: {e}, mencoba set via JS")
            try:
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
                    email_input,
                    email,
                )
            except Exception:
                pass

        # Cari tombol submit dengan beberapa strategi
        submit_clicked = False
        try:
            submit_btn = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Send me a recovery link') or contains(., 'Send recovery') or contains(., 'Kirim')]"))
            )
            safe_click(driver, submit_btn)
            submit_clicked = True
        except Exception:
            # Fallback: cari tombol/anchor yang cocok berdasarkan teks
            buttons = driver.find_elements(By.TAG_NAME, 'button') + driver.find_elements(By.TAG_NAME, 'a')
            keywords = ['send me a recovery link', 'send recovery', 'send link', 'send', 'kirim', 'kirim tautan', 'kirim link', 'recovery', 'reset']
            for b in buttons:
                try:
                    text = driver.execute_script('return (arguments[0].textContent || "").toLowerCase().trim();', b)
                    if any(k in text for k in keywords):
                        try:
                            safe_click(driver, b)
                            submit_clicked = True
                            break
                        except Exception:
                            continue
                except Exception:
                    continue

        # Jika belum berhasil, coba submit dengan Enter pada input
        if not submit_clicked:
            try:
                email_input.send_keys('\n')
                submit_clicked = True
            except Exception:
                pass

        if not submit_clicked:
            print('[!] Gagal menemukan atau mengklik tombol submit')
            return False
        print("[+] Recovery link terkirim, mengalihkan ke pengecekan inbox...")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"[!] Gagal request reset: {e}")
        return False


def dismiss_gmail_popups(driver):
    try:
        driver.execute_script("""
            document.querySelectorAll('div[role="dialog"], div[role="alertdialog"]').forEach(el => {
                el.querySelectorAll('button, div[role="button"], span[role="button"]').forEach(btn => {
                    let t = (btn.innerText || "").toLowerCase().trim();
                    if (t.includes('got it') || t.includes('skip') || t.includes('close') ||
                        t.includes('ok') || t.includes('next') || t.includes('later') ||
                        t.includes('cancel') || t.includes('not now') || t.includes('understood')) {
                        try { btn.click(); } catch(e){}
                    }
                });
                try { el.remove(); } catch(e){}
            });
            document.querySelectorAll('.Kj-JD, .dw, .nn').forEach(el => {
                try { el.remove(); } catch(e){}
            });
            document.body.style.overflow = 'auto';
        """)
        print("[+] Popup Gmail dibersihkan")
    except Exception as e:
        print(f"[!] Gagal hapus popup Gmail: {e}")


def get_reset_link(driver, max_retry=5, refresh_delay=5):
    gmail_url = "https://mail.google.com/mail/u/0/#search/in%3Aanywhere+official.link"
    try:
        driver.set_page_load_timeout(40)
        driver.get(gmail_url)
    except TimeoutException:
        print("[!] Timeout load Gmail, mencoba navigasi ulang...")
        try:
            driver.execute_script("window.stop();")
            driver.get(gmail_url)
        except:
            pass
    print(f"{datetime.now().strftime('%H:%M:%S')} Menunggu email reset masuk di inbox Gmail...")

    for attempt in range(max_retry):
        try:
            print(f"{datetime.now().strftime('%H:%M:%S')} Percobaan cek email ke-{attempt + 1}")
            try:
                driver.refresh()
            except TimeoutException:
                print("[!] Timeout refresh Gmail, mencoba ulang...")
                driver.execute_script("window.stop();")
                time.sleep(2)
                driver.refresh()
            time.sleep(4)
            dismiss_gmail_popups(driver)
            time.sleep(1)

            mails = driver.find_elements(By.CSS_SELECTOR, "tr[jscontroller], tr.zA, .zA")
            if not mails:
                print("[!] Inbox kosong / email belum masuk")
                time.sleep(refresh_delay)
                continue

            safe_click(driver, mails[0])
            print("[+] Email berhasil dibuka, menunggu konten dirender...")
            time.sleep(5)

            driver.execute_script("""
(function() {
    const expandButton = document.querySelector('[data-tooltip="Expand all"], [aria-label="Expand all"]');
    if (expandButton) {
        expandButton.click();
        console.log('[+] Berhasil mengklik tombol Expand All resmi Gmail.');
    } else {
        const emailRows = document.querySelectorAll('div[role="main"] div[aria-expanded="false"]');
        if (emailRows.length > 0) {
            let count = 0;
            emailRows.forEach(row => {
                const clickableArea = row.querySelector('.gE, .yW, [role="gridcell"]');
                if (clickableArea) {
                    clickableArea.click();
                    count++;
                } else {
                    row.click();
                    count++;
                }
            });
            console.log('[+] Berhasil memaksa klik ' + count + ' email terlipat.');
        } else {
            console.log('[-] Tidak ditemukan elemen email yang terlipat.');
        }
    }
})();
""")
            print("[+] Expand all messages dilakukan.")
            time.sleep(3)

            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"{datetime.now().strftime('%H:%M:%S')} Total link ditemukan: {len(links)}")

            reset_links = []
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    href = href.strip()
                    text = driver.execute_script("return arguments[0].textContent;", link)
                    text = text.strip().lower() if text else ""
                    if "reset password" in text or ("reset" in text and "password" in text):
                        reset_links.append(href)
                except Exception:
                    pass

            if reset_links:
                total = len(reset_links)
                print(f"\n[SUCCESS] Ditemukan {total} link reset password!")
                return reset_links
            print("[!] Link reset belum ditemukan pada percobaan ini.")
        except Exception as e:
            print(f"[!] Error Gmail UI: {e}")

        time.sleep(refresh_delay)

    print("[FAILED] Reset link tidak ditemukan setelah 5x percobaan.")
    return "tidak ada inbox"


def set_new_password(driver, password):
    try:
        wait = WebDriverWait(driver, 20)
        handle_ads_flow(driver)
        print(f"{datetime.now().strftime('%H:%M:%S')} Mengisi formulir password baru...")

        new_password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#new_password")))
        new_password_input.clear()
        new_password_input.send_keys(password)

        repeat_password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#repeat_password")))
        repeat_password_input.clear()
        repeat_password_input.send_keys(password)

        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Set password')]")))
        safe_click(driver, submit_btn)
        print("[SUCCESS] Form password baru disubmit.")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"[!] Gagal set password: {e}")
        return False


def _init_driver_worker(options):
    driver = uc.Chrome(
        options=options,
        version_main=get_chrome_version(),
        use_subprocess=True
    )
    driver.set_page_load_timeout(40)
    return driver


def buat_driver_aman():
    port = random.randint(9200, 9400)
    options = uc.ChromeOptions()

    if platform.system() == "Windows":
        chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        if not os.path.exists(chrome_path):
            chrome_path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    else:
        chrome_path = '/usr/bin/google-chrome'
        if not os.path.exists(chrome_path):
            chrome_path = '/usr/bin/chromium'
    if os.path.exists(chrome_path):
        options.binary_location = chrome_path

    options.add_argument(f'--remote-debugging-port={port}')
    options.add_argument('--remote-allow-origins=*')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-signin-promo')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--guest')

    driver = None
    TIMEOUT_BUKA_BROWSER = 15

    print(f"[Sistem] Menjalankan Chrome pada port {port}...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_init_driver_worker, options)
        try:
            driver = future.result(timeout=TIMEOUT_BUKA_BROWSER)
            print("[Sistem] Browser berhasil diluncurkan.")
        except concurrent.futures.TimeoutError:
            print(f"[PENTING] Proses buka browser STUCK!")
            return None

    return driver


SPREADSHEET_ID = "11y5rg2XN2rHZDeY0ktA_ly_QfGC-jE2sdH3Ol--B9xw"
SHEET_NAME = "data"


def _get_reset_col_letter(ws):
    headers = ws.row_values(1)
    for i, h in enumerate(headers, start=1):
        if h.strip().lower() == "reset status":
            return chr(64 + i) if i <= 26 else None
    return None


def get_data_reset(ws):
    reset_col = _get_reset_col_letter(ws)
    if not reset_col:
        print("[!] Kolom 'Reset Status' tidak ditemukan di header.")
        return None, None

    records = ws.get_all_records()
    for i, rec in enumerate(records, start=2):
        reset_status = str(rec.get("Reset Status", "")).strip()
        if not reset_status:
            cell = f"{reset_col}{i}"
            ws.update_acell(cell, "Processing")
            ws.format(cell, {
                "backgroundColor": {"red": 1, "green": 1, "blue": 0}
            })
            print(f"[+] Row {i} dikunci dengan status 'Processing'.")
            return rec, i
    return None, None


def update_reset_status(ws, row, status):
    col = _get_reset_col_letter(ws)
    if not col:
        print("[!] Gagal update: kolom Reset Status tidak ditemukan.")
        return
    cell = f"{col}{row}"
    ws.update_acell(cell, status)
    if status == "sukses":
        ws.format(cell, {
            "backgroundColor": {"red": 0, "green": 1, "blue": 0}
        })
    elif status == "Processing":
        ws.format(cell, {
            "backgroundColor": {"red": 1, "green": 1, "blue": 0}
        })
    else:
        ws.format(cell, {
            "backgroundColor": {"red": 1, "green": 0, "blue": 0}
        })


def main():
    print(f"{datetime.now().strftime('%H:%M:%S')} Memulai proses reset password...")

    gc = gspread.service_account(filename="service-account.json")
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(SHEET_NAME)

    data, row = get_data_reset(ws)
    if not data:
        print("[!] Tidak ada data yang perlu di-reset (semua sudah terisi).")
        return

    email = data.get("Email", "").strip()
    password_gmail = data.get("Password", "").strip()
    new_password = data.get("Password Link", "").strip()

    print(f"[+] Baris {row}: {email}")
    print(f"[+] New Password: {new_password}")

    if not email or not password_gmail or not new_password:
        print("[!] Data tidak lengkap (Email / Password / Password Link kosong).")
        update_reset_status(ws, row, "data tidak lengkap")
        return

    driver = buat_driver_aman()
    if driver is None:
        print("[Sistem] Gagal inisialisasi driver.")
        return

    try:
        driver.set_page_load_timeout(40)

        if not login_gmail_to_profile(driver, email, password_gmail):
            print("[!] Login Gmail gagal.")
            update_reset_status(ws, row, "login gagal")
            return

        if not clear_official_link_cookies(driver):
            print("[!] Gagal bersihkan cookies.")
            update_reset_status(ws, row, "gagal")
            return

        if not request_reset(driver, email):
            print("[!] Gagal request reset.")
            update_reset_status(ws, row, "gagal request")
            return

        reset_links = get_reset_link(driver, max_retry=5)

        if reset_links == "tidak ada inbox":
            print("[!] Email reset tidak ditemukan di inbox.")
            update_reset_status(ws, row, "tidak ada inbox")
            return

        if not reset_links or not isinstance(reset_links, list):
            print("[!] Link reset tidak valid.")
            update_reset_status(ws, row, "gagal")
            return

        print(f"{datetime.now().strftime('%H:%M:%S')} Mencoba {len(reset_links)} link (dari terbaru)...")
        link_berhasil = None
        for link in reversed(reset_links):
            print(f"[+] Buka link: {link[:70]}...")
            try:
                driver.set_page_load_timeout(15)
                driver.get(link)
            except TimeoutException:
                driver.execute_script("window.stop();")
            time.sleep(2)

            page_title = driver.title.lower()
            page_source = driver.page_source.lower()
            if "404" in page_title or "not found" in page_title or "404 not found" in page_source:
                print("[!] Link expired/404, coba link sebelumnya...")
                continue

            link_berhasil = link
            break

        if not link_berhasil:
            print("[!] Semua link reset expired (404).")
            update_reset_status(ws, row, "semua link expired")
            return

        print(f"[+] Link valid, menuju formulir reset...")
        wait = WebDriverWait(driver, 30)
        wait.until(lambda d: "reset-password" in d.current_url or "official.link" in d.current_url)
        print(f"[+] Tiba di formulir reset: {driver.current_url}")

        if set_new_password(driver, new_password):
            update_reset_status(ws, row, "sukses")
            print(f"\n[SUCCESS] Reset password untuk {email} berhasil!")
        else:
            update_reset_status(ws, row, "gagal set password")

    except Exception as e:
        print(f"[-] Fatal Error: {e}")
        try:
            update_reset_status(ws, row, "error")
        except:
            pass
    finally:
        if driver:
            try:
                driver.quit()
                del driver
            except:
                pass


if __name__ == "__main__":
    main()
