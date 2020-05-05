from pydub import AudioSegment
import moviepy.editor as mp

class Merge_class:
    def __init__(self, settings, video_name, sound_name, bgm_name):
        self.settings = settings
        self.video_name = video_name
        self.sound_name = sound_name
        self.bgm_name = bgm_name

        self.videos = list()
        self.sounds = list()
        for i in range(settings['THREAD']):
            self.videos.append('video/' + str(i) + 'th ' + video_name + '.' + settings['VIDEO_EXTENSION'])
            self.sounds.append('video/' + str(i) + 'th ' + sound_name + '.wav')

    def merge(self):

        final_sound = AudioSegment.from_file('bgm/' + self.bgm_name + '.mp3')

        for sound_file in self.sounds:
            sound = AudioSegment.from_file(sound_file)
            final_sound = final_sound.overlay(sound)

        sound_delay = AudioSegment.silent(duration=self.settings['SOUND_DELAY'] * 1000)
        final_sound = sound_delay + final_sound
        final_sound_name = 'video/' + self.sound_name + '.wav'
        final_sound.export(final_sound_name, format='wav')

        video_list = list()

        for video in self.videos:
            video_list.append(mp.VideoFileClip(video))

        final_video = mp.concatenate_videoclips(video_list)
        codec = self.settings['OUTPUT_CODEC']
        bitrate = self.settings['OUTPUT_BITRATE']
        final_video_name = 'video/' + self.video_name + '.' + self.settings['OUTPUT_EXTENSION']
        final_video.write_videofile(final_video_name, audio=final_sound_name, codec=codec, bitrate=bitrate)

