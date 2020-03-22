from contextlib import closing
from PIL import Image
import subprocess
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile
import numpy as np
import re
import math
from shutil import copyfile, rmtree, move
import os
import argparse
from pytube import YouTube

#先下载YouTube视频，再把名字中的" "换成"_"，反加文件名
def downloadFile(url):
    name = YouTube(url).streams.first().download()
    newname = name.replace(' ','_')
    os.rename(name,newname)
    return newname

#返回音量的最大最小值
def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv,-minv)

#复制文件，当取余为 19 时，返回一个保存成功的信息
def copyFrame(inputFrame,outputFrame):
    src = TEMP_FOLDER+"/frame{:06d}".format(inputFrame+1)+".jpg"
    dst = TEMP_FOLDER+"/newFrame{:06d}".format(outputFrame+1)+".jpg"
    if not os.path.isfile(src):
        return False
    if outputFrame%20 == 19:
        print(str(outputFrame+1)+" time-altered frames saved.")
    move(src, dst)
    return True

#把文件名改为加了“_ALTERED”的文件名
def inputToOutputFilename(filename):
    dotIndex = filename.rfind(".")
    return filename[:dotIndex]+"_ALTERED"+filename[dotIndex:]

#创建临时文件夹
def createPath(s):
    #assert (not os.path.exists(s)), "The filepath "+s+" already exists. Don't want to overwrite it. Aborting."

    try:  
        os.mkdir(s)
    except OSError:  
        assert False, "Creation of the directory %s failed. (The TEMP folder may already exist. Delete or rename it, and try again.)"

#删除临时文件夹
def deletePath(s): # Dangerous! Watch out!
    try:  
        rmtree(s,ignore_errors=False)
    except OSError:  
        print ("Deletion of the directory %s failed" % s)
        print(OSError)

