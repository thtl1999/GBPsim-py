from pydub import AudioSegment


class SoundMaker:
    def __init__(self, constants, notes, thread_id):
        sound_id = constants['NOTE_SOUND_ID']
        self.sounds = {
            'normal': AudioSegment.from_file('assets/' + 'note_normal_' + sound_id + '.wav'),
            'flick': AudioSegment.from_file('assets/' + 'note_flick_' + sound_id + '.wav'),
            'skill': AudioSegment.from_file('assets/note_skill.wav')
        }

        self.sound_table = {
            'Single': 'normal',
            'Long': 'normal',
            'SingleOff': 'normal',
            'Skill': 'skill',
            'Flick': 'flick',
            'Tick': 'normal'
        }

        self.notes = notes
        self.sound_name = 'video/frag/' + thread_id + '.wav'
        self.music_length = (constants.SONG_LENGTH + 5) * 1000

    def work(self):
        base = AudioSegment.silent(duration= self.music_length)

        for note in self.notes:
            if note['type'] == 'Bar' or note['type'] == 'Sim':
                continue
            sound_type = self.sound_table[note['type']]
            base = base.overlay(self.sounds[sound_type], position=note['time'] * 1000)

        base.export(self.sound_name, format='wav')



