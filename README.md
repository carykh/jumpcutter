# jumpcutter
Automatically edits videos. Explanation here: https://www.youtube.com/watch?v=DQ8orIurGxw

## Some heads-up:

It uses Python 3.

It works on Ubuntu 16.04 and Windows 10. (It might work on other OSs too, we just haven't tested it yet.)

This program relies heavily on ffmpeg. It will start subprocesses that call ffmpeg, so be aware of that!

As the program runs, it saves every frame of the video as an image file in a
temporary folder. If your video is long, this could take a LOT of space.
I have processed 17-minute videos completely fine, but be wary if you're gonna go longer.

I want to use pyinstaller to turn this into an executable, so non-techy people
can use it EVEN IF they don't have Python and all those libraries. Jabrils 
recommended this to me. However, my pyinstaller build did not work. :( HELP

## Building with nix
`nix-build` to get a script with all the libraries and ffmpeg, `nix-build -A bundle` to get a single binary.

## Install & run

#### With executeable

- Download & extract [jumpcutter.zip](https://github.com/carykh/jumpcutter/files/3964820/jumpcutter.zip)
- Open `cmd`
- Run `C:\YOUR/PATH\jumpcutter.exe --input_file C:\YOUR\FILE.mp4 --sounded_speed 1 --silent_speed 99999 --frame_margin 2`

#### With python

- Open cmd/terminal, and `cd` to the jumpcutter folder.
- 'pip install -r requirements.txt'
- Run: `python jumpcutter.py --input_file C:\YOUR\FILE.mp4 --sounded_speed 1 --silent_speed 99999 --frame_margin 2`

#### Install ffmpeg

If you have no ffmpeg installed, follow these steps:

##### Linux

`sudo apt-get install ffmpeg`

##### Windows

[Read this guide](https://windowsloop.com/install-ffmpeg-windows-10/)