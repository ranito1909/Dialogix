web: gunicorn -k eventlet -w 1 -b 0.0.0.0:$PORT dialogix:app
release: RUST_VERSION=$(cat /app/Aptfile) pip install -r requirements.txt
