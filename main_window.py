import sys
import cv2
import uuid
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QTabWidget, QTextEdit)
from PySide6.QtGui import QPixmap, QImage, Qt
from PySide6.QtCore import QTimer, QThread, Signal
from detector import FaceDetector
from database import FaceDetectionDB

class CameraWorker(QThread):
    frame_ready = Signal(object)
    
    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self.is_running = True
        self.cap = None
    
    def run(self):
        """Capture frames from camera"""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                faces, annotated, face_data = self.detector.detect_faces(frame)
                self.frame_ready.emit({
                    'frame': annotated,
                    'faces': faces,
                    'face_data': face_data
                })
            else:
                self.is_running = False
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.wait()

class FaceDetectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.detector = FaceDetector()
        self.db = FaceDetectionDB()
        self.session_id = str(uuid.uuid4())
        self.is_running = False
        self.frame_count = 0
        self.detection_history = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Face Detection System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left side - Camera feed
        left_layout = QVBoxLayout()
        
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(800, 600)
        self.camera_label.setStyleSheet("border: 2px solid #444; background-color: #000;")
        left_layout.addWidget(self.camera_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("START DETECTION")
        self.start_btn.setStyleSheet("background-color: #00AA00; color: white; font-weight: bold; padding: 10px;")
        self.start_btn.clicked.connect(self.start_detection)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("STOP DETECTION")
        self.stop_btn.setStyleSheet("background-color: #AA0000; color: white; font-weight: bold; padding: 10px;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_detection)
        button_layout.addWidget(self.stop_btn)
        
        left_layout.addLayout(button_layout)
        
        # Right side - Statistics
        right_layout = QVBoxLayout()
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Stats tab
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("background-color: #1e1e1e; color: #00FF00; font-family: monospace;")
        stats_layout.addWidget(self.stats_text)
        stats_widget.setLayout(stats_layout)
        
        # History tab
        history_widget = QWidget()
        history_layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("background-color: #1e1e1e; color: #00FF00; font-family: monospace;")
        history_layout.addWidget(self.history_text)
        history_widget.setLayout(history_layout)
        
        self.tabs.addTab(stats_widget, "Statistics")
        self.tabs.addTab(history_widget, "History")
        
        right_layout.addWidget(self.tabs)
        
        # Add left and right to main
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        central.setLayout(main_layout)
        
        # Timer for updating UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        
        # Camera worker
        self.camera_worker = None
    
    def start_detection(self):
        """Start face detection"""
        self.is_running = True
        self.frame_count = 0
        self.detection_history = []
        self.session_id = str(uuid.uuid4())
        self.db.start_session(self.session_id)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Start camera worker
        self.camera_worker = CameraWorker(self.detector)
        self.camera_worker.frame_ready.connect(self.on_frame_ready)
        self.camera_worker.start()
        
        self.update_timer.start(100)
        
        self.stats_text.setText("🟢 Detection started...\n")
    
    def on_frame_ready(self, data):
        """Handle frame from camera"""
        frame = data['frame']
        faces = data['faces']
        
        # Convert frame to QPixmap
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = 3 * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale to fit label
        scaled = pixmap.scaledToWidth(800, Qt.SmoothTransformation)
        self.camera_label.setPixmap(scaled)
        
        # Store detection
        face_count = len(faces)
        avg_conf = sum([f.det_score for f in faces]) / face_count if faces else 0
        
        self.detection_history.append({
            'time': datetime.now(),
            'face_count': face_count,
            'avg_confidence': avg_conf
        })
        
        # Log to database
        if self.frame_count % 30 == 0:  # Log every 30 frames
            self.db.log_detection(face_count, avg_conf, self.session_id)
        
        self.frame_count += 1
    
    def update_ui(self):
        """Update statistics UI"""
        if not self.is_running:
            return
        
        # Get current stats
        stats = self.detector.get_stats()
        
        # Format stats text
        stats_text = f"""
╔════════════════════════════════╗
║   FACE DETECTION STATISTICS    ║
╚════════════════════════════════╝

📊 LIVE STATISTICS:
   • Current Faces: {stats['current_faces']}
   • FPS: {stats['fps']}
   • Frames Processed: {self.frame_count}

📈 SESSION STATISTICS:
   • Total Detections: {stats['total_detections']}
   • Average Faces: {stats['average_faces']:.2f}
   • Max Faces: {stats['max_faces']}

⏱️ SESSION INFO:
   • Session ID: {self.session_id[:8]}...
   • Duration: {datetime.now().strftime('%H:%M:%S')}
   • Status: 🟢 RUNNING
"""
        self.stats_text.setText(stats_text)
        
        # Update history
        if self.detection_history:
            history_text = "📝 RECENT DETECTIONS (Last 10):\n\n"
            for detection in self.detection_history[-10:]:
                history_text += f"[{detection['time'].strftime('%H:%M:%S')}] Faces: {detection['face_count']}, Conf: {detection['avg_confidence']:.2f}\n"
            self.history_text.setText(history_text)
    
    def stop_detection(self):
        """Stop face detection"""
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.update_timer.stop()
        
        if self.camera_worker:
            self.camera_worker.stop()
        
        # End session
        self.db.end_session(self.session_id, len(self.detection_history))
        
        # Final stats
        final_stats = self.db.get_session_stats(self.session_id)
        
        final_text = f"""
╔════════════════════════════════╗
║   SESSION COMPLETED            ║
╚════════════════════════════════╝

📊 FINAL STATISTICS:
   • Total Detections: {final_stats['detections']}
   • Average Faces: {final_stats['avg_faces']:.2f}
   • Maximum Faces: {final_stats['max_faces']}
   • Total Frames: {self.frame_count}

⏱️ SESSION:
   • Session ID: {self.session_id[:8]}...
   • Status: 🔴 STOPPED

✅ Data saved to database!
"""
        self.stats_text.setText(final_text)
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.is_running:
            self.stop_detection()
        event.accept()

def main():
    app = QApplication([])
    window = FaceDetectionApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    main()
