
from PIL import Image, ImageDraw
import numpy as np
import cv2
import json
import math
import copy
import multiprocessing


class VideoPrefetch:
    def __init__(self, settings, metadata, difficulty, music_id):
        self.C = self.define_constant(settings, metadata, difficulty, music_id)
        self.P , self.C['position length'] = self.cal_positions(self.C)
        self.frames = self.cal_frames(self.C, self.P)

    def define_constant(self, settings, metadata, difficulty, music_id):
        C = {
            'bpms': metadata['bpm'][difficulty],
            'song id': music_id,
            'song length': metadata['length'],
            'difficulty': settings['DIFFICULTY'][difficulty],
            'difficulty id': difficulty,
            'width': settings['WIDTH'],
            'height': settings['HEIGHT'],
            'fps': settings['FPS'],
            'lane scale': settings['LANE_SCALE'],
            'lane space bottom': settings['LANE_SCALE'] * settings['BOTTOM_DISTANCE'],
            'lane space top': settings['LANE_SCALE'] * settings['TOP_DISTANCE'],
            'bottom': int(settings['BOTTOM_SCALE'] * settings['HEIGHT']),
            'top': int(int(settings['BOTTOM_SCALE'] * settings['HEIGHT']) - settings['BG_LINE_HEIGHT'] * settings[
                'LANE_SCALE']),
            'skip note': settings['SKIP_NOTE'],
            'note speed': settings['NOTE_SPEED'],
            'note size': settings['NOTE_SIZE'],
            'note width': settings['NOTE_WIDTH'],
            'lnl scale': settings['LNL_SCALE'],
            'flick fps': settings['FLICK_FPS'],
            'note skin id': settings['NOTE_SKIN_ID'],
            'lane skin id': settings['LANE_SKIN_ID'],

            'frame length': int((metadata['length'] + 5) * settings['FPS']),

            'edge color': settings['EDGE_COLOR'],
            'center color': settings['CENTER_COLOR'],
            'line color': settings['LINE_COLOR'],

            'codec': settings['CODEC'],
            'video name': str(music_id) + settings['DIFFICULTY'][difficulty] + '.' + settings['VIDEO_EXTENSION'],
            'number of thread': multiprocessing.cpu_count() if settings['THREAD'] == 0 else settings['THREAD'],

            'position length': None

        }

        return C

    def cal_positions(self, C):
        BX = dict()
        TX = dict()
        for x in range(1, 8):
            BX[x] = C['width'] / 2 - 4 * C['lane space bottom'] + x * C['lane space bottom']
            TX[x] = C['width'] / 2 - 4 * C['lane space top'] + x * C['lane space top']

        height = C['bottom'] - C['top']
        frame = 0
        note_pos = list()

        while self.C['note speed'] * frame**3 < height:
            position = dict()
            position['y'] = round(C['note speed'] * frame**3 + self.C['top'])
            position['r'] = (position['y'] - C['top']) / height
            position['x'] = dict()
            for x in range(1,8):
                position['x'][x] = round(TX[x] + (BX[x] - TX[x])*position['r'])
            note_pos.append(position)

            frame = frame + 1

        last = dict()
        last['y'] = self.C['bottom']
        last['r'] = 1
        last['x'] = dict()
        for x in range(1,8):
            last['x'][x] = round(BX[x])

        note_pos.append(last)

        return note_pos, len(note_pos) - 1

    def add_note(self, frame, note):
        note_info = {
            'type': note['type'],
            'lane': note['lane'],
        }

        if note['type'] == 'Bar':
            top_frame_difference = self.precise_cal(note['time'][1]) - self.precise_cal(note['time'][0])
            note_info['frame'] = [0, -top_frame_difference]
        else:
            note_info['frame'] = 0

        frame.append(note_info)

    def precise_cal(self, note_time):
        return int(note_time * self.C['fps'] - self.C['position length'])



    def add_moved_notes(self, frame, last_frame):
        copied_frame = copy.deepcopy(last_frame)
        for note in copied_frame:
            if note['type'] == 'Bar':
                note['frame'][0] += 1
                note['frame'][1] += 1

                if note['frame'][1] < self.C['position length']:
                    frame.append(note)
            else:
                note['frame'] += 1

                if note['frame'] < self.C['position length']:
                    frame.append(note)

    def get_note_start_frame(self, C, note):
        if note['type'] == 'Bar':
            note_time = note['time'][0]
        else:
            note_time = note['time']

        return int(note_time * C['fps'] - C['position length'])

    def cal_frames(self, C, P):
        # sort order for drawing order
        sort_order = {
            'Bar': 1,
            'Sim': 2,
            'Tick': 3,
            'Single': 4,
            'SingleOff': 4,
            'Skill': 4,
            'Flick': 5,
            'Long':6
        }

        frames = list()
        score_pointer = 0

        notes = json.load(open('score/' + C['song id'] + '.' + C['difficulty'] + '.json'))

        for current_frame in range(C['frame length']):
            frame = list()

            # check last frame
            if frames:
                self.add_moved_notes(frame, frames[-1])

            # check if new note should appear
            while score_pointer < len(notes):
                note_start_frame = self.get_note_start_frame(C, notes[score_pointer])
                if note_start_frame > current_frame:
                    break
                else:
                    self.add_note(frame, notes[score_pointer])
                    score_pointer += 1

            # sort note in frame for drawing order
            frame = sorted(frame, key=lambda note: sort_order[note['type']])
            frames.append(frame)

        return frames

    def copy_settings(self):
        return copy.deepcopy(self.C), copy.deepcopy(self.P)

    def get_frame_info(self):
        return self.frames


