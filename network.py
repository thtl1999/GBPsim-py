import json
import time
import requests

class NetworkClass:
    def __init__(self):
        self.retry_limit = 10
        self.retry_time_short = 30
        self.retry_time_long = 300
        self.observe_time = 300
        self.song_list = self.get_song_list()

    def download_file(self, url, retry=0):
        if retry > self.retry_limit:
            print('Download error exceeded retry value')
            print('Retry after', self.retry_time_long)
            time.sleep(self.retry_time_long)
            return self.download_file(url)

        try:
            r = requests.get(url)
            print('File downloaded', url)
            return r.content
        except:
            print('Download error', url, 'retry', retry)
            time.sleep(self.retry_time_short)
            return self.download_file(url, retry + 1)



    def get_song_list(self):
        song_list_url = 'https://bestdori.com/api/songs/all.5.json'
        song_list = json.loads(self.download_file(song_list_url))
        return song_list

    def observe_change(self):
        new_song_list = self.get_song_list()
        if self.get_song_list() == new_song_list:
            time.sleep(self.observe_time)
            return self.observe_change()
        else:

            return True

    def create_song_info(self, song_id, difficulty):
        song = {
            'song_id': song_id,
            'difficulty': difficulty
        }
        return song

    def get_added_song_list(self):
        """
        Assume
        - new song does not have special difficulty
        - new difficulty is always special difficulty
        """
        new_song_list = self.get_song_list()
        added_song_list = list()
        for key in new_song_list:
            # check if song is already exist
            if key not in self.song_list:
                song = self.create_song_info(key, '3')
                added_song_list.append(song)
            else:
                # check if special difficulty added
                if '4' in new_song_list[key]['difficulty']:
                    if '4' not in self.song_list[key]['difficulty']:
                        song = self.create_song_info(key, '4')
                        added_song_list.append(song)

        # Update song list
        self.song_list = new_song_list
        return added_song_list

    def save_raw_data(self, data, path):
        f = open(path, 'wb')
        f.write(data)
        f.close()
        print('File saved', path)

    def download_song_info(self, song_id):
        url = 'https://bestdori.com/api/songs/' + song_id + '.json'
        data = self.download_file(url)
        self.save_raw_data(data, 'metadata/' + song_id + '.json')

    def download_song_jacket(self, song_id):
        song_info = json.load(open('metadata/' + song_id + '.json', encoding='utf-8'))
        jacket_name = song_info['jacketImage'][0]
        url = 'https://res.bandori.ga/assets/musicjacket/' + jacket_name + '_rip/jacket.png'
        data = self.download_file(url)
        self.save_raw_data(data, 'jacket/' + song_id + '.png')

    def download_song_music(self, song_id):
        song_info = json.load(open('metadata/' + song_id + '.json', encoding='utf-8'))
        music_name = song_info['bgmId']
        url = 'https://bestdori.com/assets/jp/sound/' + music_name + '_rip/' + music_name + '.mp3'
        data = self.download_file(url)
        self.save_raw_data(data, 'bgm/' + music_name + '.mp3')

    def download_song_chart(self, song_id, difficulty):
        diff_table = {
            '0': 'easy',
            '1': 'normal',
            '2': 'hard',
            '3': 'expert',
            '4': 'special'
        }

        score_name = song_id + '.' + diff_table[difficulty] + '.json'
        url = 'https://bestdori.com/api/songs/chart/graphics/simulator/' + score_name
        data = self.download_file(url)
        self.save_raw_data(data, 'score/' + score_name)

    def download_song_data(self, song_list):
        for song in song_list:
            song_id = song['song_id']
            difficulty = song['difficulty']
            self.download_song_info(song_id)
            # self.download_song_jacket(song_id)
            self.download_song_music(song_id)
            self.download_song_chart(song_id, difficulty)
