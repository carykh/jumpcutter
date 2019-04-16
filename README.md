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

## Using the .exe
JABRILS WUZ HERE
The standalone exe works just like the python script, but has all dependencies packaged with it. Follow these steps to use it if on Windows:
1. Enter the 'dist' folder, or any folder containing jumpcutter.exe
2. Open your terminal of choice
3. type `.\jumpcutter -h` to see all availible options

If you'd like to be able to access jumpcutter from anywhere on your computer, add the 'dist' folder into your environment variables, you can do that by:
1. Going to Start on Windows (or press the windows key)
2. Search for "Edit the system Environment Variables" (just start typing if that start menu is up to search)
3. Click that option
4. Click Environment Variables button at the bottom
5. In System Variables panel, look for "Path"
6. Add the full directory to 'dist' to this list of environment variables
7. You should now from anywhere on your computer be able to type simply `jumpcutter -h` from a terminal & it should work!

& remember if you're reading this, you've been hax!