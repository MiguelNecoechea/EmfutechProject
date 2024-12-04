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
        # Create a temporary output file if input and output are the same
        temp_file = output_file + '.temp.mp4' if input_file == output_file else output_file
        
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
            '-y',                       # Overwrite output file if it exists
            temp_file
        ]
        
        # Run the conversion
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if process.returncode == 0:
            if input_file == output_file:
                try:
                    # First try to remove the original file
                    if os.path.exists(input_file):
                        os.remove(input_file)
                    # Then rename the temp file
                    os.rename(temp_file, output_file)
                except Exception as e:
                    print(f"Error during file replacement: {str(e)}")
                    # If rename fails, try an alternative approach
                    try:
                        import shutil
                        shutil.move(temp_file, output_file)
                    except Exception as e2:
                        print(f"Error during file move: {str(e2)}")
                        return False
            elif remove_input and input_file != output_file:
                # If we're not overwriting and remove_input is True, delete the input
                os.remove(input_file)
                
            print(f"Video successfully converted to web-compatible format: {output_file}")
            return True
        else:
            error_message = process.stderr.decode()
            print(f"Error converting video: {error_message}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file) and temp_file != output_file:
                os.remove(temp_file)
            return False
            
    except Exception as e:
        print(f"Error during video conversion: {str(e)}")
        # Clean up temp file if it exists
        if 'temp_file' in locals() and os.path.exists(temp_file) and temp_file != output_file:
            os.remove(temp_file)
        return False
