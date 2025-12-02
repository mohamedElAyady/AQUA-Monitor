from flask import Flask, render_template, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
import os
import json
import cv2
import threading
import base64
import numpy as np
import requests
import time

app = Flask(__name__)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "dashboard.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Raspberry Pi Stream Configuration
# Set PI_STREAM_URL environment variable or use default direct IP
PI_STREAM_URL = os.environ.get('PI_STREAM_URL', 'http://172.16.96.90:8000/video_feed')

# Models
class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, default=1)
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    x = db.Column(db.Float)  # Heatmap coordinates
    y = db.Column(db.Float)

    def to_dict(self):
        return {
            'id': self.id,
            'species': self.species,
            'count': self.count,
            'confidence': round(self.confidence, 2) if self.confidence else 0,
            'timestamp': self.timestamp.isoformat(),
            'x': self.x,
            'y': self.y
        }

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)  # Water temperature
    humidity = db.Column(db.Float)  # Internal humidity
    pressure = db.Column(db.Float)
    depth = db.Column(db.Float)
    turbidity = db.Column(db.Float)  # Water clarity
    lux = db.Column(db.Float)  # Light intensity
    ph = db.Column(db.Float)
    salinity = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'depth': self.depth,
            'turbidity': self.turbidity,
            'lux': self.lux,
            'ph': self.ph,
            'salinity': self.salinity,
            'timestamp': self.timestamp.isoformat()
        }

class DeviceHealth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cpu_temp = db.Column(db.Float)
    gpu_temp = db.Column(db.Float)
    battery_level = db.Column(db.Float)
    fan_status = db.Column(db.String(50))
    storage_used = db.Column(db.Float)  # Percentage
    connectivity = db.Column(db.String(50))
    yolo_fps = db.Column(db.Float)
    model_name = db.Column(db.String(100))
    cpu_usage = db.Column(db.Float)
    gpu_usage = db.Column(db.Float)
    ram_usage = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'cpu_temp': self.cpu_temp,
            'gpu_temp': self.gpu_temp,
            'battery_level': self.battery_level,
            'fan_status': self.fan_status,
            'storage_used': self.storage_used,
            'connectivity': self.connectivity,
            'yolo_fps': self.yolo_fps,
            'model_name': self.model_name,
            'cpu_usage': self.cpu_usage,
            'gpu_usage': self.gpu_usage,
            'ram_usage': self.ram_usage,
            'timestamp': self.timestamp.isoformat()
        }

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)  # detection, sensor, alert, etc
    message = db.Column(db.Text)
    severity = db.Column(db.String(20))  # info, warning, error
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'message': self.message,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat()
        }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/overview')
def overview():
    # Get all detections (no date filtering)
    all_detections = Detection.query.order_by(Detection.timestamp.desc()).all()
    
    # Get latest readings
    latest_sensor = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()
    latest_health = DeviceHealth.query.order_by(DeviceHealth.timestamp.desc()).first()
    
    # Species count (from all detections)
    species_counts = {}
    for det in all_detections:
        species_counts[det.species] = species_counts.get(det.species, 0) + det.count
    
    return render_template('overview.html', 
                         detections=all_detections[:10],  # Latest 10
                         species_counts=species_counts,
                         latest_sensor=latest_sensor,
                         latest_health=latest_health)

@app.route('/camera')
def camera():
    return render_template('camera.html', pi_stream_url=PI_STREAM_URL)

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/environment')
def environment():
    return render_template('environment.html')

@app.route('/health')
def health():
    return render_template('health.html')

@app.route('/logs')
def logs():
    logs = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
    return render_template('logs.html', logs=logs)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    # Return all logs, ordered by most recent first
    logs = Log.query.order_by(Log.timestamp.desc()).all()
    return jsonify([log.to_dict() for log in logs])

# API Routes
@app.route('/api/detections', methods=['GET'])
def get_detections():
    # Return all detections, no time filtering
    detections = Detection.query.order_by(Detection.timestamp.asc()).all()
    return jsonify([d.to_dict() for d in detections])

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    # Return all sensor readings, no time filtering
    sensors = SensorReading.query.order_by(SensorReading.timestamp.asc()).all()
    return jsonify([s.to_dict() for s in sensors])

@app.route('/api/health', methods=['GET'])
def get_health():
    # Return all device health records, no time filtering
    health = DeviceHealth.query.order_by(DeviceHealth.timestamp.asc()).all()
    return jsonify([h.to_dict() for h in health])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    # Return stats for all data, not just today
    total_detections = Detection.query.count()
    
    latest_sensor = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()
    latest_health = DeviceHealth.query.order_by(DeviceHealth.timestamp.desc()).first()
    
    return jsonify({
        'total_detections': total_detections,
        'latest_sensor': latest_sensor.to_dict() if latest_sensor else None,
        'latest_health': latest_health.to_dict() if latest_health else None
    })

