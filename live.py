import cv2
import numpy as np
import sounddevice as sd
import threading
import time
import os
from screeninfo import get_monitors
from dotenv import load_dotenv


load_dotenv()

video_device_index = int(os.getenv("VIDEO_DEVICE_ID"))

width = int(os.getenv("RESOLUTION_W"))
height = int(os.getenv("RESOLUTION_H"))
fps = int(os.getenv("FPS"))

samplerate = int(os.getenv("AUDIO_SAMPLE_RATE"))
channels = int(os.getenv("AUDIO_CHANNELS"))

input_device = int(os.getenv("AUDIO_DEVICE_ID_INPUT"))

output_device_id = int(os.getenv("AUDIO_DEVICE_ID_OUTPUT"))
output_device = None if output_device_id == -1 else output_device_id

video_codec = os.getenv("VIDEO_CODEC")

monitor_name = os.getenv("MONITOR_NAME", "")
use_primary_monitor = int(os.getenv("USE_PRIMARY_MONITOR", "1"))

window_name = "LiveCaptureCard (https://github.com/PaaaulZ/LiveCaptureCard)"

def video_thread():

    print("[+] Opening video device...")

    cap = cv2.VideoCapture(video_device_index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("[-] Unable to open video device.")
        return

    if video_codec:
        fourcc = cv2.VideoWriter_fourcc(*video_codec)
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    monitors = get_monitors()

    target_monitor = None

    for m in monitors:

        if monitor_name:
            if m.name == monitor_name:
                target_monitor = m
                break

        else:

            if use_primary_monitor == 1 and m.is_primary:
                target_monitor = m
                break

            if use_primary_monitor == 0 and not m.is_primary:
                target_monitor = m
                break

    if target_monitor is None:

        if not monitors:
            print("[-] No monitors found.")
            cap.release()
            return

        target_monitor = monitors[0]

    monitor_x = target_monitor.x
    monitor_y = target_monitor.y
    monitor_w = target_monitor.width
    monitor_h = target_monitor.height

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, monitor_w, monitor_h)
    cv2.moveWindow(window_name, monitor_x, monitor_y)

    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print(f"[+] Video stream starting, press 'q' to exit")
    print()

    while True:

        ret, frame = cap.read()

        if not ret:
            print("[!] Dropped frame")
            continue

        frame_h, frame_w = frame.shape[:2]

        frame_ratio = frame_w / frame_h
        monitor_ratio = monitor_w / monitor_h

        if frame_ratio > monitor_ratio:
            new_w = monitor_w
            new_h = int(monitor_w / frame_ratio)
        else:
            new_h = monitor_h
            new_w = int(monitor_h * frame_ratio)

        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        display = np.zeros((monitor_h, monitor_w, 3),dtype=np.uint8)

        x = (monitor_w - new_w) // 2
        y = (monitor_h - new_h) // 2

        display[y:y + new_h, x:x + new_w] = resized

        cv2.imshow(window_name, display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q") or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    print("[+] Video stopped.")

def audio_forward(indata, outdata, frames, timeinfo, status):

    if status:
        print(f"Audio status: {status}")

    outdata[:] = indata

    return


def audio_thread():

    try:

        with sd.Stream(samplerate=samplerate, blocksize=1024, dtype="int16", channels=channels, callback=audio_forward, device=(input_device, output_device)):
            print("[+] Audio stream started.")

            while True:
                time.sleep(1)

    except Exception as e:
        print(f"[-] Audio error: {e}")

if __name__ == "__main__":

    t1 = threading.Thread(target=video_thread, daemon=True)

    t2 = threading.Thread(target=audio_thread, daemon=True)

    t1.start()
    t2.start()

    try:
        for i, dev in enumerate(sd.query_devices()):
            if i == input_device:
                print(f"Input [{i}]: {dev['name']}")
    except Exception as e:
        print(f"[!] Audio device error: {e}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[!] Closing...")