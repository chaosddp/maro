# Start data service
Start-Process -FilePath "python" -ArgumentList "server.py"

# Start demo web server
Start-Process -FilePath "python" -ArgumentList "-m http.server 9988"

Start-Process -FilePath "http://127.0.0.1:9988"

echo "Done."
echo "Steps:"
echo "1. Click connect button to connect to server"
echo "2. Select category and click live source button, then ready to recieve data."
echo "3. Use 'python client.py' to send data"