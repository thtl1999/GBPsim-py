from pydub import AudioSegment


class SoundMaker:
    def __init__(self, settings, music_id, difficulty, metadata, notes, thread_id):
        sound_id = settings['NOTE_SOUND_ID']
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
        self.sound_name = 'video/' + str(thread_id) + 'th ' + str(music_id)
        self.music_length = (metadata['length'] + 5) * 1000
        self.difficulty = difficulty

    def work(self):
        base = AudioSegment.silent(duration= self.music_length)

        for note in self.notes:
            if note['type'] == 'Bar' or note['type'] == 'Sim':
                continue
            sound_type = self.sound_table[note['type']]
            base = base.overlay(self.sounds[sound_type], position=note['time'] * 1000)

        base.export(self.sound_name + self.difficulty + '.wav', format='wav')



