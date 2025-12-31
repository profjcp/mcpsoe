#!/bin/bash

# Script to run the entire project with one command

echo "Activating virtual environment..."
source venmcp/bin/activate

echo "Running preprocess.py..."
python preprocess.py

if [ $? -ne 0 ]; then
    echo "Error in preprocess.py. Exiting."
    exit 1
fi

echo "Starting MCP server in background..."
python mcp_server_local.py &
MCP_PID=$!

echo "Waiting for MCP server to start..."
sleep 5  # Adjust if needed

echo "Starting Streamlit client..."
streamlit run appclient/app_client.py &
STREAMLIT_PID=$!

echo "Project is running. MCP Server PID: $MCP_PID, Streamlit PID: $STREAMLIT_PID"
echo "Press Ctrl+C to stop."

# Wait for interrupt
trap "echo 'Stopping services...'; kill $MCP_PID $STREAMLIT_PID; exit" INT
wait