
from PIL import Image, ImageDraw
import numpy as np
import cv2
import json
import math
import copy

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
NOTE_SPEED = 0.002
NOTE_SIZE = 1
NOTE_WIDTH = 304
note_pos = list()
note_len = None
lnl = Image.open('assets/longNoteLine.png')
lnl_scale = 0.75

flickFPS = int(FPS/3)


note_skin_id = '0'
lane_skin_id = '0'

video = cv2.VideoWriter('myvideo.mp4', FOURCC, FPS, (WIDTH,HEIGHT))
images = dict()

class VideoPrefetch:
    def __init__(self, settings, metadata, difficulty, music_id):

        self.C = self.define_constant(settings, metadata, difficulty, music_id)

        self.P , self.C['position length'] = self.cal_positions(self.C)

        self.frames = self.cal_frames(self.C, self.P)


    def define_constant(self, settings, metadata, difficulty, music_id):
        C = {
            'bpms': metadata['bpm'][difficulty],
            'song id': music_id,
            'song length': metadata['length'],
            'difficulty': settings['DIFFICULTY'][difficulty],
            'difficulty id': difficulty,
            'width': settings['WIDTH'],
            'height': settings['HEIGHT'],
            'fps': settings['FPS'],
            'lane scale': settings['LANE_SCALE'],
            'lane space bottom': settings['LANE_SCALE'] * settings['BOTTOM_DISTANCE'],
            'lane space top': settings['LANE_SCALE'] * settings['TOP_DISTANCE'],
            'bottom': int(settings['BOTTOM_SCALE'] * settings['HEIGHT']),
            'top': int(int(settings['BOTTOM_SCALE'] * settings['HEIGHT']) - settings['BG_LINE_HEIGHT'] * settings[
                'LANE_SCALE']),
            'skip note': settings['SKIP_NOTE'],
            'note speed': settings['NOTE_SPEED'],
            'note size': settings['NOTE_SIZE'],
            'note width': settings['NOTE_WIDTH'],
            'lnl scale': settings['LNL_SCALE'],
            'flick fps': settings['FLICK_FPS'],
            'note skin id': settings['NOTE_SKIN_ID'],
            'lane skin id': settings['LANE_SKIN_ID'],

            'position length': None
        }

        return C

    def cal_positions(self, C):
        BX = dict()
        TX = dict()
        for x in range(1, 8):
            BX[x] = C['width'] / 2 - 4 * C['lane space bottom'] + x * C['lane space bottom']
            TX[x] = C['width'] / 2 - 4 * C['lane space top'] + x * C['lane space top']

        height = C['bottom'] - C['top']
        frame = 0
        note_pos = list()

        while self.C['note speed'] * frame**3 < height:
            position = dict()
            position['y'] = int(C['note speed'] * frame**3 + self.C['top'])
            position['r'] = (position['y'] - C['top']) / height
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

        return note_pos, len(note_pos) - 1

    def add_note(self, frame, note):
        note_info = {
            'type': note['type'],
            'lane': note['lane'],
        }

        if note['type'] == 'Bar':
            top_frame_difference = int((note['time'][1] - note['time'][0])*self.C['fps'])
            note_info['frame'] = [0, -top_frame_difference]
        else:
            note_info['frame'] = 0

        frame.append(note_info)


    def add_moved_notes(self, frame, last_frame):
        copied_frame = copy.deepcopy(last_frame)
        for note in copied_frame:
            if note['type'] == 'Bar':
                note['frame'][0] += 1
                note['frame'][1] += 1

                if note['frame'][1] < self.C['position length']:
                    frame.append(note)
            else:
                note['frame'] += 1

                if note['frame'] < self.C['position length']:
                    frame.append(note)

    def get_note_start_frame(self, C, note):
        if note['type'] == 'Bar':
            note_time = note['time'][0]
        else:
            note_time = note['time']

        return int(note_time * C['fps'] - C['position length'])

    def cal_frames(self, C, P):
        # sort order for drawing order
        sort_order = {
            'Bar': 1,
            'Sim': 2,
            'Tick': 3,
            'Single': 4,
            'SingleOff': 4,
            'Skill': 4,
            'Flick': 5,
            'Long':6
        }

        frames = list()
        score_pointer = 0

        notes = json.load(open('score/' + C['song id'] + '.' + C['difficulty'] + '.json'))

        for current_frame in range(int((C['song length'] + 5) * C['fps'])):
            frame = list()

            # check last frame
            if frames:
                self.add_moved_notes(frame, frames[-1])

            # check if new note should appear
            while score_pointer < len(notes):
                note_start_frame = self.get_note_start_frame(C, notes[score_pointer])
                if note_start_frame > current_frame:
                    break
                else:
                    self.add_note(frame, notes[score_pointer])
                    score_pointer += 1

            # sort note in frame for drawing order
            frame = sorted(frame, key=lambda note: sort_order[note['type']])
            frames.append(frame)

        return frames

    def copy_settings(self):
        return copy.deepcopy(self.C), copy.deepcopy(self.P)

    def get_frame_info(self):
        return copy.deepcopy(self.frames)