class VideoFrameMaker:
    def __init__(self, settings, note_frames, thread_id):
        self.C, self.P = settings
        self.note_frames = note_frames
        self.thread_id = thread_id

        self.images = dict()
        image_pack_list = [
            'lane ' + self.C['lane skin id'],
            'note ' + self.C['note skin id']
        ]
        for image_pack in image_pack_list:
            self.add_images(image_pack)

        self.bg = Image.open('assets/bgs.png').convert('RGB').resize((self.C['width'], self.C['height']))
        game_play_line = self.img_resize(self.images['game_play_line.png'], self.C['lane scale'])
        self.paste_center(self.bg, self.C['width'] / 2, self.C['bottom'], game_play_line)
        bg_line_rhythm = self.img_resize(self.images['bg_line_rhythm.png'], self.C['lane scale'])
        self.paste_center(self.bg, self.C['width'] / 2, self.C['bottom'] - bg_line_rhythm.height / 2, bg_line_rhythm)
        self.empty_image = Image.new("RGBA", (1, 1))

    def work(self):

        # cv2 bug: cannot create video object in __init__
        fourcc = cv2.VideoWriter_fourcc(*self.C['codec'])
        video_size = (self.C['width'], self.C['height'])
        video_name = 'video/' + str(self.thread_id) + 'th ' + self.C['video name']
        video = cv2.VideoWriter(video_name, fourcc, self.C['fps'], video_size)

        for frame in self.note_frames:
            bg = self.bg.copy()
            for note in frame:
                if note['type'] == 'Bar':
                    self.draw_bar(bg, note)
                elif note['type'] == 'Sim':
                    self.draw_sim(bg, note)
                else:
                    self.draw_note(bg, note)

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
        return

    def paste_abs(self, base, x, y, img):
        base.paste(img, (x, y), img)
        return

    def draw_bar(self, bg, note):

        if note['frame'][0] > self.C['position length']:
            bottom_distance = self.C['lane space bottom']
            total_distance = (note['lane'][1] - note['lane'][0]) * bottom_distance
            distance_per_frame = total_distance / (note['frame'][0] - note['frame'][1])
            overed_frame = note['frame'][0] - self.C['position length']
            distance = overed_frame * distance_per_frame
        else:
            distance = 0

        # frame correction
        if note['frame'][0] > self.C['position length']:
            note['frame'][0] = self.C['position length']
        if note['frame'][1] < 0:
            note['frame'][1] = 0

        # cannot draw transparent color on RGB image
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        self.draw_gradient(draw, note, distance, self.C['edge color'], self.C['center color'], self.C['line color'])
        self.paste_abs(bg, 0, 0, overlay)

    def draw_gradient(self, draw, note, prog_width, c1, c2, c3):
        c3 = tuple(c3)
        tx, ty, bx, by, ts, bs = self.get_note_pos(note)
        bx = bx + prog_width

        lnl_scale = self.C['lnl scale']
        NOTE_WIDTH = self.C['note width']
        NOTE_SIZE = self.C['note size']
        line_width = round(NOTE_SIZE * 3)

        trwh = lnl_scale * NOTE_WIDTH * NOTE_SIZE * ts / 2  # top real width half
        brwh = lnl_scale * NOTE_WIDTH * NOTE_SIZE * bs / 2  # bottom real width half

        for y in range(ty, by):
            r = 1 - (by - y) / (by - ty)
            x1 = int((1 - r) * (tx - trwh) + r * (bx - brwh))
            x2 = int((1 - r) * (tx + trwh) + r * (bx + brwh))

            color = list()
            r = math.sin(r * math.pi)
            for i in range(4):
                color.append(int((1 - r) * c1[i] + r * c2[i]))
            color = tuple(color)

            draw.line([(x1, y), (x2, y)], color)

        draw.line([(tx - trwh, ty), (bx - brwh, by)], c3, width=line_width)
        draw.line([(tx + trwh, ty), (bx + brwh, by)], c3, width=line_width)
        return

    def draw_sim(self, bg, note):
        note_sprite = self.get_sim_sprite(note)
        x1, x2, y, s = self.get_note_pos(note)
        self.paste_center(bg, (x1+x2)/2, y, note_sprite)

    def draw_note(self, bg, note):
        note_sprite = self.get_note_sprite(note)
        x, y, s = self.get_note_pos(note)
        self.paste_center(bg, x, y, note_sprite)
        if note['type'] == 'Flick':
            self.draw_flick_top(bg, note)

    def draw_flick_top(self, bg, note):
        x, y, s = self.get_note_pos(note)
        position = note['frame'] % self.C['flick fps']
        note_width = s * self.C['note width'] * self.C['note size']
        flicky = note_width * 0.1 + position * note_width * 0.3 / self.C['flick fps']
        flick_top = self.img_resize(self.images['note_flick_top.png'], s * self.C['note size'])
        self.paste_center(bg, x, y - flicky, flick_top)

    def draw_bpm(self, bg, bpms):
        pass

    def get_note_sprite(self, note):
        type_dict = {
            'Single': 'note_normal_',
            'Long': 'note_long_',
            'SingleOff': 'note_normal_gray_',
            'Skill': 'note_skill_',
            'Flick': 'note_flick_'
        }

        type = note['type']
        frame = note['frame']
        lane = note['lane']

        if type == 'Tick':
            img = self.images['note_slide_among.png']
        else:
            img = self.images[type_dict[type] + str(lane - 1) + '.png']

        return self.img_resize(img, self.P[frame]['r']*self.C['note size'])

    def img_resize(self, img, f):
        w, h = img.size
        if int(w * f) == 0 or int(h * f) == 0:
            return self.empty_image.copy()
        # .resize() method returns new resized image
        return img.resize((int(w * f), int(h * f)))

    def get_sim_sprite(self, note):
        img = self.images['simultaneous_line.png']
        x1, x2, y, s = self.get_note_pos(note)
        sim_width = abs(x2-x1)
        sim_height = round(img.height * self.C['note size'] * s)

        if sim_width == 0 or sim_height == 0:
            return self.empty_image.copy()
        else:
            # .resize() method returns new resized image
            return img.resize((sim_width, sim_height))

    def get_note_pos(self, note):
        if note['type'] == 'Bar':
            tx = self.P[note['frame'][1]]['x'][note['lane'][1]]
            ty = self.P[note['frame'][1]]['y']
            by = self.P[note['frame'][0]]['y']
            ts = self.P[note['frame'][1]]['r']
            bs = self.P[note['frame'][0]]['r']
            bx = self.P[note['frame'][0]]['x'][note['lane'][0]]
            return tx, ty, bx, by, ts, bs
        elif note['type'] == 'Sim':
            x1 = self.P[note['frame']]['x'][note['lane'][0]]
            x2 = self.P[note['frame']]['x'][note['lane'][1]]
            y = self.P[note['frame']]['y']
            s = self.P[note['frame']]['r']
            return x1, x2, y, s
        else:
            x = self.P[note['frame']]['x'][note['lane']]
            y = self.P[note['frame']]['y']
            s = self.P[note['frame']]['r']
            return x, y, s
