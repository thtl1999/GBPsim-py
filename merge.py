from pydub import AudioSegment
import moviepy.editor as mp

class Merge_class:
    def __init__(self, constants):
        self.c = constants

        self.videos = list()
        self.sounds = list()
        for i in range(self.c.THREADS):
            self.videos.append('video/frag/' + str(i) + '.' + self.c.OPENCV_VIDEO_EXT)
            self.sounds.append('video/frag/' + str(i) + '.wav')

    def merge(self):

        final_sound = AudioSegment.from_file('bgm/' + self.c.MUSIC_FILE_NAME + '.mp3')

        for sound_file in self.sounds:
            sound = AudioSegment.from_file(sound_file)
            final_sound = final_sound.overlay(sound)

        sound_delay = AudioSegment.silent(duration=self.c.SOUND_DELAY * 1000)
        final_sound = sound_delay + final_sound
        final_sound_name = 'video/frag/sound.wav'
        final_sound.export(final_sound_name, format='wav')

        video_list = list()

        for video in self.videos:
            video_list.append(mp.VideoFileClip(video))

        final_video = mp.concatenate_videoclips(video_list)
        codec = self.c.FFMPEG_CODEC
        bitrate = self.c.OUTPUT_BITRATE
        final_video_name = 'video/' + self.c.SONG_ID + '.' + self.c.OUTPUT_EXT
        final_video.write_videofile(final_video_name, audio=final_sound_name, codec=codec, bitrate=bitrate)

