import json

class FrameMaker:
    def __init__(self, constants):
        self.c = constants
        self.npos = NotePositions(self.c)

    def make_frames(self):
        frames = self.calculate_frames()
        frames = self.sort_frames(frames)
        frames = self.delete_skip_notes(frames)

        return frames

    def calculate_frames(self):
        frames = list(list() for _ in range(self.c.LANE_FRAME_LENGTH))

        note_pointer = 0
        current_combo = 0

        notes = json.load(open('score/' + self.c.SONG_ID + '.' + self.c.DIFFICULTY + '.json'))

        for current_frame_index in range(self.c.LANE_FRAME_LENGTH):
            cur_frame = frames[current_frame_index]

            # check last frame
            if not current_frame_index == 0:
                last_frame = frames[current_frame_index - 1]
                self.add_moved_obj(cur_frame, last_frame)
                increased_combo = self.increased_combo(last_frame)
                if increased_combo > 0:
                    current_combo += increased_combo
                    self.add_combo_effect(cur_frame, current_combo)

            # if no more note left, just check last frame
            if note_pointer < len(notes):
                continue

            # check if new note should appear
            while self.get_note_start_frame(notes[note_pointer]) == current_frame_index:
                self.add_note(cur_frame, notes[note_pointer])
                note_pointer += 1

        return frames

    def add_moved_obj(self, cur_frame, last_frame):
        for note_type in ['note', 'combo', 'effect']:
            for note in last_frame[note_type]:
                max_anim = None
                if note.is_note():
                    max_anim = self.c.COMBO_FRAMES
                if note.is_combo():
                    max_anim = self.c.COMBO_FRAMES

                if note.get_cur_anim() < max_anim:
                    next_note = note.get_next_note()
                    cur_frame[note_type].append(next_note)

        return


    def sort_frames(self, frames):
        # sort order for drawing order
        sort_order = {
            'Bar': 1,
            'Sim': 2,
            'Tick': 3,
            'Single': 4,
            'SingleOff': 4,
            'Skill': 4,
            'Flick': 5,
            'Long': 6,
        }

        for frame in frames:
            frame['note'] = sorted(frame['note'], key=lambda note: sort_order[note.type])

        return frames

    def delete_skip_notes(self, frames):
        skipped_frames = list()
        for frame in frames:
            skipped_frames.append(list())
            new_frame = skipped_frames[-1]
            for note in frame:
                if note.get_cur_anim() > self.c.SKIP_NOTE:
                    new_frame.append(note)

        return skipped_frames

    def add_note(self, frame, note):
        top_frame_difference = 0
        lane_ext = 0

        if note['type'] == 'Bar':
            top_frame_difference = self.time_to_frame(note['time'][1]) - self.time_to_frame(note['time'][0])

        if note['type'] == 'Sim':
            lane = note['lane'][0]
            lane_ext = note['lane'][1]
        else:
            lane = note['lane']

        new_note = Note(self.c, self.npos, note['type'], lane, lane_ext,
                        cur_anim=0, cur_anim_ext=-top_frame_difference)
        frame['note'].append(new_note)

    def increased_combo(self, frame):
        combo = 0
        for note in frame['note']:
            if note.is_real_note():
                if note.get_cur_anim() == self.c.LANE_FRAME_LENGTH - 1:
                    combo += 1
        return combo

    def add_combo_effect(self, frame, combo):
        combo_note = Note(self.c, self.npos, 'Combo', combo=combo)
        frame['combo'] = [combo_note]

    def time_to_frame(self, note_time):
        return int(note_time * self.c.FPS - self.c.LANE_FRAME_LENGTH)

    def get_note_start_frame(self, note):
        if note['type'] == 'Bar':
            note_time = note['time'][0]
        else:
            note_time = note['time']

        return self.time_to_frame(note_time)

    def get_bpm(self, seq):
        pass

    def add_single_effect(self, frames, start_frame):
        pass

    def add_long_effect(self, frames, start_frame, end_frame):
        pass

    def add_skill_effect(self, frames, start_frame):
        pass

    def add_flick_effect(self, frames, start_frame):
        pass


