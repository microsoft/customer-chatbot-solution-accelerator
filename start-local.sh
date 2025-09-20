#!/bin/bash

echo "Starting E-commerce Chat Application..."

echo ""
echo "Starting Backend (FastAPI)..."
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo ""
echo "Waiting 3 seconds for backend to start..."
sleep 3

echo ""
echo "Starting Frontend (React)..."
cd ../modern-e-commerce-ch && npm run dev &
FRONTEND_PID=$!

echo ""
echo "Both services are starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for user to stop
wait