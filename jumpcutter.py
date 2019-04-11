import argparse
import math
import numpy as np
import os
import re
import subprocess

from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from pytube import YouTube
from scipy.io import wavfile
from shutil import copyfile, rmtree

def downloadFile(url):
    name = YouTube(url).streams.first().download()
    newname = name.replace(' ','_')
    os.rename(name,newname)
    return newname

def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv, -minv)


def copyFrame(inputFrame, outputFrame):
    src = TEMP_FOLDER + "/frame{:06d}".format(inputFrame + 1) + ".jpg"
    dst = TEMP_FOLDER + "/newFrame{:06d}".format(outputFrame + 1) + ".jpg"
    if not os.path.isfile(src):
        return False
    copyfile(src, dst)
    if outputFrame % 20 == 19:
        print(str(outputFrame + 1) + " time-altered frames saved.")
    return True


def inputToOutputFilename(filename):
    dotIndex = filename.rfind(".")
    return filename[:dotIndex] + "_ALTERED" + filename[dotIndex:]


def createPath(s):
    # assert (not os.path.exists(s)), "The filepath "+s+" already exists. Don't want to overwrite it. Aborting."

    try:
        os.mkdir(s)
    except OSError:
        while "the answer is invalid":
            reply = input(f"Directory {s} already exists. Delete it? [Y/n] ").lower().strip() or "y"
            if reply[:1] == 'y':
                deletePath(s)
                return createPath(s)
            if reply[:1] == 'n':
                return exit(0)


def deletePath(s):  # Dangerous! Watch out!
    try:
        rmtree(s, ignore_errors=False)
    except OSError:
        print("Deletion of the directory %s failed" % s)
        print(OSError)

parser = argparse.ArgumentParser(
    description='Modifies a video file to play at different speeds when there is sound vs. silence.')
parser.add_argument('-i', '--input_file', type=str, help='the video file you want modified')
parser.add_argument('-u', '--url', type=str, help='A youtube url to download and process')
parser.add_argument('-o', '--output_file', type=str, default="",
                    help="the output file. (optional. if not included, it'll just modify the input file name)")
parser.add_argument('-t', '--silent_threshold', type=float, default=0.03,
                    help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". "
                         "It ranges from 0 (silence) to 1 (max volume)")
parser.add_argument('-snd', '--sounded_speed', type=float, default=1.00,
                    help="the speed that sounded (spoken) frames should be played at. Typically 1.")
parser.add_argument('-sil', '--silent_speed', type=float, default=5.00,
                    help="the speed that silent frames should be played at. 0 for jumpcutting.")
parser.add_argument('-fm', '--frame_margin', type=float, default=1,
                    help="some silent frames adjacent to sounded frames are included to prodive context. "
                         "How many frames on either the side of speech should be included? That's this variable.")
parser.add_argument('-sr', '--sample_rate', type=float, default=44100, help="sample rate of the input and output "
                                                                            "videos")
parser.add_argument('-fr', '--frame_rate', type=float, default=30,
                    help="frame rate of the input and output videos. optional... "
                         "I try to find it out myself, but it doesn't always work.")
parser.add_argument('-fq', '--frame_quality', type=int, default=3,
                    help="quality of frames to be extracted from input video. Range: (1-5). 3 is the default.")
parser.add_argument('-tmp', '--temp_folder', type=str, default='TEMP',
                    help="folder where temporary files get stored")

args = parser.parse_args()

silent_speed = 99999999 if args.silent_speed == 0 else args.silent_speed

frameRate = args.frame_rate
SAMPLE_RATE = args.sample_rate
SILENT_THRESHOLD = args.silent_threshold
FRAME_SPREADAGE = args.frame_margin
NEW_SPEED = [silent_speed, args.sounded_speed]
INPUT_FILE = args.input_file
if args.url != None:
    INPUT_FILE = downloadFile(args.url)
else:
    INPUT_FILE = args.input_file
URL = args.url
FRAME_QUALITY = args.frame_quality
TEMP_FOLDER = args.temp_folder

