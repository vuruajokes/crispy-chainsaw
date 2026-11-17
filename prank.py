import os
import sys
import math
import random
import time
import tkinter as tk

from PIL import Image, ImageTk, ImageGrab
import cv2

import pygame
from moviepy.editor import VideoFileClip


AVATAR_FILE = "Dasha.jpeg"
VIDEO_FILE = "Dasha.mp4"


def resource_path(rel_name):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_name)


class YandexCallPrank:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Входящий звонок - Яндекс")
        self.root.configure(bg="#1a1a2e")
        self.cap = None
        self.after_id = None
        self._exploding = False

        # видео
        self.clip = None
        self.video_label = None
        self.video_start = None
        self.video_after = None
        self.mixer_ready = False

        self.build_incoming_call()

    # ---------- утилиты ----------
    def center(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def load_avatar(self, size):
        for name in (AVATAR_FILE, "Dasha.jpeg", "Dasha.jpg", "Dasha.png"):
            p = resource_path(name)
            if os.path.exists(p):
                return Image.open(p).convert("RGB").resize(size)
        return Image.new("RGB", size, "#333")

    # ---------- экран входящего звонка ----------
    def build_incoming_call(self):
        self.center(420, 560)
        self.root.resizable(False, False)

        avatar = ImageTk.PhotoImage(self.load_avatar((200, 200)))
        self._avatar_ref = avatar

        tk.Label(self.root, image=avatar, bg="#1a1a2e").pack(pady=(30, 15))
        tk.Label(self.root, text="Входящий звонок",
                 font=("Segoe UI", 14), fg="#b0b0c0",
                 bg="#1a1a2e").pack()
        tk.Label(self.root, text="Даша - Яндекс HR",
                 font=("Segoe UI", 22, "bold"), fg="white",
                 bg="#1a1a2e").pack(pady=(4, 4))
        tk.Label(self.root, text="Онлайн-собеседование",
                 font=("Segoe UI", 12), fg="#b0b0c0",
                 bg="#1a1a2e").pack()

        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=40)

        def make_accept(text, color):
            return tk.Button(
                btn_frame, text=text, bg=color, fg="white",
                activebackground=color, activeforeground="white",
                font=("Segoe UI", 13, "bold"),
                width=12, height=2, relief="flat", bd=0,
                cursor="hand2", command=self.start_call,
            )

        make_accept("Принять", "#2ecc71").grid(row=0, column=0, padx=8)
        make_accept("Принять", "#27ae60").grid(row=0, column=1, padx=8)

        tk.Label(self.root, text="(Esc)",
                 font=("Segoe UI", 9), fg="#6c6c80",
                 bg="#1a1a2e").pack(side="bottom", pady=10)

        self.root.bind("<Escape>", lambda e: self.explode_and_close())
        self.root.protocol("WM_DELETE_WINDOW", self.explode_and_close)

    # ---------- экран собеседования ----------
    def start_call(self):
        for w in self.root.winfo_children():
            w.destroy()

        self.root.geometry("1080x640")
        self.center(1080, 640)
        self.root.resizable(True, True)

        header = tk.Frame(self.root, bg="#111827", height=50)
        header.pack(fill="x")
        tk.Label(header, text="Собеседование - Даша (Яндекс)",
                 font=("Segoe UI", 13, "bold"), fg="white",
                 bg="#111827").pack(side="left", padx=20, pady=12)

        main = tk.Frame(self.root, bg="#0b0b13")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # слева видео (Label, а не Frame)
        self.video_label = tk.Label(main, bg="black",
                                    bd=2, relief="solid",
                                    text="Загрузка видео...", fg="white",
                                    font=("Segoe UI", 14))
        self.video_label.pack(side="left", fill="both",
                              expand=True, padx=5)

        # справа вебка
        self.cam_label = tk.Label(main, bg="black",
                                  bd=2, relief="solid",
                                  text="Нет камеры", fg="white",
                                  font=("Segoe UI", 14))
        self.cam_label.pack(side="right", fill="both",
                            expand=True, padx=5)

        self.root.update_idletasks()
        self.root.update()

        self.root.after(200, self._start_dasha_video)

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        self.update_webcam()

    # ---------- видео Даши ----------
    def _start_dasha_video(self):
        video_path = resource_path(VIDEO_FILE)
        if not os.path.exists(video_path):
            self.video_label.config(text=f"Нет файла {VIDEO_FILE}")
            return

        try:
            self.clip = VideoFileClip(video_path, audio=True)
        except Exception as e:
            self.video_label.config(text=f"Ошибка видео: {e}")
            return

        # Звук
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(video_path)
            pygame.mixer.music.play()
            self.mixer_ready = True
        except Exception:
            self.mixer_ready = False

        self.video_start = time.time()
        fps = self.clip.fps or 25
        self.frame_delay = max(1, int(1000 / fps))

        self._play_video_frame()

    def _play_video_frame(self):
        if self._exploding or self.clip is None:
            return

        elapsed = time.time() - self.video_start
        if elapsed >= self.clip.duration:
            if self.mixer_ready:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
            self.explode_and_close()
            return

        try:
            frame = self.clip.get_frame(elapsed)
        except Exception:
            self.explode_and_close()
            return

        img = Image.fromarray(frame)
        img.thumbnail((500, 500))
        photo = ImageTk.PhotoImage(img)
        self.video_label.config(image=photo, text="")
        self.video_label.image = photo

        # компенсируем дрейф: next = start + (n+1)/fps
        # вместо фиксированного after(frame_delay) — считаем от старта
        next_time = self.video_start + (math.floor(elapsed * (1000 / self.frame_delay)) + 1) * (self.frame_delay / 1000.0)
        wait_ms = max(1, int((next_time - time.time()) * 1000))
        self.video_after = self.root.after(wait_ms, self._play_video_frame)

    # ---------- вебка ----------
    def update_webcam(self):
        if self._exploding:
            return

        if self.cap is not None and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((500, 500))
                photo = ImageTk.PhotoImage(img)
                self.cam_label.config(image=photo, text="")
                self.cam_label.image = photo

        self.after_id = self.root.after(30, self.update_webcam)

    # ---------- взрыв ----------
    def explode_and_close(self):
        if self._exploding:
            return
        self._exploding = True

        for aid_attr in ("after_id", "video_after"):
            aid = getattr(self, aid_attr, None)
            if aid:
                try:
                    self.root.after_cancel(aid)
                except tk.TclError:
                    pass
                setattr(self, aid_attr, None)

        self.root.update_idletasks()

        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        try:
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        except Exception:
            self._hard_close()
            return

        # освобождаем ресурсы
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.clip is not None:
            try:
                self.clip.close()
            except Exception:
                pass
            self.clip = None
        if self.mixer_ready:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self.mixer_ready = False

        self.root.withdraw()

        cols, rows = 10, 8
        pw = max(1, w // cols)
        ph = max(1, h // rows)
        cx, cy = w / 2.0, h / 2.0

        pieces = []
        for r in range(rows):
            for c in range(cols):
                box = (c * pw, r * ph, (c + 1) * pw, (r + 1) * ph)
                try:
                    piece_img = screenshot.crop(box)
                except Exception:
                    continue

                top = tk.Toplevel(self.root)
                top.overrideredirect(True)
                try:
                    top.attributes("-topmost", True)
                except tk.TclError:
                    pass

                px = x + c * pw
                py = y + r * ph
                top.geometry(f"{pw}x{ph}+{px}+{py}")

                photo = ImageTk.PhotoImage(piece_img)
                lbl = tk.Label(top, image=photo, bd=0, bg="black")
                lbl.image = photo
                lbl.pack()

                dx = (c * pw + pw / 2) - cx
                dy = (r * ph + ph / 2) - cy
                dist = math.hypot(dx, dy) or 1.0
                speed = random.uniform(10, 22)
                vx = dx / dist * speed + random.uniform(-3, 3)
                vy = dy / dist * speed + random.uniform(-3, 3) - 4

                pieces.append({
                    "top": top,
                    "x": float(px),
                    "y": float(py),
                    "vx": vx,
                    "vy": vy,
                    "alpha": 1.0,
                })

        def animate():
            alive = 0
            for p in pieces:
                if p["alpha"] <= 0:
                    continue
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.4
                p["vx"] *= 0.99
                p["alpha"] -= 0.018

                if p["alpha"] <= 0:
                    try:
                        p["top"].destroy()
                    except tk.TclError:
                        pass
                    continue

                alive += 1
                try:
                    p["top"].geometry(f"+{int(p['x'])}+{int(p['y'])}")
                    p["top"].attributes("-alpha", max(0.0, p["alpha"]))
                except tk.TclError:
                    pass

            if alive > 0:
                self.root.after(16, animate)
            else:
                self.root.destroy()

        animate()

    def _hard_close(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        if self.clip is not None:
            try:
                self.clip.close()
            except Exception:
                pass
            self.clip = None
        if self.mixer_ready:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self.mixer_ready = False
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    YandexCallPrank().run()
