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


def get_max_volume(s):
    max_v = float(np.max(s))
    min_v = float(np.min(s))
    return max(max_v, -min_v)


def copy_frame(in_frame, out_frame):
    src = TEMP_FOLDER + "/frame{:06d}".format(in_frame + 1) + ".jpg"
    dst = TEMP_FOLDER + "/newFrame{:06d}".format(out_frame + 1) + ".jpg"
    if not os.path.isfile(src):
        return False
    copyfile(src, dst)
    if out_frame % 20 == 19:
        print(str(out_frame + 1) + " time-altered frames saved.")
    return True


def input_to_output_filename(filename):
    dot_index = filename.rfind(".")
    return filename[:dot_index] + "_ALTERED" + filename[dot_index:]


def create_path(s):
    # assert (not os.path.exists(s)), "The filepath "+s+" already exists. Don't want to overwrite it. Aborting."

    try:
        os.mkdir(s)
    except OSError:
        assert False, "Creation of the directory %s failed. (The TEMP folder may already exist. Delete or rename it, " \
                      "and try again.) "


def delete_path(s):  # Dangerous! Watch out!
    try:
        rmtree(s, ignore_errors=False)
    except OSError:
        print("Deletion of the directory %s failed" % s)
        print(OSError)


# Sets up the command arguments
parser = argparse.ArgumentParser(
    description='Modifies a video file to play at different speeds when there is sound vs. silence.')
parser.add_argument('--input_file', type=str, help='the video file you want modified')
parser.add_argument('--output_file', type=str, default="",
                    help="the output file. (optional. if not included, it'll just modify the input file name)")
parser.add_argument('--silent_threshold', type=float, default=0.03,
                    help="the volume amount that frames' audio needs to surpass to be consider \"sounded\". It ranges "
                         "from 0 (silence) to 1 (max volume)")
parser.add_argument('--sounded_speed', type=float, default=1.00,
                    help="the speed that sounded (spoken) frames should be played at. Typically 1.")
parser.add_argument('--silent_speed', type=float, default=5.00,
                    help="the speed that silent frames should be played at. 999999 for jumpcutting.")
parser.add_argument('--frame_margin', type=float, default=1,
                    help="some silent frames adjacent to sounded frames are included to prodive context. How many "
                         "frames on either the side of speech should be included? That's this variable.")
parser.add_argument('--sample_rate', type=float, default=44100, help="sample rate of the input and output videos")
parser.add_argument('--frame_rate', type=float, default=30,
                    help="frame rate of the input and output videos. optional... I try to find it out myself, "
                         "but it doesn't always work.")
parser.add_argument('--frame_quality', type=int, default=3,
                    help="quality of frames to be extracted from input video. Range: (1-5). 3 is the default.")

# Retrieves the given command arguments
args = parser.parse_args()

FRAME_RATE = args.frame_rate
SAMPLE_RATE = args.sample_rate
SILENT_THRESHOLD = args.silent_threshold
FRAME_MARGIN = args.frame_margin
NEW_SPEED = [args.silent_speed, args.sounded_speed]
INPUT_FILE = args.input_file
FRAME_QUALITY = args.frame_quality

assert INPUT_FILE is not None, "No input file was specified"

OUTPUT_FILE = input_to_output_filename(INPUT_FILE)
if len(args.output_file) >= 1:
    OUTPUT_FILE = args.output_file

TEMP_FOLDER = "TEMP"
# Smooth out transition's audio by quickly fading in/out (arbitrary magic number whatever)
AUDIO_FADE_ENVELOPE_SIZE = 400

create_path(TEMP_FOLDER)

command = f"ffmpeg -i {INPUT_FILE} -qscale:v {FRAME_QUALITY} {TEMP_FOLDER}/frame%06d.jpg -hide_banner"
subprocess.call(command, shell=True)

command = f"ffmpeg -i {INPUT_FILE} -ab 160k -ac 2 -ar {SAMPLE_RATE} -vn {TEMP_FOLDER}/audio.wav"

subprocess.call(command, shell=True)

command = f"ffmpeg -i {TEMP_FOLDER}/input.mp4 2>&1"
f = open(f"{TEMP_FOLDER}/params.txt", "w")
subprocess.call(command, shell=True, stdout=f)

sample_rate, audio_data = wavfile.read(TEMP_FOLDER + "/audio.wav")
audio_sample_count = audio_data.shape[0]
max_audio_volume = get_max_volume(audio_data)

