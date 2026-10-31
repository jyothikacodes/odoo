import math
import struct
import wave
import os

def generate_ambient_track(output_path, total_duration_seconds=180, sample_rate=44100):
    """
    Generates a gentle, warm corporate tech ambient chord pad progression.
    Chords: Cmaj9 -> Am9 -> Fmaj7 -> Gadd9 (cycling every 8 seconds)
    """
    print(f"🎵 Synthesizing ambient corporate tech background music ({total_duration_seconds}s)...")
    
    # Chord frequencies in Hz
    # Cmaj9: C3 (130.81), G3 (196.00), B3 (246.94), D4 (293.66), E4 (329.63)
    # Am9:   A2 (110.00), E3 (164.81), G3 (196.00), B3 (246.94), C4 (261.63)
    # Fmaj7: F2 (87.31),  C3 (130.81), E3 (164.81), A3 (220.00), C4 (261.63)
    # Gsus4: G2 (98.00),  D3 (146.83), G3 (196.00), C4 (261.63), D4 (293.66)
    chords = [
        [130.81, 196.00, 246.94, 293.66, 329.63],
        [110.00, 164.81, 196.00, 246.94, 261.63],
        [87.31,  130.81, 164.81, 220.00, 261.63],
        [98.00,  146.83, 196.00, 261.63, 293.66],
    ]
    
    chord_len = 8.0 # seconds per chord
    total_samples = int(total_duration_seconds * sample_rate)
    
    # Detune offsets for lush chorus width
    detunes = [-0.004, -0.002, 0.0, 0.002, 0.004]
    
    num_channels = 2
    sampwidth = 2
    
    with wave.open(output_path, 'w') as wav:
        wav.setnchannels(num_channels)
        wav.setsampwidth(sampwidth)
        wav.setframerate(sample_rate)
        
        chunk_size = 4096
        sample_idx = 0
        
        while sample_idx < total_samples:
            frames = bytearray()
            current_chunk = min(chunk_size, total_samples - sample_idx)
            
            for i in range(current_chunk):
                t = (sample_idx + i) / sample_rate
                
                # Determine chord index and crossfade blend between consecutive chords
                cycle_pos = (t % (chord_len * len(chords)))
                curr_chord_idx = int(cycle_pos // chord_len)
                next_chord_idx = (curr_chord_idx + 1) % len(chords)
                chord_prog = (cycle_pos % chord_len) / chord_len
                
                # Smooth sinusoidal crossfade between chords
                fade_width = 1.8 # seconds of smooth transition
                fade_pos = (cycle_pos % chord_len)
                if fade_pos < fade_width:
                    blend = 0.5 - 0.5 * math.cos(math.pi * fade_pos / fade_width)
                elif fade_pos > (chord_len - fade_width):
                    blend = 0.5 + 0.5 * math.cos(math.pi * (fade_pos - (chord_len - fade_width)) / fade_width)
                else:
                    blend = 1.0
                
                c_now = chords[curr_chord_idx]
                
                # Breathing LFO
                lfo = 0.85 + 0.15 * math.sin(2 * math.pi * 0.25 * t)
                
                # Sub-bass warmth
                sub = 0.18 * math.sin(2 * math.pi * (c_now[0] / 2.0) * t)
                
                left_sig = sub
                right_sig = sub
                
                # Sum chord harmonics with gentle stereo spread
                for fi, freq in enumerate(c_now):
                    # Slight stereo detune
                    f_l = freq * (1.0 + detunes[fi])
                    f_r = freq * (1.0 - detunes[fi])
                    
                    # Soft fundamental + gentle 2nd harmonic
                    h_l = math.sin(2 * math.pi * f_l * t) + 0.25 * math.sin(4 * math.pi * f_l * t)
                    h_r = math.sin(2 * math.pi * f_r * t) + 0.25 * math.sin(4 * math.pi * f_r * t)
                    
                    weight = (0.28 / (fi + 1))
                    left_sig += h_l * weight
                    right_sig += h_r * weight
                
                left_sig *= lfo * blend * 0.15
                right_sig *= lfo * blend * 0.15
                
                # Overall fade-in (first 2s) and fade-out (last 3s)
                if t < 2.0:
                    left_sig *= (t / 2.0)
                    right_sig *= (t / 2.0)
                elif t > (total_duration_seconds - 3.0):
                    left_sig *= ((total_duration_seconds - t) / 3.0)
                    right_sig *= ((total_duration_seconds - t) / 3.0)
                
                # Clamp to 16-bit PCM
                left_int = int(max(min(left_sig, 0.99), -0.99) * 32767)
                right_int = int(max(min(right_sig, 0.99), -0.99) * 32767)
                
                frames.extend(struct.pack('<hh', left_int, right_int))
            
            wav.writeframes(frames)
            sample_idx += current_chunk
            
    print(f"✅ Ambient track generated at: {output_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "output", "audio")
    os.makedirs(out_dir, exist_ok=True)
    generate_ambient_track(os.path.join(out_dir, "ambient_pad.wav"), total_duration_seconds=200)
