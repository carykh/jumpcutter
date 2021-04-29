import subprocess
loop = True
while (loop):
    loop = False
    mode = str(input("Pick a modes: \n\t 0) JumpCut  \n\t 1) only the silence \n\t 2) Procastinator \nMode: "))
    if (mode == "0"):
        mode = "--sounded_speed 1 --silent_speed 999999"
    elif (mode == "1"):
        mode = "--sounded_speed 999999 --silent_speed 1"
    elif (mode == "2"):
        mode = "--sounded_speed 2 --silent_speed 8"
    else:
        loop = True


input_file = str(input("Input: "))

if ((input_file[0]+input_file[1]+input_file[2]+input_file[3]).lower() == 'http'):
   input_file = "--url " + input_file
else:
   input_file = "--input_file " + input_file


hd = str(input("HD? y/n: "))
if (hd[0].lower() == "y") or (hd[0].lower() == "0"):
    hd = "1"
else:
    hd = "3"

command = "python jumpcutter.py "+ input_file +" "+ mode +" --frame_margin 2 --frame_quality "+hd

subprocess.call(command, shell=True)