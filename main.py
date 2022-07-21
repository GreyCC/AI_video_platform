import datetime
import threading
import time
import tkinter as tk
import cv2
import face_recognition
import pyttsx3
import numpy
from PIL import ImageDraw
# import playsound
from tkVideoPlayer import TkinterVideo
from utils import *
from tkinter.constants import RIDGE, SUNKEN
# from pytorchyolo import detect, models
from augmentation import *
from multiprocessing.pool import ThreadPool as Pool

last_player = ''


def load_widget():
    list_label = tk.Label(root, bg='Yellow', relief=RIDGE, text='Video List', font='Verdana 15')
    list_label.place(x=15, y=40, width=110)

    video_or_label = tk.Label(root, bg='#FF00FF', relief=RIDGE, text='Source Video', font='Verdana 22 bold')
    video_or_label.place(x=150 + box_w / 2 - 150, y=30, width=300, height=40)

    video_pr_label = tk.Label(root, bg='#FFFF00', relief=RIDGE, text='Processed Video', font='Verdana 22 bold')
    video_pr_label.place(x=150 + 20 + box_w / 2 * 3 - 150, y=30, width=300, height=40)

    # save_button = tk.Button(root, text='Screenshot', relief=RIDGE, bg='white', font='Verdana 14', command=save_frame)
    # save_button.place(x=g_w - 200, y=box_h + 220, width=150, height=50)


def update_duration(event):
    """ updates the duration after finding the duration """
    end_time["text"] = str(datetime.timedelta(seconds=vid_player.duration()))
    progress_slider["to"] = int(vid_player.duration() * vid_player.frame_rate())


def update_scale(event):
    global script, instruction, speak_bool, comment
    global anno_img_name, end_anno_time, bg_img, anno_type
    global speak_bool, lines_count, video_name
    global x1, x2, y1, y2
    t = vid_player.current_duration()

    try:
        second, act, comment, instruction = line_segment(script[0])
    except IndexError:
        return 0

    if 1 < t - second:
        if len(script) > 1:
            lines_count += 1
            script.pop(0)
            second, act, comment, instruction = line_segment(script[0])

    while t - second > 1:
        lines_count += 1
        script.pop(0)
        second, act, comment, instruction = line_segment(script[0])

    if 0 < t - second <= 1:
        # act = act + ' / ' + eng2zh(act)
        action_text.insert(tk.END, str(second) + 's ' + ': ' + act + '\n')

        print_sentense = threading.Thread(target=comment_sentense, args=( [comment] ))
        print_sentense.start()
        # sentence_text.insert(tk.END, comment + '\n')

        # if speak_bool:
        #     playsound.playsound('voice/' + video_name + '_' + str(lines_count) + '.mp3', False)
        #     # speak ('voice/' + video_name + '_' + str(lines_count) + '.mp4')
        #     pass
    pass


def update_frame(event):
    global process, augment
    progress_slider.set(vid_player.current_frame())
    img_after = vid_player.frame_img().copy()
    img_after = img_after.resize((int(box_w), int(box_h)))

    if process:
        img_after = img_after.convert('L')
    if augment:
        img_after = numpy.asarray(img_after)
        cv2.circle(img_after,(200,200),200,(0,0,255),10)
        img_after = Image.fromarray(img_after)

    if process or augment:
        img_after = ImageTk.PhotoImage(img_after)
        processed_video.config(image=img_after)
        processed_video.image = img_after


def comment_sentense(comment):
    comment = comment.split()

    for i in comment:
        #if lan == 'english':
        sentence_text.insert(tk.END, i + ' ')
        #else:
        #    sentence_text.insert(tk.END, i)
        time.sleep(0.2)
    sentence_text.insert(tk.END, '\n')


