# jumpcutter ✂
Automatically edits videos. Explanation here: https://www.youtube.com/watch?v=DQ8orIurGxw
Go here for a more polished version of this software that my friends and I have been working on for the last year or so: https://jumpcutter.com/

## Some heads-up:

It uses Python 3.

It works on Ubuntu 16.04 and Windows 10. (It might work on other OSs too, we just haven't tested it yet.)

This program relies heavily on ffmpeg. It will start subprocesses that call ffmpeg, so be aware of that!

**⚠ As the program runs, it saves every frame of the video as an image file in a
temporary folder. If your video is long, this could take a LOT of space.
I have processed 17-minute videos completely fine, but be wary if you're gonna go longer.**


I wanted to use pyinstaller to turn this into an executable, so non-techy people
can use it EVEN IF they don't have Python and all those libraries. Jabrils 
recommended this to me. However, my pyinstaller build did not work. :( HELP

## Install prerequisites
Do `pip install scipy, numpy, pillow, audiotsm, pytube` to get all the dependencies.

**Make sure to install [ffmpeg codex](https://ffmpeg.org/download.html)** and to put the exe on `C:\Windows` folder (you will need admin rights to do so)

## instant jumpcut
 `instantjumpcut.py` is a more user friendly version. It makes so you can run it without writing the command every time, just run it. Just remember to have the url or file name in hand.

## Example command

`python jumpcutter.py --input_file input_video.mp4 --output_file output_video.mp4 --sounded_speed 1 --silent_speed 999999 --frame_margin 2 `
This takes the file `input_video.mp4` and gives it a jumpcut effect on silent parts then saves it as output_video.mp4

Heres a fun one `python jumpcutter.py --url https://www.youtube.com/watch?v=DQ8orIurGxw  --output_file output2_video.mp4 --sounded_speed 999999 --silent_speed 1 --frame_margin 2 `
it takes carykh's video about this code and keeps only the silent parts in the video

**Remember that if you need help use `python jumpcutter.py -h` it shows a more information about what each argument does.**

## Building with nix
`nix-build` to get a script with all the libraries and ffmpeg, `nix-build -A bundle` to get a single binary.
