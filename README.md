# Human State Monitoring System

This project is a full-stack Employee Emotion and Fatigue Monitoring System. It uses a Python (FastAPI) backend to process real-time webcam and hardware pulse data, and a React (Vite) frontend for real-time dashboard visualization.

## Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (v3.9+ recommended)
- **Git**

## Step-by-Step Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Sanjay-R33/human-state-monitoring-system.git
cd human-state-monitoring-system
```

### 2. Set Up the Backend
The backend uses FastAPI and handles all the machine learning inference (MediaPipe and PyTorch). We have a convenient script to automate the setup for Windows users.

1. Double-click the **`run_backend.bat`** file in the root of the project.
   - *Alternatively, run it via terminal:* `.\run_backend.bat`
2. **What this script does:**
   - Automatically creates a Python virtual environment (`venv`).
   - Activates it and installs all dependencies from `backend/requirements.txt`.
   - Starts the Uvicorn server at `http://localhost:8000`.

> **Note on Machine Learning Models:** 
> - The `face_landmarker.task` file will automatically download on the first run.
> - The `multitask_model.pth` (Deep Learning model) is too large for GitHub. You must ask the repository owner for this file and place it inside the `backend/` directory for full Deep Learning capabilities. (If it's missing, the system will still function using the MediaPipe fallback).

### 3. Set Up the Frontend
The frontend is a modern React application built with Vite and TailwindCSS.

1. Open a **new terminal window** (keep the backend running in the other).
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Install the dependencies:
   ```bash
   npm install
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Open your browser and go to `http://localhost:5173`.

### 4. Hardware Setup (Optional but Recommended)
The system expects an Arduino pulse sensor connected to **`COM5`**. 
- If you have the hardware, upload the `hardware/pulse_sensor.ino` file to your Arduino.
- If you don't have the hardware, the backend will automatically generate **simulated pulse data** so you can still test the software.

## Troubleshooting

- **Webcam not turning on:** Ensure no other application (like Zoom or Teams) is using your camera. The backend script will read from default camera index `0`.
- **Database errors:** The system uses SQLite. The database file will be automatically created in the `backend/` directory when you first start the FastAPI server. If you face issues, you can safely delete `*.db` files to reset your local database.
- **Port conflicts:** If port `8000` (Backend) or `5173` (Frontend) is in use, you can modify `run_backend.bat` and `frontend/package.json` respectively to use different ports.