'''
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
'''
parser = argparse.ArgumentParser(description='对视频中 有声音 和 没声音 的部分施以不同的播放速度')
parser.add_argument('--input_file', type=str,  help='输入视频文件的路径')
parser.add_argument('--url', type=str, help='如果要处理的输入文件是一个 YouTube 在线视频，就用这个选项，输入 URL ')
parser.add_argument('--output_file', type=str, default="", help="输出文件路径，可选，如果没有选这个，会有默认的输出文件名")
parser.add_argument('--silent_threshold', type=float, default=0.03, help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges from 0 (silence) to 1 (max volume)")
parser.add_argument('--sounded_speed', type=float, default=1.00, help="the speed that sounded (spoken) frames should be played at. Typically 1.")
parser.add_argument('--silent_speed', type=float, default=5.00, help="the speed that silent frames should be played at. 999999 for jumpcutting.")
parser.add_argument('--frame_margin', type=float, default=1, help="some silent frames adjacent to sounded frames are included to provide context. How many frames on either the side of speech should be included? That's this variable.")
parser.add_argument('--sample_rate', type=float, default=44100, help="sample rate of the input and output videos")
parser.add_argument('--frame_rate', type=float, default=30, help="frame rate of the input and output videos. optional... I try to find it out myself, but it doesn't always work.")
parser.add_argument('--frame_quality', type=int, default=3, help="quality of frames to be extracted from input video. 1 is highest, 31 is lowest, 3 is the default.")

args = parser.parse_args()



frameRate = args.frame_rate
SAMPLE_RATE = args.sample_rate
SILENT_THRESHOLD = args.silent_threshold
FRAME_SPREADAGE = args.frame_margin
NEW_SPEED = [args.silent_speed, args.sounded_speed]

#如果 URL 不为空，就代表有下载链接，先把它下下来，再得到文件名
if args.url != None:
    INPUT_FILE = downloadFile(args.url)
else:
    INPUT_FILE = args.input_file
URL = args.url
FRAME_QUALITY = args.frame_quality

#断言有输入文件，否则提示
assert INPUT_FILE != None , "没有收到输入文件呀！"

#如果有输出文件，就用输出文件，如果没有，就用默认的输出文件
if len(args.output_file) >= 1:
    OUTPUT_FILE = args.output_file
else:
    OUTPUT_FILE = inputToOutputFilename(INPUT_FILE)

#临时文件夹名字
TEMP_FOLDER = "TEMP"

#音频淡入淡出大小
AUDIO_FADE_ENVELOPE_SIZE = 400 # smooth out transitiion's audio by quickly fading in/out (arbitrary magic number whatever)
    
#如果临时文件已经存在，就删掉
if(os.path.exists(TEMP_FOLDER)):   
    deletePath(TEMP_FOLDER)
# test if the TEMP folder exists, when it does, delete it. Prevent the error when creating TEMP while the TEMP already exists

#创建临时文件夹
createPath(TEMP_FOLDER)

#提取帧 frame%06d.jpg
command = ["ffmpeg","-hide_banner","-i",INPUT_FILE,"-qscale:v",str(FRAME_QUALITY),TEMP_FOLDER+"/frame%06d.jpg","-hide_banner"]
subprocess.call(command, shell=True)

#提取音频流 audio.wav
command = ["ffmpeg","-hide_banner","-i",INPUT_FILE,"-ab","160k","-ac","2","-ar",str(SAMPLE_RATE),"-vn",TEMP_FOLDER+"/audio.wav"]
subprocess.call(command, shell=True)
command = ["ffmpeg","-hide_banner","-i",INPUT_FILE,"2>&1"]
f = open(TEMP_FOLDER+"/params.txt", "w")
subprocess.call(command, shell=True, stdout=f)

#变量 sampleRate, audioData ，得到采样总数为 wavfile.read("audio.wav").shape[0] ，（shape[1] 是声道数）
sampleRate, audioData = wavfile.read(TEMP_FOLDER+"/audio.wav")
audioSampleCount = audioData.shape[0]
#其实 audioData 就是一个一串数字的列表，获得最大值、最小值的负数就完了
maxAudioVolume = getMaxVolume(audioData)

#读取一下 params.txt ，找一下 fps 数值到 frameRate
f = open(TEMP_FOLDER+"/params.txt", 'r+',encoding='utf-8')
pre_params = f.read()
f.close()
params = pre_params.split('\n')
for line in params:
    m = re.search('Stream #.*Video.* ([0-9]*) fps',line)
    if m is not None:
        frameRate = float(m.group(1))
print('\n\n\n\n\n\n\n\nThe frame rate is: '+ str(frameRate) + '\n\n\n\n\n\n\n\n')

#每一帧的音频采样数=采样率/帧率
samplesPerFrame = sampleRate/frameRate

#得到音频总帧数 audioFrameCount
audioFrameCount = int(math.ceil(audioSampleCount/samplesPerFrame))

# numpy.zeros(shape, dtype=float, order='C')  Return a new array of given shape and type, filled with zeros.
# 返回一个数量为 音频总帧数 的列表，默认数值为0，用于存储这一帧的声音是否大于阈值
hasLoudAudio = np.zeros((audioFrameCount))


for i in range(audioFrameCount):
    # start 指的是这一帧的音频的起始采样点是总数第几个
    start = int(i*samplesPerFrame)
    # end 是 下一帧的音频起点 或 整个音频的终点采样点
    end = min(int((i+1)*samplesPerFrame),audioSampleCount)
    # audiochunks 就是从 start 到 end 这一段音频
    audiochunks = audioData[start:end]
    # 得到这一小段音频中的相对最大值（相对整个音频的最大值）
    maxchunksVolume = float(getMaxVolume(audiochunks))/maxAudioVolume
    # 要是这一帧的音量大于阈值，记下来。
    if maxchunksVolume >= SILENT_THRESHOLD:
        hasLoudAudio[i] = 1

chunks = [[0,0,0]]

# 返回一个数量为 音频总帧数 的列表，默认数值为0，用于存储是否该存储这一帧
shouldIncludeFrame = np.zeros((audioFrameCount))
for i in range(audioFrameCount):
    start = int(max(0,i-FRAME_SPREADAGE))
    end = int(min(audioFrameCount,i+1+FRAME_SPREADAGE))
    #如果从加上淡入淡出的起始到最后之间的几帧中，有1帧是要保留的，那就保留这一区间所有的
    shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
    #如果这一帧不是总数第一帧 且 是否保留这一帧 与 前一帧 不同
    if (i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i-1]): # Did we flip?
        # chunks 追加一个 [最后一个的第2个数值（也就是上一个切割点的帧数），本帧的序数，这一帧是否应该保留] 
        # 其实就是在整个音频线上砍了好几刀，在刀缝间加上记号：前面这几帧要保留（不保留）
        chunks.append([chunks[-1][1],i,shouldIncludeFrame[i-1]])

