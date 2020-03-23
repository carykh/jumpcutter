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
import srt

#先下载YouTube视频，再把名字中的" "换成"_"，反加文件名
def downloadFile(url):
    name = YouTube(url).streams.first().download()
    newname = name.replace(' ','_')
    os.rename(name,newname)
    return newname

# 根据音频采样率，返回字幕开始、结束时的音频采样点的序号（从1开始），比字幕区间多一些采样点空白，避免采样噪声
def samplePoint_Index_Range_Of_A_Srt_Subtitle_Block(subtitleBlock, sampleRate, margin):
    start = math.floor(( subtitleBlock.start.seconds + subtitleBlock.start.microseconds / 1000000 ) * sampleRate - margin)
    end = math.ceil(( subtitleBlock.start.seconds + subtitleBlock.start.microseconds / 1000000 ) * sampleRate + margin)
    print("\n\n\n\n\nStart audio index is: "+str(start) + "\nEnd audio index is: "+str(end) + "\n\n\n\n\n\n")
    return index(start, end)

# 输入要删除的字幕、音频采样率、音频margin，以及后一个字幕，把后一个字幕往前移。
def push_the_latter_index_backword(the_subtitle_to_be_delete, the_subtitle_to_be_adjust, sampleRate, margin):
    # 先算出毫秒数
    time_shift_caused_by_margin = int(margin / sampleRage * 1000000)
    # 再算总偏移时间
    total_shift = the_subtitle_to_be_delete.end - the_subtitle_to_be_delete.start + datetime.timedelta(microseconds = time_shift_caused_by_margin)
    # 开头偏移
    the_subtitle_to_be_adjust.start = the_subtitle_to_be_adjust.start - total_shift
    # 结尾偏移
    the_subtitle_to_be_adjust.end = the_subtitle_to_be_adjust.end - total_shift
    return the_subtitle_to_be_adjust


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


