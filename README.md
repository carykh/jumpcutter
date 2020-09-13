![image](https://user-images.githubusercontent.com/46163555/93026937-aef09e80-f5d7-11ea-9caf-e929fe461a07.png)


# jumpcutter + PySimpleGUI

This project is a mashup between jumpcutter, by carykh, and a front-end GUI using PySimpleGUI.

The original jumpcutter.py code has had a single line modification, not because of the GUI, but because of an error that's generated if a sample rate is chosen.  This error is likely due to a change in one of the packages being used by jumpcutter.  The argparse definition says it's a float, but it should have said int.

Code was changed to:

```python
parser.add_argument('--sample_rate', type=int, default=44100, help="sample rate of the input and output videos")
```
## GUI Integration

To start the GUI, run the file jumpcutter_gui.py.  This GUI integrates with the jumpcutter.py file by "running" it as if it were a command line program.  It's launched as a subprocess with the parameters collected using the GUI being passed as arguments to the program.

## GUI

When GUI is initially started it looks like this, with default parameters filled in.  These are the same defaults as the jumpcutter.py file has specified, so it's safe for you to clear them all if you don't need to change any of them.  A handy "Clear All" button is provided to do this.

![image](https://user-images.githubusercontent.com/46163555/93027127-e14ecb80-f5d8-11ea-839f-c3c2bfc0c446.png)

## PyCharm Edit Button

If you want to be able to launch PyCharm to edit the code using the "PyCharm Me" button, you will need to change the `PYCHARM` constant located at the top of the program.  It's currently set to:

```python
PYCHARM = r"C:\Program Files\JetBrains\PyCharm Community Edition 2019.1.1\bin\pycharm.bat"
```

If you locate your PyCharm folder, you should be able to locate the batch file in the bin folder.  If it's not an important feature to you, simply delete the button.

## Temp Limitiations

Things have been thrown together a bit hastily.  A couple of limitations

* Filenames need to contain no spaces at the moment (including the path).  
* The URL downloading doesn't appear to work, or it didn't the first time I tried it

I'll get to these eventually.  The GUI was put together go I could easily process my YouTube videos.  I processed my entire PySimpleGUI 2020 Playlist and have been updating the videos, adding them to this new playlist:

https://www.youtube.com/playlist?list=PLl8dD0doyrvF1nLakJJ7sl8OX2YSHclqn

## Incredible Tool!!

OK, so the reason this tool has a GUI added is that it's a miraculous tool in my opinion.  At least it was for my videos.  They all feel "tighter" to me.  The time I spend fumbling around typing, trying not to make mistakes, all the while not talking adds up to about 18% - 20% of my videos.  That's the amount of time, on average, each video was compressed.  Over the whole series, that's quite a bit of time.  Not only do they sound better, but viewers actually save real time viewing them.  It's a win win.

Hopefully your videos will get the same kind of benefits mine did.  


The remainder of the readme is from Cary's original repo:
------------------------------------

## jumpcutter
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
