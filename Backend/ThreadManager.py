from threading import Thread, Event
from typing import Dict, Optional
import logging

class ThreadManager:
    """
    A class to manage multiple threads with stop events.
    Provides functionality to add, start, stop and monitor threads safely.
    """
    def __init__(self):
        """
        Initialize the ThreadManager with empty thread and stop event dictionaries.
        Sets up basic logging configuration.
        """
        self.threads: Dict[str, Thread] = {}
        self.stop_events: Dict[str, Event] = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def add_thread(self, name: str, target, args=()) -> None:
        """
        Add a new thread with an associated stop event.

        Args:
            name (str): Unique name identifier for the thread
            target: Function to be run in the thread
            args (tuple): Arguments to pass to the target function (default: empty tuple)

        Returns:
            None
        """
        if name in self.threads and self.threads[name].is_alive():
            self.logger.warning(f"Thread {name} already exists and running")
            return

        stop_event = Event()
        thread = Thread(
            target=self._wrap_target,
            args=(target, stop_event) + args,
            name=name,
            daemon=True
        )
        
        self.threads[name] = thread
        self.stop_events[name] = stop_event
        self.logger.info(f"Thread {name} added")

    def _wrap_target(self, target, stop_event, *args):
        """
        Internal wrapper function to handle thread execution and cleanup.

        Args:
            target: The function to run in the thread
            stop_event: Event object to signal thread termination
            *args: Variable arguments to pass to the target function

        Returns:
            None
        """
        try:
            target(stop_event, *args)
        except Exception as e:
            self.logger.error(f"Thread error: {e}")
        finally:
            self.logger.info(f"Thread {Thread.current_thread().name} finished")

    def start_thread(self, name: str) -> bool:
        """
        Start a specific thread by name.

        Args:
            name (str): Name of the thread to start

        Returns:
            bool: True if thread was started successfully, False otherwise
        """
        if name in self.threads:
            if not self.threads[name].is_alive():
                self.threads[name].start()
                self.logger.info(f"Thread {name} started")
                return True
            else:
                self.logger.warning(f"Thread {name} already running")
        return False

    def stop_thread(self, name: str, timeout: float = 2.0) -> bool:
        """
        Stop a specific thread by name.

        Args:
            name (str): Name of the thread to stop
            timeout (float): Maximum time to wait for thread termination in seconds (default: 2.0)

        Returns:
            bool: True if thread was stopped successfully, False otherwise
        """
        if name in self.stop_events:
            self.stop_events[name].set()
            if name in self.threads and self.threads[name].is_alive():
                self.threads[name].join(timeout)
                if self.threads[name].is_alive():
                    self.logger.error(f"Thread {name} failed to stop")
                    return False
            self.logger.info(f"Thread {name} stopped")
            return True
        return False

    def stop_all_threads(self, timeout: float = 2.0) -> bool:
        """
        Stop all running threads.

        Args:
            timeout (float): Maximum time to wait for each thread termination in seconds (default: 2.0)

        Returns:
            bool: True if all threads were stopped successfully, False if any thread failed to stop
        """
        success = True
        for name in list(self.threads.keys()):
            if not self.stop_thread(name, timeout):
                success = False
        return success

    def is_thread_running(self, name: str) -> bool:
        """
        Check if a specific thread is currently running.

        Args:
            name (str): Name of the thread to check

        Returns:
            bool: True if the thread exists and is running, False otherwise
        """
        return name in self.threads and self.threads[name].is_alive() 