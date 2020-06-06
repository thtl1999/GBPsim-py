import json
import time
import requests

class dataChecker:
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

    def download_song_info(self, song_id):
        pass

    def download_song_jacket(self, song_id):
        pass

    def download_song_music(self, song_id):
        pass

    def download_song_chart(self, song_id, difficulty):
        pass

    def download_song_data(self, song_list):
        for song in song_list:
            song_id = song_list[song]['song_id']
            difficulty = song_list[song]['difficulty']
            self.download_song_info(song_id)
            self.download_song_jacket(song_id)
            self.download_song_music(song_id)
            self.download_song_chart(song_id, difficulty)
