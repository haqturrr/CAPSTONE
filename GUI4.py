import tkinter as tk
from tkinter import *
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
import threading
import asyncio
import aiohttp
import queue

vid = None
running = False
latest_distance = None
latest_tilt = None

model = YOLO('Corrosion Detection Yolov8s.pt') 
model2 = YOLO('Paint Inspection Yolov8.pt')

application = tk.Tk()
application.title('GUI')
application.geometry("1700x900")

from PIL import Image, ImageTk

# Load the background image
bg_image = Image.open("background.png")
bg_image = bg_image.resize((1700, 900), Image.Resampling.LANCZOS)  # Resize to fit the window
bg_photo = ImageTk.PhotoImage(bg_image)

# Create a label and place it as background
bg_label = tk.Label(application, image=bg_photo)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)




camera1 = tk.Label(application, height=640, width=640)
camera1.place(x=100, y=20)

camera2 = tk.Label(application, height=640, width=640)
camera2.place(x=860, y=20)

frame = tk.Frame(application)
frame.place(x=150, y=680)

frame2 = tk.Frame(application)
frame2.place(x=910, y=680)

log_box = tk.Text(frame, height=5, width=50, bg='black', fg='lime', wrap='none')
log_box.pack(side=tk.LEFT, fill=tk.BOTH)
log_box.configure(state='disabled')

log_box2 = tk.Text(frame2, height=5, width=50, bg='black', fg='lime', wrap='none')
log_box2.pack(side=tk.LEFT, fill=tk.BOTH)
log_box2.configure(state='disabled')

scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=log_box.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

scrollbar2 = tk.Scrollbar(frame2, orient=tk.VERTICAL, command=log_box2.yview)
scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

log_box.config(yscrollcommand=scrollbar.set)
log_box2.config(yscrollcommand=scrollbar2.set)

# ===== SSE Setup =====
sse_queue = queue.Queue()
corrosion_detected = False
paint_detected = False
corrosion_logged = False
paint_logged = False

async def read_sse():
    global latest_distance, latest_tilt
    url = 'http://172.20.10.10/events'
    headers = {'Accept': 'text/event-stream'}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print("Connected to SSE stream...")
            event_type = None
            async for line in resp.content:
                if line:
                    decoded_line = line.decode('utf-8').strip()

                    if decoded_line.startswith("event:"):
                        event_type = decoded_line.replace("event:", "").strip()
                    elif decoded_line.startswith("data:"):
                        data = decoded_line.replace("data:", "").strip()
                        if event_type == "distance":
                            latest_distance = data
                            print(f"[Distance] {data}")
                        elif event_type == "tilt":
                            latest_tilt = data
                            print(f"[Tilt] {data}")

def start_sse_thread():
    def runner():
        asyncio.run(read_sse())
    threading.Thread(target=runner, daemon=True).start()

def set_corrosion_flag(state):
    global corrosion_detected, corrosion_logged
    corrosion_detected = state
    corrosion_logged = False  # reset logged flag when resetting detection

def set_paint_flag(state):
    global paint_detected, paint_logged
    paint_detected = state
    paint_logged = False  # reset logged flag when resetting detection

# ===== Detection Function =====
def detect_corrosion(frame):
    global corrosion_detected, corrosion_logged

    results = model.predict(frame, imgsz=640, conf=0.6, verbose=False)
    detected = False

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = f"{model.names[cls]} {conf:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            detected = True

    if detected:
        corrosion_detected = True
        corrosion_logged = False
        log_box.after(5000, lambda: set_corrosion_flag(False))

    return frame

# ===== Paint Inspection Function =====
def detect_paint(frame):
    global paint_detected, paint_logged

    results = model2.predict(frame, imgsz=640, conf=0.6, verbose=False)
    detected = False

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = f"{model2.names[cls]} {conf:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            detected = True

    if detected:
        paint_detected = True
        paint_logged = False
        log_box2.after(5000, lambda: set_paint_flag(False))

    return frame

# ===== Camera Feed =====
def camera_feed():
    global vid, running

    if running and vid is not None:
        ret, frame = vid.read()
        frame = cv2.flip(frame, 1)
        if ret:
            frame_corrosion = frame.copy()
            frame_paint = frame.copy()

            corrosion_frame = detect_corrosion(frame_corrosion)
            frame1 = cv2.cvtColor(corrosion_frame, cv2.COLOR_BGR2RGBA)
            image1 = ImageTk.PhotoImage(Image.fromarray(frame1))
            camera1.photo_image = image1
            camera1.configure(image=image1)

            paint_frame = detect_paint(frame_paint)
            frame2 = cv2.cvtColor(paint_frame, cv2.COLOR_BGR2RGBA)
            image2 = ImageTk.PhotoImage(Image.fromarray(frame2))
            camera2.photo_image = image2
            camera2.configure(image=image2)

        application.after(1, camera_feed)

def open_camera():
    global vid, running
    if not running:
        #vid = cv2.VideoCapture("http://172.20.10.11:81/stream")
        vid = cv2.VideoCapture(0)
        vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
        running = True
        camera_feed()

def close_camera():
    global vid, running
    running = False
    if vid:
        vid.release()
        vid = None
    camera1.configure(image='')
    camera2.configure(image='')

# ===== Task to Update Sensor Log When Corrosion Detected =====
def task():
    global corrosion_detected, corrosion_logged, latest_distance, latest_tilt

    if corrosion_detected and not corrosion_logged:
        if latest_distance is not None and latest_tilt is not None:
            log_box.configure(state='normal')
            if latest_tilt == '1':
                log_box.insert(tk.END, f"[SENSOR] {latest_distance} cm from the floor\n")
            else:
                log_box.insert(tk.END, f"[SENSOR] {latest_distance} cm from the wall\n")
            log_box.see(tk.END)
            log_box.configure(state='disabled')
            corrosion_logged = True
            latest_distance = None
            latest_tilt = None

    log_box.after(500, task)


def task2():
    global paint_detected, paint_logged, latest_distance, latest_tilt

    if paint_detected and not paint_logged:
        if latest_distance is not None and latest_tilt is not None:
            log_box2.configure(state='normal')
            if latest_tilt == '1':
                log_box2.insert(tk.END, f"[SENSOR] {latest_distance} cm from the floor\n")
            else:
                log_box2.insert(tk.END, f"[SENSOR] {latest_distance} cm from the wall\n")
            log_box2.see(tk.END)
            log_box2.configure(state='disabled')
            paint_logged = True
            latest_distance = None
            latest_tilt = None

    log_box2.after(500, task2)


open_btn = tk.Button(application, text='Open Camera', command=open_camera)
open_btn.place(x=320, y=600)

close_btn = tk.Button(application, text='Close Camera', command=close_camera)
close_btn.place(x=1080, y=600)

start_sse_thread()
task()
task2()

camera1.lift()
camera2.lift()
frame.lift()
frame2.lift()
open_btn.lift()
close_btn.lift()

application.mainloop()
