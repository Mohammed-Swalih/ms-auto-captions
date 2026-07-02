# generator.py
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont, ImageColor
from moviepy.editor import VideoFileClip, CompositeVideoClip, VideoClip
from proglog import ProgressBarLogger
from transcription import Transcriber


# --- Custom Logger for Real Progress Bar ---
class GuiLogger(ProgressBarLogger):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def callback_message(self, message):
        pass

    def bars_callback(self, bar, attr, value, old_value=None):
        # MoviePy uses 't' for the main rendering progress
        if bar == 't':
            total = self.bars[bar]['total']
            if total and total > 0:
                percentage = (value / total) * 100
                # Scale Rendering (0-100%) to the second half of the bar (50-100%)
                final_prog = 50 + (percentage / 2)
                self.callback(percent=final_prog, msg="Rendering Video...")


class SubtitleGenerator:
    def __init__(self, config, update_status_callback, update_progress_callback):
        self.config = config
        self.update_status = update_status_callback
        self.update_progress = update_progress_callback
        self.transcriber = Transcriber(
            use_api=self.config['use_api'],
            api_key=self.config.get('api_key'),
            model_size=self.config.get('model_size', 'base'),
            callback=update_status_callback
        )

    # --- Text Processing Helpers ---
    def group_words(self, words, max_words=3):
        chunks = []
        current_chunk = []
        for word in words:
            if not word["word"]: continue
            current_chunk.append(word)
            if len(current_chunk) >= max_words:
                chunks.append(current_chunk)
                current_chunk = []
        if current_chunk: chunks.append(current_chunk)
        return chunks

    def split_text_smart(self, chunk):
        words = [w["word"] for w in chunk]
        full_text = " ".join(words)
        middle = len(full_text) // 2
        split_idx = -1
        min_dist = 1000
        current_len = 0
        for i, w in enumerate(words):
            current_len += len(w) + 1
            dist = abs(current_len - middle)
            if dist < min_dist:
                min_dist = dist
                split_idx = i
        if split_idx == -1 or split_idx == len(chunk) - 1 or split_idx == 0:
            split_idx = (len(chunk) // 2) - 1
            if split_idx < 0: split_idx = 0
        return chunk[:split_idx + 1], chunk[split_idx + 1:]

    def get_highlight_indices(self, chunk):
        word_lengths = {i: len(w["word"]) for i, w in enumerate(chunk)}
        if not word_lengths: return []
        max_len = max(word_lengths.values())
        return [i for i, length in word_lengths.items() if length >= max_len * 0.9]

    # --- Drawing Logic ---
    def draw_text_line(self, draw, line_chunk, current_time, font, font_pop, style_config, width, y_pos,
                       opacity_mult=1.0):
        base_space = draw.textlength(" ", font=font)
        extra = style_config.get("extra_space", 0)
        space_width = base_space + extra

        word_widths = []
        word_fonts = []
        eps = 1e-6

        # Pre-calc widths
        for word_data in line_chunk:
            is_active = (current_time + eps) >= word_data["start"] and (current_time - eps) <= word_data["end"]
            current_font = font_pop if style_config.get("type") == "scale" and is_active else font
            w_w = draw.textlength(word_data["word"], font=current_font)
            word_widths.append(w_w)
            word_fonts.append(current_font)

        total_text_width = sum(word_widths) + (len(line_chunk) - 1) * space_width
        start_x = max(10, (width - total_text_width) / 2)
        std_font_height = getattr(font, 'size', 40)

        # Backgrounds (Bar)
        if style_config.get("type") == "bar":
            bar_color_hex = style_config.get("bar_color", "#000000")
            opacity = int(style_config.get("opacity", 150) * opacity_mult)
            rounded = style_config.get("rounded", False)
            try:
                c = ImageColor.getrgb(bar_color_hex)
                bar_fill = (c[0], c[1], c[2], opacity)
            except:
                bar_fill = (0, 0, 0, opacity)

            padding_x, padding_y = 20, 10
            box_coords = [start_x - padding_x, y_pos - padding_y,
                          start_x + total_text_width + padding_x, y_pos + std_font_height + padding_y]
            if rounded:
                draw.rounded_rectangle(box_coords, radius=15, fill=bar_fill)
            else:
                draw.rectangle(box_coords, fill=bar_fill)

        # Draw Words
        current_x = start_x
        highlight_indices = []
        if style_config.get("type") == "cinematic" and style_config.get("highlight_enabled"):
            highlight_indices = self.get_highlight_indices(line_chunk)

        for i, word_data in enumerate(line_chunk):
            word_text = word_data["word"]
            w_width = word_widths[i]
            draw_font = word_fonts[i]
            is_active = (current_time + eps) >= word_data["start"] and (current_time - eps) <= word_data["end"]

            draw_y = y_pos
            if style_config.get("type") == "bounce" and is_active:
                draw_y -= style_config.get("bounce_offset", 15)
            if style_config.get("type") == "scale" and is_active:
                draw_y -= (font_pop.size - font.size) / 2

            if style_config.get("type") == "reveal" and current_time < word_data["start"]:
                current_x += w_width + space_width
                continue

            # Determine Color
            text_color = style_config.get("text_color", "white")
            if style_config.get("type") == "cinematic" and i in highlight_indices:
                text_color = style_config.get("highlight_color", "yellow")
            elif is_active:
                if style_config.get("type") in ["color", "outline_active"]:
                    text_color = style_config.get("active_color", "yellow")

            # Draw Styles
            if style_config.get("type") == "box" and is_active:
                padding = style_config.get("box_padding", 10)
                box_color = style_config.get("box_color", "#8A2BE2")
                draw.rounded_rectangle(
                    [current_x - padding, y_pos - padding, current_x + w_width + padding,
                     y_pos + std_font_height + padding],
                    radius=12, fill=box_color
                )

            if style_config.get("type") == "glow" and is_active:
                glow_color = style_config.get("glow_color", "#00FFFF")
                for offx in range(-3, 4, 2):
                    for offy in range(-3, 4, 2):
                        draw.text((current_x + offx, draw_y + offy), word_text, font=draw_font, fill=glow_color)

            if style_config.get("type") in ["outline", "outline_active"]:
                stroke_width = style_config.get("stroke_width", 4)
                outline_col = style_config.get("outline_color", "black")
                draw.text((current_x, draw_y), word_text, font=draw_font, fill=text_color,
                          stroke_width=stroke_width, stroke_fill=outline_col)
            elif style_config.get("type") == "cinematic":
                shadow_off = style_config.get("shadow_offset", 2)
                draw.text((current_x + shadow_off, draw_y + shadow_off), word_text, font=draw_font, fill=(0, 0, 0, 255))
                draw.text((current_x, draw_y), word_text, font=draw_font, fill=text_color)
            else:
                draw.text((current_x, draw_y), word_text, font=draw_font, fill=text_color)

            current_x += w_width + space_width

    def create_text_image(self, size, chunk, current_time, font, font_pop, style_config, multi_line):
        width, height = size
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        opacity_mult = 1.0
        if style_config.get("type") == "cinematic":
            chunk_start = chunk[0]["start"]
            chunk_end = chunk[-1]["end"]
            duration = chunk_end - chunk_start
            fade_dur = 0.5
            t_in = current_time - chunk_start
            t_out = chunk_end - current_time
            if t_in < fade_dur:
                opacity_mult = t_in / fade_dur
            elif t_out < fade_dur:
                opacity_mult = t_out / fade_dur
            opacity_mult = max(0.0, min(1.0, opacity_mult))

        line_height = getattr(font, 'size', 50) * 1.2

        if multi_line and len(chunk) > 1:
            line1, line2 = self.split_text_smart(chunk)
            y1 = (height / 2) - line_height
            self.draw_text_line(draw, line1, current_time, font, font_pop, style_config, width, y1, opacity_mult)
            y2 = (height / 2)
            self.draw_text_line(draw, line2, current_time, font, font_pop, style_config, width, y2, opacity_mult)
        else:
            y = (height - getattr(font, 'size', 40)) / 2
            self.draw_text_line(draw, chunk, current_time, font, font_pop, style_config, width, y, opacity_mult)

        if style_config.get("type") == "cinematic" and opacity_mult < 1.0:
            r, g, b, a = img.split()
            a = a.point(lambda p: p * opacity_mult)
            img = Image.merge('RGBA', (r, g, b, a))

        return img

    def compute_chunk_timing_api(self, chunks):
        CHUNK_GAP = 0.05
        HOLD_AFTER_LAST = 0.35
        MAX_CHUNK_DURATION = 1.4

        timings = []

        for i, chunk in enumerate(chunks):
            start = float(chunk[0]["start"])
            last_word_end = float(chunk[-1]["end"])

            if i < len(chunks) - 1:
                next_start = float(chunks[i + 1][0]["start"])
                end = min(
                    next_start - CHUNK_GAP,
                    last_word_end + HOLD_AFTER_LAST
                )
            else:
                end = last_word_end + HOLD_AFTER_LAST

            end = min(end, start + MAX_CHUNK_DURATION)
            duration = end - start

            if duration <= 0.05:
                continue

            timings.append((chunk, start, duration))

        return timings

    def start_process(self):
        video_path = self.config['video_path']
        output_path = self.config['output_path']
        font_path = self.config['font_path']
        font_size = self.config['font_size']

        # 1. INITIALIZATION (5%)
        self.update_progress(percent=5, msg="Loading Video File...")
        try:
            video = VideoFileClip(video_path)

            # 2. TRANSCRIPTION (10% -> 40%)
            # Since Whisper doesn't give fractional progress, we set markers
            self.update_progress(percent=10, msg="Transcribing Audio (Whisper)...")
            words = self.transcriber.run(video_path)

            if not words:
                raise Exception("Transcription failed or returned no words.")

            self.update_progress(percent=40, msg="Formatting Text...")

            if self.config.get('all_caps'):
                for w in words:
                    w['word'] = w['word'].upper()

            word_chunks = self.group_words(words, self.config['words_per_chunk'])

            # 3. FONT SETUP
            self.update_progress(percent=45, msg="Configuring Fonts...")
            try:
                # Load user-selected font file
                font = ImageFont.truetype(font_path, font_size)
                pop_scale = self.config['style_config'].get("scale_factor", 1.2)
                font_pop = ImageFont.truetype(font_path, int(font_size * pop_scale))
            except Exception as e:
                self.update_status(f"Font Error: {e}. Falling back to default.")
                font = ImageFont.load_default()
                font_pop = ImageFont.load_default()

            # 4. CLIP CREATION (45% -> 50%)
            subtitle_clips = []
            text_h = int(font_size * 5)  # Buffer height for animations
            style_config = self.config['style_config']
            multi_line = self.config['multi_line']
            position_y = self.config['position']

            # Decide timing strategy
            if self.config.get("use_api"):
                chunk_timings = self.compute_chunk_timing_api(word_chunks)
            else:
                # OLD local logic
                chunk_timings = []
                for chunk in word_chunks:
                    start = float(chunk[0]["start"])
                    end = float(chunk[-1]["end"])
                    duration = end - start
                    if duration <= 0.01:
                        continue
                    chunk_timings.append((chunk, start, duration))
                    
            for chunk, start, duration in chunk_timings:

                # Frame generation functions
                def make_frame_rgb(t, _chunk=chunk, _start=start):
                    return np.array(self.create_text_image(
                        (video.w, text_h), _chunk, _start + float(t),
                        font, font_pop, style_config, multi_line
                    ).convert("RGB"))

                def make_mask(t, _chunk=chunk, _start=start):
                    img = self.create_text_image(
                        (video.w, text_h), _chunk, _start + float(t),
                        font, font_pop, style_config, multi_line
                    )
                    return np.array(img.split()[-1]).astype(np.float32) / 255.0

                txt = VideoClip(make_frame_rgb, duration=duration)
                mask = VideoClip(make_mask, duration=duration, ismask=True)
                txt = txt.set_mask(mask)

                # Vertical Position Logic
                margin = 40
                if position_y == "top":
                    pos = ("center", margin)
                elif position_y == "bottom":
                    pos = ("center", video.h - text_h - margin)
                else:
                    pos = ("center", (video.h - text_h) / 2)

                subtitle_clips.append(txt.set_position(pos).set_start(start))

            # 5. RENDERING (50% -> 100%)
            self.update_progress(percent=50, msg="Starting Render Engine...")

            final_video = CompositeVideoClip([video] + subtitle_clips)

            temp_audio_path = os.path.join(os.environ["LOCALAPPDATA"], "MSAutoCaptions", "temp_audio.m4a")

            # Connect the GuiLogger to MoviePy
            custom_logger = GuiLogger(self.update_progress)

            final_video.write_videofile(
                output_path,
                temp_audiofile=temp_audio_path,  # <--- THIS IS THE KEY FIX
                remove_temp=True,
                codec="libx264",
                audio_codec="aac",
                fps=video.fps,
                threads=4,  # Use multiple CPU threads
                logger=custom_logger,  # This is what makes the bar move!
                preset="ultrafast"  # Speed up processing (lower file size efficiency)
            )

            # Cleanup
            video.close()
            final_video.close()

            self.update_progress(percent=100, msg="Video Saved Successfully!")
            return True

        except Exception as e:
            # Pass the error back to the UI
            self.update_progress(percent=0, msg=f"Error: {str(e)}")
            raise e