import re
import os
import random
import logging
import moviepy.editor as mp
from moviepy.video.fx import fadein, fadeout
from moviepy.video.fx.all import resize, crop
from moviepy.video.VideoClip import ImageClip
from Backend.logger import logging

def get_closest_file(folder, start_time, prefix, extension):
    """Find the closest matching file (image or audio) based on the scene number."""
    files = os.listdir(folder)
    file_numbers = [int(re.search(rf"{prefix}_(\d+)\.{extension}$", f).group(1)) 
                    for f in files if re.search(rf"{prefix}_(\d+)\.{extension}$", f)]

    if not file_numbers:
        logging.warning(f"No matching files found in {folder} for {prefix} with {extension} extension.")
        return None

    closest_scene = min(file_numbers, key=lambda x: abs(x - start_time))
    logging.info(f"Closest file for scene {prefix}_{closest_scene}.{extension} found.")
    return os.path.join(folder, f"{prefix}_{closest_scene}.{extension}")


def apply_ken_burns(image_clip):
    """Apply a random Ken Burns effect (zoom or pan) with animation."""
    w, h = image_clip.size
    duration = max(image_clip.duration, 1)
    effects = ["in", "out", "left", "right", "up", "down", None]
    chosen_effect = random.choice(effects)
    zoom_factor = random.uniform(1.05, 1.2)

    if chosen_effect == "in":
        zoom_clip = resize(image_clip, lambda t: 1 + (zoom_factor - 1) * (t / duration))
    elif chosen_effect == "out":
        zoom_clip = resize(image_clip, lambda t: zoom_factor - (zoom_factor - 1) * (t / duration))
    else:
        zoom_clip = image_clip

    move_x, move_y = int(w * 0.1), int(h * 0.1)

    def crop_function(get_frame, t):
        frame = get_frame(t)
        x, y = 0, 0
        if chosen_effect == "left": x = int((t / duration) * move_x)
        elif chosen_effect == "right": x = -int((t / duration) * move_x)
        elif chosen_effect == "up": y = int((t / duration) * move_y)
        elif chosen_effect == "down": y = -int((t / duration) * move_y)
        return crop(ImageClip(frame), x1=x, y1=y, width=w, height=h).img

    pan_clip = zoom_clip.fl(crop_function)
    logging.info(f"Applied Ken Burns effect: {chosen_effect} (Duration: {duration}s)")
    return pan_clip


def create_final_video(script_data, images_folder, voiceover_folder, bg_music_path, output_video_path):
    clips = []

    for idx, scene in enumerate(script_data["scenes"]):
        timestamp = scene["timestamp"]
        start_time, end_time = map(lambda x: int(x.split(":")[1]), timestamp.split(" - "))
        duration = end_time - start_time
        img_path = os.path.join(images_folder, f"scene_{idx+1}.png")
        audio_path = os.path.join(voiceover_folder, f"scene_{idx+1}.mp3")

        if not os.path.exists(img_path) or not os.path.exists(audio_path):
            logging.warning(f"Missing image or voiceover for scene {idx+1}, skipping...")
            continue

        img_clip = mp.ImageClip(img_path).set_duration(duration)
        img_clip = apply_ken_burns(img_clip)
        audio_clip = mp.AudioFileClip(audio_path)
        img_clip = img_clip.set_duration(audio_clip.duration).set_audio(audio_clip)

        transition = scene.get("suggested_transition_effect", "fade-in").lower()
        if transition == "fade-in":
            img_clip = fadein.fadein(img_clip, 1)
        elif transition == "crossfade":
            img_clip = fadeout.fadeout(img_clip, 1).fx(fadein.fadein, 1)
        elif transition == "zoom out":
            img_clip = resize(img_clip, lambda t: 1 + 0.05 * t)
        elif transition == "quick cuts":
            img_clip = fadeout.fadeout(img_clip, 0.5)
        else:
            logging.warning(f"Unknown transition '{transition}' for scene {idx+1}. Defaulting to fade-in.")
            img_clip = fadein.fadein(img_clip, 1)

        clips.append(img_clip)

    if not clips:
        logging.error("No valid video clips created. Check if images and audio exist.")
        raise ValueError("No valid video clips created. Check if images and audio exist.")

    final_video = mp.concatenate_videoclips(clips, method="compose")

    if os.path.exists(bg_music_path):
        bg_music = mp.AudioFileClip(bg_music_path).volumex(0.3)
        final_audio = mp.CompositeAudioClip([final_video.audio, bg_music])
        final_video = final_video.set_audio(final_audio)
        logging.info("Background music added successfully.")

    final_video.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")
    logging.info(f"Video exported successfully to {output_video_path}")
