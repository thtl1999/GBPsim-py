import json

class FrameMaker:
    def __init__(self, constants):
        self.c = constants
        self.npos = NotePositions(self.c)

    def make_frames(self):
        frames = self.calculate_frames()
        frames = self.sort_frames(frames)
        return frames

    def get_primitive_frame(self):
        primitive_frame = {
            'note': list(),
            'combo': list(),
            'effect': list(),

            'seq': None,
            'bpm': None
        }
        return primitive_frame

    def calculate_frames(self):
        frames = list(self.get_primitive_frame() for _ in range(self.c.SONG_FRAME_LENGTH))
        note_pointer = 0
        current_combo = 0

        notes = json.load(open('score/' + self.c.SONG_ID + '.' + self.c.DIFFICULTY + '.json'))

        for current_frame_index in range(self.c.SONG_FRAME_LENGTH):
            cur_frame = frames[current_frame_index]

            cur_frame['seq'] = current_frame_index
            cur_frame['bpm'] = self.get_bpm(current_frame_index)

            # check last frame
            if not current_frame_index == 0:
                last_frame = frames[current_frame_index - 1]
                self.add_moved_obj(cur_frame, last_frame)
                increased_combo = self.increased_combo(last_frame)
                if increased_combo > 0:
                    current_combo += increased_combo
                    self.add_combo_effect(cur_frame, current_combo)


            # if no more note left, just check last frame
            while note_pointer < len(notes):
                # check if new note should appear
                if self.get_note_start_frame(notes[note_pointer]) == current_frame_index:
                    self.add_note(cur_frame, notes[note_pointer])
                    note_pointer += 1
                else:
                    break

        return frames

    def add_moved_obj(self, cur_frame, last_frame):
        for note_type in ['note', 'combo', 'effect']:
            for note in last_frame[note_type]:
                max_anim = None
                if note.is_note():
                    max_anim = self.c.LANE_FRAME_LENGTH
                if note.is_combo():
                    # max_anim = self.c.COMBO_FRAMES
                    max_anim = 999999999

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

    def add_note(self, frame, note):
        top_frame_difference = 0
        lane_ext = 0

        if note['type'] == 'Bar':
            top_frame_difference = self.time_to_frame(note['time'][1]) - self.time_to_frame(note['time'][0])
            lane = note['lane'][0]
            lane_ext = note['lane'][1]
        elif note['type'] == 'Sim':
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
        current_time = seq / self.c.FPS
        bpm = None
        for section in self.c.BPMS:
            if section['start'] < current_time < section['end']:
                bpm = section['bpm']

        # if not found bpm (song end)
        if bpm is None:
            bpm = self.c.BPMS[-1]['bpm']

        return bpm

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
        if self.is_note():
            if self.type == 'Bar':
                distance = 0
                cur_anim_backup = self.cur_anim
                cur_anim_ext_backup = self.cur_anim_ext

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
                bx = self.npos.x[self.cur_anim][self.lane] + distance

                self.cur_anim = cur_anim_backup
                self.cur_anim_ext = cur_anim_ext_backup
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

        elif self.is_combo():
            x = self.c.COMBO_POSITION[0]
            y = self.c.COMBO_POSITION[1]
            anim = self.get_cur_anim()
            combo_value = self.combo
            return x, y, anim, combo_value

    def get_effect(self):
        pass