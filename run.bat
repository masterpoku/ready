
@echo off
:loop
echo [%time%] Menjalankan cok.py...
python cok.py

echo.
echo [*] Membantu membersihkan sisa proses Chrome dan Driver di Windows...
:: /F untuk force kill, /IM untuk menentukan nama proses, /T untuk membunuh child process
taskkill /F /IM chrome.exe /T >nul 2>&1
taskkill /F /IM chromedriver.exe /T >nul 2>&1

echo 1 > Bot/trigger.txt
timeout /t 10 /nobreak

echo.
echo [!] Antrean selesai atau terjadi crash.
echo [!] Menunggu 5 detik sebelum mengambil antrean berikutnya...
timeout /t 5 /nobreak

echo.
echo [*] Melakukan restart skrip...
goto loop