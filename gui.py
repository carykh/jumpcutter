import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip
import subprocess

import pkinter as pk


class Window(tk.Tk):
    def __init__(self):
        super(Window, self).__init__()
        self.title("Jump Cutter")
        self.columnconfigure(1, weight=1)

        # Main Widgets
        ttk.Label(self, text="Input File:").grid(row=0, column=0, sticky="e")
        self.input_file = pk.FilePicker(self)
        self.input_file.grid(row=0, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.input_file._entry, "The video file you want modified")

        ttk.Label(self, text="Output File:").grid(row=1, column=0, sticky="e")
        self.output_file = pk.FilePicker(self)
        self.output_file.grid(row=1, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.output_file._entry, "The modified video")

        ttk.Separator(self, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="we", padx=6)

        ttk.Label(self, text="Sounded Speed:").grid(row=3, column=0, sticky="e")
        self.sounded_speed = pk.EntryText(self, text="1.00")
        self.sounded_speed.grid(row=3, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.sounded_speed, "The speed that frame's with sound, above the threshold, should be played at")

        ttk.Label(self, text="Silent Speed:").grid(row=4, column=0, sticky="e")
        self.silent_speed = pk.EntryText(self, text="5.00")
        self.silent_speed.grid(row=4, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.silent_speed, "The speed that frame's with sound, below the threshold, should be played at")

        advanced_settings = pk.ToggledLabelFrame(self, "Hide Advanced Settings", "Show Advanced Settings")
        advanced_settings.grid(row=5, column=0, columnspan=2, sticky="nesw", padx=6, pady=2)
        advanced_settings.frame.columnconfigure(1, weight=1)
        advanced_settings._button.configure(width=30)

        run = ttk.Button(self, text="Run", command=self.run)
        run.grid(row=6, column=0, columnspan=2, pady=6)

        # Advanced Settings Widgets
        ttk.Label(advanced_settings.frame, text="Silent Threshold:").grid(row=0, column=0, sticky="e")
        self.silent_threshold = pk.EntryText(advanced_settings.frame, text="0.03")
        self.silent_threshold.grid(row=0, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.silent_threshold, "The volume amount that frames' audio needs to surpass to be consider \"sounded\"")

        ttk.Separator(advanced_settings.frame, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="we", padx=6)

        ttk.Label(advanced_settings.frame, text="Sample Rate:").grid(row=2, column=0, sticky="e")
        self.sample_rate = pk.EntryText(advanced_settings.frame, text="44100")
        self.sample_rate.grid(row=2, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.sample_rate, "The sample rate of the input and output videos")

        ttk.Separator(advanced_settings.frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="we", padx=6)

        ttk.Label(advanced_settings.frame, text="Frame Margin:").grid(row=4, column=0, sticky="e")
        self.frame_margin = pk.EntryText(advanced_settings.frame, text="1")
        self.frame_margin.grid(row=4, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.frame_margin, "The amount of silent frames adjacent to sounded frames to be included")

        ttk.Label(advanced_settings.frame, text="Frame Rate:").grid(row=5, column=0, sticky="e")
        self.frame_rate = pk.EntryText(advanced_settings.frame, text="30")
        self.frame_rate.grid(row=5, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.frame_rate, "The frame rate of the input and output videos")

        ttk.Label(advanced_settings.frame, text="Frame Quality:").grid(row=6, column=0, sticky="e")
        self.frame_quality = pk.EntryText(advanced_settings.frame, text="3")
        self.frame_quality.grid(row=6, column=1, sticky="we", padx=6, pady=2)
        Hovertip(self.frame_quality, "The quality of frames to be extracted from the input video")

    def run(self):
        subprocess.call(f"python jumpcutter.py --input_file {self.input_file.get()} --output_file {self.output_file.get()} --silent_threshold {self.silent_threshold} --sounded_speed {self.sounded_speed} --silent_speed {self.silent_speed} --frame_margin {self.frame_margin} --sample_rate {self.sample_rate} --frame_rate {self.frame_rate} --frame_quality {self.frame_quality}")


if __name__ == "__main__":
    window = Window()
    window.mainloop()
