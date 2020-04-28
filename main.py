import video
import json
from pydub import AudioSegment
import multiprocessing

def distribute_frames(frames, num_of_threads):
    distributed = list()

    for _ in range(num_of_threads):
        distributed.append(list())

    for i in range(len(frames)):
        distributed[i%num_of_threads].append(frames[i])

    return distributed

if __name__=='__main__':
    settings = json.load(open('settings.json'))

    if settings['THREAD'] == 0:
        num_of_threads = multiprocessing.cpu_count()
    else:
        num_of_threads = settings['THREAD']
    print('Process start with', num_of_threads, 'processes')

    music_id = '128'

    metadata = json.load(open('metadata/' + music_id + '.json', encoding='utf-8'))

    music = AudioSegment.from_mp3('bgm/' + metadata['bgmId'] + ".mp3")

    difficulty = '3'

    video_prefetcher = video.VideoPrefetch(settings, metadata, difficulty, music_id)
    frame_list = video_prefetcher.get_frame_info()

    distributed_frames = distribute_frames(frame_list, num_of_threads - 1)
    threads = list()
    queue = multiprocessing.Queue()

    writer = video.VideoWriter(video_prefetcher.copy_settings(), queue)
    writer_process = multiprocessing.Process(target=writer.work)
    writer_process.start()

    for i in range(num_of_threads - 1):
        maker = video.VideoFrameMaker(video_prefetcher.copy_settings(), distributed_frames[i], queue, i)
        p = multiprocessing.Process(target=maker.work)
        threads.append(p)
        p.start()


    for thread in threads:
        thread.join()
    writer_process.join()



