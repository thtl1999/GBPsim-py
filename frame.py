import multiprocessing


class FrameMaker:
    def __init__(self, settings, metadata, difficulty, music_id):
        self.C = self.define_constant(settings, metadata, difficulty, music_id)
        self.P , self.C['position length'] = self.cal_positions(self.C)
        self.frames = self.cal_frames(self.C, self.P)
        self.frames = self.delete_skip_frame(self.frames)

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

    def add_moved_combo(self, frame, last_frame):
        for note in last_frame:
            if note['type'] == 'Combo':
                if note['frame'] < self.C['combo frame']:
                    new_combo = copy.deepcopy(note)
                    new_combo['frame'] += 1
                    frame.append(new_combo)
                    break

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
            'Long': 6,
            'Combo': 7
        }

        frames = list()
        for _ in range(C['frame length']):
            frames.append(list())
        score_pointer = 0
        current_combo = 0

        notes = json.load(open('score/' + C['song id'] + '.' + C['difficulty'] + '.json'))

        for current_frame in range(C['frame length']):
            frame = frames[current_frame]
            # check last frame
            if not current_frame == 0:
                self.add_moved_notes(frame, frames[current_frame-1])

            if self.combo_increased(frames[current_frame-1]) > 0:
                current_combo += self.combo_increased(frames[current_frame-1])
                self.add_combo_effect(frame, current_combo)
            else:
                self.add_moved_combo(frame, frames[current_frame - 1])

            # check if new note should appear
            while score_pointer < len(notes):
                note_start_frame = self.get_note_start_frame(C, notes[score_pointer])
                if note_start_frame > current_frame:
                    break
                else:
                    self.add_note(frame, notes[score_pointer])
                    score_pointer += 1

        # sort note in frame for drawing order
        sorted_frames = list()
        for frame in frames:
            sorted_frames.append(sorted(frame, key=lambda note: sort_order[note['type']]))

        return sorted_frames

    def copy_settings(self):
        return copy.deepcopy(self.C), copy.deepcopy(self.P)

    def get_frame_info(self):
        return self.frames

    def delete_skip_frame(self, frames):
        skipped_frames = list()
        for frame in frames:
            skipped_frames.append(list())
            new_frame = skipped_frames[-1]
            for note in frame:
                if note['type'] == 'Bar':
                    f = note['frame'][0]
                else:
                    f = note['frame']

                if f > self.C['skip note']:
                    new_frame.append(note)

        return skipped_frames

    def combo_increased(self, last_frame):
        combo = 0
        for note in last_frame:
            if note['type'] in ['Single', 'SingleOff', 'Flick', 'Tick', 'Long', 'Skill']:
                if note['frame'] == self.C['position length']:
                    combo += 1
        return combo

    def add_combo_effect(self, frame, combo):
        note = {
            'type': 'Combo',
            'frame': 0,
            'combo': combo
        }

        frame.append(note)

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
        if self.THREADS == 0:
            self.THREADS = multiprocessing.cpu_count()

        self.LANE_FRAME_LENGTH = None


class Note:
    def __init__(self, constants, note_positions, note_data, cur_anim):
        self.c = constants
        self.npos = note_positions
        self.type = note_data['type']
        self.lane = note_data['lane']
        self.cur_anim = cur_anim

    def next_note(self, frame):
        note_data = {
            'type': self.type,
            'lane': self.lane
        }

        if self.is_note():
            max_anim = self.c.LANE_FRAME_LENGTH
        elif self.is_combo():
            max_anim = self.c.COMBO_FRAMES

        if self.type == 'Bar':
            cur_anim = [self.cur_anim[0] + 1, self.cur_anim[1] + 1]
        else:
            cur_anim = self.cur_anim + 1

        next_note = Note(self.c, self.npos, note_data, cur_anim)
        return next_note


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

    def get_pos(self):
        if not self.is_note():
            print(self.type, 'is not a note')
            exit(1)
