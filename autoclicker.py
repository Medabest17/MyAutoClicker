import threading
import time
import tkinter as tk
from tkinter import ttk

from pynput.keyboard import GlobalHotKeys
from pynput.mouse import Button, Controller


APP_NAME = "Myautoclicker"
MAX_CPS = 100
DEFAULT_CPS = 10

BG = "#0D1117"
PANEL = "#161B22"
BORDER = "#30363D"
TEXT = "#E6EDF3"
MUTED = "#8B949E"
ACCENT = "#58A6FF"
GREEN = "#3FB950"
RED = "#F85149"


class MyAutoClicker:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("440x430")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.mouse = Controller()
        self.running = threading.Event()
        self.shutdown = threading.Event()
        self.cps = tk.IntVar(value=DEFAULT_CPS)
        self.click_count = 0
        self.count_lock = threading.Lock()

        self.setup_style()
        self.build_ui()

        self.click_thread = threading.Thread(
            target=self.click_loop, daemon=True
        )
        self.click_thread.start()

        self.hotkeys = GlobalHotKeys({
            "<f6>": self.toggle_from_hotkey
        })
        self.hotkeys.start()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.refresh_ui)

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Speed.Horizontal.TScale",
            background=PANEL,
            troughcolor=BORDER,
            sliderthickness=18
        )

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=26, pady=(24, 14))

        tk.Label(
            header, text="MY",
            font=("Segoe UI", 19, "bold"),
            bg=BG, fg=ACCENT
        ).pack(side="left")

        tk.Label(
            header, text="AUTOCLICKER",
            font=("Segoe UI", 17, "bold"),
            bg=BG, fg=TEXT
        ).pack(side="left", padx=(7, 0), pady=(2, 0))

        tk.Label(
            self.root,
            text="Simple. Fast. In your control.",
            font=("Segoe UI", 10),
            bg=BG, fg=MUTED
        ).pack(anchor="w", padx=28)

        panel = tk.Frame(
            self.root, bg=PANEL,
            highlightbackground=BORDER, highlightthickness=1
        )
        panel.pack(fill="x", padx=24, pady=22)

        top = tk.Frame(panel, bg=PANEL)
        top.pack(fill="x", padx=20, pady=(18, 5))

        tk.Label(
            top, text="CLICK SPEED",
            font=("Segoe UI", 10, "bold"),
            bg=PANEL, fg=MUTED
        ).pack(side="left")

        self.speed_label = tk.Label(
            top, text=f"{DEFAULT_CPS} CPS",
            font=("Segoe UI", 16, "bold"),
            bg=PANEL, fg=ACCENT
        )
        self.speed_label.pack(side="right")

        self.speed_slider = ttk.Scale(
            panel, from_=1, to=MAX_CPS,
            orient="horizontal",
            style="Speed.Horizontal.TScale",
            command=self.change_speed
        )
        self.speed_slider.set(DEFAULT_CPS)
        self.speed_slider.pack(fill="x", padx=20, pady=12)

        limits = tk.Frame(panel, bg=PANEL)
        limits.pack(fill="x", padx=20, pady=(0, 17))

        tk.Label(
            limits, text="1 CPS",
            bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Label(
            limits, text="MAX 100 CPS",
            bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="right")

        self.toggle_button = tk.Button(
            self.root,
            text="▶   Start Clicking   [F6]",
            command=self.toggle,
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT, fg="#08111F",
            activebackground="#79C0FF",
            activeforeground="#08111F",
            relief="flat", bd=0,
            cursor="hand2", height=2
        )
        self.toggle_button.pack(fill="x", padx=24, pady=(0, 15))

        status_frame = tk.Frame(self.root, bg=BG)
        status_frame.pack(fill="x", padx=28)

        self.status_dot = tk.Label(
            status_frame, text="●",
            font=("Segoe UI", 11),
            bg=BG, fg=RED
        )
        self.status_dot.pack(side="left")

        self.status_label = tk.Label(
            status_frame, text="Stopped",
            font=("Segoe UI", 10, "bold"),
            bg=BG, fg=MUTED
        )
        self.status_label.pack(side="left", padx=7)

        self.counter_label = tk.Label(
            status_frame, text="0 clicks",
            font=("Segoe UI", 10),
            bg=BG, fg=MUTED
        )
        self.counter_label.pack(side="right")

        tk.Label(
            self.root,
            text="F6  Toggle     •     Close window  Exit",
            font=("Segoe UI", 9),
            bg=BG, fg=MUTED
        ).pack(side="bottom", pady=17)

    def change_speed(self, value):
        speed = max(1, min(MAX_CPS, round(float(value))))
        self.cps.set(speed)
        self.speed_label.config(text=f"{speed} CPS")

    def toggle_from_hotkey(self):
        # Hotkey callbacks run outside Tk's UI thread.
        self.root.after(0, self.toggle)

    def toggle(self):
        if self.running.is_set():
            self.running.clear()
        else:
            self.running.set()

    def click_loop(self):
        while not self.shutdown.is_set():
            if not self.running.wait(timeout=0.05):
                continue

            start = time.perf_counter()

            try:
                self.mouse.click(Button.left, 1)
                with self.count_lock:
                    self.click_count += 1
            except Exception:
                self.running.clear()
                continue

            delay = 1.0 / max(1, self.cps.get())
            remaining = delay - (time.perf_counter() - start)

            if remaining > 0:
                self.shutdown.wait(remaining)

    def refresh_ui(self):
        if self.running.is_set():
            self.status_dot.config(fg=GREEN)
            self.status_label.config(text="Running", fg=GREEN)
            self.toggle_button.config(
                text="■   Stop Clicking   [F6]",
                bg=RED, activebackground="#FF7B72",
                fg="#FFFFFF", activeforeground="#FFFFFF"
            )
        else:
            self.status_dot.config(fg=RED)
            self.status_label.config(text="Stopped", fg=MUTED)
            self.toggle_button.config(
                text="▶   Start Clicking   [F6]",
                bg=ACCENT, activebackground="#79C0FF",
                fg="#08111F", activeforeground="#08111F"
            )

        with self.count_lock:
            count = self.click_count

        self.counter_label.config(text=f"{count:,} clicks")
        self.root.after(100, self.refresh_ui)

    def close(self):
        self.shutdown.set()
        self.running.clear()
        self.hotkeys.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MyAutoClicker(root)
    root.mainloop()
