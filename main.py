import video
import json
import time
import numpy as np
from pydub import AudioSegment
import multiprocessing

def distribute_frames(frames, num_of_threads):
    distributed = np.array_split(frames, num_of_threads)

    # for _ in range(num_of_threads):
    #     distributed.append(list())
    #
    # for i in range(len(frames)):
    #     distributed[i%num_of_threads].append(frames[i])

    return distributed

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


    #################### Video process ####################
    print('Process start with', num_of_threads, 'processes')
    video_start_time = time.time()

    video_prefetcher = video.VideoPrefetch(settings, metadata, difficulty, music_id)
    frame_list = video_prefetcher.get_frame_info()
    distributed_frames = distribute_frames(frame_list, num_of_threads)
    threads = list()

    for i in range(num_of_threads):
        maker = video.VideoFrameMaker(video_prefetcher.copy_settings(), distributed_frames[i], i)
        p = multiprocessing.Process(target=maker.work)
        threads.append(p)
        p.start()

    for thread in threads:
        thread.join()

    video_end_time = time.time()
    print('Video processing time:', video_end_time - video_start_time)



