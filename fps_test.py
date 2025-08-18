import time
import argparse
from gsrobotics.logger import log_message
from config import GSConfig
from gsrobotics.gelsightmini import GelSightMini

def measure_fps(config, num_frames: int, device_index: int = None):
    # Pull values from the loaded config
    idx = device_index if device_index is not None else config.default_camera_index
    cam = GelSightMini(
        # target_width=1280,
        # target_height=720,
        target_width=3280,
        target_height=2460,
        # target_width=config.camera_width,
        # target_height=config.camera_height,
        border_fraction=config.border_fraction,
    )
    cam.select_device(idx)
    cam.start()

    # Warm-up
    for _ in range(30):
        cam.update(0)

    # Measure
    start = time.time()
    frames = 0
    while frames < num_frames:
        frame = cam.update(0)
        # print(frame.shape)
        if frame is None:
            break
        frames += 1
    elapsed = time.time() - start

    # Teardown
    if getattr(cam, "camera", None):
        cam.camera.release()

    fps = frames / elapsed if elapsed > 0 else 0
    print(f"📊 Captured {frames} frames in {elapsed:.2f}s → {fps:.2f} FPS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Headless FPS test for GelSight Mini"
    )
    parser.add_argument(
        "--gs-config",
        type=str,
        default=None,
        help="Path to the JSON configuration file. If not provided, default_config.json is used."
    )
    parser.add_argument(
        "--frames", "-n",
        type=int, default=120,
        help="Number of frames to grab for the test"
    )
    parser.add_argument(
        "--device", "-d",
        type=int, default=None,
        help="Camera index (overrides default in config)"
    )
    args = parser.parse_args()

    # Mirror your Kivy example’s init logic:
    if args.gs_config:
        log_message(f"Provided config path: {args.gs_config}")
    else:
        log_message("Didn't provide custom config path.")
        log_message("Using default_config.json if available in repo root.")
        args.gs_config = "default_config.json"

    # Load it
    gs_config = GSConfig(args.gs_config)
    measure_fps(
        config=gs_config.config,
        num_frames=args.frames,
        device_index=args.device
    )