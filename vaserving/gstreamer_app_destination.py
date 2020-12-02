'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

from collections import namedtuple
from enum import Enum, auto
from vaserving.app_destination import AppDestination
from vaserving.gstreamer_pipeline import GStreamerPipeline
from gstgva.video_frame import VideoFrame

GvaSample = namedtuple('GvaSample', ['sample', 'video_frame'])
GvaSample.__new__.__defaults__ = (None, None)

class GStreamerAppDestination(AppDestination):

    class Mode(Enum):
        FRAMES = auto()
        REGIONS = auto()
        TENSORS = auto()
        MESSAGES = auto()
        @classmethod
        def _missing_(cls, name):
            return cls[name.upper()]

    def __init__(self, request, pipeline, *args, **kwargs):
        AppDestination.__init__(self, request, pipeline)

        request_config = request.get("destination", {})
        self._output_queue = request_config.get("output", None)
        if (not isinstance(pipeline, GStreamerPipeline)) or (not self._output_queue):
            raise Exception("GStreamerAppDestination requires GStreamerPipeline and output queue")
        self._mode = GStreamerAppDestination.Mode(request_config.get("mode", "frames"))

    def _create_output_item(self, sample):

        try:
            video_frame = VideoFrame(sample.get_buffer(),
                                     caps=sample.get_caps())
        except Exception:
            video_frame = None

        if (self._mode == GStreamerAppDestination.Mode.FRAMES):
            return GvaSample(sample, video_frame)
        if (self._mode == GStreamerAppDestination.Mode.REGIONS):
            regions = []
            if (video_frame):
                regions = video_frame.regions()
            return regions
        if (self._mode == GStreamerAppDestination.Mode.TENSORS):
            tensors = []
            if (video_frame):
                tensors = video_frame.tensors()
            return tensors
        if (self._mode == GStreamerAppDestination.Mode.MESSAGES):
            messages = []
            if (video_frame):
                messages = video_frame.messages()
            return messages

        return None

    def process_frame(self, frame):
        self._output_queue.put(self._create_output_item(frame))

    def finish(self):
        self._output_queue.put(None)
