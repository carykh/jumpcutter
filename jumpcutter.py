from contextlib import closing
from PIL import Image
import subprocess
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile
import numpy as np
import math
from shutil import copyfile, rmtree, which, move
import os
import argparse
import youtube_dl
import cv2
import psutil
import requests
import zipfile
import tarfile

TEMP_FOLDER = "TEMP"

def downloadFile(url):
    ydl_opts = {
        'format':'best[height<=1080][ext=mp4]/best[ext=mp4]/best',
        'restrictfilenames':True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        filemetadata = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(filemetadata)

def findFramerate(filename):
    video = cv2.VideoCapture(filename)
    framerate = video.get(cv2.CAP_PROP_FPS)
    video.release()
    print("Calculated framerate of the video is: "+str(framerate))
    return framerate

def checkForFFMPEG():
    if which("ffmpeg") is None:
        if psutil.WINDOWS:
            print("Installing ffmpeg for Windows (32 bit)")
            archive = requests.get("https://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-4.1.1-win32-static.zip")
            with open("ffmpeg-4.1.1-win32-static.zip", 'wb') as t:
                t.write(archive.content)
            with zipfile.ZipFile("ffmpeg-4.1.1-win32-static.zip", "r") as zip_ref:
                zip_ref.extractall(".")
            move("ffmpeg-4.1.1-win32-static/bin/ffmpeg.exe", "ffmpeg.exe")
            rmtree("ffmpeg-4.1.1-win32-static")
            os.remove("ffmpeg-4.1.1-win32-static.zip")
        elif psutil.MACOS:
            print("Installing ffmpeg for MacOS (64 bit)")
            archive = requests.get("https://ffmpeg.zeranoe.com/builds/macos64/static/ffmpeg-4.1.1-macos64-static.zip")
            with open("ffmpeg-4.1.1-macos64-static.zip", 'wb') as t:
                t.write(archive.content)
            with zipfile.ZipFile("ffmpeg-4.1.1-macos64-static.zip", "r") as zip_ref:
                zip_ref.extractall(".")
            move("ffmpeg-4.1.1-macos64-static/bin/ffmpeg", "ffmpeg")
            rmtree("ffmpeg-4.1.1-macos64-static")
            os.remove("ffmpeg-4.1.1-macos64-static.zip")
        elif psutil.LINUX:
            print("Installing ffmpeg for Linux (32 bit)")
            archive = requests.get("https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz")
            with open("ffmpeg-release-i686-static.tar.xz", 'wb') as t:
                t.write(archive.content)
            with tarfile.open("ffmpeg-release-i686-static.tar.xz", "r") as tar_ref:
                tar_ref.extractall(".")
            move("ffmpeg-release-i686-static/ffmpeg", "ffmpeg")
            rmtree("ffmpeg-release-i686-static")
            os.remove("ffmpeg-release-i686-static.tar.xz")
        else:
            assert False, "Jumpcutter cannot find ffmpeg and automatic ffmpeg installation is not supported on your OS"

def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv,-minv)

def copyFrame(inputFrame,outputFrame):
    src = TEMP_FOLDER+"/frame{:06d}".format(inputFrame+1)+".jpg"
    dst = TEMP_FOLDER+"/newFrame{:06d}".format(outputFrame+1)+".jpg"
    if not os.path.isfile(src):
        return False
    try:
        copyfile(src, dst)
    except Exception:
        print(Exception)
        return False
    if outputFrame%100 == 99:
        print(str(outputFrame+1)+" time-altered frames saved.")
    return True

def inputToOutputFilename(filename):
    return "".join(os.path.splitext(filename)[:-1])+"_ALTERED"+os.path.splitext(filename)[-1]

def createPath(s):
    #assert (not os.path.exists(s)), "The filepath "+s+" already exists. Don't want to overwrite it. Aborting."

    try:  
        os.mkdir(s)
    except OSError:
        assert False, "Creation of the directory %s failed. (The TEMP folder may already exist. Delete or rename it, and try again.)"

def deletePath(s): # Dangerous! Watch out!
    try:  
        rmtree(s,ignore_errors=False)
    except OSError:
        print ("Deletion of the directory %s failed" % s)

