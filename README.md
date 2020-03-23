**For English version help, please scroll down**

# 中文帮助

## 简介

这个工具只是一个 python 脚本。

本脚本可以对视频中 有声音 和 没声音 的部分施以不同的播放速度，并且可以根据字幕文件中的关键词 自动剪辑（也就是删除和保留） 视频片段。只有当有 srt 输入文件的时候，才会做自动剪辑。

你可以到 https://www.bilibili.com/video/av97093907/ 查看它的工作原理。p4 视频是 jumpcutter 原作者的视频搬运。

原作者是 karykh ，但是有一些 bug 。

本版本修补了许多 bug ，加入了根据字幕自动剪辑的功能。

ArcTime 提供便宜的音频转字幕功能，但是开源的 [VideoSRT](https://github.com/wxbool/video-srt-windows) 可以用阿里云 API 自动生成字幕，更便宜（阿里云 API 前 3 个月免费每天 2 小时，之后，2.5元/小时）。

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

## 安装

脚本嘛，直接 copy 下来，装上 python 和 需要的库就能用了

一条使命装需要的库：

```
pip install -r requirements.txt
```

## 使用

举个例子：

```
python jumpcutter.py --input_file "我的vlog.mp4" --input_subtitle "我的vlog.srt" --frame_margin 2
```



# English help

## Description

Apply different speed to the sounded and silenced part of the video, and it can auto cut and save clips based on the keywords within a srt subtitle file. 

For example: 

```
python jumpcutter.py --input_file "my_vlog.mp4" --input_subtitle "my_vlog.srt" --cutKeyword "Cut it" --saveKeyword "Save it" --frame_margin 2 --silent_speed 999
```

You can goto https://www.youtube.com/watch?v=DQ8orIurGxw to see the basic mechanism. 

The difference is, karykh want to use thumb gesture as a key-point, and he didn't make it, because the technology it requires is so complicated. 

My solution is to use words in the subtitle as keywords, just like the thumb gesture, they perform the same function, but this solution is much easier to implement.

The false is that this method requires an auto generated srt subtitle. But I believe you can find many services which can convert your audio into a srt subtitle. 

For the detailed parameter help, you just run: 

```
python jumpcutter.py -h
```

As the program runs, it saves every frame of the video as an image file in a temporary folder. If your video is long, this could take a LOT of space. Be aware of that. 

If you can make this a GUI, please help. 

## Environment

It works on my win10, the other platform should be OK. But I didn't test it on other system.

I can't install numpy and scipy on Termux successfully, so Termux users may not easy to run this.

## Installation

It's a script tool, so no installation is required. But you will need to install python3 and the library the script requires: 

```
pip install -r requirements.txt
```



