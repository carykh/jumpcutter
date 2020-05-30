import argparse
import math
import os
import re
import subprocess
from shutil import copyfile, rmtree

import numpy as np
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile

try:
    from youtube_dl import YoutubeDL as YtDL


    def downloadFile(url):
        with YtDL() as ytdl:
            info = ytdl.extract_info(url)
            return ytdl.prepare_filename(info)
except ImportError as err:
    def downloadFile(url):
        assert False, "youtube_dl module not found! Please install with \"pip install youtube_dl\"\n{0}".format(
            str(err))


def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv, -minv)


def copyFrame(inFrame, outFrame):
    src = TEMP_FOLDER + "/frame{:06d}".format(inFrame + 1) + ".jpg"
    dst = TEMP_FOLDER + "/newFrame{:06d}".format(outFrame + 1) + ".jpg"
    if not os.path.isfile(src): return False
    copyfile(src, dst)
    if outFrame % 20 == 19: print(str(outFrame + 1) + " time-altered frames saved.", end="\r", flush=True)
    return True


def inputToOutputFilename(filename, formats=None):
    dotIndex = filename.rfind(".")
    return filename[:dotIndex] + "_ALTERED" + (
        filename[dotIndex:] if formats is None or formats == "" else formats if "." in formats else "." + formats)


def createPath(s):
    # assert (not os.path.exists(s)), "The filepath "+s+" already exists. Don't want to overwrite it. Aborting."

    try:
        if os.path.exists(TEMP_FOLDER): deletePath(s)
        os.mkdir(s)
    except OSError:
        assert False, "Creation of the directory %s failed. (The TEMP folder may already exist. Delete or rename it, " \
                      "and try again.)"


def deletePath(s):  # Dangerous! Watch out!
    try:
        rmtree(s)
    except OSError:
        print("Deletion of the directory %s failed" % s)
        print(OSError)


