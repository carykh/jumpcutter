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

        entry_width = 8
        row = 0

        # Main Widgets
        filetypes = [("MP4 Files", "*.mp4"), ("All Files", "*.*")]

        self.input_file = None
        self.input_label = None
        self.video_type = tk.BooleanVar()

        def input_type():
            if self.input_file is not None:
                self.input_file.grid_forget()

            if self.input_label is not None:
                self.input_label.grid_forget()

            if not self.video_type.get():
                input_label_text = "Input File:"

                self.input_file = pk.FilePicker(self, filetypes=filetypes)
                Hovertip(self.input_file._entry, "The video file you want modified")

            else:
                input_label_text = "YouTube Link:"

                self.input_file = ttk.Entry(self)
                Hovertip(self.input_file, "The YouTube video you want modified")

            self.input_label = ttk.Label(self, text=input_label_text)
            self.input_label.grid(row=0, column=0, sticky="e")
            self.input_file.grid(row=0, column=1, columnspan=2, sticky="we", padx=6, pady=2)

        input_type()

        row += 1
        self.video_type = tk.BooleanVar()
        self.file_radio_frame = ttk.Frame(self)
        self.file_radio_frame.columnconfigure((0, 1), weight=1)
        self.file_radio_frame.grid(row=row, column=0, columnspan=3, sticky="nesw")
        ttk.Radiobutton(self.file_radio_frame, text="Local File", variable=self.video_type, value=False, command=input_type).grid(row=row, column=0)
        ttk.Radiobutton(self.file_radio_frame, text="YouTube Link", variable=self.video_type, value=True, command=input_type).grid(row=row, column=1)

        row += 1
        ttk.Label(self, text="Output File:").grid(row=row, column=0, sticky="e")
        self.output_file = pk.FilePicker(self, "save", filetypes=filetypes, defaultextension=".mp4")
        self.output_file.grid(row=row, column=1, columnspan=2, sticky="we", padx=6, pady=2)
        Hovertip(self.output_file._entry, "The modified video")

        row += 1
        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="we", padx=6)

        row += 1
        ttk.Label(self, text="Sounded Speed:").grid(row=row, column=0, sticky="e")
        self.sounded_speed = pk.EntrySpinbox(self, text="1.00", to=50, increment=0.01, format_="%0.2f", width=entry_width)
        self.sounded_speed_scale = pk.RoundingScale(self, to=50, precision=2, variable=self.sounded_speed._variable)
        self.sounded_speed_scale.grid(row=row, column=1, sticky="we")
        self.sounded_speed.grid(row=row, column=2, padx=6, pady=2)
        Hovertip(self.sounded_speed, "The speed that frame's with sound, above the threshold, should be played at")

        row += 1
        ttk.Label(self, text="Silent Speed:").grid(row=row, column=0, sticky="e")
        self.silent_speed = pk.EntrySpinbox(self, text="5.00", to=50, increment=0.01, format_="%0.2f", width=entry_width)
        self.sounded_speed_scale = pk.RoundingScale(self, to=50, precision=2, variable=self.silent_speed._variable)
        self.sounded_speed_scale.grid(row=row, column=1, sticky="we")
        self.silent_speed.grid(row=row, column=2, padx=6, pady=2)
        Hovertip(self.silent_speed, "The speed that frame's with sound, below the threshold, should be played at")

        row += 1
        advanced_settings = pk.ToggledLabelFrame(self, "Hide Advanced Settings", "Show Advanced Settings")
        advanced_settings.grid(row=row, column=0, columnspan=3, sticky="nesw", padx=6, pady=2)
        advanced_settings.frame.columnconfigure(1, weight=1)
        advanced_settings._button.configure(width=30)

        row += 1
        run = ttk.Button(self, text="Run", command=self.run)
        run.grid(row=row, column=0, columnspan=3, pady=6)

        # Advanced Settings Widgets
        ttk.Label(advanced_settings.frame, text="Silent Threshold:").grid(row=0, column=0, sticky="e")
        self.silent_threshold = pk.EntrySpinbox(advanced_settings.frame, text="0.03", to=1, increment=0.01, format_="%0.2f", width=entry_width)
        self.silent_threshold_scale = pk.RoundingScale(advanced_settings.frame, to=1, precision=2, variable=self.silent_threshold._variable)
        self.silent_threshold_scale.grid(row=0, column=1, sticky="we")
        self.silent_threshold.grid(row=0, column=2, padx=6, pady=2)
        Hovertip(self.silent_threshold, "The volume amount that frames' audio needs to surpass to be consider \"sounded\"")

        ttk.Separator(advanced_settings.frame, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="we", padx=6)

        ttk.Label(advanced_settings.frame, text="Sample Rate:").grid(row=2, column=0, sticky="e")
        self.sample_rate = pk.EntrySpinbox(advanced_settings.frame, text="44100", to=44100 * 3, width=entry_width)
        self.sample_rate_scale = pk.RoundingScale(advanced_settings.frame, to=44100 * 3, precision=0, variable=self.sample_rate._variable)
        self.sample_rate_scale.grid(row=2, column=1, sticky="we")
        self.sample_rate.grid(row=2, column=2, padx=6, pady=2)
        Hovertip(self.sample_rate, "The sample rate of the input and output videos")

        ttk.Separator(advanced_settings.frame, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="we", padx=6)

        ttk.Label(advanced_settings.frame, text="Frame Margin:").grid(row=4, column=0, sticky="e")
        self.frame_margin = pk.EntrySpinbox(advanced_settings.frame, text="1", to=144, width=entry_width)
        self.frame_margin_scale = pk.RoundingScale(advanced_settings.frame, to=144, precision=0, variable=self.frame_margin._variable)
        self.frame_margin_scale.grid(row=4, column=1, sticky="we")
        self.frame_margin.grid(row=4, column=2, padx=6, pady=2)
        Hovertip(self.frame_margin, "The amount of silent frames adjacent to sounded frames to be included")

        ttk.Label(advanced_settings.frame, text="Frame Rate:").grid(row=5, column=0, sticky="e")
        self.frame_rate = pk.EntrySpinbox(advanced_settings.frame, text="30", to=144, width=entry_width)
        self.frame_rate_scale = pk.RoundingScale(advanced_settings.frame, to=144, precision=0, variable=self.frame_rate._variable)
        self.frame_rate_scale.grid(row=5, column=1, sticky="we")
        self.frame_rate.grid(row=5, column=2, padx=6, pady=2)
        Hovertip(self.frame_rate, "The frame rate of the input and output videos")

        ttk.Label(advanced_settings.frame, text="Frame Quality:").grid(row=6, column=0, sticky="e")
        self.frame_quality = pk.EntrySpinbox(advanced_settings.frame, text="3", to=31, width=entry_width)
        self.frame_quality_scale = pk.RoundingScale(advanced_settings.frame, to=31, precision=0, variable=self.frame_quality._variable)
        self.frame_quality_scale.grid(row=6, column=1, sticky="we")
        self.frame_quality.grid(row=6, column=2, padx=6, pady=2)
        Hovertip(self.frame_quality, "The quality of frames to be extracted from the input video")

    def run(self):
        subprocess.call(f"python jumpcutter.py {'--input_file' if not self.video_type else '--url'} {self.input_file.get()} --output_file {self.output_file.get()} --silent_threshold {self.silent_threshold.get()} --sounded_speed {self.sounded_speed.get()} --silent_speed {self.silent_speed.get()} --frame_margin {self.frame_margin.get()} --sample_rate {self.sample_rate.get()} --frame_rate {self.frame_rate.get()} --frame_quality {self.frame_quality.get()}")


if __name__ == "__main__":
    window = Window()
    window.mainloop()
