import video
import json
from pydub import AudioSegment
import multiprocessing

if __name__=='__main__':
    settings = json.load(open('settings.json'))

    if settings['THREAD'] == 0:
        num_of_threads = multiprocessing.cpu_count()
    else:
        num_of_threads = settings['THREAD']

    music_id = '128'

    metadata = json.load(open('metadata/' + music_id + '.json', encoding='utf-8'))

    music = AudioSegment.from_mp3('bgm/' + metadata['bgmId'] + ".mp3")

    difficulty = '3'

    video_prefetcher = video.VideoPrefetch(settings, metadata, difficulty, music_id)

    threads = list()

    for thread in range(num_of_threads - 1):
        pass

    print(video_prefetcher.copy_settings())