# Camera and Location Routes
@app.route('/api/camera/location', methods=['GET'])
def get_camera_location():
    """Return the camera's ocean location coordinates"""
    # Example: Great Barrier Reef, Australia
    location = {
        'latitude': -18.2871,
        'longitude': 147.6992,
        'name': 'Great Barrier Reef',
        'depth': 12.5,  # meters
        'region': 'Coral Sea, Australia'
    }
    return jsonify(location)

@app.route('/api/camera/frame', methods=['POST'])
def capture_frame():
    """Save captured frame data"""
    try:
        data = request.json
        frame_number = data.get('frame_number', 0)
        detections = data.get('detections', [])
        
        # Save detections to database
        for det in detections:
            detection = Detection(
                species=det.get('species', 'Unknown'),
                count=1,
                confidence=det.get('confidence', 0.0),
                timestamp=datetime.utcnow(),
                x=det.get('x', 0),
                y=det.get('y', 0)
            )
            db.session.add(detection)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Frame {frame_number} captured with {len(detections)} detections',
            'frame_number': frame_number,
            'detections_count': len(detections)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Camera streaming from Raspberry Pi
camera_lock = threading.Lock()
camera_active = False

def generate_frames():
    """Proxy frames from Raspberry Pi stream via direct IP"""
    global camera_active
    
    while camera_active:
        try:
            r = requests.get(PI_STREAM_URL, timeout=2)
            frame = r.content
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except:
            time.sleep(0.2)

@app.route('/api/camera/stream')
@app.route('/video_feed')
def camera_stream():
    """Stream camera feed from Raspberry Pi"""
    global camera_active
    camera_active = True
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """Stop camera stream"""
    global camera_active
    camera_active = False
    return jsonify({'status': 'success', 'message': 'Camera stopped'})

