
import json
import time
import os
import numpy as np
from pydub import AudioSegment
import multiprocessing
import frame
import video
import sound
import merge


def import_settings():
    settings = json.load(open('settings.json'))

    if settings['THREAD'] == 0:
        settings['THREAD'] = multiprocessing.cpu_count()

    return settings


def split_data(data, num_of_threads):
    return np.array_split(data, num_of_threads)


def make_video(constants):
    print('Video process start with', settings['THREAD'], 'processes')
    start_time = time.time()

    print('Parse score')
    frame_maker = frame.FrameMaker(constants)
    frame_list = frame_maker.make_frames()
    distributed_frames = split_data(frame_list, constants.THREADS)
    threads = list()

    print('Create processes')
    for i in range(settings['THREAD']):
        maker = video.VideoFrameMaker(constants, distributed_frames[i], i)
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
    print('Merge process start')
    start_time = time.time()

    sound_name = str(music_id) + difficulty
    video_name = str(music_id) + difficulty
    bgm_name = metadata['bgmId']

    merge_class = merge.Merge_class(settings, video_name, sound_name, bgm_name)
    merge_class.merge()

    # delete middle files

    end_time = time.time()
    print('Merge processing time:', end_time - start_time)


if __name__=='__main__':
    settings = import_settings()

    """
    music_id is not 3-digit number.
    3-digit number is required only for bgm sound file name
    which can find in song metadata
    """
    song_id = '128'

    metadata = json.load(open('metadata/' + song_id + '.json', encoding='utf-8'))

    music = AudioSegment.from_mp3('bgm/' + metadata['bgmId'] + ".mp3")

    difficulty_id = '3'

    constants = frame.Constants(settings, metadata, difficulty_id, song_id)

    make_video(constants)

    make_sound(constants)

    merge_video(constants)


    """
    TODO
    
    bar line draw to quadrangle (using polygon)
    combo
    particles
    
    """

