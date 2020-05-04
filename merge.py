from pydub import AudioSegment
import moviepy.editor as mp

class Merge_class:
    def __init__(self, threads, video_name, sound_name, bgm_name):
        self.video_name = video_name
        self.sound_name = sound_name
        self.bgm_name = bgm_name

        self.videos = list()
        self.sounds = list()
        for i in range(threads):
            self.videos.append('video/' + str(i) + 'th ' + video_name)
            self.sounds.append('video/' + str(i) + 'th ' + sound_name)

    def merge(self):
        final_sound = AudioSegment.from_file('bgm/' + self.bgm_name + '.mp3')

        for sound_file in self.sounds:
            sound = AudioSegment.from_file(sound_file)
            final_sound = final_sound.overlay(sound)

        final_sound.export('video/' + self.sound_name, format='wav')

        video_list = list()

        for video in self.videos:
            video_list.append(mp.VideoFileClip(video))

        final_video = mp.concatenate_videoclips(video_list)
        final_video.write_videofile('video/' + self.video_name, audio='video/' + self.sound_name, codec='mpeg4', bitrate='9000k')