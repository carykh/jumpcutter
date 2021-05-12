from tkinter import Tk, filedialog, Button
import subprocess


def run(file):
    command = ["python3.6", "jumpcutter.py", "--input_file", file.split("/")[-1]]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, error = process.communicate()
    print("file: ", file)
    print(output, error)


def openf():
    file = filedialog.askopenfilename()
    run(file)



root = Tk()

butt = Button(master=root, text="open file", command=openf)
butt.pack()


root.mainloop()