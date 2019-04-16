# jumpcutter
Automatically edits videos. Explanation here: https://www.youtube.com/watch?v=DQ8orIurGxw

## Some heads-up:

It uses Python 3.

It works on Ubuntu 16.04 and Windows 10. (It might work on other OSs too, we just haven't tested it yet.)

This program relies heavily on ffmpeg. It will start subprocesses that call ffmpeg, so be aware of that!

As the program runs, it saves every frame of the video as an image file in a
temporary folder. If your video is long, this could take a LOT of space.
I have processed 17-minute videos completely fine, but be wary if you're gonna go longer.

### Executable

Currently has a Windows 64-bit executable, only requires that you have ffmpeg installed and added to PATH, which is described in detail in *build.txt* in the dist.zip . This requires people on other platforms to contribute executables for other platforms. Available below:

http://www.mediafire.com/file/jmgjqa1735j1v1p/dist_build.zip/file

Hashes:
 - SHA1: 04cfcc8644ea2a6d298f978186003a4e8558e206
 - MD5: 7babd788272e080608e2a7817804c01b

## Building with nix
`nix-build` to get a script with all the libraries and ffmpeg, `nix-build -A bundle` to get a single binary.

### Future Goals

- Adding GUI and deprecating launch options (just a simple selector/input interface)
- Android
