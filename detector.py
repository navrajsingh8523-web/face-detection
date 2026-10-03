import cv2
import numpy as np
from insightface.app import FaceAnalysis
import time

class FaceDetector:
    def __init__(self):
        """Initialize face detector with InsightFace"""
        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUProvider'])
        self.app.prepare(ctx_id=0, det_thresh=0.5)
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()
        self.face_count_history = []
        
    def detect_faces(self, frame):
        """
        Detect faces in a frame
        Returns: faces, annotated_frame
        """
        # Resize frame for faster processing
        height, width = frame.shape[:2]
        scale = 1.0 if width < 1280 else 1280 / width
        
        if scale != 1.0:
            frame_resized = cv2.resize(frame, (int(width * scale), int(height * scale)))
        else:
            frame_resized = frame
        
        # Detect faces
        faces = self.app.get(frame_resized)
        
        # Draw bounding boxes
        annotated = frame.copy()
        face_data = []
        
        for face in faces:
            bbox = face.bbox.astype(int)
            # Scale back if resized
            if scale != 1.0:
                bbox = (bbox / scale).astype(int)
            
            x1, y1, x2, y2 = bbox
            
            # Draw rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Get confidence
            confidence = face.det_score
            
            # Draw confidence text
            text = f"Conf: {confidence:.2f}"
            cv2.putText(annotated, text, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            face_data.append({
                'bbox': bbox,
                'confidence': confidence
            })
        
        # Update FPS
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        
        # Draw FPS
        cv2.putText(annotated, f"FPS: {self.fps}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw face count
        face_count = len(faces)
        cv2.putText(annotated, f"Faces: {face_count}", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        self.face_count_history.append(face_count)
        
        return faces, annotated, face_data
    
    def get_stats(self):
        """Get detection statistics"""
        if not self.face_count_history:
            return {
                'total_detections': 0,
                'current_faces': 0,
                'average_faces': 0,
                'max_faces': 0,
                'fps': self.fps
            }
        
        return {
            'total_detections': len(self.face_count_history),
            'current_faces': self.face_count_history[-1],
            'average_faces': np.mean(self.face_count_history),
            'max_faces': np.max(self.face_count_history),
            'fps': self.fps
        }
