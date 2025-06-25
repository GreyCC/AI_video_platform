from pathlib import Path
from itertools import islice
from typing import Optional, Iterable

import torch
from kornia.geometry.transform import hflip

import argus
import re

from .src.indexes import StackIndexesGenerator
from .src.frames import get_frames_processor


def batched(iterable: Iterable, size: int):
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, size)):
        yield batch

def get_best_model_path(dir_path, return_score=False, more_better=True):
    dir_path = Path(dir_path)
    model_scores = []
    for model_path in dir_path.glob('*.pth'):
        score = re.search(r'-(\d+(?:\.\d+)?).pth', str(model_path))
        if score is not None:
            score = float(score.group(0)[1:-4])
            model_scores.append((model_path, score))

    if not model_scores:
        if return_score:
            return None, -np.inf
        else:
            return None

    model_score = sorted(model_scores, key=lambda x: x[1], reverse=more_better)
    best_model_path = model_score[0][0]
    if return_score:
        best_score = model_score[0][1]
        return best_model_path, best_score
    else:
        return best_model_path

class MultiDimStackerPredictor:
    def __init__(self, model_path: Path, device: str = "cuda:0", tta: bool = False):
        self.model = argus.load_model(model_path, device=device, optimizer=None, loss=None)
        self.model.eval()
        self.device = self.model.device
        self.tta = tta
        assert self.model.params["nn_module"][0] == "multidim_stacker"
        self.frames_processor = get_frames_processor(*self.model.params["frames_processor"])
        self.frame_stack_size = self.model.params["frame_stack_size"]
        self.frame_stack_step = self.model.params["frame_stack_step"]
        self.indexes_generator = StackIndexesGenerator(self.frame_stack_size,
                                                       self.frame_stack_step)
        self.model_stack_size = self.model.params["nn_module"][1]["stack_size"]

        self._frame_index2frame: dict[int, torch.Tensor] = dict()
        self._stack_indexes2features: dict[tuple[int], torch.Tensor] = dict()
        self._predict_offset: int = self.indexes_generator.make_stack_indexes(0)[-1]

        self.classes = [
            "Penalty",
            "Kick-off",
            "Goal",
            "Substitution",
            "Offside",
            "Shots on target",
            "Shots off target",
            "Clearance",
            "Ball out of play",
            "Throw-in",
            "Foul",
            "Indirect free-kick",
            "Direct free-kick",
            "Corner",
            "Card",
        ]

    def reset_buffers(self):
        self._frame_index2frame = dict()
        self._stack_indexes2features = dict()

    def _clear_old(self, minimum_index: int):
        for index in list(self._frame_index2frame.keys()):
            if index < minimum_index:
                del self._frame_index2frame[index]
        for stack_indexes in list(self._stack_indexes2features.keys()):
            if any([i < minimum_index for i in stack_indexes]):
                del self._stack_indexes2features[stack_indexes]

    @torch.no_grad()
    def predict(self, frame, index: int) -> tuple[Optional[torch.Tensor], int]:
        frame = torch.from_numpy(frame).to(self.device)
        # frame = frame.half()  # if self.device.type == "cuda" else frame.float()
        # frame /= 255.0  # Normalize to [0, 1]
        # frame = frame.permute(2, 0, 1)  # [720, 1280, 3] -> [3, 720, 1280]
        # if frame.dim() == 3:
        #     frame = frame.unsqueeze(0)

        frame = frame.to(device=self.model.device)
        self._frame_index2frame[index] = self.frames_processor(frame[None, None, ...])[0, 0]
        predict_index = index - self._predict_offset
        predict_indexes = self.indexes_generator.make_stack_indexes(predict_index)
        self._clear_old(predict_indexes[0])
        if set(predict_indexes) <= set(self._frame_index2frame.keys()):
            # print("predicting")
            stacks_indexes = list(batched(predict_indexes, self.model_stack_size))
            for stack_indexes in stacks_indexes:
                if stack_indexes not in self._stack_indexes2features:
                    frames = torch.stack([self._frame_index2frame[i] for i in stack_indexes], dim=0)
                    if self.tta:
                        frames = torch.stack([frames, hflip(frames)], dim=0)
                    else:
                        frames = frames.unsqueeze(0)
                    features = self.model.nn_module.forward_2d(frames)
                    self._stack_indexes2features[stack_indexes] = features
            features = torch.cat([self._stack_indexes2features[s] for s in stacks_indexes], dim=1)
            features = self.model.nn_module.forward_3d(features)
            prediction = self.model.nn_module.forward_head(features)
            prediction = self.model.prediction_transform(prediction)
            prediction = torch.mean(prediction, dim=0)

            if prediction.dim() == 2:  # Batched tensor
                prediction = prediction.squeeze(0)  # Remove batch dimension
            if torch.max(prediction) >= 0.7:
                # Find the index of the maximum value
                max_index = torch.argmax(prediction).item()

                # Get the predicted class
                predicted_class = self.classes[max_index]
            else:
                predicted_class = None
            return predicted_class #, predict_index
        else:
            return None