def load_video(evt):
    """ loads the video """
    global players_encode, players_list, player_script, video_name, lines_count
    lines_count = 1
    w = evt.widget  # get widget that call this function
    index = int(w.curselection()[0])  # get the index of the object clicked
    video_name = w.get(index)[:-4]
    file_path = 'Video/' + w.get(index)  # get the name accroding to the index

    global anno_img_name, script, bg_img, anno_type, end_anno_time, x1, x2, y1, y2
    anno_img_name, script, bg_img, anno_type = '', '', '', ''
    end_anno_time = 0
    x1, x2, y1, y2 = 0, 0, 0, 0
    # file_path = filedialog.askopenfilename()

    if file_path:
        vid_player.load(file_path)

        progress_slider.config(to=0, from_=0)
        progress_slider.set(0)

        vid_player.play()
        play_pause_btn["text"] = "Pause"
        play_pause_btn.config(bg="red")

    for name in script_list:
        if w.get(index)[:-4] in name:
            with open('script/' + name, encoding="utf-8") as file:
                script = file.readlines()
    action_text.delete('1.0', tk.END)
    sentence_text.delete('1.0', tk.END)


def seek(value):
    """ used to seek a specific timeframe """
    vid_player.seekframe(int(value))


def skip(value: int):
    """ skip seconds """
    vid_player.skip_sec(value)
    progress_slider.set(progress_slider.get() + value)


def play_pause():
    """ pauses and plays """
    if vid_player.is_paused():
        vid_player.play()
        play_pause_btn["text"] = "Pause"
        play_pause_btn.config(bg="red")

    else:
        vid_player.pause()
        play_pause_btn["text"] = "Play"
        play_pause_btn.config(bg="grey")


def video_ended(event):
    # global video_name, script
    # """ handle video ended """
    # progress_slider.set(progress_slider["from"])
    # with open('script/' + video_name + '.txt', encoding="utf-8") as file:
    #     script = file.readlines()
    # vid_player.play()
    # play_pause_btn["text"] = "Play"
    pass

def commentary(sentences):

    #     comment = threading.Thread(target=zhspeak, args=[sentences])
    #     comment.start()
    pass


def print_list():
    video_list = tk.Listbox(bg='white', relief=SUNKEN)  # Set a list
    video_list.place(x=15, y=80, width=110)  # Set position
    for i, name in enumerate(list):  # Enumerate: return [index, content]
        video_list.insert(i, name)  # List name w.r.t. index and name
    video_list.bind('<<ListboxSelect>>', load_video)  # When selected, run onselect\


def detect_bool():
    global process
    process = not process
    if process:
        process_btn["text"] = "Stop Process"
        process_btn.config(bg="red")
    else:
        process_btn["text"] = "Process"
        process_btn.config(bg="#DDDDDD")
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        img = ImageTk.PhotoImage(img)
        processed_video.config(image=img)
        processed_video.image = img


def augment_bool():
    global augment
    augment = not augment
    if augment:
        augment_button.config(bg='red')
        augment_button["text"] = 'Remove'
    else:
        augment_button.config(bg='#DDDDDD')
        augment_button["text"] = 'Augmentation'
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        img = ImageTk.PhotoImage(img)
        processed_video.config(image=img)
        processed_video.image = img


def tts_bool():
    global speak_bool, last_eng_comment
    speak_bool = not speak_bool
    if speak_bool:
        tts_button.config(bg='red')
        tts_button["text"] = 'Stop Speaking'
        # commentary(eng2zh(last_eng_comment), 'cantonese')
    else:
        tts_button.config(bg='#DDDDDD')
        tts_button["text"] = 'Start Speaking'


