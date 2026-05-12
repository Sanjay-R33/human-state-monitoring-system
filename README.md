# Human State Monitoring System

A full-stack, real-time employee monitoring system that detects **emotion**, **fatigue**, and **pulse rate** using AI-powered facial analysis and hardware sensors. Built with a FastAPI backend, React (Vite) frontend, and Arduino hardware integration.

## System Features

- **Employee Dashboard** — Employees view their real-time stats: Pulse, Emotion, Fatigue, and Session Duration.
- **Manager Dashboard** — Managers oversee the real-time status of all employees, with usage tracking and over-time alerts. Inactive employees default to neutral stats for clarity.
- **Multimodal AI** — Uses MediaPipe for facial landmarks and a custom PyTorch multitask deep learning model (`MultitaskBlendshapeNet`) to estimate emotion and fatigue. Falls back seamlessly to MediaPipe heuristics if the model file is absent.
- **Hardware Integration** — Integrates with Arduino serial pulse sensors with Exponential Moving Average (EMA) noise cancellation. Supports simulated pulse data if hardware is unavailable.
- **Session Tracking** — Tracks login/logout sessions with daily usage statistics and 8-hour overtime alerts for managers.
- **Auto-Reset Logic** — If an employee leaves the camera frame, stats automatically reset to Neutral after a short timeout.

## Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (v3.9+ recommended)
- **MySQL Server** (v8.0+ recommended)
- **Git**
- **Arduino IDE** (optional, for hardware setup)

## Project Structure

```
human-state-monitoring-system/
├── backend/                  # FastAPI backend (ML inference, API, WebSocket)
│   ├── main.py               # API routes and WebSocket handler
│   ├── monitor.py             # MonitorService (camera, MediaPipe, pulse)
│   ├── ml_model.py            # MultitaskBlendshapeNet PyTorch model
│   ├── extract_features.py    # Feature extraction from facial landmarks
│   ├── models.py              # SQLAlchemy ORM models
│   ├── database.py            # Database connection config
│   ├── auth.py                # JWT authentication helpers
│   ├── train_multitask.py     # Model training script
│   └── requirements.txt       # Python dependencies
├── frontend/                 # React + Vite frontend
│   └── src/
│       ├── components/
│       │   ├── Login.jsx             # Login & Registration page
│       │   ├── EmployeeDashboard.jsx # Employee monitoring view
│       │   └── ManagerDashboard.jsx  # Manager overview dashboard
│       ├── App.jsx            # App router
│       └── main.jsx           # Entry point
├── database/
│   └── schema.sql             # Reference MySQL schema
├── hardware/
│   └── pulse_sensor.ino       # Arduino pulse sensor firmware
└── run_backend.bat            # Windows backend startup script
```

## Step-by-Step Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Sanjay-R33/human-state-monitoring-system.git
cd human-state-monitoring-system
```

### 2. Set Up MySQL Database

1. Ensure MySQL Server is running on `localhost`.
2. Create the database and tables by running the reference schema:
   ```bash
   mysql -u root -p < database/schema.sql
   ```
   > **Note:** The default credentials in the backend are `root:root`. Update `backend/database.py` if your MySQL credentials differ.

### 3. Set Up the Backend

The backend uses FastAPI and handles all machine learning inference (MediaPipe + PyTorch).

**Option A — Using the startup script (Windows):**

1. Double-click **`run_backend.bat`** in the project root (or run `.\run_backend.bat` in a terminal).
2. The script will:
   - Create a Python virtual environment (`venv`) if one doesn't exist.
   - Install all dependencies from `backend/requirements.txt`.
   - Start the Uvicorn server at `http://localhost:8000`.

**Option B — Manual setup:**

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

> **Note on ML Models:**
> - `face_landmarker.task` — Will download automatically on first run.
> - `multitask_model.pth` — The pre-trained deep learning model is **included in the repository**. It works out of the box after cloning.
> - **No dataset download is required to run the system.** The FER2013 dataset is only needed if you want to retrain the model (see Step 6).

### 4. Set Up the Frontend

The frontend is a React application built with Vite.

1. Open a **new terminal** (keep the backend running).
2. Navigate and install:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open your browser at `http://localhost:5173`.

### 5. Hardware Setup (Optional)

The system integrates with an Arduino pulse sensor on **COM5**.

- **With hardware:** Upload `hardware/pulse_sensor.ino` to your Arduino using the Arduino IDE.
- **Without hardware:** The backend automatically generates simulated pulse data.

### 6. Retraining the Model (Optional)

This is **not required** to run the system. Only follow these steps if you want to retrain the deep learning model from scratch.

1. Download the [FER2013 dataset](https://www.kaggle.com/datasets/msambare/fer2013) from Kaggle.
2. Extract it into `backend/archive/` so the structure looks like:
   ```
   backend/archive/
   ├── train/
   │   ├── angry/
   │   ├── disgust/
   │   ├── fear/
   │   ├── happy/
   │   ├── neutral/
   │   ├── sad/
   │   └── surprise/
   └── test/
       └── ...
   ```
3. Run the feature extraction script (processes images → blendshape features):
   ```bash
   cd backend
   python extract_features.py
   ```
4. Train the model:
   ```bash
   python train_multitask.py
   ```
5. The trained model will be saved as `backend/multitask_model.pth`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Webcam not turning on** | Ensure no other app (Zoom, Teams, etc.) is using the camera. The backend reads from camera index `0`. |
| **MySQL connection error** | Verify MySQL is running and credentials in `backend/database.py` match your setup. Run `database/schema.sql` to initialize tables. |
| **Port conflicts** | Backend uses port `8000`, frontend uses `5173`. Modify `run_backend.bat` or `frontend/vite.config.js` to change ports. |
| **Missing ML model** | `multitask_model.pth` is included in the repo. If it's missing, the system still works using MediaPipe fallback. To retrain, see Step 6. |
