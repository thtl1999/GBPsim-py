
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import json
import math

class VideoFrameMaker:
    def __init__(self, constants, note_frames, thread_id):
        self.c = constants
        self.note_frames = note_frames
        self.thread_id = thread_id

        self.images = dict()
        image_pack_list = [
            'lane ' + self.c.LANE_SKIN_ID,
            'note ' + self.c.NOTE_SKIN_ID,
            'common'
        ]
        for image_pack in image_pack_list:
            self.add_images(image_pack)

        self.bg = self.make_static_bg()
        self.empty_image = Image.new("RGBA", (1, 1))

    def make_static_bg(self):
        bg = Image.open('assets/bgs.png').convert('RGB').resize((self.c.WIDTH, self.c.HEIGHT))
        game_play_line = self.img_resize(self.images['game_play_line.png'], self.c.LANE_SCALE)
        self.paste_center(bg, self.c.WIDTH / 2, self.c.BOTTOM_Y, game_play_line)
        bg_line_rhythm = self.img_resize(self.images['bg_line_rhythm.png'], self.c.LANE_SCALE)
        self.paste_center(bg, self.c.WIDTH / 2, self.c.BOTTOM_Y - bg_line_rhythm.height / 2, bg_line_rhythm)
        jacket = self.img_resize(Image.open(self.c.SONG_JACKET), self.c.JACKET_SCALE)
        self.paste_center(bg, self.c.JACKET_POSITION[0], self.c.JACKET_POSITION[1], jacket)
        font = ImageFont.truetype('NotoSansJP-Bold.otf', self.c.FONT_SIZE)
        draw = ImageDraw.Draw(bg)
        draw.text(tuple(self.c.SONG_NAME_POSITION), self.c.SONG_NAME, align="left", font=font)
        return bg

    def make_video_bg(self, frame_seq):
        return self.bg.copy()

    def work(self):

        # cv2 bug: cannot create video object in __init__
        fourcc = cv2.VideoWriter_fourcc(*self.c.OPENCV_CODEC)
        video_size = (self.c.WIDTH, self.c.HEIGHT)
        video_name = 'video/frag/' + str(self.thread_id) + '.' + self.c.OPENCV_VIDEO_EXT
        video = cv2.VideoWriter(video_name, fourcc, self.c.FPS, video_size)

        for frame in self.note_frames:
            # make background
            if self.c.BACKGROUND_VIDEO:
                bg = self.make_video_bg(frame['seq'])
            else:
                bg = self.bg.copy()

            # draw notes
            for note in frame['note']:
                # Skip if the position is smaller than skip value
                if note.cur_anim < self.c.SKIP_NOTE:
                    continue

                note_type = note.type
                if note_type == 'Bar':
                    self.draw_bar(bg, note)
                elif note_type == 'Sim':
                    self.draw_sim(bg, note)
                elif note_type == 'Flick':
                    self.draw_flick(bg, note)
                else:
                    self.draw_simple_note(bg, note)

            # draw combo
            for combo in frame['combo']:
                pass
                # self.draw_combo(bg, combo)

            #draw effect
            for effect in frame['effect']:
                pass

            cv2_img = self.pil2cv(bg)
            video.write(cv2_img)

        video.release()

    def pil2cv(self, pil_image):
        numpy_image = np.array(pil_image)
        if pil_image.mode == 'RGB':
            return cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        elif pil_image.mode == 'RGBA':
            return cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGRA)

    def add_images(self, file_name):
        json_dict = json.load(open('assets/' + file_name + '.json'))
        image = Image.open('assets/' + file_name + '.png')

        for obj in json_dict['frames']:
            frame = json_dict['frames'][obj]['frame']
            x1 = frame['x']
            y1 = frame['y']
            x2 = x1 + frame['w']
            y2 = y1 + frame['h']

            self.images[obj] = image.crop((x1, y1, x2, y2)).convert('RGBA')

    def paste_center(self, base, x, y, img):
        w, h = img.size
        base.paste(img, (int(x - w / 2), int(y - h / 2)), img)

    def paste_abs(self, base, x, y, img):
        base.paste(img, (x, y), img)

    def draw_combo(self, bg, combo):
        x, y, anim, combo_value = combo.get_pos()


    def draw_bar(self, bg, note):
        self.draw_gradient(bg, note)

        # draw long note sprite when current animation is below bottom
        if note.cur_anim > self.c.LANE_FRAME_LENGTH:
            self.draw_fake_long(bg, note)

    def draw_gradient(self, bg, note):
        # cannot draw transparent color on RGB image
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        tx, ty, bx, by, ts, bs = note.get_pos()
        scale = self.c.BAR_SCALE * self.c.NOTE_WIDTH * self.c.NOTE_SCALE

        trwh = scale * ts / 2  # top real width half
        brwh = scale * bs / 2  # bottom real width half

        for y in range(ty, by):
            r = 1 - (by - y) / (by - ty)
            x1 = int((1 - r) * (tx - trwh) + r * (bx - brwh))
            x2 = int((1 - r) * (tx + trwh) + r * (bx + brwh))

            color = list()
            r = math.sin(r * math.pi)
            for i in range(4):
                color.append(int((1 - r) * self.c.BAR_EDGE_COLOR[i] + r * self.c.BAR_CENTER_COLOR[i]))
            draw.line([(x1, y), (x2, y)], tuple(color))

        line_width = round(self.c.NOTE_SCALE * 3)
        draw.line([(tx - trwh, ty), (bx - brwh, by)], tuple(self.c.BAR_LINE_COLOR), width=line_width)
        draw.line([(tx + trwh, ty), (bx + brwh, by)], tuple(self.c.BAR_LINE_COLOR), width=line_width)
        self.paste_abs(bg, 0, 0, overlay)

    def draw_fake_long(self, bg, note):
        tx, ty, bx, by, ts, bs = note.get_pos()
        long_note = note.copy_note()
        long_note.type = 'Long'
        long_note.cur_anim = self.c.LANE_FRAME_LENGTH
        long_note_sprite = self.get_note_sprite(long_note)
        self.paste_center(bg, bx, by, long_note_sprite)

    def draw_sim(self, bg, note):
        note_sprite = self.get_sim_sprite(note)
        x1, x2, y, s = note.get_pos()
        self.paste_center(bg, (x1+x2)/2, y, note_sprite)

    def draw_simple_note(self, bg, note):
        note_sprite = self.get_note_sprite(note)
        x, y, s = note.get_pos()
        self.paste_center(bg, x, y, note_sprite)

    def draw_flick(self, bg, note):
        note_sprite = self.get_note_sprite(note)
        x, y, s = note.get_pos()
        self.paste_center(bg, x, y, note_sprite)
        self.draw_flick_top(bg, note)

    def draw_flick_top(self, bg, note):
        x, y, s = note.get_pos()
        position = note.get_cur_anim() % self.c.FLICK_FRAMES
        note_width = s * self.c.NOTE_WIDTH * self.c.NOTE_SCALE
        flick_y = note_width * 0.1 + position * note_width * 0.3 / self.c.FLICK_FRAMES
        flick_top = self.img_resize(self.images['note_flick_top.png'], s * self.c.NOTE_SCALE)
        self.paste_center(bg, x, y - flick_y, flick_top)

    def draw_bpm(self, bg, bpm):
        pass

    def get_note_sprite(self, note):
        sprite_name = note.get_sprite_name()
        img = self.images[sprite_name]
        x, y, s = note.get_pos()
        return self.img_resize(img, s * self.c.NOTE_SCALE)

    def img_resize(self, img, f):
        w, h = img.size
        if int(w * f) == 0 or int(h * f) == 0:
            return self.empty_image.copy()
        # .resize() method returns new resized image
        return img.resize((int(w * f), int(h * f)))

    def get_sim_sprite(self, note):
        img = self.images['simultaneous_line.png']
        x1, x2, y, s = note.get_pos()
        sim_width = abs(x2-x1)
        sim_height = round(img.height * self.c.NOTE_SCALE * s)

        if sim_width == 0 or sim_height == 0:
            return self.empty_image.copy()
        else:
            # .resize() method returns new resized image
            return img.resize((sim_width, sim_height))