if __name__ == "__main__":
    lines_count = 0
    comment = ''
    video_name = ''
    anno_img_name, script, bg_img, anno_type, instruction = '', '', '', '', ''
    sentence, action, augment = False, False, False
    language = 'cantonese'
    script_list = call_from_folder("script")
    end_anno_time = 0
    x1, x2, y1, y2 = 0, 0, 0, 0
    lines = []
    players_encode, players_list, player_scipt = [], [], []
    # INIT TKINTER & UTILS:
    while True:
        root = tk.Tk()
        root.title("Tkinter media")
        root.attributes('-zoomed', True)  # Ubuntu
        # root.state('zoomed')  # Window
        # root.resizable(0, 0)  # Window
        root.update()

        root_h = root.winfo_height()
        root_w = root.winfo_width()

        box_w = (root_w - 200) / 2  # video box width
        box_h = box_w * 9 / 16  # video box height
        # load_btn = tk.Button(root, text="Load", command=load_video)
        # load_btn.pack()
        load_widget()
        list = call_from_folder("Video")  # Find all files in the folder
        list.sort()
        print_list()  # List out all files

        vid_player = TkinterVideo(scaled=True, pre_load=False, master=root, bg='white', relief=SUNKEN)
        vid_player.place(x=150, y=80, width=box_w, height=box_h)

        processed_video = tk.Label(root, bg='white', relief=SUNKEN)
        processed_video.place(x=150 + 20 + box_w, y=80, width=box_w, height=box_h)

        play_pause_btn = tk.Button(root, text="Play", command=play_pause, bg="grey", font=('bold', 16))
        play_pause_btn.place(x=150, y=80 + box_h + 20, width=120, height=30)

        skip_min_5sec = tk.Button(root, text="Skip -5 sec", command=lambda: skip(-5 * 25))
        skip_min_5sec.place(x=50, y=80 + box_h + 20, width=100)

        skip_plus_5sec = tk.Button(root, text="Skip +5 sec", command=lambda: skip(5 * 25))
        skip_plus_5sec.place(x=150 + box_w, y=80 + box_h + 20, width=100)

        start_time = tk.Label(root, text=str(datetime.timedelta(seconds=0)))
        start_time.place(x=90, y=80 + box_h)

        end_time = tk.Label(root, text=str(datetime.timedelta(seconds=0)))
        end_time.place(x=150 + box_w, y=80 + box_h)

        progress_slider = tk.Scale(root, from_=0, to=0, orient="horizontal", showvalue=0, command=seek)
        progress_slider.place(x=150, y=80 + box_h, width=box_w)

        vid_player.bind("<<Duration>>", update_duration)
        vid_player.bind("<<SecondChanged>>", update_scale)
        vid_player.bind("<<FrameChanged>>", update_frame)
        vid_player.bind("<<Ended>>", video_ended)

        process = False
        process_btn = tk.Button(root, text="Process", command=detect_bool, bg="#DDDDDD", font=('bold', 18))
        process_btn.place(x=500 + box_w, y=80 + box_h + 30, width=200)

        speak_bool = False
        tts_button = tk.Button(root, text="Start Speaking", command=tts_bool, bg="#DDDDDD", font=('bold', 18))
        tts_button.place(x=620 + box_w, y=80 + box_h + 80, width=200)

        augment_button = tk.Button(root, text='Augmentation', command=augment_bool, bg='#DDDDDD', font=('bold', 18))
        augment_button.place(x=720 + box_w, y=80 + box_h + 30, width=200)

        button_w = int(root_w * 0.2)
        button_h = root_h - box_h - 220
        action_label = tk.Label(root, text='Action', font='Verdana 12 bold')
        action_label.place(x=150, y=80 + box_h + 100)

        action_text = tk.Text(root, bg='#FDFDFD', relief=SUNKEN, font=("Arial", 15), spacing1=3, spacing2=3, spacing3=3)
        action_text.place(x=150, y=80 + box_h + 130, width=button_w, height=button_h)

        sentence_w = int(root_w * 0.4)
        sentence_label = tk.Label(root, text='Sentence', font='Verdana 12 bold')
        sentence_label.place(x=150 + button_w + 50, y=80 + box_h + 100)

        sentence_text = tk.Text(root, bg='#FDFDFD', relief=SUNKEN, font=("Arial", 15),
                                spacing1=3, spacing2=3, spacing3=3)
        sentence_text.place(x=150 + button_w + 50, y=80 + box_h + 130, width=sentence_w, height=button_h)

        break

root.mainloop()
