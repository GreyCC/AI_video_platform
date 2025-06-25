
from codeop import CommandCompiler
from distutils import command
from re import L
import json
import random


def load_action(action_name=None):
    """
    Load all action sentences from a JSON file if not already loaded.
    If action_name is provided, return sentences for that specific action.

    Args:
        action_name: The action to get sentences for (optional function parameter)

    Returns:
        dict: Nested dictionary containing English and Chinese sentences for all actions
    """
    # File path
    FILE_PATH = 'load_sentences/action_sentences.json'

    with open(FILE_PATH, 'r', encoding='utf-8') as file:
        action_sentences = json.load(file)
    print("Action sentences loaded successfully!")

    # If specific action requested, return that action's sentences
    if action_name:
        # Your Video class will handle the random selection here
        return {
            'en': action_sentences.get('actions', {}).get(action_name, {}).get('eng', []),
            'cn': action_sentences.get('actions', {}).get(action_name, {}).get('can', [])
        }

    return action_sentences


# Cantonese Only
def load_comment(name):
    sentences = []
    with open(f'Video/comment/{name}.txt', encoding="utf-8") as file:
        a = file.readlines()
    for line in a:
        sentences.append(line)
    return sentences


# def load_comment(name):
#     English = False
#     English_command = []
#     Cantonese_command = []
#     with open(f'Video/comment/{name}.txt', encoding="utf-8") as file:
#         command = file.readlines()
#     for line in command:
#         if line.split()[0] == '#English':
#             English = True
#         elif English:
#             English_command.append(line)
#         else: Cantonese_command.append(line)
#     return English_command, Cantonese_command


def line_segment(list):
    second = 0
    action_eng = []
    action_can = []
    English = False
    for line in list:
        line = line.split()
        if line[0] == '-English':
            English = True
        next_word = ''
        label = ''
        for word in line:
            if word[0] == '-':
                next_word = word
            else:
                if next_word[1] == 't':
                    second = float(word)
                elif next_word[1] == 'l':
                    label = label + word + ' '
        if next_word[1] == 'l':
            if English:
                action_eng.append([second, label[:-1]])
            else: action_can.append([second, label[:-1]])
    return action_eng, action_can


# def translate(word):
#     if word == 'throw':
#         word = '界外球'
#     elif word == 'out':
#         word = '出界'
#     elif word == 'clearance':
#         word = '解圍'
#     elif word == 'free':
#         word = '自由球'
#     elif word == 'yellow':
#         word = '黃牌'
#     elif word == 'shot':
#         word = '射球'
#     elif word == 'corner':
#         word = '角球'
#     return word


if __name__ == '__main__':
    script = load_action('cantonese_clip_1')
    tt = line_segment(script)
    print(tt)
