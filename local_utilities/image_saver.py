"""
Image Saver

This utility is designed to accomodate the easy recording of images as either
many image files or a single video file.

It is designed to run as a thread/process, and read the image from a pipe.
"""

from multiprocessing import Pipe

from local_utilities import image_utils

def image_saver(pipe: Pipe):
    print("STARTED IMAGE SAVER!")
    in_pipe, out_pipe = pipe
    out_pipe.close()

    try:
        while not in_pipe.closed:
            image = in_pipe.recv()
            image_utils.show_image(image, "IMAGE SAVER")
    except SystemExit:
        print("User terminated image saver")
    except EOFError:
        print("EOF. Closing the image saver")
    in_pipe.close()
    print("Closed pipes")
