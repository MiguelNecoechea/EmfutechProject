import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from multiprocessing import Pool, cpu_count
from DataProcessing.ffmpegPostProcessing import post_process_video

class GazeHeatmapProcessor:
    @staticmethod
    def process_video(video_file: str, csv_file: str, output_file: str, batch_size: int = 16):
        # Create a temporary output file for OpenCV
        temp_output = output_file + '.temp.mp4'
        
        print("---> Heatmap process started <----")
        
        # Check for GPU availability
        use_gpu = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if use_gpu:
            print("GPU acceleration enabled")
        else:
            print(f"Running on CPU with {cpu_count()} cores")

        # Read gaze data from CSV
        gaze_data = GazeHeatmapProcessor._read_gaze_data(csv_file)

        # Load and validate video
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            print("Error: Unable to open the video file.")
            return

        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate milliseconds per frame
        ms_per_frame = 1000 / fps

        # Use temp file for OpenCV output
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (frame_width, frame_height))

        # Initialize heatmap
        heatmap = np.zeros((frame_height, frame_width), dtype=np.float32)
        if use_gpu:
            gpu_heatmap = cv2.cuda_GpuMat(frame_height, frame_width, cv2.CV_32F)
            gpu_frame = cv2.cuda_GpuMat()
            gpu_heatmap_colored = cv2.cuda_GpuMat()
            gpu_overlay = cv2.cuda_GpuMat()
            gpu_stream = cv2.cuda_Stream()
            
            # Initialize GPU heatmap with zeros
            gpu_heatmap.upload(heatmap)

        decay_rate = 0.9

        frames = []
        heatmaps = []
        frame_idx = 0
        current_time = 0  # Current time in milliseconds
        last_gaze_idx = 0  # Keep track of last used gaze data index
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Calculate frame timestamps
            current_time = frame_idx * ms_per_frame
            next_frame_time = (frame_idx + 1) * ms_per_frame

            if use_gpu:
                # Upload frame to GPU
                gpu_frame.upload(frame)
                
                # Decay previous points on GPU
                gpu_heatmap.convertTo(gpu_heatmap, cv2.CV_32F, decay_rate, 0, gpu_stream)
                
                # Update heatmap with new gaze points
                for i in range(last_gaze_idx, len(gaze_data)):
                    timestamp, x, y = gaze_data[i]
                    if timestamp > next_frame_time:
                        break
                    if timestamp >= current_time and timestamp < next_frame_time:
                        x, y = int(x), int(y)
                        if 0 <= x < frame_width and 0 <= y < frame_height:
                            # Create temporary CPU heatmap for the new point
                            point_heatmap = np.zeros_like(heatmap)
                            cv2.circle(point_heatmap, (x, y), radius=90, color=1, thickness=-1)
                            # Upload and add to GPU heatmap
                            point_gpu = cv2.cuda_GpuMat()
                            point_gpu.upload(point_heatmap)
                            cv2.cuda.add(gpu_heatmap, point_gpu, gpu_heatmap, stream=gpu_stream)
                            point_gpu.release()
                    last_gaze_idx = i
                
                # Process the frame on GPU
                overlay = GazeHeatmapProcessor._process_frame_gpu(
                    gpu_frame, gpu_heatmap, gpu_heatmap_colored, gpu_overlay, gpu_stream)
                out.write(overlay)
            else:
                # Collect frames and heatmaps for batch processing
                frames.append(frame)
                heatmaps.append(heatmap.copy())
                
                # Process in batches of 16 frames (or when reaching end of video)
                if len(frames) >= 16 or frame_idx == frame_count - 1:
                    with Pool() as pool:
                        # Process frames in parallel
                        process_args = [(f, h) for f, h in zip(frames, heatmaps)]
                        overlays = pool.starmap(GazeHeatmapProcessor._process_frame_cpu, process_args)
                        
                        # Write processed frames
                        for overlay in overlays:
                            out.write(overlay)
                    
                    # Clear the batches
                    frames = []
                    heatmaps = []

            frame_idx += 1

        # Release resources
        cap.release()
        out.release()
        if use_gpu:
            gpu_heatmap.release()
            gpu_frame.release()
            gpu_heatmap_colored.release()
            gpu_overlay.release()

        # Post-process with FFmpeg
        success = post_process_video(temp_output, output_file)
        if success:
            print(f"Heatmap video saved to {output_file}")
        else:
            print("FFmpeg processing failed, using original output")
        
        print("Finished")

    @staticmethod
    def _read_gaze_data(csv_file: str) -> list:        
        df = pd.read_csv(csv_file)

        # Get column names
        columns = df.columns.tolist()
        
        # Find timestamp and coordinate columns
        timestamp_col = next(col for col in columns if 'time' in col.lower())
        x_col = next(col for col in columns if 'x' in col.lower())
        y_col = next(col for col in columns if 'y' in col.lower())
        
        # Convert timestamps to milliseconds if needed
        timestamps = df[timestamp_col].values
        if timestamps.max() < 1000:  # If timestamps are in seconds
            timestamps = timestamps * 1000
        
        # Create list of coordinates with timestamps
        gaze_data = list(zip(timestamps,
                           df[x_col].astype(float), 
                           df[y_col].astype(float)))
        return gaze_data

    @staticmethod
    def _process_frame_gpu(gpu_frame: cv2.cuda_GpuMat, gpu_heatmap: cv2.cuda_GpuMat,
                          gpu_heatmap_colored: cv2.cuda_GpuMat, 
                          gpu_overlay: cv2.cuda_GpuMat,
                          stream: cv2.cuda_Stream) -> np.ndarray:
        # Apply Gaussian blur on GPU
        cv2.cuda.GaussianBlur(gpu_heatmap, (0, 0), 40, gpu_heatmap, stream=stream)
        
        # Normalize the heatmap on GPU
        cv2.cuda.normalize(gpu_heatmap, gpu_heatmap, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U, stream=stream)
        
        # Apply colormap on GPU
        cv2.cuda.cvtColor(gpu_heatmap, cv2.COLOR_GRAY2BGR, gpu_heatmap_colored, stream=stream)
        cv2.cuda.applyColorMap(gpu_heatmap_colored, cv2.COLORMAP_JET, gpu_heatmap_colored, stream=stream)
        
        # Blend images on GPU
        cv2.cuda.addWeighted(gpu_frame, 0.6, gpu_heatmap_colored, 0.4, 0, gpu_overlay, stream=stream)
        
        # Download result back to CPU
        return gpu_overlay.download()

    @staticmethod
    def _process_frame_cpu(frame: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
        # Make sure inputs are copied to avoid multiprocessing issues
        frame = frame.copy()
        heatmap = heatmap.copy()
        
        # Original CPU processing method
        smoothed_heatmap = gaussian_filter(heatmap, sigma=40)
        heatmap_normalized = cv2.normalize(smoothed_heatmap, None, 0, 255, cv2.NORM_MINMAX)
        heatmap_colored = cv2.applyColorMap(heatmap_normalized.astype(np.uint8), cv2.COLORMAP_JET)
        return cv2.addWeighted(frame, 0.6, heatmap_colored, 0.4, 0)
    