@echo off
title Python Auto Installer

set PYTHON_VER=3.13.9

rem Detect architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set ARCH=amd64
) else if "%PROCESSOR_ARCHITEW6432%"=="AMD64" (
    set ARCH=amd64
) else (
    set ARCH=x86
)

echo ===================================
echo Detected: %ARCH% architecture
echo Python version: %PYTHON_VER%
echo ===================================

rem Check if Python already installed
python --version >nul 2>&1
if %errorlevel%==0 (
    echo Python already installed, skipping download...
    goto :install_packages
)

echo ===================================
echo Downloading Python %PYTHON_VER% (%ARCH%)...
echo ===================================

set DOWNLOAD_URL=https://www.python.org/ftp/python/%PYTHON_VER%/python-%PYTHON_VER%-%ARCH%.exe
set OUTFILE=%TEMP%\python-installer.exe

rem Try TLS 1.2 first, fallback to 1.1, then 1.0
powershell -Command "& { $ok = $false; foreach ($tls in @('Tls12','Tls11','Tls')) { try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::$tls; Write-Host 'Trying' $tls; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%OUTFILE%' -ErrorAction Stop; $ok = $true; break } catch { Write-Host $tls 'failed, trying next...' } }; if (-not $ok) { exit 1 } }"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Download failed! Check your internet connection.
    pause
    exit /b 1
)

echo.
echo ===================================
echo Installing Python quietly...
echo ===================================

"%OUTFILE%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

if %errorlevel% neq 0 (
    echo [WARN] Installer might have errors, continuing anyway...
)

echo.
echo Waiting for installation to complete...
timeout /t 15 /nobreak >nul

:install_packages
echo.
echo ===================================
echo Updating pip...
echo ===================================

python -m pip install --upgrade pip

echo.
echo ===================================
echo Installing packages...
echo ===================================

python -m pip install ^
setuptools ^
certifi ^
undetected-chromedriver ^
selenium ^
beautifulsoup4 ^
requests ^
gspread

echo.
echo ===================================
echo DONE!
echo ===================================

python --version

pause
