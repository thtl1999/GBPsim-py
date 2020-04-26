from PIL import Image, ImageDraw
import numpy as np
import cv2
import json

BPMS = [{"bpm":85,"start":0,"end":14.117647058823529},{"bpm":186,"start":14.117647058823529,"end":103.872}]
SONG_ID = '128'
SONG_LEN = 103.872
DIFFICULTY = 'expert'
WIDTH = 1920
HEIGHT = 1080
FOURCC = cv2.VideoWriter_fourcc(*'mp4v')
FPS = 60
LANE_SCALE = 1.4
LANE_SPACE_BOTTOM = 154*LANE_SCALE      #game_play_line.png bottom space
LANE_SCALE_TOP = 16/7*LANE_SCALE
BOTTOM = int(HEIGHT/5*4)
TOP = int(BOTTOM - 610 * LANE_SCALE)    #int(BOTTOM - bg_line_rhythm.height)
BX = dict()
TX = dict()
for x in range(1,8):
    BX[x] = WIDTH/2 - 4*LANE_SPACE_BOTTOM + x*LANE_SPACE_BOTTOM
    TX[x] = WIDTH/2 - 4*LANE_SCALE_TOP + x*LANE_SCALE_TOP
SKIP_NOTE = 5
NOTE_SPEED = 0.005
NOTE_SIZE = 1
NOTE_WIDTH = 304
note_pos = list()
note_len = None


note_skin_id = '0'
lane_skin_id = '0'

video = cv2.VideoWriter('myvideo.mp4', FOURCC, FPS, (WIDTH,HEIGHT))
images = dict()

def pil2cv(pil):
    return np.array(pil)[:, :, ::-1].copy()

def write_frame(img):
    frame = pil2cv(img)
    video.write(frame)
    cv2.destroyAllWindows()

def add_images(file_name):
    json_dict = json.load(open('assets/' + file_name + '.json'))
    image = Image.open('assets/' + file_name + '.png')

    for obj in json_dict['frames']:
        frame = json_dict['frames'][obj]['frame']
        x1 = frame['x']
        y1 = frame['y']
        x2 = x1 + frame['w']
        y2 = y1 + frame['h']

        images[obj] = image.crop((x1,y1,x2,y2)).convert('RGBA')

def paste_center(base, x, y, img):
    w, h = img.size
    base.paste(img, (int(x - w/2), int(y - h/2)), img)

def paste_abs(base, x, y, img):
    base.paste(img, (x, y), img)

def img_resize(img, f):
    w, h = img.size

    if int(w*f) == 0 or int(h*f) == 0:
        return Image.new("RGBA", (1, 1))
    return img.resize((int(w*f), int(h*f)))

def cal_frames():
    height = BOTTOM - TOP
    frame = 0

    while NOTE_SPEED * frame**3 < height:
        position = dict()
        position['y'] = int(NOTE_SPEED * frame**3 + TOP)
        position['r'] = (position['y'] - TOP) / height
        position['x'] = dict()
        for x in range(1,8):
            position['x'][x] = int(TX[x] + (BX[x] - TX[x])*position['r'])
        note_pos.append(position)

        frame = frame + 1

    last = dict()
    last['y'] = BOTTOM
    last['r'] = 1
    last['x'] = dict()
    for x in range(1,8):
        last['x'][x] = int(BX[x])

    note_pos.append(last)

    print(note_pos, len(note_pos))
    return len(note_pos) - 1

def get_note_sprite(note):
    type_dict = {
        'Single' : 'note_normal_'
    }

    type = note['type']
    frame = note['frame']
    lane = note['lane']

    if type == 'Tick':
        img = images['note_slide_among.png']
    else:
        img = images[type_dict[type] + str(lane - 1) + '.png']

    return img_resize(img, note_pos[frame]['r'])

