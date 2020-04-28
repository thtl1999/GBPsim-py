import video
import json
import time
import numpy as np
from pydub import AudioSegment
import multiprocessing


def import_settings():
    settings = json.load(open('settings.json'))

    if settings['THREAD'] == 0:
        settings['THREAD'] = multiprocessing.cpu_count()

    return settings


def distribute_frames(frames, num_of_threads):
    return np.array_split(frames, num_of_threads)


def make_video(settings, metadata, music_id, difficulty):
    print('Video process start with', settings['THREAD'], 'processes')
    video_start_time = time.time()

    video_prefetcher = video.VideoPrefetch(settings, metadata, difficulty, music_id)
    frame_list = video_prefetcher.get_frame_info()
    distributed_frames = distribute_frames(frame_list, settings['THREAD'])
    threads = list()

    for i in range(settings['THREAD']):
        maker = video.VideoFrameMaker(video_prefetcher.copy_settings(), distributed_frames[i], i)
        p = multiprocessing.Process(target=maker.work)
        threads.append(p)
        p.start()

    for thread in threads:
        thread.join()

    video_end_time = time.time()
    print('Video processing time:', video_end_time - video_start_time)


if __name__=='__main__':
    settings = import_settings()

    music_id = '128'

    metadata = json.load(open('metadata/' + music_id + '.json', encoding='utf-8'))

    music = AudioSegment.from_mp3('bgm/' + metadata['bgmId'] + ".mp3")

    difficulty = '3'

    make_video(settings, metadata, music_id, difficulty)