# Seed data for development
@app.route('/api/seed', methods=['POST'])
def seed_database():
    """Populate database with mock data from mock-data.json"""
    try:
        # Clear existing data
        db.session.query(Detection).delete()
        db.session.query(SensorReading).delete()
        db.session.query(DeviceHealth).delete()
        db.session.query(Log).delete()
        
        # Load mock data from JSON file
        mock_data_path = os.path.join(basedir, 'mock-data.json')
        with open(mock_data_path, 'r') as f:
            mock_data = json.load(f)
        
        # Helper function to parse ISO timestamp
        def parse_timestamp(ts_str):
            # Remove 'Z' and parse ISO format
            ts_str = ts_str.replace('Z', '')
            # Handle microseconds if present
            if '.' in ts_str:
                dt_str, micro = ts_str.split('.')
                micro = micro[:6]  # Limit to 6 digits
                return datetime.strptime(f"{dt_str}.{micro}", "%Y-%m-%dT%H:%M:%S.%f")
            else:
                return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
        
        # Find the most recent timestamp in mock data to calculate offset
        all_timestamps = []
        for det_data in mock_data.get('detections', []):
            all_timestamps.append(parse_timestamp(det_data['timestamp']))
        for sensor_data in mock_data.get('sensor_readings', []):
            all_timestamps.append(parse_timestamp(sensor_data['timestamp']))
        for health_data in mock_data.get('device_health', []):
            all_timestamps.append(parse_timestamp(health_data['timestamp']))
        for log_data in mock_data.get('logs', []):
            all_timestamps.append(parse_timestamp(log_data['timestamp']))
        
        if all_timestamps:
            # Find the most recent timestamp in mock data
            max_mock_time = max(all_timestamps)
            # Calculate offset to make it recent (within last 2 hours)
            now = datetime.utcnow()
            time_offset = now - max_mock_time - timedelta(hours=2)
        else:
            time_offset = timedelta(0)
        
        # Helper function to adjust timestamp to be recent
        def adjust_timestamp(ts_str):
            parsed = parse_timestamp(ts_str)
            return parsed + time_offset
        
        # Add detection data
        for det_data in mock_data.get('detections', []):
            det = Detection(
                species=det_data['species'],
                count=det_data['count'],
                confidence=det_data['confidence'],
                timestamp=adjust_timestamp(det_data['timestamp']),
                x=det_data['x'],
                y=det_data['y']
            )
            db.session.add(det)
        
        # Add sensor data
        for sensor_data in mock_data.get('sensor_readings', []):
            sensor = SensorReading(
                temperature=sensor_data['temperature'],
                humidity=sensor_data['humidity'],
                pressure=sensor_data['pressure'],
                depth=sensor_data['depth'],
                turbidity=sensor_data['turbidity'],
                lux=sensor_data['lux'],
                ph=sensor_data['ph'],
                salinity=sensor_data['salinity'],
                timestamp=adjust_timestamp(sensor_data['timestamp'])
            )
            db.session.add(sensor)
        
        # Add device health data
        for health_data in mock_data.get('device_health', []):
            health = DeviceHealth(
                cpu_temp=health_data['cpu_temp'],
                gpu_temp=health_data['gpu_temp'],
                battery_level=health_data['battery_level'],
                fan_status=health_data['fan_status'],
                storage_used=health_data['storage_used'],
                connectivity=health_data['connectivity'],
                yolo_fps=health_data['yolo_fps'],
                model_name=health_data['model_name'],
                cpu_usage=health_data['cpu_usage'],
                gpu_usage=health_data['gpu_usage'],
                ram_usage=health_data['ram_usage'],
                timestamp=adjust_timestamp(health_data['timestamp'])
            )
            db.session.add(health)
        
        # Add logs
        for log_data in mock_data.get('logs', []):
            log = Log(
                event_type=log_data['event_type'],
                message=log_data['message'],
                severity=log_data['severity'],
                timestamp=adjust_timestamp(log_data['timestamp'])
            )
            db.session.add(log)
        
        db.session.commit()
        return jsonify({
            'status': 'success', 
            'message': f'Database seeded with {len(mock_data.get("detections", []))} detections, {len(mock_data.get("sensor_readings", []))} sensor readings, {len(mock_data.get("device_health", []))} health records, and {len(mock_data.get("logs", []))} logs'
        }), 201
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'mock-data.json file not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def load_mock_data_if_empty():
    """Automatically load mock data if database is empty"""
    with app.app_context():
        if Detection.query.count() == 0:
            try:
                mock_data_path = os.path.join(basedir, 'mock-data.json')
                with open(mock_data_path, 'r') as f:
                    mock_data = json.load(f)
                
                def parse_timestamp(ts_str):
                    ts_str = ts_str.replace('Z', '')
                    if '.' in ts_str:
                        dt_str, micro = ts_str.split('.')
                        micro = micro[:6]
                        return datetime.strptime(f"{dt_str}.{micro}", "%Y-%m-%dT%H:%M:%S.%f")
                    else:
                        return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
                
                # Find the most recent timestamp in mock data to calculate offset
                all_timestamps = []
                for det_data in mock_data.get('detections', []):
                    all_timestamps.append(parse_timestamp(det_data['timestamp']))
                for sensor_data in mock_data.get('sensor_readings', []):
                    all_timestamps.append(parse_timestamp(sensor_data['timestamp']))
                for health_data in mock_data.get('device_health', []):
                    all_timestamps.append(parse_timestamp(health_data['timestamp']))
                for log_data in mock_data.get('logs', []):
                    all_timestamps.append(parse_timestamp(log_data['timestamp']))
                
                if all_timestamps:
                    # Find the most recent timestamp in mock data
                    max_mock_time = max(all_timestamps)
                    # Calculate offset to make it recent (within last 2 hours)
                    now = datetime.utcnow()
                    time_offset = now - max_mock_time - timedelta(hours=2)
                else:
                    time_offset = timedelta(0)
                
                # Helper function to adjust timestamp to be recent
                def adjust_timestamp(ts_str):
                    parsed = parse_timestamp(ts_str)
                    return parsed + time_offset
                
                # Add detections
                for det_data in mock_data.get('detections', []):
                    det = Detection(
                        species=det_data['species'],
                        count=det_data['count'],
                        confidence=det_data['confidence'],
                        timestamp=adjust_timestamp(det_data['timestamp']),
                        x=det_data['x'],
                        y=det_data['y']
                    )
                    db.session.add(det)
                
                # Add sensors
                for sensor_data in mock_data.get('sensor_readings', []):
                    sensor = SensorReading(
                        temperature=sensor_data['temperature'],
                        humidity=sensor_data['humidity'],
                        pressure=sensor_data['pressure'],
                        depth=sensor_data['depth'],
                        turbidity=sensor_data['turbidity'],
                        lux=sensor_data['lux'],
                        ph=sensor_data['ph'],
                        salinity=sensor_data['salinity'],
                        timestamp=adjust_timestamp(sensor_data['timestamp'])
                    )
                    db.session.add(sensor)
                
                # Add health
                for health_data in mock_data.get('device_health', []):
                    health = DeviceHealth(
                        cpu_temp=health_data['cpu_temp'],
                        gpu_temp=health_data['gpu_temp'],
                        battery_level=health_data['battery_level'],
                        fan_status=health_data['fan_status'],
                        storage_used=health_data['storage_used'],
                        connectivity=health_data['connectivity'],
                        yolo_fps=health_data['yolo_fps'],
                        model_name=health_data['model_name'],
                        cpu_usage=health_data['cpu_usage'],
                        gpu_usage=health_data['gpu_usage'],
                        ram_usage=health_data['ram_usage'],
                        timestamp=adjust_timestamp(health_data['timestamp'])
                    )
                    db.session.add(health)
                
                # Add logs
                for log_data in mock_data.get('logs', []):
                    log = Log(
                        event_type=log_data['event_type'],
                        message=log_data['message'],
                        severity=log_data['severity'],
                        timestamp=adjust_timestamp(log_data['timestamp'])
                    )
                    db.session.add(log)
                
                db.session.commit()
                print("✓ Mock data loaded automatically (database was empty)")
            except FileNotFoundError:
                print("⚠ mock-data.json not found - skipping auto-load")
            except Exception as e:
                print(f"⚠ Error loading mock data: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_mock_data_if_empty()
    app.run(debug=True)
