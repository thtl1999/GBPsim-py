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
        song_difficulty_text = str(self.DIFFICULTY).upper()
        song_difficulty_rate = str(metadata['difficulty'][self.DIFFICULTY_ID]['playLevel'])
        self.SONG_INFO = song_difficulty_text + ' ' + song_difficulty_rate

        self.BPMS = metadata['bpm'][self.DIFFICULTY_ID]
        self.SONG_LENGTH = metadata['length']
        self.SONG_NAME = metadata['musicTitle'][0]
        self.MUSIC_FILE_NAME = metadata['bgmId']


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
        self.NOTE_SOUND_ID = settings['NOTE_SOUND_ID']

        self.SONG_JACKET = 'jacket/' + self.SONG_ID + '.png'
        self.JACKET_SCALE = settings['JACKET_SCALE']
        self.JACKET_POSITION = settings['JACKET_POSITION']

        self.FONT_SIZE = settings['FONT_SIZE']
        self.FONT_NAME = settings['FONT_NAME']
        self.SONG_NAME_POSITION = settings['SONG_NAME_POSITION']
        self.SONG_INFO_POSITION = settings['SONG_INFO_POSITION']
        self.BPM_POSITION = settings['BPM_POSITION']
        self.CHIBI_POSITION = settings['CHIBI_POSITION']
        self.CHIBI_SCALE = settings['CHIBI_SCALE']
        self.BAND_ID = str(metadata['bandId'])

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
        self.BACKGROUND_VIDEO_DELAY = settings['BACKGROUND_VIDEO_DELAY']
        self.SOUND_DELAY = settings['SOUND_DELAY']

        self.LANE_FRAME_LENGTH = None

def generate_constants(settings, song_data, difficulty_id, song_id):
    return Constants(settings, song_data, difficulty_id, song_id)