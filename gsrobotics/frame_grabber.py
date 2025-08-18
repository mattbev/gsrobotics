import glob
import platform
import re
import subprocess
from typing import Tuple

import cv2
import ffmpeg
import numpy as np
from gsrobotics.image_processing import crop_and_resize


class FrameGrabber:
    def __init__(
        self,
        device_idx: int,
        target_height: int = 2464,
        target_width: int = 3280,
        frequency: int = 25,
        raw_height: int = 2464,
        raw_width: int = 3280,
        border_fraction: float = 0.0,
        warmup: int = 0,
        encoding="bgr8",
    ):
        self.device_idx = device_idx
        self.target_height = target_height
        self.target_width = target_width
        self.frequency = frequency
        self.raw_height = raw_height
        self.raw_width = raw_width
        self.raw_size = self.raw_height * self.raw_width * 3
        self.border_fraction = border_fraction
        self.warmup = warmup

        # select device
        self.device_id, self.serial_number = self.select_device(self.device_idx)

    def connect(self, verbose=True):
        """
        Connect to the camera using FFMpeg streamer.
        """
        # Command to capture video using ffmpeg and high resolution
        self.ffmpeg_command = (
            ffmpeg.input(
                f"/dev/video{self.device_idx}",
                format="v4l2",
                framerate=self.frequency,
                video_size="%dx%d" % (self.raw_width, self.raw_height),
            )
            .output("pipe:", format="rawvideo", pix_fmt="bgr24")
            .global_args("-fflags", "nobuffer")
            .global_args("-flags", "low_delay")
            .global_args("-fflags", "+genpts")
            .global_args("-rtbufsize", "0")
            .compile()
        )
        self.process = subprocess.Popen(
            self.ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        # Warm-up phase: discard the first few frames
        if verbose and self.warmup > 0:
            print("Warming up the camera...")
        for _ in range(self.warmup):
            self.process.stdout.read(self.raw_size)
        if verbose:
            print("Camera ready for use!")

    def get_image(self):
        """
        Get the image from the camera from raw data stream.

        :return: np.ndarray; The image from the camera.
        """
        frame = np.frombuffer(
            self.process.stdout.read(self.raw_size), np.uint8
        ).reshape((self.raw_height, self.raw_width, 3))
        if self.target_height != self.raw_height or self.target_width != self.raw_width:
            frame = crop_and_resize(
                frame,
                target_size=(self.target_width, self.target_height),
                border_fraction=self.border_fraction,
            )
        return frame

    def release(self):
        """
        Release the camera resource.
        """
        self.process.stdout.close()
        self.process.wait()

    @classmethod
    def select_device(cls, device_idx: int = None) -> Tuple[str, str]:
        device_id = None
        serial_number = None

        if device_idx == None and platform.system() == "Windows":
            (dev, desc) = cls.find_cameras_windows("GelSight Mini")
            print("Found: ", desc, ", dev: ", dev)
            device_idx = dev
            # Parse serial number from description
            match = re.search("[A-Z0-9]{4}-[A-Z0-9]{4}", desc)
            if match:
                serial_number = match.group()

        if platform.system() == "Linux":
            devices = cls.list_devices()
            for ix in range(0, len(devices)):
                print("Device: ", devices[ix])
            if isinstance(devices.get(device_idx), str):
                device_id = devices[device_idx]
        else:
            device_id = device_idx

        return device_id, serial_number

    @staticmethod
    def list_devices() -> dict:
        """
        Enumerate available camera devices.

        On Linux, returns unique device paths from /dev/v4l/by-id/.
        On Windows/macOS, tests numeric indices 0..5.

        Returns:
            dict: A mapping from index to device identifier.
        """
        devices = {}
        os_name = platform.system()
        if os_name == "Linux":
            paths = glob.glob("/dev/v4l/by-id/*")
            for idx, path in enumerate(paths):
                devices[idx] = path
        else:
            for idx in range(6):
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    devices[idx] = f"Camera {idx}"
                    cap.release()
        return devices

    @staticmethod
    def find_cameras_windows(camera_name):
        from pygrabber.dshow_graph import FilterGraph

        graph = FilterGraph()

        # get the device name
        allcams = graph.get_input_devices()  # list of camera device
        description = ""
        for cam in allcams:
            if camera_name in cam:
                description = cam

        try:
            device = graph.get_input_devices().index(description)
        except ValueError as e:
            print("Device is not in this list")
            print(graph.get_input_devices())
            import sys

            sys.exit()

        return (device, description)
