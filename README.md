# AQUA Monitor

**Underwater Detection and Environmental Monitoring System**

AQUA Monitor is a comprehensive dashboard system for monitoring marine environments using computer vision and environmental sensors. The system tracks marine species detections, environmental conditions, and device health metrics in real-time.

## 🌊 Features

### Core Capabilities
- **Real-time Species Detection**: YOLO-based object detection for fish species, plants, and coral monitoring
- **Environmental Monitoring**: Track water temperature, humidity, pressure, depth, turbidity, light intensity (lux), pH, and salinity
- **Device Health Tracking**: Monitor CPU/GPU temperatures, battery level, storage usage, connectivity status, and YOLO inference performance (FPS)
- **Camera Streaming**: Live camera feed with frame capture and detection logging
- **Analytics Dashboard**: Visualize detection patterns, species distribution, and environmental trends
- **Event Logging**: Comprehensive logging system for all system events

## 🏗️ Architecture

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Computer Vision**: OpenCV for camera handling and image processing
- **API**: RESTful API endpoints for data access and camera control

### Frontend
- **Framework**: Next.js 16 with React 19
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS
- **Charts**: Recharts for data visualization

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 18+** and **pnpm** (or npm/yarn)
- **Webcam** (optional, for camera streaming)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd INTERFACE
```

### 2. Backend Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

The required Python packages are:
- Flask 2.3.2
- Flask-SQLAlchemy 3.0.5
- Werkzeug 2.3.6
- opencv-python 4.8.1.78
- numpy 1.24.3
- requests 2.31.0

### 3. Frontend Setup

Install Node.js dependencies:

```bash
pnpm install
```

Or using npm:

```bash
npm install
```

## 🎯 Usage

### Starting the Backend Server

Run the Flask application:

```bash
python app.py
```

The backend server will start on `http://localhost:5000` (default Flask port).

**Note**: The database (`dashboard.db`) will be automatically created on first run. If the database is empty, mock data will be automatically loaded from `mock-data.json`.

### Starting the Frontend Development Server

In a separate terminal, start the Next.js development server:

```bash
pnpm dev
```

Or using npm:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Building for Production

Build the Next.js application:

```bash
pnpm build
pnpm start
```

## 📡 API Endpoints

### Detection Endpoints
- `GET /api/detections` - Get all species detections
- `POST /api/camera/frame` - Capture and save a frame with detections

### Sensor Endpoints
- `GET /api/sensors` - Get all environmental sensor readings

### Health Endpoints
- `GET /api/health` - Get all device health records

### Statistics
- `GET /api/stats` - Get summary statistics

### Camera Endpoints
- `GET /api/camera/stream` - Stream live camera feed (MJPEG)
- `POST /api/camera/stop` - Stop camera stream
- `GET /api/camera/location` - Get camera location coordinates

### Logs
- `GET /api/logs` - Get all system logs

### Database Management
- `POST /api/seed` - Seed database with mock data from `mock-data.json`

## 📊 Database Models

### Detection
Tracks marine species detections:
- Species name
- Count
- Confidence score
- Timestamp
- Location coordinates (x, y)

### SensorReading
Environmental sensor data:
- Temperature (°C)
- Humidity (%)
- Pressure (bar)
- Depth (meters)
- Turbidity
- Light intensity (lux)
- pH level
- Salinity

### DeviceHealth
System health metrics:
- CPU/GPU temperatures
- Battery level (%)
- Storage usage (%)
- Connectivity status
- YOLO FPS
- Model name
- CPU/GPU/RAM usage (%)

### Log
System event logs:
- Event type
- Message
- Severity (info, warning, error)
- Timestamp

## 🗂️ Project Structure

```
INTERFACE/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/             # React components
│   ├── ui/                # shadcn/ui components
│   └── theme-provider.tsx # Theme configuration
├── templates/             # Flask HTML templates
│   ├── index.html         # Landing page
│   ├── overview.html      # Dashboard overview
│   ├── camera.html        # Camera feed
│   ├── analytics.html     # Analytics dashboard
│   ├── environment.html   # Environmental sensors
│   ├── health.html        # Device health
│   └── logs.html          # System logs
├── static/                # Static assets
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── hooks/                 # React hooks
├── lib/                   # Utility functions
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
├── mock-data.json         # Sample data for seeding
└── dashboard.db           # SQLite database (auto-generated)
```

## 🔧 Configuration

### Database
The SQLite database is automatically created at `dashboard.db` in the project root. To reset the database, simply delete this file and restart the Flask application.

### Raspberry Pi Camera Stream
The system is configured to stream video from a Raspberry Pi via direct IP connection. To configure the stream URL:

**Option 1: Environment Variable (Recommended)**
```bash
# Windows PowerShell
$env:PI_STREAM_URL="http://172.16.96.90:8000/video_feed"

# Windows CMD
set PI_STREAM_URL=http://172.16.96.90:8000/video_feed

# Linux/Mac
export PI_STREAM_URL="http://172.16.96.90:8000/video_feed"
```

**Option 2: Edit app.py directly**
Update the IP address in `app.py` line 25 with your Raspberry Pi's IP address:
```python
PI_STREAM_URL = os.environ.get('PI_STREAM_URL', 'http://172.16.96.90:8000/video_feed')
```

**Note**: 
- The stream endpoint expects MJPEG format (`multipart/x-mixed-replace`)
- Make sure your Raspberry Pi is accessible on the same network at the configured IP address
- The default IP `172.16.96.90:8000` should be updated to match your Raspberry Pi's actual IP address

### Mock Data
Sample data can be loaded via:
- Automatic loading on first run (if database is empty)
- Manual seeding via `POST /api/seed` endpoint
- Using the "Generate test data" link on the homepage

## 🛠️ Development

### Backend Development
- The Flask app runs in debug mode by default
- Database migrations are handled automatically via SQLAlchemy
- API endpoints return JSON responses

### Frontend Development
- Uses Next.js App Router
- TypeScript support enabled
- Hot module replacement (HMR) enabled in development

## 📝 Notes

- The system is designed for underwater/marine monitoring applications
- Camera streaming uses MJPEG format for real-time video
- All timestamps are stored in UTC
- Mock data timestamps are automatically adjusted to be recent (within last 2 hours)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

[Specify your license here]

## 👥 Authors

[Your name/team]

---

**AQUA Monitor** - Monitoring the depths, one detection at a time 🌊

