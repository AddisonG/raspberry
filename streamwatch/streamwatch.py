#!/usr/bin/env python3

import cv2
import time
import logging
import pathlib
import argparse
from decimal import Decimal
from datetime import datetime, timedelta
from multiprocessing import Pipe, Process

from local_utilities.logging_utils import simple_logging
from local_utilities import image_utils, image_saver


simple_logging("streamwatch", level=logging.DEBUG, stdout=True)

MAX_STABILITY = 5
MAX_MOTION_SECONDS = 5


class StreamWatch():
    def __init__(self,
                 url: str,
                 fps: int = None,
                 speed: int = 1,
                 duration: int = None,
                 prefix: str = None,
                 video_path: str = None,
                 image_path: str = None,
                 debug: bool = False,
                ):
        # Deal with params
        self.url = url
        self.output_fps = fps
        self.speed = speed or 1
        self.duration = duration
        self.prefix = prefix or ""
        self.video_path = video_path
        self.image_path = image_path
        self.debug = debug or False

        # Configure
        self.setup()

        # Begin watching the stream
        self.watch()

    def setup(self):
        # Initialise internal variables
        self.video_writer = None
        self.recent_motion = 0
        self.stability = MAX_STABILITY
        self.nightvision = False

        # Advanced customisation
        self.codec = cv2.VideoWriter_fourcc(*'XVID')
        # XVID, DIVX and MP4V all give identical output on my computer
        # MJPG gives a huge file, about 4x - 6x the size of XVID
        # X264 and H264 are not supported on my computer
        # My camera/stream reports that it is supposedly using H264 encoding
        # I don't know if this means it would be faster/better? Probably not

        # Deal with start/end times
        self.start_time = datetime.now()
        self.finish_time = None
        if self.duration:
            self.finish_time = self.start_time + timedelta(seconds=self.duration)

        self.formatted_start_time = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        if self.video_path:
            self.output_video_file = f"{self.video_path}/{self.prefix}{self.formatted_start_time}.avi"

        if self.image_path:
            self.image_path += f"/{self.prefix}{self.formatted_start_time}/"
            pathlib.Path(self.image_path).mkdir(parents=True, exist_ok=True)

    def watch(self) -> None:
        cap = cv2.VideoCapture(self.url)
        self.stream_fps = int(cap.get(cv2.CAP_PROP_FPS))
        self.stream_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.stream_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        # The scale is based on the smallest dimension. e.g: 1920x1080 = 10x
        self.scale = min(self.stream_height, self.stream_width) // 100

        if not self.output_fps:
            self.output_fps = self.stream_fps

        logging.info(f"Streaming from '{self.url}' ({self.stream_width}x{self.stream_height} - {self.stream_fps}FPS).")
        if self.video_path:
            logging.info(f"Recording video to '{self.output_video_file}' at {self.speed}x speed ({self.output_fps} -> {self.output_fps * self.speed} FPS).")
        if self.image_path:
            logging.info(f"Recording images to '{self.image_path}'.")

        frame_num = 0
        old_frames = [None] * max(self.stream_fps // 2, 1)
        # TODO - is duplex faster or not? Is queue faster?
        saving_pipe = Pipe()
        p = Process(target=image_saver.image_saver, args=(saving_pipe,))
        p.start()
        saving_pipe[0].close()
        while (cap.isOpened()):
            ret, frame = cap.read()
            frame_num += 1

            if not self.stability_check(cap, ret, frame, frame_num):
                continue

            saving_pipe[1].send(frame)

            # Check if we're nightvision every few frames
            if frame_num % self.stream_fps == 0 and self.nightvision != image_utils.is_greyscale(frame):
                from_string, to_string = ("nightvision", "color") if self.nightvision else ("color", "nightvision")
                logging.info(f"Changed from {from_string} to {to_string}.")
                self.nightvision = (not self.nightvision)

            # Keep track of the last several frames
            # FIXME - maybe don't blur nightvision images? The greys REALLY blend together
            new_simple = image_utils.simplify_image(frame.copy(), greyscale=True, blur=True)
            old_frames.insert(0, new_simple)

            # Detect motion (compare to several frames ago)
            old_frame = old_frames.pop()
            motion_area = image_utils.detect_motion(old_frame, new_simple, self.scale, self.nightvision)

            self.handle_motion(motion_area)

            # Write frame to video and/or image
            self.save_video(frame, frame_num)
            self.save_image(frame, frame_num)

            if self.debug:
                debug_frame = frame.copy()

                # Print the biggest movement detected
                (x, y, w, h) = motion_area
                cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                cv2.putText(debug_frame, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), (1, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.putText(debug_frame, "Motion: " + str(self.recent_motion), (1, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                image_utils.show_image(debug_frame, "Debug Visualisation")

            if self.finish_time is not None and datetime.now() > self.finish_time:
                logging.info("Duration is up. Exiting.")
                break

        self.cleanup(cap, p)

    def cleanup(self, cap: cv2.VideoCapture, p) -> None:
        logging.info("Cleaning up")
        if self.video_writer is not None:
            self.video_writer.release()
        cap.release()
        cv2.destroyAllWindows()
        p.join()

    def stability_check(self, cap, ret, frame, frame_num):
        # Error handling + Stability monitoring
        if self.stability <= 0:
            # If stability is too low, give up and exit
            logging.fatal("Connection is too unstable. Exiting.")
            self.cleanup(cap)
            raise SystemExit("Connection is too unstable. Exiting.")
        if not ret:
            logging.warning("Failed to read frame from stream.")
            self.stability -= 1
            return False
        elif frame is None or frame.size == 0:
            logging.warning("Bad/blank frame.")
            self.stability -= 1
            return False
        elif self.stability < MAX_STABILITY:
            # Successfully processing a frame restores lost stability
            self.stability = min(self.stability + 1, MAX_STABILITY)

        # Lag detection (CPU-bottlenecked devices)
        stream_frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
        if frame_num != stream_frame_num:
            logging.warning(f"LAGGING BEHIND FEED! THIS IS BAD!!! {frame_num} vs {stream_frame_num}.")
            stream_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC), 2)
            logging.warning(f"The stream is apparently {stream_ms}ms in.")
            # TODO - Actually do something about this? Reduce FPS?
            return False
        return True

    def handle_motion(self, motion_area):
        """
        recent_motion is a measure of how much motion there has been over
        the past few seconds. This value has a maximum value that it caps at.

        If this value is already 0, then there has been no recent motion.

        As soon as this value drops down from 1 to 0, a segment of recent motion
        is said to have stopped.

        TODO - Add a "threshold" here. A single frame of tiny movement should
        not count as movement. Movement should be based on size as well.
        A single frame of major movement might be enough to trigger the start
        of movement, or several frames of small movement.
        Consider categorising movement (small, medium, large)?
        """
        if not motion_area or motion_area == (0, 0, 0, 0):
            # No motion detected
            if self.recent_motion == 1:
                logging.info("Motion has stopped")
            self.recent_motion = max(0, self.recent_motion - 1)
        elif self.recent_motion == 0:
            # New motion detected
            logging.info("New motion detected")
            self.recent_motion = self.stream_fps * MAX_MOTION_SECONDS
        else:
            # Motion is continuing
            self.recent_motion = min(self.recent_motion + MAX_MOTION_SECONDS, self.stream_fps * MAX_MOTION_SECONDS)

    def save_video(self, frame, frame_num):
        if not self.video_path:
            return

        # Create a new file to save the video to
        if self.video_writer is None:
            logging.debug("Initialising video file.")
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

    def save_image(self, frame, frame_num):
        if not self.image_path:
            return

        logging.debug(f"Saving frame #{frame_num} as image.")
        cv2.imwrite(self.image_path + f"{frame_num}.jpg", frame)


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
