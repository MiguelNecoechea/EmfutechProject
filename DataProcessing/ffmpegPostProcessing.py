import subprocess
import os
import shutil
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
        # Always use a temporary file with a unique name
        temp_file = output_file + '.processing.mp4'
        
        # Remove any existing temporary file
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not remove existing temp file: {str(e)}")
        
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
            # If the temp file was created successfully
            if os.path.exists(temp_file):
                try:
                    # Remove the target file if it exists
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    
                    # Try to move the temp file to the target location
                    shutil.move(temp_file, output_file)
                    
                    # If we need to remove the input file and it's different from the output
                    if remove_input and input_file != output_file and os.path.exists(input_file):
                        os.remove(input_file)
                        
                    print(f"Video successfully converted to web-compatible format: {output_file}")
                    return True
                except Exception as e:
                    print(f"Error during file operations: {str(e)}")
                    return False
            else:
                print("Error: FFmpeg completed but output file was not created")
                return False
        else:
            error_message = process.stderr.decode()
            print(f"Error converting video: {error_message}")
            return False
            
    except Exception as e:
        print(f"Error during video conversion: {str(e)}")
        return False
    finally:
        # Clean up temp file if it exists
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            print(f"Warning: Could not remove temporary file: {str(e)}")
