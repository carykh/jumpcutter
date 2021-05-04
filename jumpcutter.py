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
import argparse
from pytube import YouTube
import sys

def main():
    args = parseArguments()

    frameRate        = args.frame_rate
    sample_rate      = args.sample_rate
    silent_threshold = args.silent_threshold
    frame_spreadage  = args.frame_margin
    new_speeds       = [args.silent_speed, args.sounded_speed]
    input_file       = downloadYoutubeFile(args.url) if args.url != None else args.input_file
    frame_quality    = args.frame_quality

    assert input_file != None , "why u put no input file, that dum"
        
    if len(args.output_file) >= 1:
        output_file = args.output_file
    else:
        output_file = inputToOutputFilename(input_file)

    audio_fade_envelope_size = 400 # smooth out transitiion's audio by quickly fading in/out (arbitrary magic number whatever)
        
    createTempFolder()

    extractAudioFromInputFile(input_file, sample_rate)
    inputFrameRate = getFrameRate(input_file)
    if inputFrameRate:
        frameRate = inputFrameRate
    else:
        assert frameRate > 0, 'The supplied frame rate must be greater than zero'

    # Get the video's audio track statistics
    sampleRate, audioData = wavfile.read(f'{getTempFolder()}/audio.wav')
    audioSampleCount = audioData.shape[0]
    maxAudioVolume = getMaxVolume(audioData)
    samplesPerFrame = sampleRate/frameRate
    audioFrameCount = int(math.ceil(audioSampleCount/samplesPerFrame))


    chunkHasLoudAudio = flagLoudAudioChunks(audioFrameCount, samplesPerFrame, audioSampleCount, audioData, 
                                       maxAudioVolume, silent_threshold)

    speedChangeList = computeSpeedChangeList(audioFrameCount, frame_spreadage, chunkHasLoudAudio, new_speeds)

    extractFramesFromInputFile(input_file, frame_quality)

    outputAudioData = np.zeros((0,audioData.shape[1]))
    outputPointer = 0
    lastExistingFrame = None
    premask = np.arange(audio_fade_envelope_size) / audio_fade_envelope_size
    mask = np.repeat(premask[:, np.newaxis], 2, axis=1) # make the fade-envelope mask stereo
    for start_stop_cnt, speedChange in enumerate(speedChangeList):
        startFrame = speedChange[0]
        stopFrame  = speedChange[1]
        speed      = speedChange[2]
        print(f' - SpeedChanges: {start_stop_cnt} of {len(speedChangeList)} NumFrames:{stopFrame-startFrame}')

        audioChunk = audioData[int(startFrame*samplesPerFrame) : int(stopFrame*samplesPerFrame)]
        alteredAudioData, length = changeAudioSpeed(audioChunk, sample_rate, speed)
        endPointer = outputPointer + length
        outputAudioData = np.concatenate((outputAudioData,alteredAudioData/maxAudioVolume))

        #outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume
        smoothAudioTransitioningBetweenSpeeds(outputAudioData, length, mask, audio_fade_envelope_size, outputPointer, endPointer)
        copyFramesForOutputBasedOnSpeed(outputPointer, samplesPerFrame, endPointer, startFrame, speed, lastExistingFrame)
        outputPointer = endPointer

    wavfile.write(f'{getTempFolder()}/audioNew.wav', sample_rate, outputAudioData)

    '''
    outputFrame = math.ceil(outputPointer/samplesPerFrame)
    for endGap in range(outputFrame,audioFrameCount):
        copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)
    '''

    command = f'ffmpeg -y -framerate {frameRate} -i {getTempFolder()}/newFrame%06d.jpg -i {getTempFolder()}/audioNew.wav -strict -2 {output_file}'
    subprocess.call(command, shell=True)

    deletePath(getTempFolder())

def parseArguments():
    parser = argparse.ArgumentParser(description='Modifies a video file to play at different speeds when there is sound vs. silence.')
    parser.add_argument('--input_file', type=str,  help='the video file you want modified')
    parser.add_argument('--url', type=str, help='A youtube url to download and process')
    parser.add_argument('--output_file', type=str, default="", help="the output file. (optional. if not included, it'll just modify the input file name)")
    parser.add_argument('--silent_threshold', type=float, default=0.03, help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges from 0 (silence) to 1 (max volume)")
    parser.add_argument('--sounded_speed', type=float, default=1.00, help="the speed that sounded (spoken) frames should be played at. Typically 1.")
    parser.add_argument('--silent_speed', type=float, default=5.00, help="the speed that silent frames should be played at. 999999 for jumpcutting.")
    parser.add_argument('--frame_margin', type=float, default=1, help="some silent frames adjacent to sounded frames are included to provide context. How many frames on either the side of speech should be included? That's this variable.")
    parser.add_argument('--sample_rate', type=float, default=44100, help="sample rate of the input and output videos")
    parser.add_argument('--frame_rate', type=float, default=30, help="frame rate of the input and output videos. optional... I try to find it out myself, but it doesn't always work.")
    parser.add_argument('--frame_quality', type=int, default=3, help="quality of frames to be extracted from input video. 1 is highest, 31 is lowest, 3 is the default.")

    args = parser.parse_args()
    return args

def downloadYoutubeFile(url):
    name = YouTube(url).streams.first().download()
    newname = name.replace(' ','_')
    os.rename(name,newname)
    return newname

def extractFramesFromInputFile(input_file, frame_quality):
    temp_folder = getTempFolder()
    command = f"ffmpeg -i {input_file} -qscale:v {frame_quality} {temp_folder}/frame%06d.jpg -hide_banner"
    subprocess.call(command, shell=True)

def extractAudioFromInputFile(input_file, sample_rate):
    temp_folder = getTempFolder()
    audio_file = f"{temp_folder}/audio.wav"
    print(f'Extracting audio file:{audio_file}')
    command = f"ffmpeg -i {input_file} -ab 160k -ac 2 -ar {sample_rate} -vn {audio_file}"
    print(f'  - Cmd:{command}')
    subprocess.call(command, shell=True)
    print()

def getFrameRate(input_file):
    temp_folder = getTempFolder()
    params_file_name = f'{temp_folder}/params.txt'
    command = f"ffmpeg -i {input_file} 2>&1"
    with open(params_file_name, 'w') as f:
        subprocess.call(command, shell=True, stdout=f)
    with open(params_file_name, 'r') as f:
        pre_params = f.read()

    frameRate = None
    params = pre_params.split('\n')
    for line in params:
        m = re.search('Stream #.*Video.* ([0-9]*) fps', line)
        if m is not None:
            frameRate = float(m.group(1))
            print(f'Detected frame rate:{frameRate}')
    return frameRate


def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv,-minv)

