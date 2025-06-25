import tkinter as tk
from VideoWidget import Video
import platform
import os
from tkinter.constants import RIDGE, SUNKEN

def call_from_folder(path):
    video_path = path  # Folder name contain your testing video
    video_list = os.listdir(video_path)  # list out all files inside folder
    return video_list  # Return list


class load_widget:
    def __init__(self, root, root_h, root_w, box_w, box_h):
        def augment():
            self.augment_button.config(bg='#DDDDDD')

        list_label = tk.Label(root, bg='Yellow', relief=RIDGE, text='Video List', font='Verdana 20')
        list_label.place(x=50, y=40, width=150)

        video_label = tk.Label(root, bg='#FF00FF', relief=RIDGE, text='Source Video', font='Verdana 22 bold')
        video_label.place(x=box_w*0.45 + box_w / 2 - 150, y=15, width=300, height=40)

        sentence_label = tk.Label(root, text='Sentence', font='Verdana 12 bold')
        sentence_label.place(x=50, y=box_h*0.48)

        # sentence_text = tk.Text(root, bg='#FDFDFD', relief=SUNKEN, font=("Arial", 15),
        #                         spacing1=3, spacing2=3, spacing3=3)
        # sentence_text.place(x=50, y=40 + box_h*0.45, width=root_w - box_w - 200, height=box_h * 0.55 + 20)


class GUI_init:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tkinter media")
        if platform.system() == 'Windows':
            self.root.state('zoomed')   # Window
            self.root.resizable(0, 0)   # Window
        else:
            self.root.attributes('-zoomed', True)  # Ubuntu

        self.root.update()

        root_h = self.root.winfo_height()
        root_w = self.root.winfo_width()
        box_w = (root_w * 0.65)  # video box width
        box_h = box_w * 9 / 16  # video box height
        load_widget(self.root, root_h, root_w, box_w, box_h)

        Video_sub = Video(self.root, root_w, root_h, box_w, box_h)
        list = call_from_folder("Video")  # Find all files in the folder
        list.sort()
        Video_sub.print_list(list)

    def start(self):
        self.root.mainloop()
