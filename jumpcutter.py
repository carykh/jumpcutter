#!/usr/bin/env python

from contextlib import closing
from PIL import Image
import subprocess
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile
import numpy as np
import re
import math
from shutil import copyfile, rmtree
import os
from os.path import splitext, basename, dirname
import sys
import argparse
from tempfile import mkdtemp
from pytube import YouTube

def downloadFile(url):
    name = YouTube(url).streams.first().download()
    newname = name.replace(' ','_')
    os.rename(name,newname)
    return newname

def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv,-minv)

def copyFrame(inputFrame, outputFrame):
    src = TEMP_FOLDER+"/frame{:06d}".format(inputFrame+1)+".jpg"
    dst = TEMP_FOLDER+"/newFrame{:06d}".format(outputFrame+1)+".jpg"
    if not os.path.isfile(src):
        return False
    copyfile(src, dst)
    if outputFrame%20 == 19:
        print(str(outputFrame+1)+" time-altered frames saved.")
    return True

def inputToOutputFilename(filename):
    splitName = splitext(filename)
    return os.path.join(dirname(filename), splitName[0] + "_ALTERED" + splitName[1])

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
        print(OSError)

def parseArguments():
    parser = argparse.ArgumentParser(description='Modifies a video file to play at different speeds when there is sound vs. silence.')
    parser.add_argument('--input_file', 
                        type=str,
                        help='the video file you want modified')
    parser.add_argument('--url', 
                        type=str, 
                        help='A youtube url to download and process')
    parser.add_argument('--output_file', 
                        type=str, 
                        help="the output file. (optional. if not included, it'll just modify the input file name)")
    parser.add_argument('--silent_threshold', 
                        type=float, 
                        default=0.03, 
                        help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges from 0 (silence) to 1 (max volume)")
    parser.add_argument('--sounded_speed', 
                        type=float, 
                        default=1.00, 
                        help="the speed that sounded (spoken) frames should be played at. Typically 1.")
    parser.add_argument('--silent_speed', 
                        type=float, 
                        default=5.00, 
                        help="the speed that silent frames should be played at. 999999 for jumpcutting.")
    parser.add_argument('--frame_margin', 
                        type=float, 
                        default=1, 
                        help="How many frames on either the side of speech should be included in \"sounded\" periods.")
    parser.add_argument('--sample_rate', 
                        type=float, 
                        default=44100, 
                        help="sample rate of the input and output videos")
    parser.add_argument('--frame_rate', 
                        type=float, 
                        default=30, 
                        help="frame rate of the input and output videos. optional.")
    parser.add_argument('--frame_quality', 
                        type=int, 
                        default=3, 
                        help="quality of frames to be extracted from input video. 1 is highest, 31 is lowest, 3 is the default.")

    return parser.parse_args()


def main(frameRate, sampleRate, silentThreshold, frameSpreadage, inputFile, frameQuality, silentSpeed, soundedSpeed, outputFile=None):
    NEW_SPEED = [silentSpeed, soundedSpeed]

    if outputFile is not None:
        OUTPUT_FILE = args.output_file
    else:
        OUTPUT_FILE = inputToOutputFilename(inputFile)

    TEMP_FOLDER = mkdtemp(prefix="jumpcutter")
    AUDIO_FADE_ENVELOPE_SIZE = 400 # smooth out transitiion's audio by quickly fading in/out (arbitrary magic number whatever)

    createPath(TEMP_FOLDER)

    subprocess.call(["ffmpeg", "-i", inputFile, "-qscale:v", str(FRAME_QUALITY), TEMP_FOLDER + "/frame%06d.jpg", "-hide-banner"])

    subprocess.call(["ffmpeg", "-i", inputFile, "-ab", "160k", "-ac", 2, "-ar", str(sampleRate), "-vn", TEMP_FOLDER+"/audio.wav"])

    command = "ffmpeg -i "+TEMP_FOLDER+"/input.mp4 2>&1"
    f = open(TEMP_FOLDER+"/params.txt", "w")
    subprocess.call(["ffmpeg", "-i", TEMP_FOLDER+"/input.mp4"], stderr=STDOUT, stdout=f)

    sampleRate, audioData = wavfile.read(TEMP_FOLDER+"/audio.wav")
    audioSampleCount = audioData.shape[0]
    maxAudioVolume = getMaxVolume(audioData)

    f = open(TEMP_FOLDER+"/params.txt", 'r+')
    pre_params = f.read()
    f.close()
    params = pre_params.split('\n')
    for line in params:
        m = re.search('Stream #.*Video.* ([0-9]*) fps',line)
        if m is not None:
            frameRate = float(m.group(1))

    samplesPerFrame = sampleRate/frameRate

    audioFrameCount = int(math.ceil(audioSampleCount/samplesPerFrame))

    hasLoudAudio = np.zeros((audioFrameCount))



    for i in range(audioFrameCount):
        start = int(i*samplesPerFrame)
        end = min(int((i+1)*samplesPerFrame),audioSampleCount)
        audiochunks = audioData[start:end]
        maxchunksVolume = float(getMaxVolume(audiochunks))/maxAudioVolume
        if maxchunksVolume >= silentThreshold:
            hasLoudAudio[i] = 1

    chunks = [[0,0,0]]
    shouldIncludeFrame = np.zeros((audioFrameCount))
    for i in range(audioFrameCount):
        start = int(max(0,i-frameSpreadage))
        end = int(min(audioFrameCount,i+1+frameSpreadage))
        shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
        if (i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i-1]): # Did we flip?
            chunks.append([chunks[-1][1],i,shouldIncludeFrame[i-1]])

    chunks.append([chunks[-1][1],audioFrameCount,shouldIncludeFrame[i-1]])
    chunks = chunks[1:]

    outputAudioData = np.zeros((0,audioData.shape[1]))
    outputPointer = 0

    lastExistingFrame = None
    for chunk in chunks:
        audioChunk = audioData[int(chunk[0]*samplesPerFrame):int(chunk[1]*samplesPerFrame)]

        sFile = TEMP_FOLDER+"/tempStart.wav"
        eFile = TEMP_FOLDER+"/tempEnd.wav"
        wavfile.write(sFile,sampleRate,audioChunk)
        with WavReader(sFile) as reader:
            with WavWriter(eFile, reader.channels, reader.samplerate) as writer:
                tsm = phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])])
                tsm.run(reader, writer)
                _, alteredAudioData = wavfile.read(eFile)
                leng = alteredAudioData.shape[0]
                endPointer = outputPointer+leng
                outputAudioData = np.concatenate((outputAudioData,alteredAudioData/maxAudioVolume))

        #outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume

        # smooth out transitiion's audio by quickly fading in/out

        if leng < AUDIO_FADE_ENVELOPE_SIZE:
            outputAudioData[outputPointer:endPointer] = 0 # audio is less than 0.01 sec, let's just remove it.
        else:
            premask = np.arange(AUDIO_FADE_ENVELOPE_SIZE)/AUDIO_FADE_ENVELOPE_SIZE
            mask = np.repeat(premask[:, np.newaxis],2,axis=1) # make the fade-envelope mask stereo
            outputAudioData[outputPointer:outputPointer+AUDIO_FADE_ENVELOPE_SIZE] *= mask
            outputAudioData[endPointer-AUDIO_FADE_ENVELOPE_SIZE:endPointer] *= 1-mask

        startOutputFrame = int(math.ceil(outputPointer/samplesPerFrame))
        endOutputFrame = int(math.ceil(endPointer/samplesPerFrame))
        for outputFrame in range(startOutputFrame, endOutputFrame):
            inputFrame = int(chunk[0]+NEW_SPEED[int(chunk[2])]*(outputFrame-startOutputFrame))
            didItWork = copyFrame(inputFrame,outputFrame)
            if didItWork:
                lastExistingFrame = inputFrame
            else:
                copyFrame(lastExistingFrame,outputFrame)

        outputPointer = endPointer

    wavfile.write(TEMP_FOLDER+"/audioNew.wav",sampleRate,outputAudioData)

    '''
    outputFrame = math.ceil(outputPointer/samplesPerFrame)
    for endGap in range(outputFrame,audioFrameCount):
        copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)
    '''

    subprocess.call(["ffmpeg", "-framerate", str(frameRate), "-i", TEMP_FOLDER+"/newFrame%06d.jpg", "-i", TEMP_FOLDER+"/audioNew.wav", "-strict", "-2", OUTPUT_FILE])

    deletePath(TEMP_FOLDER)

if __name__ == "__main__":
    args = parseArguments()
    frameRate = args.frame_rate
    sampleRate = args.sample_rate
    silentThreshold = args.silent_threshold
    frameSpreadage = args.frame_margin
    if args.url != None:
        inputFile = downloadFile(args.url)
        frameQuality = None
    else:
        inputFile = args.input_file
        frameQuality = args.frame_quality

    assert inputFile is not None, "Please supply either an input_file or url"

    main(frameRate, sampleRate, silentThreshold, frameSpreadage, inputFile, frameQuality, args.silent_speed, args.sounded_speed, args.output_file)
