#!/usr/bin/env python3

import cv2
import logging
import pathlib
import argparse
from decimal import Decimal
from datetime import datetime, timedelta

from local_utilities.logging_utils import simple_logging


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

        # TODO - test different codecs out?
        self.codec = cv2.VideoWriter_fourcc(*'DIVX')
        # self.codec = cv2.VideoWriter_fourcc(*'XVID') # ???
        # self.codec = cv2.VideoWriter_fourcc(*'MJPG') # big?
        # self.codec = cv2.VideoWriter_fourcc(*'X264') # small?

        # Create paths
        if video_path and pathlib.Path(video_path).exists():
            pathlib.Path(video_path).mkdir(parents=True, exist_ok=True)
        if image_path and pathlib.Path(image_path).exists():
            pathlib.Path(image_path).mkdir(parents=True, exist_ok=True)

        self.video_path = video_path or "."
        self.image_path = image_path or "."

        self.start_time = datetime.now()
        self.finish_time = self.start_time + timedelta(minutes=self.duration)

        # Begin watching the stream
        self.watch()

    def watch(self) -> None:
        cap = cv2.VideoCapture(self.url)
        stream_fps = int(cap.get(cv2.CAP_PROP_FPS))
        stream_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        stream_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        if not self.output_fps:
            self.output_fps = stream_fps

        formatted_start_time = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        output_video_file = f"{self.video_path}/{self.prefix}{formatted_start_time}.avi"

        video_writer = cv2.VideoWriter(
            output_video_file,
            self.codec,
            self.output_fps * self.speed,
            (stream_width, stream_height),
        )

        frame_num = 0
        stability = MAX_STABILITY

        # TODO - LOTS of debug output here
        logging.info(f"Streaming from '{self.url}' ({stream_width}x{stream_height} - {stream_fps}FPS).")
        logging.info(f"Recording to '{output_video_file}' at {self.speed}x speed ({self.output_fps} -> {self.output_fps * self.speed} FPS).")

        while (cap.isOpened()):
            ret, frame = cap.read()

            # Write to video file
            if frame_num % (Decimal(stream_fps) / Decimal(self.output_fps)) < 1:
                # Record every "xth" frame, to satisfy the FPS limit.
                logging.debug(f"Recording frame #{frame_num} to video.")
                video_writer.write(frame)

            # Error handling + Stability monitoring
            if not ret:
                logging.warning("Failed to read frame from stream.")
                stability -= 1
            elif frame is None or frame.size == 0:
                logging.warning("Bad/blank frame.")
                stability -= 1
            elif stability < MAX_STABILITY:
                # Successfully processing a frame increases stability
                stability = min(stability + 1, MAX_STABILITY)
            if datetime.now() > self.finish_time:
                logging.info("Duration is up. Exiting.")
                break
            if stability <= 0:
                # If stability is too low, give up and exit
                logging.fatal("Connection is too unstable. Exiting.")
                break

            self.show_frame(frame)

            frame_num += 1

        self.cleanup(cap, video_writer)

    def cleanup(self, cap: cv2.VideoCapture, video_writer: cv2.VideoWriter) -> None:
        logging.info("Cleaning up")
        video_writer.release()
        cap.release()
        cv2.destroyAllWindows()

    def save_image(self):
        return

    def save_video(self):
        return

    def show_frame(self, frame):
        # Visualise the feed for the user in realtime
        if (self.visualise):
            cv2.imshow("frame", frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                raise Exception("User pressed 'q', exiting.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="streamwatch",
        description="Connects to an RTSP stream and records video/png",
    )
    parser.add_argument("--url", "-u", type=str, help="The URL to watch. This can be an RTSP stream, file:// link, or more.", required=True)
    parser.add_argument("--fps", "-f", type=int, help="The max FPS to record.")
    parser.add_argument("--speed", "-s", type=int, help="The speed multiplier. The video moves twice as fast when this is 2.")
    parser.add_argument("--duration", "-d", type=int, help="The duration in minutes to record for. Defaults to forever.")
    parser.add_argument("--prefix", "-p", type=str, help="The prefix to use for saved files.")
    parser.add_argument("--video-path", "-v", type=str,
        help="The path to save videos to. No video is saved without this.")
    parser.add_argument("--image-path", "-i", type=str,
        help="The path to save images to. No images are saved without this.")
    parser.add_argument("--debug", "-x", type=str,
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