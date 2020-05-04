from pydub import AudioSegment
import moviepy.editor as mp

# def readone(f):
#     line = f.readline().replace('\n','')
#     return line
#
# def get_time(line,bpm,lbb,lbt):
#     beat = float(line.split('/')[0]) - lbb
#     return (beat * 60000/bpm) + lbt
#
# def get_notes(musiccode):
#     f = open('data/score/' + musiccode + 'ex.txt')
#     notes = []
#     music_offset = 0
#     ns = ['1','3','4','5','6','7','8','10','11','9','21','25']
#     fs = ['2','26','12','13']
#     ss = ['0','20']
#
#     music_offset = int(readone(f))
#     bpm = float(readone(f))
#     lbb = 0     #last bpm beat
#     lbt = 0     #last bpm time
#
#     lines = f.readlines()
#     for line in lines:
#         type = line.split('/')[1]
#         if type == '0':
#             music_offset += get_time(line,bpm,lbb,lbt)
#         if type == '20':
#             lbt = get_time(line, bpm, lbb, lbt)
#             bpm = float(line.split('/')[2].replace('\n',''))
#             lbb = float(line.split('/')[0])
#         if type in ns:
#             notes.append({'type':'n','time':get_time(line,bpm,lbb,lbt)})
#         if type in fs:
#             notes.append({'type':'f','time':get_time(line,bpm,lbb,lbt)})
#
#     return (notes, music_offset)

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


# musiccode = '123'
# musiccode = input('Write 3 digit number: ')
# notes, music_offset = get_notes(musiccode)
# print(notes)
#
# default_offset = 332
# music_vol = 0
# se_vol = -5
# master_vol = 0
#
# normal = AudioSegment.from_file("data/normal.wav")
# flick = AudioSegment.from_file("data/flick.wav")
# music = AudioSegment.from_file("data/music/bgm" + musiccode + ".mp3")
# offset = AudioSegment.silent(duration= default_offset + music_offset)
#
# music = music + music_vol
# normal = normal + se_vol
# flick = flick + se_vol
#
# sound = AudioSegment.silent(duration=0) + music
# for note in notes:
#     if note['type'] == 'n':
#         se_type = normal
#     if note['type'] == 'f':
#         se_type = flick
#     pos = int(note['time'])
#
#     sound = sound.overlay(se_type, position=pos)
#
# sound = offset + sound
# sound = sound + master_vol
#
# sound.export("out.mp3", format="mp3")
#
# video = mp.VideoFileClip('Recorded.avi')
#
# video.write_videofile('output.mp4', audio='out.mp3')



