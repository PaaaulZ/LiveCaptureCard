import cv2
import sounddevice as sd
import threading
import time
import os
from screeninfo import get_monitors
from dotenv import load_dotenv

load_dotenv()

video_device_index = int(os.getenv('VIDEO_DEVICE_ID'))
width, height = int(os.getenv('RESOLUTION_W')), int(os.getenv('RESOLUTION_H'))
fps = int(os.getenv('FPS'))

samplerate = int(os.getenv('AUDIO_SAMPLE_RATE'))
channels = int(os.getenv('AUDIO_CHANNELS'))
input_device = int(os.getenv('AUDIO_DEVICE_ID_INPUT'))
output_device = None if int(os.getenv('AUDIO_DEVICE_ID_OUTPUT')) == -1 else int(os.getenv('AUDIO_DEVICE_ID_OUTPUT'))

window_name = "LiveCaptureCard (github.com/PaaaulZ/LiveCaptureCard)"

def video_thread():
    cap = cv2.VideoCapture(video_device_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*os.getenv('VIDEO_CODEC')))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    if not cap.isOpened():
        print("[-] Unable to open video device. In use?")
        return False

    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    monitors = get_monitors()
    target_monitor = None
    for m in monitors:
        if (int(os.getenv('USE_PRIMARY_MONITOR')) == 1 and m.is_primary) or (int(os.getenv('USE_PRIMARY_MONITOR')) == 0 and not m.is_primary):
            target_monitor = m
            break

    if target_monitor:
        cv2.moveWindow(window_name, target_monitor.x, target_monitor.y)
    else:
        print(f"[!] Using the only available monitor")

    print(f"[+] Video stream starting, press 'q' to exit")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[!] Dropped frame")
            time.sleep(0.1)
            continue

        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def audio_forward(indata, outdata, frames, timeinfo, status):
    if status:
        print(f"Audio status: {status}")
    outdata[:] = indata

def audio_thread():
    with sd.Stream(samplerate=samplerate,
                   blocksize=1024,
                   dtype='int16',
                   channels=channels,
                   callback=audio_forward,
                   device=(input_device, output_device)):
        print("[+] Audio stream started (CTRL+C) to terminate")
        while True:
            time.sleep(1.0)

if __name__ == "__main__":

    t1 = threading.Thread(target=video_thread, daemon=True)
    t2 = threading.Thread(target=audio_thread, daemon=True)
    t1.start()
    t2.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("[!] Closing")
