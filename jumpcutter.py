import argparse
import math
import os
import re
import traceback
from ast import literal_eval
from shutil import copyfile, rmtree
from subprocess import CalledProcessError, run

import numpy as np
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile

try:
    from youtube_dl import YoutubeDL as YtDL


    def downloadFile(url):
        ydl_opts = {
            "restrictfilenames": True
        }
        with YtDL(ydl_opts) as ytdl:
            info = ytdl.extract_info(url)
            return ytdl.prepare_filename(info)
except ImportError:
    def downloadFile(url):
        raise ModuleNotFoundError("youtube_dl module not found! Please install with \"pip install youtube_dl\"")


def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv, -minv)


def copyFrame(inFrame, outFrame):
    src = os.path.join(TEMP_FOLDER, "frame{:06d}".format(inFrame + 1) + ".jpg")
    dst = os.path.join(TEMP_FOLDER, "newFrame{:06d}".format(outFrame + 1) + ".jpg")
    if not os.path.isfile(src): return False
    copyfile(src, dst)
    if outFrame % 20 == 19: print(str(outFrame + 1) + " time-altered frames saved.", end="\r", flush=True)
    return True


def inputToOutputFilename(filename, formats=None):
    sep = filename.rpartition(".")
    return "{}_ALTERED.{}".format(sep[0], formats.lstrip(".") if formats else sep[2])


def createPath(s):
    try:
        if os.path.exists(TEMP_FOLDER): deletePath(s)
        os.mkdir(s)
    except OSError:
        raise OSError("Creation of the directory %s failed. (The TEMP folder may already exist. Delete or rename it, and try again.)")


def deletePath(s):  # Dangerous! Watch out!
    try:
        rmtree(s)
    except OSError:
        print("Deletion of the directory %s failed" % s)
        traceback.print_exc()


def safe_eval(expression):
    safe_expressions = {}
    code = compile(expression, "<string>", "eval")
    for name in code.co_names:
        if name not in safe_expressions: raise NameError(f"A unsafe expression '{name}' has been found during evaluation")
    return eval(expression, {"__builtins__": {}}, safe_expressions)


