from tts import *
from custom_tkVideoPlayer.tkVideoPlayer import TkinterVideo
from tkinter.constants import SUNKEN
from load_sentences.load_commentary_sentences import load_action, load_comment
from Commentator.commentator_class import commentator
from action_spotter.predictors import MultiDimStackerPredictor, get_best_model_path
import tkinter as tk
import numpy as np
import datetime
import random


class Video:
    def __init__(self, root, root_w, root_h, box_w, box_h):
        # Initialize action predictor
        self.action_predictor = MultiDimStackerPredictor(get_best_model_path("action_spotter/action_model"))
        self.next_action = None
        self.action = None
        self.check_other_comment = True
        self.current_time = 0
        self.img_count = 0
        self.info_time = 0
        self.root = root
        self.box_w = box_w
        self.box_h = box_h

        # Initialize video players
        self.vid_player = TkinterVideo(scaled=True, master=root, bg='white', relief=SUNKEN)
        self.vid_player.place(x=box_w * 0.45, y=60, width=box_w, height=box_h)
        self.play_pause_btn = tk.Button(root, text="Play", command=self.play_pause, bg="grey", font=('bold', 16))
        self.play_pause_btn.place(x=box_w * 0.45, y=100 + box_h + 20, width=120, height=30)

        self.progress_slider = tk.Scale(root, from_=0, to=0, orient="horizontal", showvalue=False, command=self.seek)
        self.progress_slider.place(x=box_w * 0.45, y=100 + box_h, width=box_w)

        self.start_time = tk.Label(root, text=str(datetime.timedelta(seconds=0)))
        self.start_time.place(x=box_w * 0.45 - 60, y=100 + box_h)
        self.end_time = tk.Label(root, text=str(datetime.timedelta(seconds=0)))
        self.end_time.place(x=box_w * 0.45 + box_w, y=100 + box_h)

        self.vid_player.bind("<<Duration>>", self.update_duration)
        self.vid_player.bind("<<SecondChanged>>", self.update_scale)
        self.vid_player.bind("<<FrameChanged>>", self.update_frame)

        # Initialize text widget for comments
        self.sentence_text = tk.Text(root, bg='#FDFDFD', relief=SUNKEN, font=("Arial", 15), spacing1=3, spacing2=3,
                                     spacing3=3)
        self.sentence_text.place(x=50, y=40 + box_h * 0.45, width=root_w - box_w - 200, height=box_h * 0.55 + 20)
        self.scrollb = tk.Scrollbar(root, command=self.sentence_text.yview)
        self.scrollb.place(x=50 + root_w - box_w - 200, y=40 + box_h * 0.45, width=20, height=box_h * 0.55 + 20)
        self.sentence_text['yscrollcommand'] = self.scrollb.set


        # Initialize Robot commentator (Daisy)
        self.commentator_player = TkinterVideo(scaled=True, pre_load=False, master=root, bg='white', relief=SUNKEN)
        self.commentator_player.place(x=box_w * 0.25, y=60, width=box_h / 3, height=box_h / 3)

        self.commentator = commentator(name='Commentator/daisy.png')


        # Initialize TTS
        self.tts = TTSManager()
        self.tts.set_active_engine(TTS_ENGINE.SAPI5)
        self.is_speaking = False

        # Load action and background sentences
        self.all_action_sentences = load_action()
        self.background_sentences = None

        # Initialize variables
        self.cantonese = True
        self.frame_count = 0
        self.silent_time = 0
        self.action_silent_time = 0

    def seek(self, value):
        """ used to seek a specific timeframe """
        self.vid_player.seekframe(int(value))

    def get_text(self, cantonese_text, english_text):
        return cantonese_text if self.cantonese else english_text

    def print_list(self, videolist):
        video_list = tk.Listbox(bg='white', relief=SUNKEN)  # Set a list
        video_list.place(x=50, y=80, width=200)  # Set position
        for i, name in enumerate(videolist):  # Enumerate: return [index, content]
            if name[-4:] == ".mp4" or name[-4:] == "mkv":
                video_list.insert(i, name)  # List name w.r.t. index and name
        video_list.bind('<<ListboxSelect>>', self.load_video)  # When selected, run onselect\

    def load_video(self, evt):
        self.external_stop_tts()
        """ loads the video """
        w = evt.widget  # get widget that call this function
        index = int(w.curselection()[0])  # get the index of the object clicked
        file_path = 'Video/' + w.get(index)  # get the name accroding to the index
        self.commentator_player.show_commentator('Commentator/daisy.png')

        if file_path:
            self.vid_player.load(file_path)
            self.progress_slider.config(to=0, from_=0)
            self.progress_slider.set(0)
            self.vid_player.play()
            self.play_pause_btn["text"] = "Pause"
            self.play_pause_btn.config(bg="red")
            self.background_sentences = load_comment(w.get(index)[:-4])

        self.silent_time = 0
        self.action_silent_time = 0
        self.frame_count = 0

    def update_duration(self, event):
        self.end_time["text"] = str(datetime.timedelta(seconds=self.vid_player.duration()))[:10]
        self.progress_slider["to"] = int(self.vid_player.duration() * self.vid_player.frame_rate())

    def update_scale(self, event):
        self.silent_time += 1
        self.action_silent_time += 1
        self.current_time = self.vid_player.current_duration()

        if self.silent_time >= 5:
            self.silent_time = 0
            num_line = random.randint(0, len(self.background_sentences) - 1)
            comment = str(self.background_sentences[num_line])
            self.sentence_text.insert('end', comment)
            self.sentence_text.see(tk.END)
            self.background_sentences.pop(num_line)
            self.speak_line(comment)

    def update_frame(self, event):
        self.frame_count += 1
        self.progress_slider.set(self.vid_player.current_frame())
        self.start_time["text"] = str(datetime.timedelta(seconds=self.vid_player.current_duration()))[:10]

        img_after = self.vid_player.frame_img().copy()
        img_after = img_after.convert('L')
        img_after = np.array(img_after)
        predictions = self.action_predictor.predict(img_after, self.frame_count)
        if predictions is not None and self.action_silent_time >= 2:
            lan = 'can' if self.cantonese else 'eng'
            comment = random.choice(self.all_action_sentences.get(predictions).get(lan))
            self.sentence_text.insert(tk.END, f'{predictions}: {comment}\n')
            self.sentence_text.see(tk.END)
            self.speak_line(comment)
            self.silent_time = 0
            self.action_silent_time = 0

    def play_pause(self):
        if self.vid_player.is_paused():
            self.vid_player.play()
            self.play_pause_btn["text"] = "Pause"
            self.play_pause_btn.config(bg="red")
        else:
            self.vid_player.pause()
            self.play_pause_btn["text"] = "Play"
            self.play_pause_btn.config(bg="grey")

    # Keep the speak_line and _speech_worker methods
    def speak_line(self, text):
        """Enqueue a line to be spoken"""
        if self.tts.is_speaking:
            # Optional: You could implement a way to queue multiple lines
            self.external_stop_tts()
        self.tts.speak_line(text)

    def external_stop_tts(self):
        """Public method to stop TTS from anywhere"""
        self.tts.stop()
