# Export settings

The bundled Remotion composition defaults to 1080×1920, 30 fps, H.264, yuv420p, BT.709, and AAC audio. These are implementation defaults for a vertical social video workflow, not a promise that every platform or project should use them.

Before export, confirm the delivery platform's current size, frame rate, codec, bitrate/quality, audio, and file-size guidance. Match the source frame rate where practical, use the intended aspect ratio, and inspect the rendered file after export. For other formats, recompose the project and change the renderer settings intentionally.

Run `pipeline/qc_video.py` to inspect dimensions, frame rate, codec, audio presence, optional expected duration, black frames, freezes, loudness, and optionally create a contact sheet. Its checks are technical and do not judge composition, caption accuracy, story, or rights.