parser = argparse.ArgumentParser(description="Modifies a video file to play at different speeds when there is sound vs. silence.")
parser.add_argument('-i', '--input_file', type=str, help="the video file you want modified")
parser.add_argument('-u', '--url', type=str, help="A youtube video url to download and process")
parser.add_argument('-y', '--overwrite', help="Automatically overwrite existing file", action="store_true")
parser.add_argument('-o', '--output_file', type=str, default="", help="the output file. (optional. if not included, it'll just modify the input file name, overwrites output_format)")
parser.add_argument('-O', '--output_format', type=str, default="", help="format of output video (optional. if not included uses input)")
parser.add_argument('--silent_threshold', type=float, default=0.03, help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges from 0 (silence) to 1 (max volume)")
parser.add_argument('-S', '--sounded_speed', type=float, default=1.00, help="the speed that sounded (spoken) frames should be played at. Typically 1.")
parser.add_argument('-s', '--silent_speed', type=float, default=5.00, help="the speed that silent frames should be played at. 999999 for jumpcutting.")
parser.add_argument('-L', '--loglevel', type=str, default='error', help="change the log level of FFmpeg (Levels: quiet, panic, fatal, error, warning, info, verbose, debug, trace)")
parser.add_argument('--frame_margin', type=float, default=1, help="some silent frames adjacent to sounded frames are included to provide context. How many frames on either the side of speech should be included? That's this variable.")
parser.add_argument('--sample_rate', type=float, default=0, help="sample rate of the input and output videos")
parser.add_argument('-fps', '--frame_rate', type=float, default=0, help="frame rate of the input and output videos. optional... I try to find it out myself, but it doesn't always work.")
parser.add_argument('-q', '--frame_quality', type=int, default=3, help="quality of frames to be extracted from input video. 1 is highest, 31 is lowest, 3 is the default.")

args = parser.parse_args()

FILE_OVERWRITE = args.overwrite
FRAME_RATE = args.frame_rate
SAMPLE_RATE = args.sample_rate
SILENT_THRESHOLD = args.silent_threshold
FRAME_SPREADAGE = args.frame_margin
LOG_LEVEL = str(args.loglevel).lower() if re.search("quiet|panic|fatal|error|warning|info|verbose|debug|trace|\d+", str(args.loglevel).lower()) else "error"
NEW_SPEED = [args.silent_speed, args.sounded_speed]
INPUT_FILE = downloadFile(args.url) if args.url is not None else args.input_file
OUTPUT_FORMAT = args.output_format
FRAME_QUALITY = args.frame_quality

assert INPUT_FILE is not None, "why u put no input file, that dum"

OUTPUT_FILE = args.output_file if args.output_file else inputToOutputFilename(INPUT_FILE, OUTPUT_FORMAT)

TEMP_FOLDER = "TEMP"
AUDIO_FADE_ENVELOPE_SIZE = 400  # smooth out transition's audio by quickly fading in/out (arbitrary magic number whatever)

createPath(TEMP_FOLDER)

command = "ffprobe -v quiet -hide_banner -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 \"" + INPUT_FILE + "\""
subprocess.run(command, shell=True, stdout=open(os.path.join(TEMP_FOLDER, "sample_rate.txt"), "w"), check=True)
SAMPLE_RATE = eval(open(os.path.join(TEMP_FOLDER, "sample_rate.txt")).read()) if SAMPLE_RATE <= 0 else SAMPLE_RATE

command = "ffprobe -v quiet -hide_banner -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate \"" + INPUT_FILE + "\""
subprocess.run(command, shell=True, stdout=open(os.path.join(TEMP_FOLDER, "fps.txt"), "w"), check=True)
FRAME_RATE = eval(open(os.path.join(TEMP_FOLDER, "fps.txt")).read()) if FRAME_RATE <= 0 else FRAME_RATE
assert FRAME_RATE > 0 and FRAME_RATE != "", "Invalid framerate, check your options or video or set manually (0 and below)"

command = "ffmpeg -i \"" + INPUT_FILE + "\" -hide_banner -loglevel " + LOG_LEVEL + " -stats -qscale:v " + str(FRAME_QUALITY) + " " + os.path.join(TEMP_FOLDER, "frame%06d.jpg")
subprocess.run(command, shell=True, check=True)

command = "ffmpeg -i \"" + INPUT_FILE + "\" -hide_banner -loglevel " + LOG_LEVEL + " -stats -ab 160k -ac 2 -ar " + str(SAMPLE_RATE) + " -vn " + os.path.join(TEMP_FOLDER, "audio.wav")
subprocess.run(command, shell=True, check=True)

sampleRate, audioData = wavfile.read(os.path.join(TEMP_FOLDER, "audio.wav"))
sampleRate = sampleRate if SAMPLE_RATE <= 0 else SAMPLE_RATE
audioSampleCount = audioData.shape[0]
maxAudioVolume = getMaxVolume(audioData)

samplesPerFrame = sampleRate / FRAME_RATE

audioFrameCount = int(math.ceil(audioSampleCount / samplesPerFrame))

hasLoudAudio = np.zeros(audioFrameCount)

for i in range(audioFrameCount):
    start = int(i * samplesPerFrame)
    end = min(int((i + 1) * samplesPerFrame), audioSampleCount)
    audiochunks = audioData[start:end]
    maxchunksVolume = float(getMaxVolume(audiochunks)) / maxAudioVolume
    if maxchunksVolume >= SILENT_THRESHOLD:
        hasLoudAudio[i] = 1

chunks = [[0, 0, 0]]
shouldIncludeFrame = np.zeros(audioFrameCount)
tempI = 0
for i in range(audioFrameCount):
    start = int(max(0, i - FRAME_SPREADAGE))
    end = int(min(audioFrameCount, i + 1 + FRAME_SPREADAGE))
    shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
    if i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i - 1]:  # Did we flip?
        chunks.append([chunks[-1][1], i, shouldIncludeFrame[i - 1]])
    tempI = i

chunks.append([chunks[-1][1], audioFrameCount, shouldIncludeFrame[tempI - 1]])
chunks = chunks[1:]

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
print("%s time-altered frames saved." % (outputFrame + 1))

wavfile.write(os.path.join(TEMP_FOLDER, "audioNew.wav"), SAMPLE_RATE, outputAudioData)

# outputFrame = math.ceil(outputPointer/samplesPerFrame)
# for endGap in range(outputFrame,audioFrameCount):
#     copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)

command = "ffmpeg -hide_banner -loglevel " + LOG_LEVEL + " -stats -framerate " + str(FRAME_RATE) + " -i " + os.path.join(TEMP_FOLDER, "newFrame%06d.jpg") + " -i " + os.path.join(TEMP_FOLDER, "audioNew.wav") + " -strict -2 \"" + OUTPUT_FILE + "\""
if FILE_OVERWRITE: command += " -y"
try:
    subprocess.run(command, shell=True, check=True)
except subprocess.CalledProcessError:
    raise Exception("Either you have canceled the operation, or the operation has failed")

deletePath(TEMP_FOLDER)
