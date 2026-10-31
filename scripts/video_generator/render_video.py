import os
import sys
import json
import subprocess

def render_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "output")
    clips_dir = os.path.join(out_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    manifest_path = os.path.join(out_dir, "scenes_manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: {manifest_path} not found. Run generate_narration.py first.")
        sys.exit(1)
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    font_file = "/usr/share/fonts/noto/NotoSans-Bold.ttf"
    fps = 30
    clip_files = []
    
    print("🎬 Starting FFmpeg Scene Rendering...")
    for idx, scene in enumerate(manifest, 1):
        scene_id = scene["id"]
        image_path = os.path.join(out_dir, "screenshots", scene["image"])
        audio_path = os.path.join(out_dir, "audio", scene["audio_file"])
        clip_path = os.path.join(clips_dir, f"clip_{scene_id}.mp4")
        clip_files.append(f"file '{clip_path}'\n")
        
        duration = scene["scene_duration"]
        total_frames = int(duration * fps)
        
        # Clean text for drawtext: replace %, :, '
        section_txt = scene["section"].replace("%", " Percent").replace(":", "\\:").replace("'", "\\'")
        title_txt = scene["title"].replace("%", " Percent").replace(":", "\\:").replace("'", "\\'")
        
        # Skip if already rendered and valid
        if os.path.exists(clip_path) and os.path.getsize(clip_path) > 200000:
            print(f"  [{idx}/{len(manifest)}] {scene_id} already rendered ({os.path.getsize(clip_path)//1024} KB). Skipping.")
            continue
            
        print(f"  Rendering [{idx}/{len(manifest)}] {scene_id} ({duration}s)...")
        
        vf = (
            f"scale=1920:1080,"
            f"zoompan=z='min(zoom+0.00018,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1920x1080:fps={fps},"
            f"drawbox=x=60:y=890:w=1280:h=120:color=black@0.78:t=fill,"
            f"drawbox=x=60:y=890:w=8:h=120:color=#6366F1:t=fill,"
            f"drawtext=fontfile={font_file}:text='{section_txt}':fontcolor=#22D3EE:fontsize=22:x=90:y=915,"
            f"drawtext=fontfile={font_file}:text='{title_txt}':fontcolor=white:fontsize=32:x=90:y=955"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-filter_complex",
            f"[0:v]{vf}[v];[1:a]apad[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            clip_path
        ]
        
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            print(f"Error rendering {clip_path}:")
            print(res.stderr.decode()[-800:])
            sys.exit(1)
            
    print("✅ All individual scene clips rendered!")
    
    # Write concat list
    concat_list_path = os.path.join(out_dir, "concat_list.txt")
    with open(concat_list_path, "w") as f:
        f.writelines(clip_files)
        
    raw_video_path = os.path.join(out_dir, "concatenated_raw.mp4")
    print("🔗 Concatenating scenes into continuous video track...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        raw_video_path
    ]
    subprocess.check_call(concat_cmd)
    
    # Final step: Mix with ambient background music
    ambient_path = os.path.join(out_dir, "audio", "ambient_pad.wav")
    final_output_path = os.path.abspath(os.path.join(base_dir, "..", "..", "brightloop_demo_explanation.mp4"))
    
    total_duration = sum(s["scene_duration"] for s in manifest)
    print(f"🎛 Mixing narration with ambient background audio (total {total_duration:.1f}s)...")
    
    if os.path.exists(ambient_path):
        mix_cmd = [
            "ffmpeg", "-y",
            "-i", raw_video_path,
            "-i", ambient_path,
            "-filter_complex",
            f"[1:a]volume=0.075,atrim=0:{total_duration},afade=t=out:st={total_duration - 3.5}:d=3.5[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            final_output_path
        ]
    else:
        mix_cmd = [
            "ffmpeg", "-y",
            "-i", raw_video_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            final_output_path
        ]
        
    subprocess.check_call(mix_cmd)
    
    # Copy to brain artifact directory as well for convenience
    artifact_dir = "/home/jyothika/.gemini/antigravity-cli/brain/25f6c6f8-0a30-4efa-86c1-f43b38f34c2c"
    artifact_video = os.path.join(artifact_dir, "brightloop_demo_explanation.mp4")
    try:
        subprocess.check_call(["cp", final_output_path, artifact_video])
    except Exception as e:
        print(f"Notice: could not copy to artifact dir: {e}")
        
    print(f"🎉 Final MP4 video successfully created at:")
    print(f"👉 {final_output_path}")

if __name__ == "__main__":
    render_all()