class VideoFrameMaker:
    def __init__(self):
        pass

class VideoWriter:
    def __init__(self):
        pass


def pil2cv(pil):
    numpy_image = np.array(pil)
    if pil.mode == 'RGB':
        return cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    elif pil.mode == 'RGBA':
        return cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGRA)
    # return np.array(pil)[:, :, ::-1].copy()

def cv2pil(cvimg):
    if cvimg.shape[2] == 3:
        return Image.fromarray(cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB))
    if cvimg.shape[2] == 4:
        return Image.fromarray(cv2.cvtColor(cvimg, cv2.COLOR_BGRA2RGBA))

def write_frame(img):
    frame = pil2cv(img)
    video.write(frame)

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

def paste_center_no_mask(base, x, y, img):
    w, h = img.size
    base.paste(img, (int(x - w / 2), int(y - h / 2)))

def paste_abs(base, x, y, img):
    base.paste(img, (x, y), img)

def img_resize(img, f):
    w, h = img.size

    if int(w*f) == 0 or int(h*f) == 0:
        return Image.new("RGBA", (1, 1))
    return img.resize((int(w*f), int(h*f)))

def simultaneous_line_resize(sim, w, r):
    if int(w) == 0 or int(sim.height*NOTE_SIZE*r) == 0:
        return Image.new("RGBA", (1, 1))

    return sim.resize((int(w), int(sim.height*NOTE_SIZE*r)))



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
        'Single' : 'note_normal_',
        'Long' : 'note_long_',
        'SingleOff' : 'note_normal_gray_',
        'Skill' : 'note_skill_',
        'Flick' : 'note_flick_'
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

def make_line_old(canvas, note):
    tx, ty, bx, by, ts, bs = get_note_pos(note)

    trwh = NOTE_WIDTH*NOTE_SIZE*ts/2     #top real width half
    brwh = NOTE_WIDTH*NOTE_SIZE*bs/2     #botoom real width half

    prog = (note['frame'][2])/(note['time'][1]*FPS - note['time'][0]*FPS)
    prog_width = (BX[note['lane'][1]] - BX[note['lane'][0]]) * prog

    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    draw.polygon([(tx-trwh, ty), (bx-brwh + prog_width, by), (bx+brwh + prog_width, by), (tx+trwh, ty)], fill=(255, 100, 255, 100))
    paste_abs(canvas, 0, 0, overlay)

def draw_gradient(draw, pos, prog_width, c1, c2, c3):
    tx, ty, bx, by, ts, bs = pos
    bx = bx + prog_width

    trwh = lnl_scale * NOTE_WIDTH * NOTE_SIZE * ts / 2  # top real width half
    brwh = lnl_scale * NOTE_WIDTH * NOTE_SIZE * bs / 2  # bottom real width half

    for y in range(ty, by):
        r = 1 - (by-y)/(by-ty)
        x1 = int((1-r)*(tx - trwh) + r*(bx - brwh))
        x2 = int((1-r)*(tx + trwh) + r*(bx + brwh))

        color = list()
        r = math.sin(r * math.pi)
        for i in range(4):
            color.append(int((1-r)*c1[i] + r*c2[i]))
        color = tuple(color)

        draw.line([(x1,y),(x2,y)], color)

    draw.line([(tx - trwh, ty), (bx - brwh, by)], c3, width=NOTE_SIZE * 3)
    draw.line([(tx + trwh, ty), (bx + brwh, by)], c3, width=NOTE_SIZE * 3)


