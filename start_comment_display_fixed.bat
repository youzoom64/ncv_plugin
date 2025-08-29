@echo off
echo ========================================
echo Comment Display System Launcher
echo ========================================
echo.

echo Step 1: Starting WebSocket server...
start "Comment Server" python gui/comment_websocket_server.py
if errorlevel 1 (
    echo ERROR: Failed to start WebSocket server
    pause
    exit /b 1
)

echo Step 2: Waiting for server to start...
timeout /t 3 /nobreak >nul

echo Step 3: Opening HTML file...
if exist "gui\comment_display.html" (
    start "" "gui\comment_display.html"
    echo SUCCESS: HTML file opened in browser
) else (
    echo ERROR: HTML file not found
    echo Expected path: gui\comment_display.html
)

echo.
echo ========================================
echo System startup completed!
echo ========================================
echo.
echo Next steps:
echo 1. Check if browser opened with HTML file
echo 2. In OBS, add Browser Source
echo 3. Set URL to the HTML file path
echo 4. Set width: 512px, height: as needed
echo 5. Check "Shutdown source when not visible"
echo.
pause