parser = argparse.ArgumentParser(description="Modifies a video file to play at different speeds when there is sound vs. silence.")
parser.add_argument(dest='name', metavar="File or URL", type=str, help="Provide a filename or a youtube video URL to process (cannot use the arguments like --file or --url to put url or file name)")
parser.add_argument('-f', '--file', dest="isFile", help="the video file you want modified. Optional parameter", action="store_true")
# clarification: if you use a video id, it is not a link and therefore needs to be defined as a link
parser.add_argument('-u', '--url', dest="isURL", help="A youtube video url to download and process. Optional parameter", action="store_true")
parser.add_argument('-y', '--overwrite', help="Automatically overwrite existing file", action="store_true")
parser.add_argument('-o', '--output-file', metavar="filename", dest="output_file", type=str, default="", help="the output file. (optional. if not included, it'll just modify the input file name, overwrites output_format)")
parser.add_argument('-O', '--output-format', metavar="Format", dest="output_format", type=str, default="", help="format of output video (optional. if not included uses input file)")
parser.add_argument('-s', '--silent-speed', metavar="Speed", dest="silent_speed", type=float, default=5.00, help="the speed that silent frames should be played at. 999999 for jumpcutting.")
parser.add_argument('-S', '--sounded-speed', metavar="Speed", dest="sounded_speed", type=float, default=1.00, help="the speed that sounded (spoken) frames should be played at. Typically 1.")
parser.add_argument('--silent-threshold', metavar="silence", dest="silent_threshold", type=float, default=0.03, help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges from 0 (silence) to 1 (max volume)")
parser.add_argument('-L', '--log-level', metavar="error", dest="log_level", type=str, default='error', help="change the log level of FFmpeg (Levels: quiet, panic, fatal, error, warning, info, verbose, debug, trace, or any number from 0)")
parser.add_argument('--frame-margin', metavar="margin", dest="frame_margin", type=float, default=1, help="some silent frames adjacent to sounded frames are included to provide context. How many frames on either the side of speech should be included? That's this variable.")
parser.add_argument('-fps', '--frame-rate', metavar="FPS", dest="frame_rate", type=float, default=0, help="frame rate of the input and output videos. (optional)")
parser.add_argument('--sample-rate', metavar="rate", dest="sample_rate", type=float, default=0, help="sample rate of the input and output videos")
parser.add_argument('-q', '--frame-quality', metavar="quality", dest="frame_quality", type=int, default=3, help="quality of frames to be extracted from input video. 1 is highest, 31 is lowest, 3 is the default.")
parser.add_argument('-audio', '--audio-only', default=False, action="store_true", dest="audio_only")

args = parser.parse_args()

FILE_OVERWRITE = args.overwrite
FRAME_RATE = args.frame_rate
SAMPLE_RATE = args.sample_rate
SILENT_THRESHOLD = args.silent_threshold
FRAME_SPREADAGE = args.frame_margin
LOG_LEVEL = str(args.log_level).lower() if re.search("quiet|panic|fatal|error|warning|info|verbose|debug|trace|\d+", str(args.log_level).lower()) else "error"
NEW_SPEED = [args.silent_speed, args.sounded_speed]
INPUT_FILE = downloadFile(args.name) if (re.match("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", args.name) or args.isURL) and not args.isFile else args.name
OUTPUT_FORMAT = args.output_format
FRAME_QUALITY = args.frame_quality
AUDIO_ONLY = args.audio_only

OUTPUT_FILE = args.output_file if args.output_file else inputToOutputFilename(INPUT_FILE, OUTPUT_FORMAT)

TEMP_FOLDER = "TEMP"
AUDIO_FADE_ENVELOPE_SIZE = 400  # smooth out transition's audio by quickly fading in/out (arbitrary magic number whatever)

createPath(TEMP_FOLDER)

command = "ffprobe -i '{0}' -v {1} -hide_banner -select_streams a -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1"\
    .format(INPUT_FILE, LOG_LEVEL)
run(command, stdout=open(os.path.join(TEMP_FOLDER, "sample_rate.txt"), "w"), check=True, shell=True)
SAMPLE_RATE = literal_eval(open(os.path.join(TEMP_FOLDER, "sample_rate.txt")).read()) if SAMPLE_RATE <= 0 else SAMPLE_RATE

if not AUDIO_ONLY:
    command = "ffprobe -i '{0}' -v {1} -hide_banner -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate"\
        .format(INPUT_FILE, LOG_LEVEL)
    run(command, stdout=open(os.path.join(TEMP_FOLDER, "fps.txt"), "w"), check=True, shell=True)
    FRAME_RATE = safe_eval(open(os.path.join(TEMP_FOLDER, "fps.txt")).read()) if FRAME_RATE <= 0 else FRAME_RATE
    if not FRAME_RATE > 0:
        raise ValueError("Invalid framerate, check your options or video or set manually (0 or below)")

if not AUDIO_ONLY:
    command = "ffmpeg -i '{0}' {1} -hide_banner -loglevel {2} -stats -qscale:v {3}" \
        .format(INPUT_FILE, os.path.join(TEMP_FOLDER, "frame%06d.jpg"), LOG_LEVEL, str(FRAME_QUALITY))
    run(command, check=True, shell=True)


command = "ffmpeg -i '{0}' -hide_banner -loglevel {1} -stats -ab 160k -ac 2 -ar {2} -vn {3}"\
    .format(INPUT_FILE, LOG_LEVEL, str(SAMPLE_RATE), os.path.join(TEMP_FOLDER, "audio.wav"))
run(command, check=True, shell=True)

sampleRate, audioData = wavfile.read(os.path.join(TEMP_FOLDER, "audio.wav"))
sampleRate = sampleRate if SAMPLE_RATE <= 0 else SAMPLE_RATE
audioSampleCount = audioData.shape[0]
maxAudioVolume = getMaxVolume(audioData)

samplesPerFrame = sampleRate / FRAME_RATE if not AUDIO_ONLY else sampleRate

audioFrameCount = int(math.ceil(audioSampleCount / samplesPerFrame))

hasLoudAudio = np.zeros(audioFrameCount)

for i in range(audioFrameCount):
    start = int(i * samplesPerFrame)
    end = min(int((i + 1) * samplesPerFrame), audioSampleCount)
    audiochunks = audioData[start:end]
    maxchunksVolume = float(getMaxVolume(audiochunks)) / maxAudioVolume
    if maxchunksVolume >= SILENT_THRESHOLD: hasLoudAudio[i] = 1

chunks = [[0, 0, 0]]
shouldIncludeFrame = np.zeros(audioFrameCount)
tempI = 0
for i in range(audioFrameCount):
    start = int(max(0, i - FRAME_SPREADAGE))
    end = int(min(audioFrameCount, i + 1 + FRAME_SPREADAGE))
    shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
    if i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i - 1]: chunks.append(
        [chunks[-1][1], i, shouldIncludeFrame[i - 1]])  # Did we flip?
    tempI = i

