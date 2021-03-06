
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


        self.empty_image = Image.new("RGBA", (1, 1))

    def load_chibi(self):
        chibi_images = list()
        for i in range(len(self.c.CHIBI_POSITION)):
            chibi = self.img_resize(Image.open('chibi/' + str(i) + '.png'), self.c.CHIBI_SCALE)
            chibi_images.append(chibi)
        return chibi_images

    def paste_bg_chibi(self, bg):
        for i, chibi_position in enumerate(self.c.CHIBI_POSITION):
            self.paste_center(bg, chibi_position[0], chibi_position[1], self.chibi_images[i])

    def paste_bg_components(self, bg, bpm):
        self.paste_center(bg, self.c.WIDTH / 2, self.c.BOTTOM_Y, self.game_play_line)
        self.paste_center(bg, self.c.WIDTH / 2, self.c.BOTTOM_Y - self.bg_line_rhythm.height / 2, self.bg_line_rhythm)
        self.paste_center(bg, self.c.JACKET_POSITION[0], self.c.JACKET_POSITION[1], self.jacket)
        draw = ImageDraw.Draw(bg)
        draw.text(tuple(self.c.SONG_NAME_POSITION), self.c.SONG_NAME, align="left", font=self.font)
        draw.text(tuple(self.c.SONG_INFO_POSITION), self.c.SONG_INFO, align="left", font=self.font)
        draw.text(tuple(self.c.BPM_POSITION), 'BPM: ' + str(bpm), align="left", font=self.font)

    def make_static_bg(self, bpm):
        bg = Image.open('assets/bgs.png').convert('RGB').resize((self.c.WIDTH, self.c.HEIGHT))
        self.paste_bg_chibi(bg)
        self.paste_bg_components(bg, bpm)
        return bg

    def make_video_bg(self, frame_seq, bpm):
        video = cv2.VideoCapture('mv/' + self.c.SONG_ID + '.mp4')
        video_fps = video.get(cv2.CAP_PROP_FPS)
        video_frame_seq = int((frame_seq/self.c.FPS - self.c.BACKGROUND_VIDEO_DELAY) * video_fps)

        if video_frame_seq >= video.get(cv2.CAP_PROP_FRAME_COUNT):
            video_frame_seq = video.get(cv2.CAP_PROP_FRAME_COUNT) - 1

        if video_frame_seq < 0:
            video_frame_seq = 0

        video.set(cv2.CAP_PROP_POS_FRAMES, video_frame_seq)
        ret, cv_image = video.read()

        bg = self.cv2pil(cv_image)
        bg = bg.resize((self.c.WIDTH, self.c.HEIGHT))
        self.paste_bg_components(bg, bpm)

        return bg

    def work(self):

        # cv2 bug: cannot create video object in __init__
        fourcc = cv2.VideoWriter_fourcc(*self.c.OPENCV_CODEC)
        video_size = (self.c.WIDTH, self.c.HEIGHT)
        video_name = 'video/frag/' + str(self.thread_id) + '.' + self.c.OPENCV_VIDEO_EXT
        video = cv2.VideoWriter(video_name, fourcc, self.c.FPS, video_size)

        self.chibi_images = self.load_chibi()
        self.game_play_line = self.img_resize(self.images['game_play_line.png'], self.c.LANE_SCALE)
        self.bg_line_rhythm = self.img_resize(self.images['bg_line_rhythm.png'], self.c.LANE_SCALE)
        self.jacket = self.img_resize(Image.open(self.c.SONG_JACKET), self.c.JACKET_SCALE)
        self.font = ImageFont.truetype(self.c.FONT_NAME, self.c.FONT_SIZE)
        self.bg = self.make_static_bg(0)

        for frame in self.note_frames:
            # make background
            if self.c.BACKGROUND_VIDEO:
                bg = self.make_video_bg(frame['seq'], frame['bpm'])
            else:
                # bg = self.bg.copy()
                bg = self.make_static_bg(frame['bpm'])


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
                self.draw_combo(bg, combo)

            #draw effect
            for effect in frame['effect']:
                pass

            cv2_img = self.pil2cv(bg)
            video.write(cv2_img)

        video.release()
        del video

    def pil2cv(self, pil_image):
        numpy_image = np.array(pil_image)
        if pil_image.mode == 'RGB':
            return cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        elif pil_image.mode == 'RGBA':
            return cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGRA)

    def cv2pil(self, cv_image):
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        return pil_image

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
        if img.mode == 'RGBA':
            base.paste(img, (int(x - w / 2), int(y - h / 2)), img)
        else:
            base.paste(img, (int(x - w / 2), int(y - h / 2)))

    def paste_abs(self, base, x, y, img):
        if img.mode == 'RGBA':
            base.paste(img, (int(x), int(y)), img)
        else:
            base.paste(img, (int(x), int(y)))

    def draw_combo(self, bg, combo):
        x, y, anim, combo_value = combo.get_pos()
        combo_image = self.create_combo_image(combo_value)

        # Scale overlay
        combo_frames = self.c.COMBO_FRAMES
        scale_a = self.c.COMBO_SCALE_A
        scale_b = self.c.COMBO_SCALE_B
        half_frame = combo_frames/2

        if anim < half_frame:
            scale = scale_a + (scale_b - scale_a)/half_frame * anim
        elif anim < combo_frames:
            scale = scale_b - (scale_b - 1)/half_frame * (anim - half_frame)
        else:
            scale = 1

        combo_image = self.img_resize(combo_image, scale)
        self.paste_center(bg, x, y, combo_image)

    def create_combo_image(self, combo_value):
        numbers = [int(digit) for digit in str(combo_value)] # [3,4,2]
        number_sprites = list()
        for i in range(10):
            number_sprites.append(self.images[str(i)+'.png'])
        number_sprite_width, number_sprite_height = number_sprites[0].size
        combo_sprite = self.images['combo.png']
        combo_sprite_width, combo_sprite_height = combo_sprite.size
        width = max(number_sprite_width*len(numbers), combo_sprite_width)
        height = number_sprite_height + combo_sprite_height

        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        numbers_width = number_sprite_width * len(numbers)
        numbers_start_x = (width - numbers_width)/2
        for i, number in enumerate(numbers):
            self.paste_abs(overlay, numbers_start_x + i*number_sprite_width, 0, number_sprites[number])
        self.paste_center(overlay, width/2, number_sprite_height + combo_sprite_height/2, combo_sprite)

        return overlay

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
