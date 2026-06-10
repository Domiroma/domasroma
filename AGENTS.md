# AGENTS.md

## Cursor Cloud specific instructions

### Repository layout

This repo is primarily a personal document store. Branches differ in what they contain:

| Branch | Contents |
|---|---|
| `main` | Volunteer agreement templates (`.docx`/`.pdf`) and a minimal README — no runnable code |
| `cursor/animated-video-cv-b38b` | Offline Python CLI that renders a 90-second animated video CV (MP4 + SRT) |
| `cursor/perla-assessment-word-296b` | Assessment Center marketing experience documents |

There are no web servers, databases, Docker Compose stacks, or CI/lint configs. The only runnable "application" is the video CV generator on the animated-video CV branch.

### Running the video CV generator

1. Check out a branch that includes `requirements.txt` and `video_cv/` (e.g. `cursor/animated-video-cv-b38b` or `cursor/dev-environment-setup-06d9`).
2. Install Python deps: `python3 -m pip install -r requirements.txt`
3. Ensure `ffmpeg` is on `PATH` (pre-installed on the Cloud VM).
4. Generate output:

```bash
python3 video_cv/generate_animated_cv.py
```

Outputs land in `video_cv/output/`:

- `dominika_romanow_video_cv.mp4` (1280×720, 30 fps, ~90 s)
- `dominika_romanow_video_cv.srt`

Optional voiceover mux:

```bash
python3 video_cv/generate_animated_cv.py --voiceover path/to/voiceover.wav
```

### Gotchas

- **Full render time:** Expect ~2 minutes for the complete 90-second video (2700 frames rendered procedurally with Pillow, then encoded with FFmpeg).
- **FFmpeg libncurses warnings:** When run inside tmux, FFmpeg may print harmless `libncursesw.so.6: no version information available` warnings; encoding still succeeds.
- **No automated tests or linters:** Validate changes with `python3 -m py_compile video_cv/generate_animated_cv.py` and a full generator run.
- **Branch-specific files:** On `main`, `requirements.txt` does not exist — the update script guards for this.

See `README.md` on the video CV branch for user-facing usage notes.
