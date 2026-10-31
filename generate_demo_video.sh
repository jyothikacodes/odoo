#!/usr/bin/env bash
set -e

echo "================================================================="
echo "🎥 Brightloop Platform: End-to-End MP4 Demo Video Generator"
echo "================================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Capture high-res UI screenshots
echo ""
echo "📸 Step 1/4: Capturing 10 Full HD application screenshots..."
node scripts/video_generator/capture_scenes.js

# 2. Synthesize ambient corporate tech background soundtrack
echo ""
echo "🎵 Step 2/4: Generating ambient corporate tech background audio..."
.venv/bin/python scripts/video_generator/generate_ambient_audio.py

# 3. Synthesize neural voiceover narration
echo ""
echo "🎙 Step 3/4: Synthesizing Edge-TTS neural voiceover narration..."
.venv/bin/python scripts/video_generator/generate_narration.py

# 4. Render and assemble final 1080p MP4
echo ""
echo "🎬 Step 4/4: Assembling and encoding final 1080p MP4 with FFmpeg..."
.venv/bin/python scripts/video_generator/render_video.py

echo ""
echo "================================================================="
echo "✅ Video generation complete!"
echo "Output: $(pwd)/brightloop_demo_explanation.mp4"
echo "================================================================="
