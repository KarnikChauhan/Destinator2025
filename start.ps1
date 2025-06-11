# Clear the console
Clear-Host

# Function to print colored messages
function Print-Colored {
    param (
        [int]$color,
        [string]$message
    )
    Write-Host $message -ForegroundColor ([System.ConsoleColor]$color)
}

# Kill any Lavalink process running on port 8080
$existingProcess = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne $null }
if ($existingProcess) {
    $processId = $existingProcess.OwningProcess
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Print-Colored 14 "Stopped existing Lavalink process (PID: $processId) running on port 8080."
}

# Read bot token from config/config.json
if (Test-Path "config/config.json") {
    $BOT_TOKEN = (Get-Content "config/config.json" | ConvertFrom-Json).bot_token
} else {
    Print-Colored 12 "Error: config/config.json not found"
    exit 1
}

# Check if token exists
if (-not $BOT_TOKEN -or $BOT_TOKEN -eq "null") {
    Print-Colored 12 "Error: Bot token not found in config/config.json"
    exit 1
}

# Activate or create virtual environment
if (Test-Path ".venv/Scripts/Activate") {
    Print-Colored 10 "Activating virtual environment..."
    .\.venv\Scripts\Activate
} else {
    Print-Colored 14 "Creating virtual environment..."
    python -m venv .venv
    .\.venv\Scripts\Activate
}

# Ensure pip is up to date
python -m pip install --upgrade pip

# Check if requirements.txt exists
if (-not (Test-Path "requirements.txt")) {
    Print-Colored 12 "Error: requirements.txt not found"
    exit 1
}

# Ensure dependencies are installed
$installed_packages = pip freeze 2>$null
if (-not $installed_packages) {
    Print-Colored 14 "Installing dependencies..."
    python -m pip install -r requirements.txt
} else {
    $missing_reqs = Compare-Object (Get-Content "requirements.txt" | Sort-Object) ($installed_packages | Sort-Object)
    if ($missing_reqs) {
        Print-Colored 14 "Installing missing dependencies..."
        python -m pip install -r requirements.txt
    } else {
        Print-Colored 10 "All requirements are already installed."
    }
}

# Start Lavalink server
if (Test-Path "lavalink.jar") {
    Print-Colored 10 "Starting Lavalink server..."
    Start-Process -FilePath "java.exe" -ArgumentList "-jar lavalink.jar"
} else {
    Print-Colored 12 "Error: lavalink.jar not found"
}

# Start bot
Print-Colored 10 "Starting bot..."
python src/main.py --token "$BOT_TOKEN"
