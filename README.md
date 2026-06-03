# domasroma

## Animated video CV

This repository includes a procedural animated video CV for Dominika Romanow.
The generator renders a 90-second, 1280x720, 30 fps video with smooth scene
transitions, subtle camera motion, and hand-drawn sketch accents.

Generate the MP4 and SRT subtitles:

```bash
python3 -m pip install -r requirements.txt
python3 video_cv/generate_animated_cv.py
```

Outputs:

- `video_cv/output/dominika_romanow_video_cv.mp4`
- `video_cv/output/dominika_romanow_video_cv.srt`

To add a recorded voiceover:

```bash
python3 video_cv/generate_animated_cv.py --voiceover path/to/voiceover.wav
```