def flagLoudAudioChunks(audioFrameCount, samplesPerFrame, audioSampleCount, audioData, maxAudioVolume, silent_threshold):
    chunkHasLoudAudio = np.zeros((audioFrameCount))
    for i in range(audioFrameCount):
        start = int(i*samplesPerFrame)
        end = min(int((i+1)*samplesPerFrame),audioSampleCount)
        audiochunks = audioData[start:end]
        maxchunksVolume = float(getMaxVolume(audiochunks))/maxAudioVolume
        if maxchunksVolume >= silent_threshold:
            chunkHasLoudAudio[i] = 1
    return chunkHasLoudAudio

def computeSpeedChangeList(audioFrameCount, frame_spreadage, chunkHasLoudAudio, new_speeds):
    # FrameNumberStart, FrameNumberStop, speed
    chunks = [[0,0,0]]
    frameSpeed = np.zeros((audioFrameCount))
    for i in range(audioFrameCount):
        start = int(max(0, i-frame_spreadage))
        end   = int(min(audioFrameCount, i+1+frame_spreadage))
        isLoud = int(np.max(chunkHasLoudAudio[start:end]))
        frameSpeed[i] = new_speeds[isLoud]
        if (i >= 1 and frameSpeed[i] != frameSpeed[i-1]): # Did we flip?
            chunks.append([chunks[-1][1], i, frameSpeed[i-1]])

    chunks.append([chunks[-1][1],audioFrameCount,frameSpeed[i-1]])
    chunks = chunks[1:]
    return chunks

def changeAudioSpeed(audioChunk, sample_rate, speed):
    temp_folder = getTempFolder()
    startWavFile = f'{temp_folder}/tempStart.wav'
    endWavFile   = f'{temp_folder}/tempEnd.wav'
    wavfile.write(startWavFile, sample_rate, audioChunk)
    with WavReader(startWavFile) as reader:
        with WavWriter(endWavFile, reader.channels, reader.samplerate) as writer:
            tsm = phasevocoder(reader.channels, speed=speed)
            tsm.run(reader, writer)
    _, alteredAudioData = wavfile.read(endWavFile)
    length = alteredAudioData.shape[0]
    return (alteredAudioData, length)

def smoothAudioTransitioningBetweenSpeeds(outputAudioData, length, mask, audio_fade_envelope_size, outputPointer, endPointer):
    if length < audio_fade_envelope_size:
        outputAudioData[outputPointer:endPointer] = 0 # audio is less than 0.01 sec, let's just remove it.
    else:
        outputAudioData[outputPointer:outputPointer+audio_fade_envelope_size] *= mask
        outputAudioData[endPointer-audio_fade_envelope_size:endPointer] *= 1-mask

def copyFramesForOutputBasedOnSpeed(outputPointer, samplesPerFrame, endPointer, startFrame, speed, lastExistingFrame):
    temp_folder = getTempFolder()
    startOutputFrame = int(math.ceil(outputPointer / samplesPerFrame))
    endOutputFrame   = int(math.ceil(endPointer / samplesPerFrame))
    for outputFrame in range(startOutputFrame, endOutputFrame):
        inputFrame = int(startFrame + speed * (outputFrame - startOutputFrame))
        didItWork = copyFrame(inputFrame, outputFrame, temp_folder)
        if didItWork:
            lastExistingFrame = inputFrame
        else:
            copyFrame(lastExistingFrame, outputFrame, temp_folder)

def copyFrame(inputFrame, outputFrame, temp_folder):
    src = f'{temp_folder}/frame{inputFrame+1:06d}.jpg'
    dst = f'{temp_folder}/newFrame{outputFrame+1:06d}.jpg'
    if not os.path.isfile(src):
        return False
    copyfile(src, dst)
    return True

def inputToOutputFilename(filename):
    dotIndex = filename.rfind(".")
    return filename[:dotIndex]+"_ALTERED"+filename[dotIndex:]

def getTempFolder():
    temp_folder = "TEMP"
    return temp_folder

def createTempFolder():
    #assert (not os.path.exists(s)), "The filepath "+s+" already exists. Don't want to overwrite it. Aborting."
    temp_folder = getTempFolder()

    if os.path.exists(temp_folder):
        import shutil
        shutil.rmtree(temp_folder)
    try:  
        os.mkdir(temp_folder)
    except OSError:  
        assert False, "Creation of the directory %s failed. (The TEMP folder may already exist. Delete or rename it, and try again.)"

    return temp_folder

def deletePath(s): # Dangerous! Watch out!
    try:  
        rmtree(s,ignore_errors=False)
    except OSError:  
        print ("Deletion of the directory %s failed" % s)
        print(OSError)


if __name__ == '__main__':
    main()