def execute(input_file="", url="", output_file="", silent_threshold=0.03, sounded_speed=1.00, silent_speed=5.00, frame_margin=1, sample_rate=44100, frame_quality=3):
    SAMPLE_RATE = sample_rate
    SILENT_THRESHOLD = silent_threshold
    FRAME_SPREADAGE = frame_margin
    NEW_SPEED = [silent_speed, sounded_speed]
    if url != "" and url != None:
        INPUT_FILE = downloadFile(url)
    else:
        INPUT_FILE = input_file
    FRAME_QUALITY = frame_quality

    assert INPUT_FILE != "" and INPUT_FILE != None, "why u put no input file, that dum"

    if len(output_file) >= 1:
        OUTPUT_FILE = output_file
    else:
        OUTPUT_FILE = inputToOutputFilename(INPUT_FILE)
    print("Saving to: "+OUTPUT_FILE)

    AUDIO_FADE_ENVELOPE_SIZE = 400  # smooth out transitiion's audio by quickly fading in/out (arbitrary magic number whatever)

    createPath(TEMP_FOLDER)

    checkForFFMPEG()

    command = "ffmpeg -i " + INPUT_FILE + " -qscale:v " + str(
        FRAME_QUALITY) + " " + TEMP_FOLDER + "/frame%06d.jpg -hide_banner"
    subprocess.call(command, shell=True)

    command = "ffmpeg -i " + INPUT_FILE + " -ab 160k -ac 2 -ar " + str(
        SAMPLE_RATE) + " -vn " + TEMP_FOLDER + "/audio.wav"

    subprocess.call(command, shell=True)

    sampleRate, audioData = wavfile.read(TEMP_FOLDER + "/audio.wav")
    audioSampleCount = audioData.shape[0]
    maxAudioVolume = getMaxVolume(audioData)

    frameRate = findFramerate(INPUT_FILE)

    samplesPerFrame = sampleRate / frameRate

    audioFrameCount = int(math.ceil(audioSampleCount / samplesPerFrame))

    hasLoudAudio = np.zeros((audioFrameCount))

    for i in range(audioFrameCount):
        start = int(i * samplesPerFrame)
        end = min(int((i + 1) * samplesPerFrame), audioSampleCount)
        audiochunks = audioData[start:end]
        maxchunksVolume = float(getMaxVolume(audiochunks)) / maxAudioVolume
        if maxchunksVolume >= SILENT_THRESHOLD:
            hasLoudAudio[i] = 1

    chunks = [[0, 0, 0]]
    shouldIncludeFrame = np.zeros((audioFrameCount))
    for i in range(audioFrameCount):
        start = int(max(0, i - FRAME_SPREADAGE))
        end = int(min(audioFrameCount, i + 1 + FRAME_SPREADAGE))
        shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
        if (i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i - 1]):  # Did we flip?
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

        # smooth out transitiion's audio by quickly fading in/out

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

    command = "ffmpeg -y -framerate " + str(frameRate) + " -i " + TEMP_FOLDER + "/newFrame%06d.jpg -i " + TEMP_FOLDER + "/audioNew.wav -strict -2 " + OUTPUT_FILE
    subprocess.call(command, shell=True)

    deletePath(TEMP_FOLDER)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Modifies a video file to play at different speeds when there is sound vs. silence.')
    parser.add_argument('--input_file', type=str, help='the video file you want modified')
    parser.add_argument('--url', type=str, help='A video url to download and process through youtube-dl')
    parser.add_argument('--output_file', type=str, default="",
                        help="the output file. (optional. if not included, it'll just modify the input file name)")
    parser.add_argument('--silent_threshold', type=float, default=0.03,
                        help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges from 0 (silence) to 1 (max volume)")
    parser.add_argument('--sounded_speed', type=float, default=1.00,
                        help="the speed that sounded (spoken) frames should be played at. Typically 1.")
    parser.add_argument('--silent_speed', type=float, default=5.00,
                        help="the speed that silent frames should be played at. 999999 for jumpcutting.")
    parser.add_argument('--frame_margin', type=float, default=1,
                        help="some silent frames adjacent to sounded frames are included to provide context. How many frames on either the side of speech should be included? That's this variable.")
    parser.add_argument('--sample_rate', type=float, default=44100, help="sample rate of the input and output videos")
    parser.add_argument('--frame_quality', type=int, default=3,
                        help="quality of frames to be extracted from input video. 1 is highest, 31 is lowest, 3 is the default.")
    args = parser.parse_args()

    execute(args.input_file, args.url, output_file=args.output_file, silent_threshold=args.silent_threshold, sounded_speed=args.sounded_speed, silent_speed=args.silent_speed, frame_margin=args.frame_margin, sample_rate=args.sample_rate, frame_quality=args.frame_quality)