assert INPUT_FILE is not None, "why u put no input file, that dum"

OUTPUT_FILE = args.output_file if len(args.output_file) >= 1 else inputToOutputFilename(INPUT_FILE)

createPath(TEMP_FOLDER)

command = "ffmpeg -i " + INPUT_FILE + " -qscale:v " + str(
    FRAME_QUALITY) + " " + TEMP_FOLDER + "/frame%06d.jpg -hide_banner"
subprocess.call(command, shell=True)

command = "ffmpeg -i " + INPUT_FILE + " -ab 160k -ac 2 -ar " + str(SAMPLE_RATE) + " -vn " + TEMP_FOLDER + "/audio.wav"

subprocess.call(command, shell=True)

command = "ffmpeg -i " + TEMP_FOLDER + "/input.mp4 2>&1"
f = open(TEMP_FOLDER + "/params.txt", "w")
subprocess.call(command, shell=True, stdout=f)

sampleRate, audioData = wavfile.read(TEMP_FOLDER + "/audio.wav")
audioSampleCount = audioData.shape[0]
maxAudioVolume = getMaxVolume(audioData)

f = open(TEMP_FOLDER + "/params.txt", 'r+')
pre_params = f.read()
f.close()
params = pre_params.split('\n')
for line in params:
    m = re.search('Stream #.*Video.* ([0-9]*) fps', line)
    if m is not None:
        frameRate = float(m.group(1))

samplesPerFrame = sampleRate / frameRate

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
for i in range(audioFrameCount):
    start = int(max(0, i - FRAME_SPREADAGE))
    end = int(min(audioFrameCount, i + 1 + FRAME_SPREADAGE))
    shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
    if i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i - 1]:  # Did we flip?
        chunks.append([chunks[-1][1], i, shouldIncludeFrame[i - 1]])

chunks.append([chunks[-1][1], audioFrameCount, shouldIncludeFrame[i - 1]])
chunks = chunks[1:]

outputAudioData = np.zeros((0, audioData.shape[1]))
outputPointer = 0

lastExistingFrame = None
for chunk in chunks:
    audioChunk = audioData[int(chunk[0] * samplesPerFrame):int(chunk[1] * samplesPerFrame)]

    sFile = TEMP_FOLDER + "/tempStart.wav"
    eFile = TEMP_FOLDER + "/tempEnd.wav"
    wavfile.write(sFile, SAMPLE_RATE, audioChunk)
    with WavReader(sFile) as reader:
        with WavWriter(eFile, reader.channels, reader.samplerate) as writer:
            tsm = phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])])
            tsm.run(reader, writer)
    _, alteredAudioData = wavfile.read(eFile)
    leng = alteredAudioData.shape[0]
    endPointer = outputPointer + leng
    outputAudioData = np.concatenate((outputAudioData, alteredAudioData / maxAudioVolume))

    # outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume

    # smooth out transition's audio by quickly fading in/out

    if leng < AUDIO_FADE_ENVELOPE_SIZE:
        outputAudioData[outputPointer:endPointer] = 0  # audio is less than 0.01 sec, let's just remove it.
    else:
        premask = np.arange(AUDIO_FADE_ENVELOPE_SIZE) / AUDIO_FADE_ENVELOPE_SIZE
        mask = np.repeat(premask[:, np.newaxis], 2, axis=1)  # make the fade-envelope mask stereo
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

wavfile.write(TEMP_FOLDER + "/audioNew.wav", SAMPLE_RATE, outputAudioData)

'''
outputFrame = math.ceil(outputPointer/samplesPerFrame)
for endGap in range(outputFrame,audioFrameCount):
    copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)
'''

tf = TEMP_FOLDER
command = f"ffmpeg -framerate {frameRate} -i {tf}/newFrame%06d.jpg -i {tf}/audioNew.wav -strict -2 {OUTPUT_FILE}"
subprocess.call(command, shell=True)

deletePath(TEMP_FOLDER)