f = open(f"{TEMP_FOLDER}/params.txt", 'r+')
pre_params = f.read()
f.close()
params = pre_params.split('\n')
for line in params:
    m = re.search('Stream #.*Video.* ([0-9]*) fps', line)
    if m is not None:
        FRAME_RATE = float(m.group(1))

samples_per_frame = sample_rate / FRAME_RATE

audio_frame_count = int(math.ceil(audio_sample_count / samples_per_frame))

has_loud_audio = np.zeros(audio_frame_count)

for i in range(audio_frame_count):
    start = int(i * samples_per_frame)
    end = min(int((i + 1) * samples_per_frame), audio_sample_count)
    audio_chunks = audio_data[start:end]
    max_chunks_volume = float(get_max_volume(audio_chunks)) / max_audio_volume
    if max_chunks_volume >= SILENT_THRESHOLD:
        has_loud_audio[i] = 1

chunks = [[0, 0, 0]]
should_include_frame = np.zeros(audio_frame_count)
for i in range(audio_frame_count):
    start = int(max(0, i - FRAME_MARGIN))
    end = int(min(audio_frame_count, i + 1 + FRAME_MARGIN))
    should_include_frame[i] = np.max(has_loud_audio[start:end])
    if i >= 1 and should_include_frame[i] != should_include_frame[i - 1]:  # Did we flip?
        chunks.append([chunks[-1][1], i, should_include_frame[i - 1]])

chunks.append([chunks[-1][1], audio_frame_count, should_include_frame[i - 1]])
chunks = chunks[1:]

output_audio_data = np.zeros((0, audio_data.shape[1]))
output_pointer = 0

last_existing_frame = None
for chunk in chunks:
    audio_chunk = audio_data[int(chunk[0] * samples_per_frame):int(chunk[1] * samples_per_frame)]

    s_file = f"{TEMP_FOLDER}/tempStart.wav"
    e_file = f"{TEMP_FOLDER}/tempEnd.wav"
    wavfile.write(s_file, SAMPLE_RATE, audio_chunk)

    with WavReader(s_file) as reader:
        with WavWriter(e_file, reader.channels, reader.samplerate) as writer:
            tsm = phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])])
            tsm.run(reader, writer)
    _, altered_audio_data = wavfile.read(e_file)

    length = altered_audio_data.shape[0]
    end_pointer = output_pointer + length
    output_audio_data = np.concatenate((output_audio_data, altered_audio_data / max_audio_volume))

    # output_audio_data[output_pointer:endPointer] = altered_audio_data/maxAudioVolume

    # Smooth out transition audio by quickly fading in/out
    if length < AUDIO_FADE_ENVELOPE_SIZE:
        output_audio_data[output_pointer:end_pointer] = 0  # audio is less than 0.01 sec, let's just remove it.
    else:
        pre_mask = np.arange(AUDIO_FADE_ENVELOPE_SIZE) / AUDIO_FADE_ENVELOPE_SIZE
        mask = np.repeat(pre_mask[:, np.newaxis], 2, axis=1)  # make the fade-envelope mask stereo
        output_audio_data[output_pointer:output_pointer + AUDIO_FADE_ENVELOPE_SIZE] *= mask
        output_audio_data[end_pointer - AUDIO_FADE_ENVELOPE_SIZE:end_pointer] *= 1 - mask

    start_output_frame = int(math.ceil(output_pointer / samples_per_frame))
    end_output_frame = int(math.ceil(end_pointer / samples_per_frame))

    for output_frame in range(start_output_frame, end_output_frame):
        input_frame = int(chunk[0] + NEW_SPEED[int(chunk[2])] * (output_frame - start_output_frame))
        did_it_work = copy_frame(input_frame, output_frame)
        if did_it_work:
            last_existing_frame = input_frame
        else:
            copy_frame(last_existing_frame, output_frame)

    output_pointer = end_pointer

wavfile.write(f"{TEMP_FOLDER}/audioNew.wav", SAMPLE_RATE, output_audio_data)

'''
output_frame = math.ceil(output_pointer/samplesPerFrame)
for endGap in range(output_frame,audioFrameCount):
    copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)
'''

command = f"ffmpeg -framerate {FRAME_RATE} -i {TEMP_FOLDER}/newFrame%06d.jpg -i {TEMP_FOLDER}/audioNew.wav -strict -2 {OUTPUT_FILE}"
subprocess.call(command, shell=True)

delete_path(TEMP_FOLDER)
