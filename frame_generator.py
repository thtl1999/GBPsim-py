import json

def get_empty_frame():
    return {
        "combo": None,
        "combo_anim": None,
        "notes": [],
        "sequence": None,
        "bpm": None,
        "effects": []
    }

def separate_bestdori_notes(bestdori_notes):
    notes = []
    note_id = 0
    for bestdori_note in bestdori_notes:
        note_type = bestdori_note['type']

        if note_type == 'System': continue   # Ignore system type. Assume music starts at beat 0

        if note_type == 'Slide':
            previous_note = None
            for connection in bestdori_note['connections']:
                if previous_note:
                    connection['type'] = 'Connected'
                    connection['connected'] = [previous_note['id'], previous_note['lane']]
                else:
                    connection['type'] = 'Single'
                connection['id'] = note_id
                notes.append(connection)
                previous_note = connection
                note_id = note_id + 1
        else:   # Single and BPM
            bestdori_note['id'] = note_id
            notes.append(bestdori_note)
            note_id = note_id + 1
    return sorted(notes, key=lambda note: note['beat'])

def load_notes(C):
    bestdori_notes = json.load(open(f'score/{C.SONG_ID}.{C.DIFFICULTY}.json'))
    notes = separate_bestdori_notes(bestdori_notes)

    notes_with_timing = []
    BPM = None
    for note in notes:
        if note['type'] == 'BPM':
            BPM = note['bpm']

        note['timing'] = note['beat'] * 60 / BPM
        notes_with_timing.append(note)
    return notes_with_timing

def generate_frames(constants):
    C = constants
    frames = [get_empty_frame() for _ in range(C.SONG_FRAME_LENGTH)]

    notes = load_notes(C)

    combo = 0
    combo_anim = 99999
    sequence = 0

    for note in notes:
        pass