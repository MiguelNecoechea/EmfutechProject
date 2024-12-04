import cv2
import threading
import time

class CameraManager:
    """
    Thread-safe singleton camera manager for OpenCV camera operations.
    Handles camera access and frame sharing across multiple consumers.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._camera = None
        self._camera_lock = threading.Lock()
        self._frame = None
        self._frame_lock = threading.Lock()
        self._users = set()
        self._update_thread = None
        self._running = False
        self._initialized = True

    def _update_frame_loop(self):
        """Continuously update the shared frame in a separate thread."""
        while self._running:
            if self._camera and self._camera.isOpened():
                ret, frame = self._camera.read()
                if ret:
                    with self._frame_lock:
                        self._frame = frame.copy()
            time.sleep(0.033)  # ~30 FPS

    def register_user(self, user_id: str) -> bool:
        """
        Register a new camera user and start the camera if needed.
        
        Args:
            user_id: Unique identifier for the camera user
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        with self._camera_lock:
            try:
                if not self._camera or not self._camera.isOpened():
                    self._camera = cv2.VideoCapture(0)
                    if not self._camera.isOpened():
                        raise Exception("Could not open camera")
                    self._running = True
                    self._update_thread = threading.Thread(
                        target=self._update_frame_loop, 
                        daemon=True
                    )
                    self._update_thread.start()
                
                self._users.add(user_id)
                return True
            except Exception as e:
                print(f"Error registering camera user: {e}")
                self.cleanup_camera()
                return False

    def unregister_user(self, user_id: str):
        """
        Unregister a camera user and cleanup if no users remain.
        
        Args:
            user_id: Unique identifier for the camera user
        """
        with self._camera_lock:
            if user_id in self._users:
                self._users.remove(user_id)
                
            if not self._users:
                self.cleanup_camera()

    def get_frame(self):
        """
        Get the latest frame from the shared frame buffer.
        
        Returns:
            numpy.ndarray or None: Copy of the current frame if available
        """
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None

    def cleanup_camera(self):
        """Clean up camera resources."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=1.0)
            self._update_thread = None
            
        if self._camera:
            self._camera.release()
            self._camera = None
            
        with self._frame_lock:
            self._frame = None
            
        cv2.destroyAllWindows()
        self._users.clear()

    def is_camera_open(self) -> bool:
        """Check if camera is currently open and operational."""
        return self._camera is not None and self._camera.isOpened()

    def get_user_count(self) -> int:
        """Get the current number of registered users."""
        return len(self._users)

    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup_camera() 