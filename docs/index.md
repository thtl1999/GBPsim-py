# GBPsim-py document

## How the program works
1. bestdori reads game data and convert it to json format
2. GBPsim-py gets the json files and create video with assets
3. GBPsim-py upload the video to YouTube by youtube-api

## How the video created
1. GBPsim-py observe bestdori whether new data came in. Or You can manually set song info
2. Download song score(chart), music and cover image
3. Generate every frame information to process with multi-core
4. Make image of a frame for all the frames
5. Generate sound with se and music
6. Merge images and sound
7. Upload it to YouTube

## bestdori api document
### Song list

### Song information
`https://bestdori.com/api/songs/{song ID}.json`
- Examples
    - `https://bestdori.com/api/songs/31.json`
    
### Score data
`https://bestdori.com/api/charts/{song ID}/{difficulty name}.json`
- Examples
    - `https://bestdori.com/api/charts/187/expert.json`

### music

### Cover image

## bestdori score document
- lane

There are 7 lanes in bandori. `[0,1,2,3,4,5,6]` However, can be float value between `0` and `6`

- beat

Actual timing = beat / BPM * 60

- JSON file
```
[{note}]
```
### note
- BPM
```json
{
  "type":"BPM",
  "bpm":73,
  "beat":34
}
```

- System

Do Starting music or fever control
  
Can assume music starts at beat 0
```json
{
  "type":"System",
  "data":"bgm999.wav",
  "beat":0
}
```
- Single

Inlcudes flick. May change color if not integer beat

```
{
  "type":"Single",
  "lane":1,
  "beat":8
}

{
  "type":"Single",
  "lane":3,
  "beat":15,
  "flick":true
}

{
  "type":"Single",
  "lane":5,
  "beat":16,
  "skill":true
}
```


- Slide

If hidden, the note exist only for visual effect. First and last connections become long start and end
```
{
  "type":"Slide",
  "connections":[]
}

connections: {
  "lane":6,
  "beat":9
}

connections: {
  "lane":6,
  "beat":9,
  "flick":true
}

connections: {
    "lane":5.6,
    "beat":9.0625,
    "hidden":true
}
```

- Directional

For width, start on lane and stretch width to own direction

```json
{
  "type":"Directional",
  "beat":8,
  "lane":1,
  "direction":"Left",
  "width":1
}
```
## Frame information generator

- Frame data
```
"frame": {
  "combo": 13,
  "combo_anim": 4,
  "notes": [],
  "sequence": 123,
  "bpm": 135,
  effects: []
}

"notes": {
  "id": 20,
  "x": 135,
  "y": 678,
  "lane": 3,
  "type": "single",
          
  /* optional */
          
  "connected": [345, 5] or none,  // for slide [note id, lane]
  "direction": ['left', 2], // for directional [direction, width]
  "animation": 21 // for flick and directional. animation sequence,
  "feature": 'off' or 'hidden'  // for single off and hidden tick
}
```

- Note type
    - single / single off
    - flick
    - directional
    - long
    - tick / hidden
    - bar

- How to generate frame info
  - Read score file. Separate Slide connections to each note
    1. Record id to notes
    2. Sort by beat sequence
  - Read sorted notes
    1. Calculate timing(sec) with BPM
    2. Append note(id and lane) to frames where the note appears on
    3. Add count to frame where the note finished
  
  - Read Frame
    1. Calculate combo with count
    2. If two notes start with the frame, add bar note
    3. Sort notes depending on drawing depth

## Image generator

## Sound generator

## Merge process
