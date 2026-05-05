# Keep working directory at google-adk-agent.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Load .env from the repository root.
$envFile = "..\\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
        }
    }
    Write-Host "Environment variables loaded from .env" -ForegroundColor Green
} else {
    Write-Host "Warning: .env file not found at $envFile" -ForegroundColor Yellow
}

# Set MCP URL (only if not already set).
# - BGH:    http://localhost:8002/mcp
# - States: http://localhost:8004/mcp
if (-not $env:MCP_URL) {
    $env:MCP_URL = "http://localhost:8004/mcp"
}

Write-Host "Starting ADK Agent from google-adk-agent directory..." -ForegroundColor Cyan
Write-Host "MCP_URL: $($env:MCP_URL)" -ForegroundColor Gray

# Start the agent (ADK auto-detects the agent subdirectory).
adk web