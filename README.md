# jumpcutter
Automatically edits videos. Explanation here: https://www.youtube.com/watch?v=DQ8orIurGxw

## Usage:

`jumpcutter -h` will give you a list of all possible launch options with brief description of what they do

Launch Options:
- `--input_file`, the video file you want modified (*required unless `--url` is used*)
- `--url`, a youtube url to download and process (optional, if used `--input_file` should not be used)
- `--output_file`, the name of the output file. (default: modifies input file name automatically)
- `--silent_threshold`, the volume amount that a frames' audio needs to surpass to be consider "sounded". It ranges from 0 (silence) to 1 (max volume). (default: 0.03)
- `--sounded_speed`, the speed that "sounded" frames should be played at. (default: 1)
- `--silent_speed`, the speed that silent frames should be played at. 999999 to cut all "non-sounded" frame sections. (default: 5)
- `--frame_margin`, silent frames adjacent to sounded frames not removed to provide context/reduce nausea. "How many frames on either the side of speech should be included?" That's this variable. (default: 1)
- `--sample_rate`, sample rate of the input and output audio channels. (default: 44100)
- `--frame_rate`, frame rate of the input and output videos. optional... I try to find it out myself, but it doesn't always work. (default: 30)
- `--frame_quality`, quality of frames to be extracted from input video. 1 is highest, 31 is lowest. (default: 3)

ie. `jumpcutter --input_file cat.mp4 --sounded_speed 1 --silent_speed 999999` would automatically edit my cat video to only include parts of the video where there is noise (most likely the cat meowing :))) )

## Some heads-up:

It uses Python 3.

It works on Ubuntu 16.04 and Windows 10. (It might work on other OSs too, we just haven't tested it yet.)

This program relies heavily on ffmpeg. It will start subprocesses that call ffmpeg, so be aware of that!

As the program runs, it saves every frame of the video as an image file in a
temporary folder. If your video is long, this could take a LOT of space.
I have processed 17-minute videos completely fine, but be wary if you're gonna go longer.

### Executable

Currently has a Windows 64-bit executable, only requires that you have ffmpeg installed and added to PATH, which is described in detail in *build.txt* in the dist.zip . This requires people on other platforms to contribute executables for other platforms. Latest build (1.01) available below:

http://www.mediafire.com/file/x5ayz8fjqvvsslj/dist_build_1-01.zip/file

Hashes:
 - SHA1: 9dfe7a5aba31f6659f50374f1a51167b5a25a0db
 - MD5: d16354bcb7719513e7ce45cd820c150c

## Building with nix
`nix-build` to get a script with all the libraries and ffmpeg, `nix-build -A bundle` to get a single binary.

### Future Goals

- Adding GUI and deprecating launch options (just a simple selector/input interface)
- Android
