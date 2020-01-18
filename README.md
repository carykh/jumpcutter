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

## Example Setup
using virtualenv
```
    cd jumpcutter
    virtualenv --python python3 env
    source env/bin/activate
    pip install -r requirements.txt
```

## Example Usage

### Jumpcut
regular speed for talking and 99,999,999% speedup during silence, original at 60fps
```python jumpcutter.py --input_file slow_meme.mp4 --sounded_speed 1 --silent_speed 999999 --frame_margin 2 --frame_rate 60```

### Lecture Speedup
bit faster talking and 500% speedup during silence, original at 60fps
```python jumpcutter.py --input_file dull_lecture.mp4 --sounded_speed 1.2 --silent_speed 5 --frame_margin 2 --frame_rate 60```


## Expectations
- Temporary files are placed in a new directory called 'TEMP'
- Default output file is `[file_name]_ALTERNED.[file extension]`
- Time to process a 6min video of 1346x904@60fps using H.264, AAC on a MacBookPro took 9min 45sec.  Nearly *1:1.5 video to processing time*

