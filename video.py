from PIL import Image, ImageDraw
import numpy as np
import cv2
import json
import math

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
lnl = Image.open('assets/longNoteLine.png')
lnl_scale = 0.75


note_skin_id = '0'
lane_skin_id = '0'

video = cv2.VideoWriter('myvideo.mp4', FOURCC, FPS, (WIDTH,HEIGHT))
images = dict()

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
    brwh = lnl_scale * NOTE_WIDTH * NOTE_SIZE * bs / 2  # botoom real width half

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
    tx, ty, bx, by, ts, bs = get_note_pos(note)



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
        elif note['type'] == 'Sim':
            pass

        else:
            cur_frame = note['frame']

            # note = img_resize(images['note_normal_' + str(obj['lane'] - 1) + '.png'],NOTE_SIZE*note_pos[cur_frame]['r'])
            note_sprite = get_note_sprite(note)
            x, y, s = get_note_pos(note)
            paste_center(canvas, x, y, note_sprite)
            note['frame'] = note['frame'] + 1

    write_frame(canvas)
    frame = frame + 1

    # if frame > 1200:
    #     break


# note = {
#     'type':'Bar',
#     'frame':[54,15,0],
#     'lane':[1,6],
#     'time':[1,2]
# }
#
# make_line(bg, note)

# bg.show()


video.release()