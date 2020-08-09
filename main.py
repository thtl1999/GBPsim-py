
import json
import time
import shutil
import os
import numpy as np
from pydub import AudioSegment
import multiprocessing
import frame
import video
import sound
import merge
import network
import youtube


def import_settings():
    settings = json.load(open('settings.json'))

    if settings['THREADS'] == 0:
        settings['THREADS'] = multiprocessing.cpu_count()

    return settings


def init_program():
    if os.path.isdir('video/frag'):
        shutil.rmtree('video/frag')


def split_data(data, num_of_threads):
    return np.array_split(data, num_of_threads)


def make_video(constants):
    print('Video process start with', constants.THREADS, 'processes')
    start_time = time.time()

    print('Copy chibi image')
    if constants.BAND_ID in ['1', '2', '3', '4', '5', '18', '21']:
        band_id = constants.BAND_ID
    else:
        band_id = '1'
    for chibi_id in range(5):
        chibi_image = 'chibi/preset/' + band_id + '/' + str(chibi_id) + '.png'
        shutil.copy2(chibi_image, 'chibi/')

    print('Parse score')
    frame_maker = frame.FrameMaker(constants)
    frame_list = frame_maker.make_frames()
    distributed_frames = split_data(frame_list, constants.THREADS)
    threads = list()

    print('Create processes')
    os.mkdir('video/frag')
    for i in range(constants.THREADS):
        maker = video.VideoFrameMaker(constants, distributed_frames[i], i)
        p = multiprocessing.Process(target=maker.work)
        threads.append(p)
        p.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print('Video processing time:', end_time - start_time)


def make_sound(constants):
    print('Sound process start with', constants.THREADS, 'processes')
    start_time = time.time()

    notes = json.load(open('score/' + constants.SONG_ID + '.' + constants.DIFFICULTY + '.json'))
    distributed_notes = split_data(notes, constants.THREADS)
    threads = list()

    for i in range(constants.THREADS):
        maker = sound.SoundMaker(constants, distributed_notes[i], str(i))
        p = multiprocessing.Process(target=maker.work)
        threads.append(p)
        p.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print('Sound processing time:', end_time - start_time)


def merge_video(constants):
    print('Merge process start')
    start_time = time.time()

    merge_class = merge.Merge_class(constants)
    merge_class.merge()

    # delete middle files
    time.sleep(2)
    shutil.rmtree('video/frag')

    end_time = time.time()
    print('Merge processing time:', end_time - start_time)


def make_process(song_id, difficulty):
    settings = import_settings()
    metadata = json.load(open('metadata/' + song_id + '.json', encoding='utf-8'))
    constants = frame.Constants(settings, metadata, difficulty, song_id)

    init_program()
    make_video(constants)
    make_sound(constants)
    merge_video(constants)
    return constants


def manual_mode():
    network_class = network.NetworkClass()

    print('Please input song id')
    song_id = input()
    if song_id not in network_class.song_list:
        print('Wrong song id')
        exit(2)
    print('Choose song difficulty')
    print(network_class.song_list[song_id]['difficulty'])
    difficulty = input()
    if difficulty not in network_class.song_list[song_id]['difficulty']:
        print('Wrong difficulty')
        exit(3)

    song = [network_class.create_song_info(song_id, difficulty)]
    network_class.download_song_data(song)
    constants = make_process(song_id, difficulty)
    # youtube.upload_video(constants)


def observer_mode():
    network_class = network.NetworkClass()
    while True:
        if network_class.observe_change():
            songs = network_class.get_added_song_list()
            network_class.download_song_data(songs)
            for song in songs:
                constants = make_process(song['song_id'], song['difficulty'])
                youtube.upload_video(constants)


def upload_test():
    song_id = '284'
    difficulty = '3'
    settings = import_settings()
    metadata = json.load(open('metadata/' + song_id + '.json', encoding='utf-8'))
    constants = frame.Constants(settings, metadata, difficulty, song_id)
    youtube.upload_video(constants, True)

if __name__=='__main__':
    settings = import_settings()

    """
    music_id is not 3-digit number.
    3-digit number is required only for bgm sound file name
    which can find in song metadata
    """

    print('Welcome! This is GBP simulator python')
    print('1. Manual mode')
    print('2. Observer mode')

    selection = input()

    if selection == '1':
        manual_mode()
    elif selection == '2':
        observer_mode()
    elif selection == '3':
        upload_test()
    else:
        print('Wrong input')
        exit(1)


    """
    TODO
    youtube api
    particles
    """

