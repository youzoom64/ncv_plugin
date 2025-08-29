# Comment Display System Launcher (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Comment Display System Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Starting WebSocket server..." -ForegroundColor Yellow
try {
    Start-Process -FilePath "python" -ArgumentList "gui/comment_websocket_server.py" -WindowStyle Minimized
    Write-Host "SUCCESS: WebSocket server started" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to start WebSocket server" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "Step 2: Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Step 3: Opening HTML file..." -ForegroundColor Yellow
$htmlPath = Join-Path $PSScriptRoot "gui/comment_display.html"
if (Test-Path $htmlPath) {
    try {
        Start-Process $htmlPath
        Write-Host "SUCCESS: HTML file opened in browser" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to open HTML file" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: HTML file not found" -ForegroundColor Red
    Write-Host "Expected path: $htmlPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "System startup completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Check if browser opened with HTML file" -ForegroundColor Gray
Write-Host "2. In OBS, add Browser Source" -ForegroundColor Gray
Write-Host "3. Set URL to the HTML file path" -ForegroundColor Gray
Write-Host "4. Set width: 512px, height: as needed" -ForegroundColor Gray
Write-Host "5. Check 'Shutdown source when not visible'" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to continue"
