# Test URLs for StepScribe

## YouTube — short tutorial with auto-captions (fast path)
https://www.youtube.com/watch?v=rfscVS0vtbw
(Python in 5 minutes — short, has captions, good first test)

## YouTube — longer tutorial
https://www.youtube.com/watch?v=ZDa-Z5JzLYM
(Python full course for beginners)

## Instagram
Only public reels work. Private accounts return a friendly error.
Example flow: find a public reel URL on Instagram and paste it directly.

## Notes
- YouTube with captions = fastest (no Whisper compute)
- Instagram = Whisper always runs (captions rarely available)
- First Ollama run is slower (model loads into memory); subsequent runs are faster
