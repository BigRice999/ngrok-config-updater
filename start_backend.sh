#!/bin/bash

source venv/bin/activate

# Purpose:
# 1. Start Flask backend
# 2. Start ngrok tunnel to localhost:5000
# 3. Extract public ngrok URL
# 4. Write it to a JSON file
# 5. Optionally upload this file to GitHub (or another static hosting service)

# ============ Step 1: Start Flask Backend ============
echo "[INFO] Starting Flask backend on port 5000..."
# Run Flask in the background
python3 app.py &
FLASK_PID=$!

sleep 3

# ============ Step 2: Start ngrok tunnel ============
echo "[INFO] Starting ngrok tunnel..."
# Kill existing ngrok processes (optional)
pkill -f "ngrok"

# Start ngrok in background and log to file
ngrok http 5000 > ngrok.log &
sleep 5

# ============ Step 3: Extract ngrok public URL ============
NGROK_URL=""
RETRIES=10

while [ $RETRIES -gt 0 ]; do
  NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*' | head -n 1)
  if [ ! -z "$NGROK_URL" ]; then
    echo "[SUCCESS] ngrok URL: $NGROK_URL"
    break
  fi
  sleep 2
  ((RETRIES--))
done

if [ -z "$NGROK_URL" ]; then
  echo "[ERROR] Failed to get ngrok public URL"
  kill $FLASK_PID
  exit 1
fi

# ============ Step 4: Write to JSON config ============
echo "[INFO] Writing server_config.json..."
echo -e "{\n  \"server_url\": \"$NGROK_URL\"\n}" > server_config.json

# ============ Step 5: Upload to GitHub (optional) ============
# Replace this section with your upload logic (e.g. git commit + push or curl to Netlify)
# echo "[INFO] Uploading config to GitHub..."
# git add server_config.json
# git commit -m "Update ngrok URL"
# git push origin main

# ============ Done ============
echo "[DONE] Backend running, ngrok URL published."
echo "You can now access the API from: $NGROK_URL"
echo "Make sure your Flutter app reads this from a known URL!"

# Wait for Flask to exit
wait $FLASK_PID
