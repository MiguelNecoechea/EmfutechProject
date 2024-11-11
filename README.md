# Project Overview

This project is a comprehensive application that integrates eye tracking, emotion recognition, and data collection functionalities. It is designed to work with both frontend and backend components, facilitating real-time data processing and user interaction.

## Dependencies and Libraries

### Frontend
- HTML5
- CSS3
- Node.js v20.18.0
- Tailwind CSS (version not specified)
- Electron v28.0.0
- Eel v0.17.0
- Bootstrap v5.3.2

### Backend
- dlib 19.24.6
- mne-base 1.8.0
- mne-lsl 1.6.0
- deepface 0.0.93
- TensorFlow 2.17.0
- OpenCV-Python 4.10.0.84
- dxcam 0.0.5
- pandas 2.2.3
- NumPy 1.26.4
- Pynput 1.7.7

### Backend and Frontend Communication
- Eel
- bottle-websocket
- gevent

### Languages
- Python 3.11.5
- C++ 17

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

## Running the Application


`1`. **Launch the Electron app:**
   ```bash
   npm run start
   ```

## Acknowledgments

Special thanks to Sergey Kuldin for the development of LaserGaze.