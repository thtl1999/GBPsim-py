from simple_youtube_api.Channel import Channel
from simple_youtube_api.LocalVideo import LocalVideo


def upload_video(c, test_flag=False):

    # loggin into the channel
    channel = Channel()
    channel.login("client_secret.json", "credentials.storage")

    # setting up the video that is going to be uploaded
    video = LocalVideo(file_path="video/" + c.VIDEO_NAME)

    # setting snippet
    title = 'GBPsim-py - ' + c.SONG_NAME + ' ' + c.DIFFICULTY.upper()
    video.set_title(title)

    description = 'https://github.com/thtl1999/GBPsim-py\n' + c.SONG_INFO + '\nThis video is uploaded with automatic process'
    video.set_description(description)
    # video.set_tags(["this", "tag"])
    video.set_category("gaming")
    video.set_default_language("ja")

    # setting status
    video.set_embeddable(True)
    video.set_license("youtube")

    if test_flag:
        video.set_privacy_status("private")
    else:
        video.set_privacy_status("public")

    video.set_public_stats_viewable(True)

    # setting thumbnail
    #video.set_thumbnail_path("test_thumb.png")
    # video.set_playlist("")

    # uploading video and printing the results
    video = channel.upload_video(video)
    print(video.id)
    print(video)

    # liking video
    # video.like()