def make_line(canvas, note):
    prog = (note['frame'][2])/(note['time'][1]*FPS - note['time'][0]*FPS)
    prog_width = (BX[note['lane'][1]] - BX[note['lane'][0]]) * prog

    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    edge_color = (75,226,111,151)
    center_color = (76,228,112,77)
    line_color = (74, 227,112,192)

    draw_gradient(draw,get_note_pos(note), prog_width, edge_color, center_color, line_color)
    paste_abs(canvas, 0, 0, overlay)

def make_line_perspective(canvas, note):
    tx, ty, bx, by, ts, bs = get_note_pos(note)

    if ty == by:
        return canvas

    background = Image.new('RGBA', (WIDTH, HEIGHT))



    rtwh = lnl.width*lnl_scale*NOTE_SIZE*ts/2   # real top width half
    rbwh = lnl.width*lnl_scale*NOTE_SIZE*bs/2   # real bottom width half


    # paste_center_no_mask(background, WIDTH/2, HEIGHT/2, lnl)
    background.paste(lnl, (0,0))

    cvimg = pil2cv(background)

    nw = [0,0]
    ne = [lnl.width,0]
    sw = [0,lnl.height]
    se = [lnl.width,lnl.height]

    # nw, sw, ne, se
    origin = np.float32([nw, sw, se, ne])

    nw = [tx - rtwh, ty]
    ne = [tx + rtwh, ty]
    sw = [bx - rbwh, by]
    se = [bx + rbwh, by]

    # nw, sw, ne, se
    target = np.float32([nw, sw, se, ne])
    M = cv2.getPerspectiveTransform(origin, target)


    dst = cv2.warpPerspective(cvimg, M, (WIDTH, HEIGHT))

    newimg = cv2pil(dst)
    paste_abs(canvas,0,0,newimg)


    # cv2.imshow('img',cvimg)
    # cv2.waitKey(0)

    # lnl = lnl.transform((WIDTH, HEIGHT), Image.PERSPECTIVE, (1,0.3,-700,0,1,-700))
    # lnl.show()

    return canvas


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

while frame*t < SONG_LEN and False:
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
        elif note['type'] == 'Sim':
            sim = images['simultaneous_line.png'].copy()
            x1, x2, y, s = get_note_pos(note)
            sim = simultaneous_line_resize(sim, abs(x1 - x2), s)
            paste_center(canvas, (x1 + x2) / 2, y, sim)
            note['frame'] = note['frame'] + 1

        else:
            cur_frame = note['frame']
            note_sprite = get_note_sprite(note)
            x, y, s = get_note_pos(note)
            paste_center(canvas, x, y, note_sprite)
            note['frame'] = note['frame'] + 1

            if note['type'] == 'Flick':
                flicky = s * NOTE_WIDTH * 0.1 + (note['frame'] % flickFPS) * s * NOTE_WIDTH * 0.3 / flickFPS
                flick_top = img_resize(images['note_flick_top.png'].copy(), s)
                paste_center(canvas, x, y - flicky, flick_top)

    write_frame(canvas)
    frame = frame + 1

    # if frame > 1200:
    #     break


# note = {
#     'type':'Flick',
#     'frame':55,
#     'lane':1,
# }
#
# note_sprite = get_note_sprite(note)
# x, y, s = get_note_pos(note)
# paste_center(bg, x, y, note_sprite)
# flicky = (note['frame'] % flickFPS)*s*NOTE_WIDTH*0.3/flickFPS
# flick_top = img_resize(images['note_flick_top.png'].copy(), s)
# paste_center(bg, x, y - flicky, flick_top)


# make_line(bg, note)

# bg.show()


video.release()