chunks.append([chunks[-1][1], audioFrameCount, shouldIncludeFrame[tempI - 1]])
chunks = chunks[1:]
del tempI

outputAudioData = np.zeros((0, audioData.shape[1]))
outputPointer = 0

lastExistingFrame = None
sFile = os.path.join(TEMP_FOLDER, "tempStart.wav")
eFile = os.path.join(TEMP_FOLDER, "tempEnd.wav")
outputFrame = 0
for chunk in chunks:
    audioChunk = audioData[int(chunk[0] * samplesPerFrame):int(chunk[1] * samplesPerFrame)]

    wavfile.write(sFile, SAMPLE_RATE, audioChunk)
    with WavReader(sFile) as reader:
        phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])]).run(reader, WavWriter(eFile, reader.channels, reader.samplerate))
    _, alteredAudioData = wavfile.read(eFile)
    leng = alteredAudioData.shape[0]
    endPointer = outputPointer + leng
    outputAudioData = np.concatenate((outputAudioData, alteredAudioData / maxAudioVolume))

    # outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume

    # smooth out transition's audio by quickly fading in/out

    if leng < AUDIO_FADE_ENVELOPE_SIZE:
        outputAudioData[outputPointer:endPointer] = 0  # audio is less than 0.01 sec, let's just remove it.
    else:
        mask = np.repeat((np.arange(AUDIO_FADE_ENVELOPE_SIZE) / AUDIO_FADE_ENVELOPE_SIZE)[:, np.newaxis], 2, axis=1)  # make the fade-envelope mask stereo
        outputAudioData[outputPointer:outputPointer + AUDIO_FADE_ENVELOPE_SIZE] *= mask
        outputAudioData[endPointer - AUDIO_FADE_ENVELOPE_SIZE:endPointer] *= 1 - mask

    if AUDIO_ONLY: continue  # skip rest of loop if audio only
    startOutputFrame = int(math.ceil(outputPointer / samplesPerFrame))
    endOutputFrame = int(math.ceil(endPointer / samplesPerFrame))
    for outputFrame in range(startOutputFrame, endOutputFrame):
        inputFrame = int(chunk[0] + NEW_SPEED[int(chunk[2])] * (outputFrame - startOutputFrame))
        didItWork = copyFrame(inputFrame, outputFrame)
        if didItWork:
            lastExistingFrame = inputFrame
        else:
            copyFrame(lastExistingFrame, outputFrame)

    outputPointer = endPointer
if not AUDIO_ONLY: print("%s time-altered frames saved." % (outputFrame + 1))

wavfile.write(os.path.join(TEMP_FOLDER, "audioNew.wav"), SAMPLE_RATE, outputAudioData)

# outputFrame = math.ceil(outputPointer/samplesPerFrame)
# for endGap in range(outputFrame,audioFrameCount):
#     copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)

if not AUDIO_ONLY:
    command = "ffmpeg -hide_banner -loglevel {0} -stats -framerate {1} -i {2} -i {3} -strict -2 '{4}'" \
        .format(LOG_LEVEL, str(FRAME_RATE), os.path.join(TEMP_FOLDER, "newFrame%06d.jpg"),
                os.path.join(TEMP_FOLDER, "audioNew.wav"), OUTPUT_FILE)
    if FILE_OVERWRITE: command += " -y"
    try:
        run(command, check=True, shell=True)
    except CalledProcessError:
        raise Exception("Either you have canceled the operation, or the operation has failed")
else:
    copyfile(os.path.join(TEMP_FOLDER, "audioNew.wav"), OUTPUT_FILE)

deletePath(TEMP_FOLDER)
