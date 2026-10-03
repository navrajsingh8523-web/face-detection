#!/usr/bin/env python3
"""
Face Detection System
Main entry point to run the application
"""

import sys
from main_window import FaceDetectionApp
from PySide6.QtWidgets import QApplication

def main():
    """Main function to run the app"""
    app = QApplication(sys.argv)
    
    # Set app style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = FaceDetectionApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
