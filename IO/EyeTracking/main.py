from LaserGaze.GazeProcessor import GazeProcessor
from LaserGaze.VisualizationOptions import VisualizationOptions
from  LaserGaze import landmarks
import asyncio

async def gaze_vectors_collected(left, right):
    print(f"left: {left}, right: {right}")

async def main():
    vo = VisualizationOptions()
    gp = GazeProcessor(visualization_options=vo, callback=gaze_vectors_collected)
    await gp.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()