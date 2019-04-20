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

## Arguments
### Required
`--input_file` - the video you want to be modified 〖_`string`_ 〗    
_**OR**_
`--url` - An YouTube URL you want to be downloaded & processed 〖_`string`_ 〗    
### Optional  
`--output_file` - File to save the modified video to. If not specified, the file from `--input_file` will be used. 〖_`string`_ 〗    
`--silent_threshold` - The volume amount the frames' audio will be considered 'sounded'. Range: 0 (silence) to 1 (max volume) 〖_default: 0.03 `float`_ 〗    
`--sounded_speed` - The speed that 'sounded' (spoken) frames will be played in. Typically 1. 〖_default: 1.00 `float`_ 〗    
`--silent_speed` - The speed that silent frames will be played at. `999999` for jumpcutting. 〖_default: 5.00 `float`_ 〗    
`--frame_margin` - This value is used to determine silent frames next to the sounded frames, to provide more context. 〖_default: 1 `float`_ 〗  
`--sample_rate` - Sample rate of the input and output videos' audio. 〖_default: 44100 `float`_ 〗  
`--frame_rate` - Framerate of the input and output videos **If you specify the wrong amount than the input video, your audio will have sync issues!** 〖_default: 30 `float`_ 〗  
`--frame_quality` - Quality of the frames to be extracted. Range: 1 (highest) - 31 (lowest) 〖_default: 3 `int`_ 〗  
## Windows  
Type `python -m pip install -r requirements.txt` in your `jumpcutter.py` folder. Also, you need [ffmpeg](https://ffmpeg.zeranoe.com/builds/). I suggest you download it, unzip, and put everything from `bin` to your system32 folder, as it is already in the PATH. Or make another folder and add it to the PATH variable. It needs to be callable from any location in CMD.
