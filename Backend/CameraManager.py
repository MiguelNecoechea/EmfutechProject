import cv2
import threading
import time
import multiprocessing

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
        self._shutdown = False

    def _update_frame_loop(self):
        """Continuously update the shared frame in a separate thread."""
        while self._running and not self._shutdown:
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
        if self._shutdown:
            return False

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
        print(f"Unregistering camera user: {user_id}")
        with self._camera_lock:
            if user_id in self._users:
                self._users.remove(user_id)
                print(f"Current users after removal: {self._users}")
                
                if not self._users:  # If this was the last user
                    print("No more users, cleaning up camera...")
                    self._running = False
                    
                    # Stop the update thread
                    if self._update_thread and self._update_thread.is_alive():
                        print("Stopping update thread...")
                        self._update_thread.join(timeout=1.0)
                        self._update_thread = None
                        print("Update thread stopped")
                    
                    # Release camera with multiple attempts
                    if self._camera:
                        print("Releasing camera...")
                        try:
                            # First attempt: normal release
                            self._camera.release()
                            
                            # Second attempt: force release if still open
                            if self._camera.isOpened():
                                print("Camera still open, forcing release...")
                                for _ in range(3):  # Try up to 3 times
                                    self._camera.release()
                                    if not self._camera.isOpened():
                                        break
                                    time.sleep(0.1)
                            
                            # Final check
                            if self._camera.isOpened():
                                print("Warning: Camera may still be open")
                            else:
                                print("Camera successfully released")
                                
                        except Exception as e:
                            print(f"Error during camera release: {e}")
                        finally:
                            # Force delete the camera object
                            self._camera = None
                            # Try to force garbage collection
                            import gc
                            gc.collect()
                    
                    # Clear frame
                    with self._frame_lock:
                        self._frame = None
                    
                    # Cleanup OpenCV windows
                    cv2.destroyAllWindows()

    def get_frame(self):
        """
        Get the latest frame from the shared frame buffer.
        
        Returns:
            numpy.ndarray or None: Copy of the current frame if available
        """
        if self._shutdown:
            return None

        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None

    def cleanup_camera(self):
        """Clean up camera resources."""
        print("Starting CameraManager cleanup_camera...")
        self._running = False
        
        # Stop the update thread
        if self._update_thread and self._update_thread.is_alive():
            print("Stopping update thread...")
            self._update_thread.join(timeout=1.0)
            self._update_thread = None
            print("Update thread stopped")
            
        # Release camera with multiple attempts
        if self._camera:
            print("Releasing camera...")
            try:
                # First attempt: normal release
                self._camera.release()
                
                # Second attempt: force release if still open
                if self._camera.isOpened():
                    print("Camera still open, forcing release...")
                    for _ in range(3):  # Try up to 3 times
                        self._camera.release()
                        if not self._camera.isOpened():
                            break
                        time.sleep(0.1)
                
                # Final check
                if self._camera.isOpened():
                    print("Warning: Camera may still be open")
                else:
                    print("Camera successfully released")
                    
            except Exception as e:
                print(f"Error during camera release: {e}")
            finally:
                # Force delete the camera object
                self._camera = None
                # Try to force garbage collection
                import gc
                gc.collect()
            
        # Clear frame
        with self._frame_lock:
            print("Clearing frame buffer...")
            self._frame = None
            print("Frame buffer cleared")
            
        # Cleanup OpenCV windows
        print("Destroying OpenCV windows...")
        cv2.destroyAllWindows()
        # Force window cleanup
        for _ in range(5):
            cv2.waitKey(1)
        print(f"Current users before clearing: {self._users}")
        self._users.clear()
        print("Users cleared")

    def is_camera_open(self) -> bool:
        """Check if camera is currently open and operational."""
        return self._camera is not None and self._camera.isOpened()

    def get_user_count(self) -> int:
        """Get the current number of registered users."""
        return len(self._users)

    def shutdown(self):
        """Shutdown the camera manager completely."""
        print("Starting CameraManager shutdown...")
        self._shutdown = True
        self.cleanup_camera()
        
        # Clean up multiprocessing resources
        try:
            print("Final multiprocessing cleanup in CameraManager shutdown...")
            import multiprocessing
            
            # Access trackers through main module
            if hasattr(multiprocessing, '_resource_tracker'):
                tracker = getattr(multiprocessing._resource_tracker, '_resource_tracker', None)
                if tracker:
                    tracker._cleanup()
                    
            if hasattr(multiprocessing, '_semaphore_tracker'):
                tracker = getattr(multiprocessing._semaphore_tracker, '_semaphore_tracker', None)
                if tracker:
                    tracker._cleanup()
                    
        except Exception as e:
            print(f"Error in final multiprocessing cleanup: {str(e)}")
        print("CameraManager shutdown complete")

    def __del__(self):
        """Ensure cleanup is called when the object is deleted."""
        if not self._shutdown:  # Only call shutdown if it hasn't been called already
            print("CameraManager.__del__ calling shutdown")
            self.shutdown() 