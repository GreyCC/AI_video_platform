import cv2
import numpy
from PIL import Image
from utils import add_transparent


def additional_information(img, anno_name, x_ratio, y_ratio, text):
    anno_img = Image.fromarray(img)

    anno = Image.open("annotation/" + anno_name)
    anno_size = (int(anno_img.size[0] * x_ratio), int(anno_img.size[1] * y_ratio))
    anno = anno.resize(anno_size)

    cloud = Image.open("annotation/cloud.png")
    cloud_size = (int(anno_img.size[0] * x_ratio), int(anno_img.size[1] * y_ratio / 2))
    cloud = cloud.resize(cloud_size)

    anno_img = add_transparent(anno_img, anno, (int(anno_img.size[0] - anno.size[0]), 0))
    anno_img = add_transparent(anno_img, cloud, (int(anno_img.size[0] - anno.size[0]), anno.size[1]))

    anno_img = numpy.asarray(anno_img)

    font = cv2.FONT_HERSHEY_COMPLEX
    text_pos = (int(anno_img.shape[1] - anno.size[0] * 0.8), int(anno.size[1] * 1.31))
    cv2.putText(anno_img, text, text_pos, font, 0.8, [0, 0, 0], 1)
    # anno_img = cv2.cvtColor(anno_img, cv2.COLOR_BGR2RGB)

    return anno_img


def super_resolute(img, x_ratio, y_ratio, enlarge_area, position):
    img_width, img_height = img.shape[0], img.shape[1]
    box, _ = box_pos(img_width, img_height, x_ratio, y_ratio, position)
    pass


def box_pos(img_height, img_width, x_ratio, y_ratio, position):
    box_width = round(img_width * x_ratio)
    box_height = round(img_height * y_ratio)
    if position == 'TR' or position == 'TL':  # Top
        box_y_pos = [0, box_height]
    else:
        box_y_pos = [img_height - box_height, img_height]

    if position == 'TL' or position == 'BL':  # Left
        box_x_pos = [0, box_width]
    else:
        box_x_pos = [img_width - box_width, img_width]
    box = [[box_x_pos[0] - 5, box_y_pos[0] - 5], [box_x_pos[1] - 5, box_y_pos[1] - 5]]
    text_x = int(box_x_pos[0] + (box_width / 8))
    text_y = int(box_y_pos[0] + (box_height / 2))
    text_box = [text_x, text_y]
    return box, text_box


def select_region(self):
    self.select_x_pos = [self.closeup_x, self.closeup_x + self.box_width]
    self.select_x_pos = [self.closeup_y, self.closeup_y + self.box_height]


if __name__ == '__main__':
    img = additional_information(cv2.imread("annotation/test.jpg"), 'test_1.jpg', 0.2, 0.2, 'Exampleee')
    img = Image.fromarray(img)
    img.show()
