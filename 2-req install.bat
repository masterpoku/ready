@echo off


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
seleniumbase ^
beautifulsoup4 ^
requests ^
gspread

echo.
echo ===================================
echo DONE!
echo ===================================

python --version

pause