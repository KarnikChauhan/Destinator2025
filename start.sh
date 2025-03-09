#!/bin/bash

clear

# Function to print colored messages
print_colored() {
    color=$1
    message=$2
    echo -e "\e[${color}m${message}\e[0m"
}

# Detect OS
OS="$(uname -s)"

# Read bot token from config/config.json
if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    BOT_TOKEN=$(jq -r '.bot_token' config/config.json)
elif [[ "$OS" =~ MINGW64_NT|MSYS_NT|CYGWIN_NT ]]; then
    BOT_TOKEN=$(jq -r ".bot_token" config/config.json < config/config.json)
else
    print_colored 1 "Unsupported OS: $OS"
    exit 1
fi

# Check if jq command succeeded and token is not empty
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" == "null" ]; then
    print_colored 1 "Error: Bot token not found in config/config.json"
    exit 1
fi

# Activate virtual environment
if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        print_colored 3 "Creating env and activating it"
        python3 -m venv .venv
        source .venv/bin/activate
    fi
elif [[ "$OS" =~ MINGW64_NT|MSYS_NT|CYGWIN_NT ]]; then
    if [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
    else
        print_colored 3 "Creating env and activating it"
        python -m venv .venv
        source .venv/Scripts/activate
    fi
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_colored 1 "Error: requirements.txt not found"
    exit 1
fi

# Check if requirements are already installed
missing_requirements=$(comm -23 <(sort requirements.txt) <(pip freeze | sort))

if [ -n "$missing_requirements" ]; then
    print_colored 3 "Installing missing requirements..."
    python -m pip install -r requirements.txt
else
    print_colored 2 "All requirements are already installed."
fi

# Start Lavalink server
if [ -f "lavalink.jar" ]; then
    print_colored 2 "Starting Lavalink server..."
    if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
        nohup java -jar lavalink.jar > lavalink.log 2>&1 &
    elif [[ "$OS" =~ MINGW64_NT|MSYS_NT|CYGWIN_NT ]]; then
        start "" javaw -jar lavalink.jar
    fi
else
    print_colored 1 "Error: lavalink.jar not found"
fi

# Start bot
print_colored 2 "Starting bot..."
python src/main.py --token "$BOT_TOKEN"
