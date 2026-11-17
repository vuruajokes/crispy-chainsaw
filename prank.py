<meta name='viewport' content='width=device-width, initial-scale=1'/>import tkinter as tk
from PIL import Image, ImageTk, ImageGrab
import cv2
import os
import sys
import math
import random

try:
    import vlc
    HAS_VLC = True
except ImportError:
    HAS_VLC = False

AVATAR_FILE = "Dasha.png"
VIDEO_FILE = "Dasha.mp4"


class YandexCallPrank:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Входящий звонок - Яндекс")
        self.root.configure(bg="#1a1a2e")
        self.cap = None
        self.after_id = None
        self.vlc_instance = None
        self.vlc_player = None
        self._exploding = False
        self._video_ended = False
        self.build_incoming_call()

    def center(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def load_avatar(self, size):
        for name in (AVATAR_FILE, "Dasha.jpg", "Dasha.jpeg"):
            if os.path.exists(name):
                return Image.open(name).convert("RGB").resize(size)
        return Image.new("RGB", size, "#333")

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

        self.video_frame = tk.Frame(main, bg="black",
                                    bd=2, relief="solid")
        self.video_frame.pack(side="left", fill="both",
                              expand=True, padx=5)

        self.cam_label = tk.Label(main, bg="black",
                                  bd=2, relief="solid",
                                  text="Нет камеры", fg="white",
                                  font=("Segoe UI", 14))
        self.cam_label.pack(side="right", fill="both",
                            expand=True, padx=5)

        self.root.update_idletasks()
        self.root.update()

        self.root.after(300, self._start_dasha_video)

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        self.update_webcam()

    def _start_dasha_video(self):
        if not HAS_VLC:
            tk.Label(self.video_frame, text="pip install python-vlc",
                     fg="white", bg="black",
                     font=("Segoe UI", 14)).pack(expand=True)
            return

        if not os.path.exists(VIDEO_FILE):
            tk.Label(self.video_frame,
                     text=f"Нет файла {VIDEO_FILE}",
                     fg="white", bg="black",
                     font=("Segoe UI", 14)).pack(expand=True)
            return

        self.vlc_instance = vlc.Instance("--no-video-title-show")
        self.vlc_player = self.vlc_instance.media_player_new()
        media = self.vlc_instance.media_new(os.path.abspath(VIDEO_FILE))
        self.vlc_player.set_media(media)

        hwnd = self.video_frame.winfo_id()
        if sys.platform.startswith("win"):
            self.vlc_player.set_hwnd(hwnd)
        elif sys.platform == "darwin":
            self.vlc_player.set_nsobject(hwnd)
        else:
            self.vlc_player.set_xwindow(hwnd)

        em = self.vlc_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached,
                        self._on_video_end)

        self.vlc_player.play()

    def _on_video_end(self, event):
        # Вызывается из потока VLC. Просто ставим флаг,
        # главный поток его подхватит в update_webcam.
        self._video_ended = True

    def update_webcam(self):
        if self._exploding:
            return
        if self._video_ended:
            self.explode_and_close()
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

    def explode_and_close(self):
        if self._exploding:
            return
        self._exploding = True

        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        # Сначала снимаем скрин живого окна,
        # потом уже останавливаем VLC и камеру.
        self.root.update_idletasks()

        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        try:
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        except Exception:
            if self.cap:
                self.cap.release()
            if self.vlc_player:
                try:
                    self.vlc_player.stop()
                except Exception:
                    pass
            self.root.destroy()
            return

        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.vlc_player:
            try:
                self.vlc_player.stop()
            except Exception:
                pass

        self.root.withdraw()

        cols, rows = 10, 8
        pw = max(1, w // cols)
        ph = max(1, h // rows)
        cx, cy = w / 2.0, h / 2.0

        pieces = []
        for r in range(rows):
            for c in range(cols):
                box = (c * pw, r * ph, (c + 1) * pw, (r + 1) * ph)
                piece_img = screenshot.crop(box)

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

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    YandexCallPrank().run()