import cv2
import os

from PIL import Image, ImageTk


def create_color_by_class(class_no):
    colors = []
    step = 255 / class_no
    for i in range(class_no + 1):
        colors.append([step * i, step * (class_no - i), step * i])
    return colors


def draw_box(image, boxes, colors):
    with open('yolo/coco.name', 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    font = cv2.FONT_HERSHEY_PLAIN
    for i in range(len(boxes)):
        x, y, x2, y2, cls, label = boxes[i]
        if x2 - x < 400 or y2 - y < 400:
            color = colors[int(label)]
            label = str(float("{:.3f}".format(cls))) + str(classes[int(label)])
            cv2.rectangle(image, (int(x), int(y)), (int(x2), int(y2)), color, 3)
            cv2.putText(image, label, (int(x), int(y) - 5), font, 1, color, 2)
    return image


def call_from_folder(path):
    video_path = path  # Folder name contain your testing video
    video_list = os.listdir(video_path)  # list out all files inside folder
    return video_list  # Return list


def get_video_info(vid_name):
    fps = cv2.VideoCapture('Video/' + vid_name).get(cv2.CAP_PROP_FPS)
    frame_interval = 1 / fps
    screenshot_name = vid_name[:-4]
    return fps, frame_interval, screenshot_name


def screenshot(name, frame, img, img_pr, start):
    turned_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGRA)
    cv2.imwrite('Screenshot/' + name + '_' + str(frame) + '.jpg', turned_img)
    if start:
        turned_img = cv2.cvtColor(img_pr, cv2.COLOR_RGB2BGRA)
        cv2.imwrite('Screenshot/' + name + '_' + str(frame) + '_result' + '.jpg', turned_img)


def frame_resize(image, w, h):
    if image.shape[0] > image.shape[1]:
        if image.shape[0] > h:
            image = cv2.resize(image, (0, 0), fx=(h / image.shape[0]), fy=(h / image.shape[0]),
                               interpolation=cv2.INTER_AREA)
        elif image.shape[1] > w:
            image = cv2.resize(image, (0, 0), fx=(w / image.shape[1]), fy=(w / image.shape[1]),
                               interpolation=cv2.INTER_AREA)
    else:
        if image.shape[1] > w:
            image = cv2.resize(image, (0, 0), fx=(w / image.shape[1]), fy=(w / image.shape[1]),
                               interpolation=cv2.INTER_AREA)
        elif image.shape[0] > h:
            image = cv2.resize(image, (0, 0), fx=(h / image.shape[0]), fy=(h / image.shape[0]),
                               interpolation=cv2.INTER_AREA)
    return image


def show_image(image):
    image_frame = Image.fromarray(image)
    frame_image = ImageTk.PhotoImage(image_frame)
    return frame_image


def frame2second(f, fps):
    s = f / fps
    return s


def line_segment(line):
    line = line.split()
    second = 0
    next_word = ''
    action = ''
    eng_comment = ''
    can_comment = ''
    instruction = ''
    for word in line:
        if word[0] == '-':
            next_word = word
        else:
            if next_word[1] == 's':
                second = float(word)
            elif next_word[1] == 'a':
                action = action + word + ' '
            elif next_word[1] == 'c':
                if next_word[2] == 'E':
                    eng_comment = eng_comment + word + ' '
                else:
                    can_comment = can_comment + word + ' '
            elif next_word[1] == 'z':
                instruction = instruction + word + ' '
    return second, action, eng_comment, can_comment, instruction


def add_transparent(bg, anno, pos):
    # bg_x, bg_y = bg.size[0], bg.size[1]
    bg.paste(anno, pos, anno.convert('RGBA'))
    return bg


if __name__ == "__main__":
    # EXAMPLE TO USE LINE_SEGMENT
    s, a, ec, cc, ins = line_segment(
        "-s 40 -a ball out of play -cE B team shoot, but miss, what a shame -cC 日本政府或最快下周宣布放寬入境管制措施 -z img.jpg 10 brabara")
    print(s, a, ec, cc, ins)
    # EXAMPLE OF CREATE COLOR LIST FOR ANNOTATION
    # colors = create_color_by_class(80)
    # print(colors[33])
    #
    # fr_img = Image.open("annotation/test.png")
    # bg_img = Image.open("annotation/test.jpg")
    # img = add_transparent(bg_img, fr_img)
    # img.show()
