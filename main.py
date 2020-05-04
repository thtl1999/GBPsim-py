import video
import sound
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


def split_data(data, num_of_threads):
    return np.array_split(data, num_of_threads)


def make_video(settings, metadata, music_id, difficulty_id):
    print('Video process start with', settings['THREAD'], 'processes')
    start_time = time.time()

    video_prefetcher = video.VideoPrefetch(settings, metadata, difficulty_id, music_id)
    frame_list = video_prefetcher.get_frame_info()
    distributed_frames = split_data(frame_list, settings['THREAD'])
    threads = list()

    for i in range(settings['THREAD']):
        maker = video.VideoFrameMaker(video_prefetcher.copy_settings(), distributed_frames[i], i)
        p = multiprocessing.Process(target=maker.work)
        threads.append(p)
        p.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print('Video processing time:', end_time - start_time)


def make_sound(settings, metadata, music_id, difficulty):
    print('Sound process start with', settings['THREAD'], 'processes')
    start_time = time.time()

    notes = json.load(open('score/' + music_id + '.' + difficulty + '.json'))
    distributed_notes = split_data(notes, settings['THREAD'])
    threads = list()

    for i in range(settings['THREAD']):
        maker = sound.SoundMaker(settings, music_id, difficulty, metadata, distributed_notes[i], i)
        p = multiprocessing.Process(target=maker.work)
        threads.append(p)
        p.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print('Sound processing time:', end_time - start_time)

def merge_video(settings, metadata, music_id, difficulty):
    print('Merge process start with', settings['THREAD'], 'processes')
    start_time = time.time()

    end_time = time.time()
    print('Merge processing time:', end_time - start_time)


if __name__=='__main__':
    settings = import_settings()

    """
    music_id is not 3-digit number.
    3-digit number is required only for bgm sound file name
    which can find in song metadata
    """
    music_id = '128'

    metadata = json.load(open('metadata/' + music_id + '.json', encoding='utf-8'))

    music = AudioSegment.from_mp3('bgm/' + metadata['bgmId'] + ".mp3")

    difficulty_id = '3'

    #make_video(settings, metadata, music_id, difficulty_id)

    make_sound(settings, metadata, music_id, settings['DIFFICULTY'][difficulty_id])



    """
    TODO
    
    skip first nth notes function
    particles
    
    """