parser = argparse.ArgumentParser(description='''
对视频中 有声音 和 没声音 的部分施以不同的播放速度，并且可以根据字幕文件中的关键词 自动剪辑（也就是删除和保留） 视频片段。只有当有 srt 输入文件的时候，才会做自动剪辑。

你可以到 https://www.bilibili.com/video/av97093907/ 查看它的工作原理。p4 视频是 jumpcutter 原作者的视频搬运。

原作者是 karykh ，但是有一些 bug 。

本版本修补了许多 bug ，加入了根据字幕自动剪辑的功能。

下面是选项的帮助：

--input_file INPUTFILE    指定一个输入的视频文件

--url URL    如果要处理的输入文件是一个 YouTube 在线视频，就用这个选项，输入 URL 

--input_subtitle SUBTITLE    如果要依据字幕来自动剪辑，就输入字幕文件路径，要求 srt 字幕

--cutKeyword    字幕中的关键字，这是切除片段的关键词。默认是“切掉”

--saveKeyword    字幕中的关键字，这是保留片段的关键词。默认是“保留”

--output_file    输出视频文件路径，可选，如果没有选这个，会有默认自动的输出文件名

--silent_threshold    静音阈值，低于多少的音量可以被认为是静音（取值在 0 - 1 之间，是相对于整个音频中的最大音量的相对值，不是绝对值。）

--sounded_speed    有声音部分的速度，默认是 1.00 

--silent_speed    没有声音部分的速度，默认是 5.00

--frame_margin    加速留白。就是在静音区间两端留几帧，不要加速，防止音频没有停顿。默认是 1 帧

--sample_rate    音频采样率，默认是 44100 ，目前程序不支持自动获得采样率，如果你的采样率不是这个值，需要手动填写

--frame_rate    视频帧速，默认30，一般会自动识别，不用管。如果帧速出了问题，再来这里调节

--frame_quality    帧质量。处理时，会先把视频中的每一帧提取出来，保存到 jpg 格式的图片，这个选项决定了保存图片的质量。取值在 1 - 31 之间，1 代表质量最高，31代表质量最差。默认是3
 
  
   
    
     
     
Above are Chinese help info. English Help is here: 
 
  
   
   
Apply different speed to the sounded and silenced part of the video, and it can auto cut and save clips based on the keywords within a srt subtitle file. 

For example: 
python jumpcutter.py --input_file "my_vlog.mp4" --input_subtitle "my_vlog.srt" --cutKeyword "Cut it" --saveKeyword "Save it" --frame_margin 2 --silent_speed 999

You can goto https://www.youtube.com/watch?v=DQ8orIurGxw to see the basic mechanism. 

The difference is, karykh want to use thumb gesture as a keypoint, and he didn't make it, because the technology it requires is so complicated. 

My solution is to use words in the subtitle as keywords, just like the thumb gesture, they perform the same function, but this solution is much easier to implement.

The false is that this method requires an auto generated srt subtitle. But I believe you can find many services which can convert your audio into a srt subtitle. 
 
  
   
    
     
     
''',formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--input_file', type=str,  help='the video file you want modified')
parser.add_argument('--url', type=str, help='A youtube url to download and process')
parser.add_argument('--input_subtitle', type=str,default="", help='If you want to autocut the video base on the key words within the srt subtitle, then give it the srt path')
parser.add_argument('--cutKeyword', type=str,default="切掉", help='the keyword which indicates cut and drop the previous clip. Only when the whole subtitle exactly matches the key word, then it can work.  The default is "切掉" . If you are a non-Chinese speaker, you may want to change it into eg."Cut it".')
parser.add_argument('--saveKeyword', type=str,default="保留", help='the keyword which indicates to save the previous clip. Only when the whole subtitle exactly matches the key word, then it can work.  The default is "保留" . If you are a non-Chinese speaker, you may want to change it into eg."Save it".')
parser.add_argument('--output_file', type=str, default="", help="the output file. (optional. if not included, it'll just modify the input file name)")
parser.add_argument('--silent_threshold', type=float, default=0.03, help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges from 0 (silence) to 1 (max volume)")
parser.add_argument('--sounded_speed', type=float, default=1.00, help="the speed that sounded (spoken) frames should be played at. Typically 1.")
parser.add_argument('--silent_speed', type=float, default=5.00, help="the speed that silent frames should be played at. 999999 for jumpcutting.")
parser.add_argument('--frame_margin', type=float, default=1, help="some silent frames adjacent to sounded frames are included to provide context. How many frames on either the side of speech should be included? That's this variable.")
parser.add_argument('--sample_rate', type=float, default=44100, help="sample rate of the input and output videos, the default value is 44100 , so if your audio stream sample rate differs from this, you will need to set this")
parser.add_argument('--frame_rate', type=float, default=30, help="frame rate of the input and output videos. optional... actually it can auto get your frame rate, so you can leave this option")
parser.add_argument('--frame_quality', type=int, default=3, help="quality of frames to be extracted from input video. 1 is highest, 31 is lowest, 3 is the default.")

args = parser.parse_args()

frameRate = args.frame_rate
SAMPLE_RATE = args.sample_rate
SILENT_THRESHOLD = args.silent_threshold
FRAME_SPREADAGE = args.frame_margin
NEW_SPEED = [args.silent_speed, args.sounded_speed]
# the two keyword in the subtitle indicates to save the clip or cut it away, they have default values
key_word = [args.cutKeyword, args.saveKeyword]




#如果 URL 不为空，就代表有下载链接，先把它下下来，再得到文件名
if args.url != None:
    INPUT_FILE = downloadFile(args.url)
else:
    INPUT_FILE = args.input_file
URL = args.url
FRAME_QUALITY = args.frame_quality

#断言有输入文件，否则提示
assert INPUT_FILE != None , "没有收到输入文件呀！\n No input file received, could you please check again?"

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

print("\n\n\n\n\n\n正在分析音频\nAnalysing the audio\n\n\n\n\n\n")
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

# 剪切点，这个点很重要。
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
print(str(chunks))

# if the subtitle file is input, then we start to manipulate the chunks before processing audio and video.
if re.match('.+srt', args.input_subtitle):
    print("\n\n\n检测到有输入字幕\n"+args.input_subtitle+"\n\n")
    subtitleFile = open(args.input_subtitle, "r",encoding='utf-8')
    subtitleContent = subtitleFile.read()
    subtitleLists = list(srt.parse(subtitleContent))
    subtitleKeywordLists = []
    for i in subtitleLists:
        if re.match( '(%s)|(%s)$' % (key_word[0],key_word[1]) , i.content) :
            subtitleKeywordLists.append(i)
    lastEnd = 0
    # this q means the index of the chunks
    q = 2
    for i in range(len(subtitleKeywordLists)):
        q -= 2
        print(str(subtitleKeywordLists[i]))
        if i > 0 :
            lastEnd = int((subtitleKeywordLists[i-1].end.seconds + subtitleKeywordLists[i-1].end.microseconds / 1000000) * frameRate)
        thisStart = int((subtitleKeywordLists[i].start.seconds + subtitleKeywordLists[i].start.microseconds / 1000000) * frameRate)
        thisEnd = int((subtitleKeywordLists[i].end.seconds + subtitleKeywordLists[i].end.microseconds / 1000000) * frameRate)
        print("\n\n\nlastEnd:" + str(lastEnd))
        print("\n\n\n这是区间是: " + str(thisStart) + " 到 " + str(thisEnd))
        
        # note that the key_word[0] is cut keyword
        if re.match( '(%s)' % (key_word[0]), subtitleKeywordLists[i].content):
            while q < len(chunks):
                if chunks[q][1] < lastEnd :
                    print('这个 chunk  %s 到 %s 在在 cut 区间  %s 到 %s  左侧，下一个 chunk' % (chunks[q][0],chunks[q][1],thisStart,thisEnd))
                    q += 1
                    continue
                elif chunks[q][0] > thisEnd :
                    print('这个 chunk  %s 到 %s 在在 cut 区间  %s 到 %s  右侧，下一个区间' % (chunks[q][0],chunks[q][1],thisStart,thisEnd))
                    q += 1
                    break
                elif chunks[q][1] < thisEnd :
                    print(str(chunks[q][1]) +" < "+ str(thisEnd))
                    print("这个chunk 的右侧 %s 小于区间的终点  %s ，删掉" % (chunks[q][1],thisEnd))
                    del chunks[q]
                elif chunks[q][1] > thisEnd :
                    print("这个chunk 的右侧 %s 大于区间的终点 %s ，把它的左侧 %s 改成本区间的终点 %s " % (chunks[q][1],thisEnd,chunks[q][0].thisEnd))
                    chunks[q][0] = thisEnd
                    q += 1
        # key_word[1] is save keyword
        elif re.match( '(%s)' % (key_word[1]), subtitleKeywordLists[i].content):
            while q < len(chunks) :
                if chunks[q][1] < thisStart :
                    print("这个区间 %s 到 %s 在起点 %s 左侧，放过，下一个 chunk" % (chunks[q][0], chunks[q][1], thisStart))
                    q += 1
                    continue
                elif chunks[q][0] > thisEnd :
                    print('这个 chunk  %s 到 %s 在在 cut 区间  %s 到 %s  右侧，下一个区间' % (chunks[q][0],chunks[q][1],thisStart,thisEnd))
                    q += 1
                    break
                elif chunks[q][1] > thisStart and chunks[q][0] < thisStart :
                    print("这个区间 %s 到 %s 的右侧，在起点 %s 和终点 %s 之间，修改区间右侧为 %s " % (chunks[q][0], chunks[q][1], thisStart, thisEnd, thisStart))
                    chunks[q][1] = thisStart
                    q += 1
                elif chunks[q][0] > thisStart and chunks[q][1] > thisEnd :
                    print("这个区间 %s 到 %s 的左侧，在起点 %s 和终点 %s 之间，修改区间左侧为 %s " % (chunks[q][0], chunks[q][1], thisStart, thisEnd, thisEnd))
                    chunks[q][0] = thisEnd
                    q += 1
                elif chunks[q][0] > thisStart and chunks[q][1] < thisEnd :
                    print("这个区间 %s 到 %s 整个在起点 %s 和终点 %s 之间，删除 " % (chunks[q][0], chunks[q][1], thisStart, thisEnd))
                    del chunks[q]
                elif chunks[q][0] < thisStart and chunks[q][1] > thisEnd :
                    print("这个区间 %s 到 %s 横跨了 %s 到 %s ，分成两个：从 %s 到 %s ，从 %s 到 %s  " % (chunks[q][0], chunks[q][1], thisStart, thisEnd, chunks[q][0], thisStart, thisEnd, chunks[q][1]))
                    temp = chunks[q]
                    temp[0]=thisEnd
                    chunks[q][1] = thisStart
                    chunks.insert(q+1,temp)
                    q += 1
print("\n\n\n即将处理音频\n\n\n")


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
    # 记一下，原始音频输出帧，这回输出到哪一个采样点时该停下
    # endPointer 是上一回输出往下的采样点地方
    endPointer = outputPointer+leng
    # 输出数据接上 改变后的数据/最大音量
    outputAudioData = np.concatenate((outputAudioData,alteredAudioData/maxAudioVolume))


    #outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume

    # smooth out transitiion's audio by quickly fading in/out
    
    if leng < AUDIO_FADE_ENVELOPE_SIZE:
        # 把 0 到 400 的数值都变成0 ，之后乘以音频就会让这小段音频静音。
        outputAudioData[0:leng] = 0 # audio is less than 0.01 sec, let's just remove it. 
    else:
        # 做一个 1 - 400 的等差数列，分别除以 400，得到淡入时，400 个数就分别是每个音频应乘以的系数。
        premask = np.arange(AUDIO_FADE_ENVELOPE_SIZE)/AUDIO_FADE_ENVELOPE_SIZE
        # 将这个数列乘以 2 ，变成2轴数列，就能用于双声道
        mask = np.repeat(premask[:, np.newaxis],2,axis=1) # make the fade-envelope mask stereo
        # 淡入
        outputAudioData[0:0+AUDIO_FADE_ENVELOPE_SIZE] *= mask
        # 淡出
        outputAudioData[leng-AUDIO_FADE_ENVELOPE_SIZE:leng] *= 1-mask
    
    # 开始输出帧是 outputPointer/samplesPerFrame ，根据音频所在帧数决定视频从哪帧开始输出
    startOutputFrame = int(math.ceil(outputPointer/samplesPerFrame))
    # 终止输出帧是 endPointer/samplesPerFrame ，根据音频所在帧数决定视频到哪里就不要再输出了
    endOutputFrame = int(math.ceil(endPointer/samplesPerFrame))
    # 对于所有输出帧
    for outputFrame in range(startOutputFrame, endOutputFrame):
        # 该复制第几个输入帧 ＝ （开始帧序号 + 新速度*（输出序数-输入序数））
        # 新速度*（输出序数-输入序数） 其实是：（输出帧的当前帧数 - 输出帧的起始帧数）* 时间系数，得到应该是原始视频线的第几帧
        inputFrame = int(chunk[0]+NEW_SPEED[int(chunk[2])]*(outputFrame-startOutputFrame))
        # 从原始视频线复制输入帧 到 新视频线 输出帧
        didItWork = copyFrame(inputFrame,outputFrame)
        # 如果成功了，最后一帧就是最后那个输入帧
        if didItWork:
            lastExistingFrame = inputFrame
        else:
            # 如果没成功，那就复制上回的最后一帧到输出帧。没成功的原因大概是：所谓输入帧不存在，比如视频末尾，音频、视频长度不同。
            copyFrame(lastExistingFrame,outputFrame)
    # 记一下，原始音频输出帧，输出到哪一个采样点了，这就是下回输出的起始点
    outputPointer = endPointer
    wavfile.write(TEMP_FOLDER+"/audioNew_" + "%06d" % i + ".wav",SAMPLE_RATE,outputAudioData)
    concat.write("file "+ "audioNew_" + "%06d" % i + ".wav\n")
concat.close()


'''
outputFrame = math.ceil(outputPointer/samplesPerFrame)
for endGap in range(outputFrame,audioFrameCount):
    copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)
'''
print("\n\n\n\n\n\n\n现在开始合并音频\nStarting concaenating audio clips\n\n\n\n\n\n\n\n\n")
command = ["ffmpeg","-y","-hide_banner","-safe","0","-f","concat","-i",TEMP_FOLDER+"/concat.txt","-framerate",str(frameRate),TEMP_FOLDER+"/audioNew.wav"]
subprocess.call(command, shell=True)

print("\n\n\n\n\n\n\n现在开始合并音视频\nStarting merging audio and video stream\n\n\n\n\n\n\n\n\n")
command = ["ffmpeg","-y","-hide_banner","-framerate",str(frameRate),"-i",TEMP_FOLDER+"/newFrame%06d.jpg","-i",TEMP_FOLDER+"/audioNew.wav","-strict","-2",OUTPUT_FILE]
subprocess.call(command, shell=True)

deletePath(TEMP_FOLDER)