class NotePositions:
    def __init__(self, c):
        self.c = c
        BX = dict()
        TX = dict()
        for x in range(1, 8):
            BX[x] = c.WIDTH / 2 - 4 * c.LANE_SPACE_BOTTOM + x * c.LANE_SPACE_BOTTOM
            TX[x] = c.WIDTH / 2 - 4 * c.LANE_SPACE_TOP + x * c.LANE_SPACE_TOP

        height = c.BOTTOM_Y - c.TOP_Y
        frame_num = 0
        self.x = list()
        self.y = list()
        self.r = list()

        while c.NOTE_SPEED * frame_num ** 3 < height:
            y = round(c.NOTE_SPEED * frame_num ** 3 + c.TOP_Y)
            r = (y - c.TOP_Y) / height
            x = dict()
            for lane in range(1, 8):
                x[lane] = round(TX[lane] + (BX[lane] - TX[lane]) * r)

            self.x.append(x)
            self.y.append(y)
            self.r.append(r)
            frame_num += 1

        c.LANE_FRAME_LENGTH = frame_num

        # set last position
        self.y.append(c.BOTTOM_Y)
        self.r.append(1)
        last_x = dict()
        for lane in range(1, 8):
            last_x[lane] = round(BX[lane])
        self.x.append(last_x)


class Constants:
    def __init__(self, settings, metadata, difficulty, song_id):
        diff_table = {
            '0': 'easy',
            '1': 'normal',
            '2': 'hard',
            '3': 'expert',
            '4': 'special'
        }

        self.DIFFICULTY = diff_table[difficulty]
        self.DIFFICULTY_ID = difficulty
        self.SONG_ID = song_id

        self.BPMS = metadata['bpm'][self.DIFFICULTY_ID]
        self.SONG_LENGTH = metadata['length']
        self.SONG_NAME = metadata['musicTitle'][0]

        self.WIDTH = settings['WIDTH']
        self.HEIGHT = settings['HEIGHT']
        self.FPS = settings['FPS']
        self.LANE_SCALE = settings['LANE_SCALE']
        self.LANE_SPACE_BOTTOM = self.LANE_SCALE * settings['BOTTOM_DISTANCE']
        self.LANE_SPACE_TOP = self.LANE_SCALE * settings['TOP_DISTANCE']
        self.BOTTOM_Y = round(settings['LANE_BOTTOM_RATIO'] * self.HEIGHT)
        self.TOP_Y = int(self.BOTTOM_Y - settings['BG_LINE_HEIGHT'] * self.LANE_SCALE)
        self.SKIP_NOTE = settings['SKIP_NOTE']
        self.NOTE_SPEED = settings['NOTE_SPEED']
        self.NOTE_SCALE = settings['NOTE_SCALE']
        self.NOTE_WIDTH = settings['NOTE_WIDTH']
        self.BAR_SCALE = settings['BAR_SCALE']
        self.FLICK_FRAMES = settings['FLICK_FRAMES']
        self.NOTE_SKIN_ID = settings['NOTE_SKIN_ID']
        self.LANE_SKIN_ID = settings['LANE_SKIN_ID']

        self.SONG_JACKET = 'jacket/' + self.SONG_ID + '/jacket.png'
        self.JACKET_SCALE = settings['JACKET_SCALE']
        self.JACKET_POSITION = settings['JACKET_POSITION']

        self.FONT_SIZE = settings['FONT_SIZE']
        self.SONG_NAME_POSITION = settings['SONG_NAME_POSITION']

        self.COMBO_SCALE_A = settings['COMBO_SCALE_A']
        self.COMBO_SCALE_B = settings['COMBO_SCALE_B']
        self.COMBO_FRAMES = settings['COMBO_FRAMES']
        self.COMBO_POSITION = settings['COMBO_POSITION']

        self.MUSIC_EXTRA_TIME = settings['MUSIC_EXTRA_TIME']
        self.SONG_FRAME_LENGTH = int((self.SONG_LENGTH + self.MUSIC_EXTRA_TIME) * self.FPS)
        self.BAR_EDGE_COLOR = settings['BAR_EDGE_COLOR']
        self.BAR_CENTER_COLOR = settings['BAR_CENTER_COLOR']
        self.BAR_LINE_COLOR = settings['BAR_LINE_COLOR']

        self.OPENCV_CODEC = settings['OPENCV_CODEC']
        self.OPENCV_VIDEO_EXT = settings['OPENCV_VIDEO_EXT']
        self.FFMPEG_CODEC = settings['FFMPEG_CODEC']
        self.OUTPUT_BITRATE = settings['OUTPUT_BITRATE']
        self.OUTPUT_EXT = settings['OUTPUT_EXT']
        self.VIDEO_NAME = str(self.SONG_ID) + self.DIFFICULTY + '.' + self.OUTPUT_EXT

        self.THREADS = settings['THREADS']

        self.BACKGROUND_VIDEO = settings['BACKGROUND_VIDEO']

        self.LANE_FRAME_LENGTH = None


