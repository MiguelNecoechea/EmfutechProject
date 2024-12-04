import subprocess
import os
from typing import Optional

def post_process_video(input_file: str, output_file: str, remove_input: bool = True) -> bool:
    """
    Post-processes a video file using FFmpeg to ensure web compatibility and optimal playback.
    
    Args:
        input_file (str): Path to the input video file
        output_file (str): Path where the processed video should be saved
        remove_input (bool): Whether to remove the input file after successful processing
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        print("Post-processing video with FFmpeg...")
        command = [
            'ffmpeg',
            '-i', input_file,      # Input file
            '-c:v', 'h264',        # Video codec
            '-preset', 'medium',    # Encoding preset
            '-profile:v', 'baseline',  # Maximum compatibility
            '-level', '3.0',
            '-movflags', '+faststart',  # Web playback optimization
            '-pix_fmt', 'yuv420p',      # Ensure pixel format compatibility
            '-f', 'mp4',                # Force MP4 format
            output_file
        ]
        
        # Run the conversion
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if process.returncode == 0:
            print(f"Video successfully converted to web-compatible format: {output_file}")
            if remove_input and input_file != output_file:
                os.remove(input_file)  # Clean up input file
            return True
        else:
            error_message = process.stderr.decode()
            print(f"Error converting video: {error_message}")
            # If FFmpeg fails and input is different from output, use input as fallback
            if input_file != output_file:
                os.replace(input_file, output_file)
            return False
            
    except Exception as e:
        print(f"Error during video conversion: {str(e)}")
        # If FFmpeg processing fails and input is different from output, use input as fallback
        if input_file != output_file:
            os.replace(input_file, output_file)
        return False
