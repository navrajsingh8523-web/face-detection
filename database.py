import sqlite3
import os
from datetime import datetime

class FaceDetectionDB:
    def __init__(self, db_path="face_detection.db"):
        """Initialize database"""
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self):
        """Create necessary tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Detection logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                face_count INTEGER,
                avg_confidence REAL,
                session_id TEXT
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                start_time DATETIME,
                end_time DATETIME,
                total_detections INTEGER,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_session(self, session_id):
        """Start a new detection session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (id, start_time)
            VALUES (?, ?)
        ''', (session_id, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def log_detection(self, face_count, avg_confidence, session_id):
        """Log a face detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO detections (face_count, avg_confidence, session_id)
            VALUES (?, ?, ?)
        ''', (face_count, avg_confidence, session_id))
        
        conn.commit()
        conn.close()
    
    def end_session(self, session_id, total_detections):
        """End a detection session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions
            SET end_time = ?, total_detections = ?
            WHERE id = ?
        ''', (datetime.now(), total_detections, session_id))
        
        conn.commit()
        conn.close()
    
    def get_session_stats(self, session_id):
        """Get statistics for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*), AVG(face_count), MAX(face_count)
            FROM detections
            WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == 0:
            return {'detections': 0, 'avg_faces': 0, 'max_faces': 0}
        
        return {
            'detections': result[0],
            'avg_faces': result[1],
            'max_faces': result[2]
        }
    
    def get_all_sessions(self):
        """Get all sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions ORDER BY start_time DESC')
        sessions = cursor.fetchall()
        conn.close()
        
        return sessions
    
    def clear_old_data(self, days=30):
        """Clear detection data older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM detections
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        conn.commit()
        conn.close()