class Note:
    TYPE_DICT = {
        'Single': 'note_normal_',
        'Long': 'note_long_',
        'SingleOff': 'note_normal_gray_',
        'Skill': 'note_skill_',
        'Flick': 'note_flick_'
    }

    def __init__(self, constants, note_positions, note_type, note_lane=0, note_lane_ext=0,
                 cur_anim=0, cur_anim_ext=0, combo=0, seed=0):
        self.c = constants
        self.npos = note_positions
        self.type = note_type
        self.lane = note_lane
        self.lane_ext = note_lane_ext
        self.cur_anim = cur_anim
        self.cur_anim_ext = cur_anim_ext
        self.combo = combo
        self.seed = seed

    def is_real_note(self):
        if self.type in ['Single', 'SingleOff', 'Flick', 'Tick', 'Long', 'Skill']:
            return True
        else:
            return False

    def is_fake_note(self):
        if self.type in ['Sim', 'Bar']:
            return True
        else:
            return False

    def is_note(self):
        if self.is_real_note() or self.is_fake_note():
            return True
        else:
            return False

    def is_combo(self):
        if self.type == 'Combo':
            return True
        else:
            return False

    def is_effect(self):
        if self.type in ['Combo']:
            return True
        else:
            return False

    def get_cur_anim(self):
        if self.type == 'Bar':
            return self.cur_anim_ext
        else:
            return self.cur_anim

    def get_next_note(self):
        next_note = Note(self.c, self.npos, self.type, self.lane, self.lane_ext,
                         self.cur_anim + 1, self.cur_anim_ext + 1, self.combo, self.seed)
        return next_note

    def copy_note(self):
        note = Note(self.c, self.npos, self.type, self.lane, self.lane_ext,
                         self.cur_anim, self.cur_anim_ext, self.combo, self.seed)
        return note

    def get_sprite_name(self):
        if not self.is_real_note():
            print(self.type, 'is not a real note')
            exit(2)

        if self.type == 'Tick':
            return 'note_slide_among.png'
        else:
            return self.TYPE_DICT[self.type] + str(self.lane - 1) + '.png'

    def get_pos(self):
        if not self.is_note():
            print(self.type, 'is not a note')
            exit(1)

        if self.type == 'Bar':
            distance = 0

            # correction for note position
            if self.cur_anim > self.c.LANE_FRAME_LENGTH:
                total_bottom_distance = (self.lane_ext - self.lane)*self.c.LANE_SPACE_BOTTOM
                distance_per_frame = total_bottom_distance / (self.cur_anim - self.cur_anim_ext)
                bottom_progress = self.cur_anim - self.c.LANE_FRAME_LENGTH
                distance = bottom_progress * distance_per_frame
                self.cur_anim = self.c.LANE_FRAME_LENGTH
            if self.cur_anim_ext < self.c.SKIP_NOTE:
                self.cur_anim_ext = self.c.SKIP_NOTE

            tx = self.npos.x[self.cur_anim_ext][self.lane_ext]
            ty = self.npos.y[self.cur_anim_ext]
            by = self.npos.y[self.cur_anim]
            ts = self.npos.r[self.cur_anim_ext]
            bs = self.npos.r[self.cur_anim]
            bx = self.npos.x[self.cur_anim][self.lane_ext] + distance
            return tx, ty, bx, by, ts, bs

        elif self.type == 'Sim':
            x1 = self.npos.x[self.cur_anim][self.lane]
            x2 = self.npos.x[self.cur_anim][self.lane_ext]
            y = self.npos.y[self.cur_anim]
            s = self.npos.r[self.cur_anim]
            return x1, x2, y, s
        else:
            x = self.npos.x[self.cur_anim][self.lane]
            y = self.npos.y[self.cur_anim]
            s = self.npos.r[self.cur_anim]
            return x, y, s


    def get_combo(self):
        pass

    def get_effect(self):
        pass