def get_note_pos(note):
    if note['type'] == 'Bar':
        tx = note_pos[note['frame'][1]]['x'][note['lane'][1]]
        ty = note_pos[note['frame'][1]]['y']
        bx = note_pos[note['frame'][0]]['x'][note['lane'][0]]
        by = note_pos[note['frame'][0]]['y']
        ts = note_pos[note['frame'][1]]['r']
        bs = note_pos[note['frame'][0]]['r']
        return tx, ty, bx, by, ts, bs
    elif note['type'] == 'Sim':
        x1 = note_pos[note['frame']]['x'][note['lane'][0]]
        x2 = note_pos[note['frame']]['x'][note['lane'][1]]
        y = note_pos[note['frame']]['y']
        s = note_pos[note['frame']]['r']
        return x1, x2, y, s
    else:
        x = note_pos[note['frame']]['x'][note['lane']]
        y = note_pos[note['frame']]['y']
        s = note_pos[note['frame']]['r']
        return x, y, s

def make_line(canvas, note):
    tx, ty, bx, by, ts, bs = get_note_pos(note)

    trwh = NOTE_WIDTH*NOTE_SIZE*ts/2     #top real width half
    brwh = NOTE_WIDTH*NOTE_SIZE*bs/2     #botoom real width half

    prog = (note['frame'][2])/(note['time'][1]*FPS - note['time'][0]*FPS)
    prog_width = (BX[note['lane'][1]] - BX[note['lane'][0]]) * prog

    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    draw.polygon([(tx-trwh, ty), (bx-brwh + prog_width, by), (bx+brwh + prog_width, by), (tx+trwh, ty)], fill=(255, 100, 255, 100))
    paste_abs(canvas, 0, 0, overlay)


note_len = cal_frames()
bg = Image.open('assets/bgs.png').convert('RGB').resize((WIDTH,HEIGHT))
add_images('lane ' + lane_skin_id)
add_images('note ' + note_skin_id)

game_play_line = img_resize(images['game_play_line.png'], LANE_SCALE)
paste_center(bg, WIDTH/2, BOTTOM, game_play_line)
bg_line_rhythm = img_resize(images['bg_line_rhythm.png'], LANE_SCALE)
paste_center(bg, WIDTH/2, BOTTOM - bg_line_rhythm.height/2, bg_line_rhythm)




notes = json.load(open('score/' + SONG_ID + '.' + DIFFICULTY + '.json'))

drawing = []
frame = 0
t = 1/FPS

while frame*t < SONG_LEN:
    canvas = bg.copy()
    read = True

    #draw bpm
    for bpm in BPMS:
        pass

    #add to drawing
    while read and notes:
        if notes[0]['type'] == 'Bar':
            if notes[0]['time'][0] < note_len*t + frame*t:
                notes[0]['frame'] = [0,0,0]
                drawing.append(notes[0])
                notes = notes[1:]
            else:
                read = False
        elif notes[0]['time'] < note_len*t + frame*t:
            notes[0]['frame'] = 0
            drawing.append(notes[0])
            notes = notes[1:]
        else:
            read = False

    #draw in drawing
    for note in drawing:
        # skip finished notes
        if type(note['frame']) is list:
            if note['frame'][1] == note_len:
                continue
        else:
            if note['frame'] == note_len:
                continue

        # Draw line
        if note['type'] == 'Bar':
            make_line(canvas, note)

            if note['frame'][0] != note_len:
                note['frame'][0] = note['frame'][0] + 1
            else:
                note['frame'][2] = note['frame'][2] + 1

            if note['time'][1] < note_len*t + frame*t:
                note['frame'][1] = note['frame'][1] + 1


        # simultaneous note
        if note['type'] == 'Sim':
            pass

        elif note['type'] == 'Single':
            cur_frame = note['frame']

            # note = img_resize(images['note_normal_' + str(obj['lane'] - 1) + '.png'],NOTE_SIZE*note_pos[cur_frame]['r'])
            note_sprite = get_note_sprite(note)
            x, y, s = get_note_pos(note)
            paste_center(canvas, x, y, note_sprite)
            note['frame'] = note['frame'] + 1

    write_frame(canvas)
    frame = frame + 1

    if frame > 1200:
        break


# make_line(bg, note)
#
# bg.show()

video.release()