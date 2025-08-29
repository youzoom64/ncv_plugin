@echo off
echo Starting Comment Display System...
echo.

echo 1. Starting WebSocket server...
start "Comment Display Server" python gui/comment_websocket_server.py

echo 2. Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo 3. Opening HTML file...
start "" "gui/comment_display.html"

echo.
echo System started successfully!
echo Open the HTML file in OBS as Browser Source.
echo.
pause
