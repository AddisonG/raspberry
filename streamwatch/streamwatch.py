#!/usr/bin/env python3

import cv2
import logging
import pathlib
import argparse
from decimal import Decimal
from datetime import datetime, timedelta

from local_utilities.logging_utils import simple_logging
from local_utilities import image_utils


simple_logging("streamwatch", level=logging.DEBUG, stdout=True)

MAX_STABILITY = 10


class StreamWatch():
    def __init__(self,
                 url: str,
                 fps: int,
                 speed: int,
                 duration: int,
                 prefix: str,
                 video_path: str,
                 image_path: str,
                 debug: bool,
                ):
        self.url = url
        self.output_fps = fps
        self.speed = speed or 1
        self.duration = duration or None
        self.prefix = prefix or ""
        self.debug = debug or False
        self.visualise = False
        self.video_writer = None
        self.recent_motion = 0

        # TODO - test different codecs out?
        self.codec = cv2.VideoWriter_fourcc(*'DIVX')
        # self.codec = cv2.VideoWriter_fourcc(*'XVID') # ???
        # self.codec = cv2.VideoWriter_fourcc(*'MJPG') # big?
        # self.codec = cv2.VideoWriter_fourcc(*'X264') # small?
        # self.codec = cv2.VideoWriter_fourcc(*'h264') # the native codec of my camera? faster?

        # Create paths
        if image_path and pathlib.Path(image_path).exists():
            pathlib.Path(image_path).mkdir(parents=True, exist_ok=True)

        self.video_path = video_path or "."
        self.image_path = image_path or "."

        self.start_time = datetime.now()
        self.finish_time = None
        if self.duration:
            self.finish_time = self.start_time + timedelta(seconds=self.duration)

        self.formatted_start_time = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        self.output_video_file = f"{self.video_path}/{self.prefix}{self.formatted_start_time}.avi"

        # Begin watching the stream
        self.watch()

    def watch(self) -> None:
        cap = cv2.VideoCapture(self.url)
        self.stream_fps = int(cap.get(cv2.CAP_PROP_FPS))
        self.stream_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.stream_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        if not self.output_fps:
            self.output_fps = self.stream_fps

        frame_num = 0
        stability = MAX_STABILITY

        # TODO - LOTS of debug output here
        logging.info(f"Streaming from '{self.url}' ({self.stream_width}x{self.stream_height} - {self.stream_fps}FPS).")
        logging.info(f"Recording to '{self.output_video_file}' at {self.speed}x speed ({self.output_fps} -> {self.output_fps * self.speed} FPS).")

        # TODO - Make this auto-adjust for FPS. Probably always 0.5 seconds?
        old_frames = [None] * 5
        while (cap.isOpened()):
            ret, frame = cap.read()
            frame_num += 1

            # Error handling + Stability monitoring
            if stability <= 0:
                # If stability is too low, give up and exit
                logging.fatal("Connection is too unstable. Exiting.")
                break
            if not ret:
                logging.warning("Failed to read frame from stream.")
                stability -= 1
                continue
            elif frame is None or frame.size == 0:
                logging.warning("Bad/blank frame.")
                stability -= 1
                continue
            elif stability < MAX_STABILITY:
                # Successfully processing a frame increases stability
                stability = min(stability + 1, MAX_STABILITY)

            # Lag detection (CPU-bottlenecked devices)
            stream_frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
            if frame_num != stream_frame_num:
                logging.warning(f"LAGGING BEHIND FEED! THIS IS BAD!!! {frame_num} vs {stream_frame_num}.")
                stream_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC), 2)
                logging.warning(f"The stream is apparently {stream_ms}ms in.")

            # Detect motion (compare to several frames ago)
            diff_frame = old_frames.pop()
            old_frames.insert(0, frame)
            motion_area = image_utils.detect_motion(diff_frame, frame)

            self.handle_motion(motion_area)

            # Write to video
            self.save_video(frame, frame_num)

            # TODO - Write to image

            if self.visualise:
                image_utils.show_image(frame, "Visualisation")

            if self.finish_time is not None and datetime.now() > self.finish_time:
                logging.info("Duration is up. Exiting.")
                break

        self.cleanup(cap, self.video_writer)

    def cleanup(self, cap: cv2.VideoCapture, video_writer: cv2.VideoWriter) -> None:
        logging.info("Cleaning up")
        if video_writer is not None:
            video_writer.release()
        cap.release()
        cv2.destroyAllWindows()

    def save_image(self):
        return

    def handle_motion(self, motion_area):
        """
        recent_motion is a measure of how much motion there has been over
        the past few seconds. This value has a maximum value that it caps at.

        If this value is 0, then there has been no recent motion.

        As soon as this value drops down to 0, a segment of recent motion is
        said to have stopped.
        """
        if not motion_area or motion_area == (0, 0, 0, 0):
            # No motion detected
            if self.recent_motion == 1:
                logging.debug("Motion has stopped")
            self.recent_motion = max(0, self.recent_motion - 1)
        elif self.recent_motion == 0:
            # New motion detected
            logging.debug("New motion detected")
            # FIXME - base this on framerate
            self.recent_motion = 15
        else:
            # Motion is continuing
            # FIXME - base this on framerate
            self.recent_motion = min(self.recent_motion + 1, 15)

        #

    def save_video(self, frame, frame_num):
        # Create a new file to save the video to
        if self.video_writer is None:
            if self.video_path and pathlib.Path(self.video_path).exists():
                pathlib.Path(self.video_path).mkdir(parents=True, exist_ok=True)
            self.video_writer = cv2.VideoWriter(
                self.output_video_file,
                self.codec,
                self.output_fps * self.speed,
                (self.stream_width, self.stream_height),
            )

        # Record every "xth" frame, to satisfy the FPS limit.
        if frame_num % (Decimal(self.stream_fps) / Decimal(self.output_fps)) < 1:
            logging.debug(f"Recording frame #{frame_num} to video.")
            self.video_writer.write(frame)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="streamwatch",
        description="Connects to an RTSP stream and records video/png",
    )

    parser.add_argument("--url", "-u", type=str, required=True,
        help="The URL to watch. This can be an RTSP stream, file:// link, or more.")
    parser.add_argument("--fps", "-f", type=int,
        help="The max FPS to record.")
    parser.add_argument("--speed", "-s", type=int,
        help="The speed multiplier. The video moves twice as fast when this is 2.")
    parser.add_argument("--duration", "-d", type=int,
        help="The duration in seconds to record for. Defaults to forever.")
    parser.add_argument("--prefix", "-p", type=str,
        help="The prefix to use for saved files.")
    parser.add_argument("--video-path", "-v", type=str,
        help="The path to save videos to. No video is saved without this.")
    parser.add_argument("--image-path", "-i", type=str,
        help="The path to save images to. No images are saved without this.")
    parser.add_argument("--debug", "-x", action='store_true',
        help="Enable debugging,")

    args = parser.parse_args()

    StreamWatch(
        url=args.url,
        fps=args.fps,
        speed=args.speed,
        duration=args.duration,
        prefix=args.prefix,
        video_path=args.video_path,
        image_path=args.image_path,
        debug=args.debug,
    )
