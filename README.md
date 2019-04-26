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

The batch file will allow windows users to have a more simple menu for adjusting setting. Linux users can
also run the batch file but must install Wine to do so :D

## The set-up
To be able to use this editor, you will have to do the following:

1. Download the files here
2. Move all of these files into your \videos folder
3. Download and install Python 3 (Note: I recommend getting the 64-bit version)
4. Download and install get-pip (Note: You will need get-pip to download the needed libarys)
5. Download and install ffmpeg
6. Move ffmpeg.exe to the \videos folder
7. In control pannel, go to "System" -> "Advance system settings" -> "Enviroment Variables", find Path in System Variables list and double click it
8. Add the path to the python folder and the python scripts folder and then click ok to all the windows
9. Open cmd and run the following lines:
``cd \videos
  pip install -r requirements.txt``
10. Now double click jumpcutter.bat

The program should now be running and ready to use

## Building with nix
`nix-build` to get a script with all the libraries and ffmpeg, `nix-build -A bundle` to get a single binary.