# chunks 追加一个 [最后一个的第2个数值，总帧数，这一帧是否应该保留] 
# 就是在音频线末尾砍了一刀，加上记号：最后这几帧要保留（不保留）
chunks.append([chunks[-1][1],audioFrameCount,shouldIncludeFrame[i-1]])
#把开头哪个[0,0,0]去掉
chunks = chunks[1:]

# 输出指针为0
outputPointer = 0
# 上一个帧为空
lastExistingFrame = None
i = 0
concat = open(TEMP_FOLDER+"/concat.txt","a")
for chunk in chunks:
    i += 1
    # 返回一个数量为 0 的列表，数据类型为声音 shape[1]
    outputAudioData = np.zeros((0,audioData.shape[1]))
    #得到一块音频区间
    audioChunk = audioData[int(chunk[0]*samplesPerFrame):int(chunk[1]*samplesPerFrame)]
    
    sFile = TEMP_FOLDER+"/tempStart.wav"
    eFile = TEMP_FOLDER+"/tempEnd.wav"
    #将得到的音频区间写入到 sFile(startFile)
    wavfile.write(sFile,SAMPLE_RATE,audioChunk)
    #临时打开 sFile(startFile) 到 reader 变量
    with WavReader(sFile) as reader:
    #临时打开 eFile(endFile) 到 writer 变量
        with WavWriter(eFile, reader.channels, reader.samplerate) as writer:
            #给音频区间设定变速 time-scale modification
            tsm = phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])])
            #按照指定参数，将输入变成输出
            tsm.run(reader, writer)
    #读取 endFile ，赋予 改变后的数据
    _, alteredAudioData = wavfile.read(eFile)
    # 长度就是改变后数据的总采样数
    leng = alteredAudioData.shape[0]
    # 终点指针 = 输出指针 + 改变后数据的采样数
    endPointer = outputPointer+leng
    # 输出数据接上 改变后的数据/最大音量
    outputAudioData = np.concatenate((outputAudioData,alteredAudioData/maxAudioVolume))

    #outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume

    # smooth out transitiion's audio by quickly fading in/out
    
    if leng < AUDIO_FADE_ENVELOPE_SIZE:
        outputAudioData[0:leng] = 0 # audio is less than 0.01 sec, let's just remove it.
    else:
        premask = np.arange(AUDIO_FADE_ENVELOPE_SIZE)/AUDIO_FADE_ENVELOPE_SIZE
        mask = np.repeat(premask[:, np.newaxis],2,axis=1) # make the fade-envelope mask stereo
        outputAudioData[0:0+AUDIO_FADE_ENVELOPE_SIZE] *= mask
        outputAudioData[leng-AUDIO_FADE_ENVELOPE_SIZE:leng] *= 1-mask
    
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
    wavfile.write(TEMP_FOLDER+"/audioNew_" + "%06d" % i + ".wav",SAMPLE_RATE,outputAudioData)
    concat.write("file "+ "audioNew_" + "%06d" % i + ".wav\n")
concat.close()


'''
outputFrame = math.ceil(outputPointer/samplesPerFrame)
for endGap in range(outputFrame,audioFrameCount):
    copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)
'''
print("\n\n\n\n\n\n\n现在开始合并音频\n\n\n\n\n\n\n\n\n\n")
command = ["ffmpeg","-hide_banner","-safe","0","-f","concat","-i",TEMP_FOLDER+"/concat.txt","-framerate",str(frameRate),TEMP_FOLDER+"/audioNew.wav"]
subprocess.call(command, shell=True)

print("\n\n\n\n\n\n\n现在开始合并音视频\n\n\n\n\n\n\n\n\n\n")
command = ["ffmpeg","-hide_banner","-framerate",str(frameRate),"-i",TEMP_FOLDER+"/newFrame%06d.jpg","-i",TEMP_FOLDER+"/audioNew.wav","-strict","-2",OUTPUT_FILE]
subprocess.call(command, shell=True)

deletePath(TEMP_FOLDER)
