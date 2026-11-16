---
name: edit-long-interview
description: >-
  Edit and deliver long-form interview or podcast videos with timed bilingual
  subtitles, opening overlays, question cards, sourced graphics, and an optional
  musical outro. Use for Riverside edits, local FFmpeg finishing, caption timing
  checks, YouTube review cuts, and private media handoffs. Also applies to
  长视频剪辑、双语字幕、片头片尾、长片审看版 and 字幕时间码.
---

# Edit Long Interviews

## Establish the source timeline

1. Identify the current cut and capture its duration, aspect ratio, audio, and visible layout. Confirm the actual file or editor state before using its timestamps.
2. Verify speaker names and the subject from the recording or notes. Record the difference between source time, current edited time, and the intended final timeline. Use the current edited time for cards and captions.
3. Locate the best available video and editable caption files. Work on a duplicate or review export when the editor supports one. Keep a list of approved changes so a new finishing pass picks up where the previous one ended.

## Edit for the conversation

- Open on the first usable exchange. Place the subject and speaker names over the original opening for about four seconds when existing captions should retain their timing. Use the project's aspect ratio and framing.
- Place question or chapter graphics at major changes of topic. Let the actual question start, use the available negative space, and keep faces and subtitles clear. Read the opening and each new graphic at phone size.
- Show a referenced chart when it is named. Hold the complete figure briefly for context, then use a legible crop of the relevant panels if needed. Keep the original scales, labels, and attribution. Match an on-screen source number to a full source link in the episode notes.
- Let emotional answers and pauses carry their own rhythm. Put any closing quote after its spoken setup, keep the original wording, and attribute it only when the speaker is verified.
- Bring in music after the last intelligible line when the user requested an outro. Use the supplied or authorized recording, check its intended duration, and leave enough time to read any quote cards.

## Work in the chosen editor

Use the live editor's verified controls for uploads, overlays, layout, and preview when the user is working there. Position the playhead by a transcript phrase and check the visible timeline edit time before applying a graphic. Verify the object on the timeline and preview its entrance and exit. Use the exported media and local rendering when the user authorizes a standalone review cut or when the workflow can proceed from the approved export. State which changes are editable in the web project and which are in the rendered file.

Keep video and audio synchronized through overlays. Where feasible, preserve the source dialogue track. When re-encoding or splicing a long file, verify timestamps and playback across the changed boundaries, including the transition to the outro.

## Prepare bilingual captions

Treat a current, reviewed SRT as the timing reference. Correct actual transcription errors, names, and punctuation with the conversation as context. Preserve the speaker's voice and the meaning of each cue. If translating line by line, preserve the same start and end times in both files.

Apply the same time transformations to all caption languages after any added intro or dialogue cut. A visual-only overlay or a tail appended after the interview keeps the existing cues on their original timeline. Check the first and last cues, cues at edits, the placement around graphics, and uninterrupted dialogue in both languages.

## Verify and deliver

Run the bundled checker against the completed export and captions. Add `--match-cues` when both tracks are intended to have the same cue boundaries. Use `--subtitle-end` when captions are intended to stop before an outro.

```bash
python3 scripts/check_review.py review.mp4 --srt english.srt --srt chinese.srt \
  --match-cues --subtitle-end 00:40:00,000
```

Preview the opening, a representative question card, both edges of any sourced image insert, the last spoken line, and the complete handoff to music. Verify picture, captions, cue alignment, and audio where they overlap. Report only the checks performed.

Deliver a video, each requested language track, and a short review note with key timecodes and any remaining issues. If a hosting service is requested, verify the completed upload, its audience, and the download page. Verify the recipient and follow the user's sending or review instructions before sharing.
