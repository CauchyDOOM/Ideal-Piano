from midiutil import MIDIFile
from copy import deepcopy as copy
import os, math, random
from mido.midifiles.midifiles import MidiFile as midi
from mido import Message
import mido.midifiles.units as unit
from mido.midifiles.tracks import merge_tracks as merge
from mido.midifiles.midifiles import MidiFile
from mido.midifiles.tracks import MidiTrack
from mido.midifiles.meta import MetaMessage
from difflib import SequenceMatcher
from database import *
from structures import note, chord, scale, circle_of_fifths, circle_of_fourths
'''
mido and midiutil is requried for this module, please make sure you have
these two modules with this file
'''
# the old name is audio_generator.py


def toNote(notename, duration=1, volume=100):
    num = eval(''.join([x for x in notename if x.isdigit()]))
    name = ''.join([x for x in notename if not x.isdigit()])
    return note(name, num, duration, volume)


def degree_to_note(degree, duration=1, volume=100):
    name = standard_reverse[degree % 12]
    num = degree // 12
    return note(name, num, duration, volume)


def totuple(x):
    if isinstance(x, str):
        return (x, )
    try:
        return tuple(x)
    except:
        return (x, )


def getf(y):
    if type(y) != note:
        y = toNote(y)
    return 440 * math.exp((y.degree - 57) * math.log(2) / 12)


def secondary_dom(root, mode='major'):
    if type(root) == str:
        root = toNote(root)
    newscale = scale(root, mode)
    return newscale.dom_chord()


def secondary_dom7(root, mode='major'):
    if type(root) == str:
        root = toNote(root)
    newscale = scale(root, mode)
    return newscale.dom7_chord()


def get_related_chord(scale1):
    # fu4 shu3 he2 xian2 and so on
    pass


def getchord_by_interval(start,
                         interval1,
                         duration=1,
                         interval=0,
                         cummulative=False):

    if not isinstance(start, note):
        start = toNote(start)
    result = [start]
    if not cummulative:
        # in this case all the notes has distance only with the start note
        startind = start.degree
        result += [
            degree_to_note(startind + interval1[i])
            for i in range(len(interval1))
        ]
    else:
        # in this case current note and next note has distance corresponding to the given interval
        startind = start.degree
        for i in range(len(interval1)):
            startind += interval1[i]
            result.append(degree_to_note(startind))
    return chord(result, duration, interval)


def inversion(chord1, num=1):
    return chord1.inversion(num)


def getchord(start,
             mode=None,
             duration=1,
             intervals=None,
             addition=None,
             interval=None,
             cummulative=False,
             pitch=5,
             b=None,
             sharp=None,
             ind=0):
    if not isinstance(start, note):
        try:
            start = toNote(start)
        except:
            start = note(start, pitch)
    if interval is not None:
        return getchord_by_interval(start, interval, duration, intervals,
                                    cummulative)
    premode = mode
    mode = mode.lower().replace(' ', '')
    initial = start.degree
    chordlist = [start]
    interval_premode = chordTypes(premode, mode=1, index=ind)
    if interval_premode != 'not found':
        interval = interval_premode
    else:
        interval_mode = chordTypes(mode, mode=1, index=ind)
        if interval_mode != 'not found':
            interval = interval_mode
        else:
            if mode[:3] == 'add':
                try:
                    addnum = int(mode[3:])
                    interval = [
                        major_third, perfect_fifth,
                        scale(start,
                              'major').notes[:-1][(addnum % 7) - 1].degree -
                        start.degree + octave * (addnum // 7)
                    ]
                except:
                    return 'add(n) chord: n should be an integer'
            elif mode[:4] == 'madd':
                try:
                    addnum = int(mode[4:])
                    interval = [
                        minor_third, perfect_fifth,
                        scale(start,
                              'minor').notes[:-1][(addnum % 7) - 1].degree -
                        start.degree + octave * (addnum // 7)
                    ]
                except:
                    return 'add(n) chord: n should be an integer'
            else:
                print('could not detect the chord types')
                return
    for i in range(len(interval)):
        chordlist.append(degree_to_note(initial + interval[i]))
    if addition is not None:
        chordlist.append(degree_to_note(initial + addition))
    if b != None:
        for each in b:
            chordlist[each - 1] = chordlist[each - 1].down()
    if sharp != None:
        for every in sharp:
            chordlist[every - 1] = chordlist[every - 1].up()
    return chord(chordlist, duration, intervals)


chd = getchord
#a = chord(['C5','#D5','G5'],20)
#a = getchord('D5','mM7',4,0)
#b = getchord('A4','mM7',4,0)
#c = getchord('B4','min7',4,0)
#d = getchord('F#4','min7',4,0)
#e = getchord('G4','min7',4,0)
#f = getchord('D4','min7',4,0)
#g = getchord('G4','min7',4,0)
#h = getchord('A4','min7',4,0)


def concat(chordlist):
    temp = copy(chordlist[0])
    for t in chordlist[1:]:
        temp += t
    return temp


def play(chord1,
         tempo=80,
         track=0,
         channel=0,
         time1=0,
         track_num=1,
         name='temp',
         modes='new2'):
    file = write(name,
                 chord1,
                 tempo,
                 track=0,
                 channel=0,
                 time1=0,
                 track_num=1,
                 mode=modes)
    os.startfile(f'{name}.mid')


def read(name, trackind=1, track=1):
    # read from a midi file and return a notes list
    x = midi(str(name))
    try:
        tracklist = list(enumerate(x.tracks))[trackind]
    except:
        return 'error'
    try:
        t = tracklist[track]
    except:
        return 'error'
    interval_unit = x.ticks_per_beat
    hason = []
    hasoff = []
    intervals = []
    notelist = []
    for i in range(len(t)):
        if t[i].type == 'note_on' and t[i].velocity != 0:
            if i not in hason and i not in hasoff:
                hason.append(i)
                find_interval = False
                find_end = False
                time2 = 0
                realtime = None
                for k in range(i + 1, len(t) - 1):
                    current_note = t[k]
                    time2 += current_note.time
                    if not find_interval:
                        if current_note.type == 'note_on' and current_note.velocity != 0:
                            find_interval = True
                            interval1 = time2 / interval_unit
                            if interval1.is_integer():
                                interval1 = int(interval1)
                            intervals.append(interval1)
                    if not find_end:
                        if current_note.type == 'note_off' or (
                                current_note.type == 'note_on'
                                and current_note.velocity == 0):
                            if current_note.note == t[i].note:
                                hasoff.append(k)
                                find_end = True
                                realtime = time2

                if not find_interval:
                    intervals.append(
                        sum([t[x].time
                             for x in range(i,
                                            len(t) - 1)]) / interval_unit)
                if not find_end:
                    realtime = time2
                duration1 = realtime / interval_unit
                if duration1.is_integer():
                    duration1 = int(duration1)
                #if not find_interval:
                #intervals.append(sum([t[x].time for x in range(i,len(t)-1)])/interval_unit)
                notelist.append(
                    degree_to_note(t[i].note,
                                   duration=duration1,
                                   volume=t[i].velocity))

    result = chord(notelist, interval=intervals)
    for tr in x.tracks:
        if 'tempo' in tr[0].__dict__:
            tempo = tr[0].tempo
            return unit.tempo2bpm(tempo), result
    for tr1 in x.tracks:
        for tr2 in tr1:
            if 'tempo' in tr2.__dict__:
                tempo = tr2.tempo
                return unit.tempo2bpm(tempo), result


def write(name_of_midi,
          chord1,
          tempo=80,
          track=0,
          channel=0,
          time1=0,
          track_num=1,
          mode='new2'):
    if isinstance(chord1, note):
        chord1 = chord([chord1])
    if not isinstance(chord1, list):
        chord1 = [chord1]
    chordall = concat(chord1)
    if mode == 'new2':
        newmidi = MidiFile(ticks_per_beat=tempo * 4)
        newtempo = unit.bpm2tempo(tempo)

        for g in range(track_num + 1):
            newmidi.add_track()
        newmidi.tracks[0] = MidiTrack([
            MetaMessage('set_tempo', tempo=newtempo, time=0),
            MetaMessage('end_of_track', time=0)
        ])
        newmidi.save(f'{name_of_midi}.mid')
        write(name_of_midi,
              chord1,
              tempo,
              track,
              channel,
              time1,
              track_num,
              mode='m+')

    if mode == 'new':
        # write to a new midi file or overwrite an existing midi file
        MyMIDI = MIDIFile(track_num)
        MyMIDI.addTempo(track, time1, tempo)
        degrees = [x.degree for x in chordall.notes]
        duration = [x.duration for x in chordall.notes]
        for i in range(len(degrees)):
            #if i != len(degrees) - 1:
            MyMIDI.addNote(track, channel, degrees[i], time1, duration[i],
                           chordall[i + 1].volume)
            time1 += chordall.interval[i]
            #if i == len(degrees) - 1:
            #last = chordall.interval[-1]
            #MyMIDI.addNote(track, channel, degrees[i], time1+duration[i]-last, last, 0)
            #else:
            #MyMIDI.addNote(track, channel, degrees[i], time1, duration[i], chordall[i].volume)
            #if chordall.interval[i] < duration[i]:
            #time1 += duration[i]
            #else:
            #time1 += chordall.interval[i]+duration[i]
            #MyMIDI.addNote(track, channel, degrees[i], time1, duration[i], 0)

        with open(f'{name_of_midi}.mid', "wb") as output_file:
            MyMIDI.writeFile(output_file)
    elif mode in ['m+', 'm']:
        # modify existing midi files, m+: add at the end of the midi file,
        # m: add from the beginning of the midi file
        x = midi(f'{name_of_midi}.mid')
        tracklist = [x[1] for x in list(enumerate(x.tracks))][1:]
        track_modify = tracklist[track]
        interval_unit = x.ticks_per_beat
        if mode == 'm+':
            degrees = [x.degree for x in chordall.notes]
            duration = [
                int(x.duration * interval_unit) for x in chordall.notes
            ]
            interval2 = [int(x * interval_unit) for x in chordall.interval]
            has = []
            for t in range(len(duration)):
                distance = sum(interval2[:t])
                has.append((distance, t, 'note_on'))
                has.append((distance + duration[t], t, 'note_off'))
            sorthas = sorted(has, key=lambda x: x[0])
            for n in range(len(sorthas)):
                if n == 0:
                    track_modify.append(
                        Message(sorthas[n][2],
                                note=degrees[sorthas[n][1]],
                                velocity=chordall[sorthas[n][1] + 1].volume,
                                time=0))
                else:
                    track_modify.append(
                        Message(sorthas[n][2],
                                note=degrees[sorthas[n][1]],
                                velocity=chordall[sorthas[n][1] + 1].volume,
                                time=sorthas[n][0] - sorthas[n - 1][0]))
        elif mode == 'm':
            write('tempmerge', chord1, tempo, track, channel, time1, track_num)
            tempmid = midi('tempmerge.mid')
            newtrack = [y[1]
                        for y in list(enumerate(tempmid.tracks))][1:][track]
            aftertrack = merge([track_modify, newtrack])
            x.tracks[track + 1] = aftertrack
            os.remove('tempmerge.mid')
        x.save(f'{name_of_midi}.mid')


#x = midi('so.mid')
MODIFY = 'modify'
NEW = 'new'


def detect_scale(chord1):
    # receive a piece of music and analyze what modes it is using,
    # return a list of most likely and exact modes the music has.
    pass


def modulation(chord1, old_scale, new_scale):
    # change notes (including both of melody and chords) in the given piece
    # of music from a given scale to another given scale, and return
    # the new changing piece of music.
    return chord1.modulation(old_scale, new_scale)


def exp(form):
    # return a function that follows a mode of translating a given chord to the wanted result,
    # form is a chains of functions you want to perform on the variables.
    # e.g. exp('up(2).period(2).reverse()')
    def express(chord1):
        chordname = [x for x, y in locals().items() if y == chord1][0]
        result = chord([])
        expression = f'result = {chordname}.{form}'
        exec(expression, locals(), globals())
        return result

    return express


def notels(a):
    return [notedict[i] for i in a]


def torealnotes(a, mode=0):
    if mode == 0:
        result = a.split('Dg')
    else:
        result = a.split()
    return [[notedict[i] for i in j] for j in result]


def read12notesfile(path, mode=0):
    with open(path) as f:
        data = f.read()
        result = torealnotes(data, mode)
    return result


def torealnotes(a, combine=0, bychar=0, mode=0):
    if mode == 0:
        result = a.split('Dg')
    else:
        result = a.split()
    if combine == 0:
        if bychar == 0:
            return [notels(i.replace(' ', '')) for i in result]
        else:
            return [[notels(i) for i in j.split()] for j in result]
    else:
        return [notedict[i] for i in a]


def torealnotesfile(path,
                    name='torealnotes conversion.txt',
                    combine=0,
                    bychar=0,
                    mode=0):
    with open(path, "r") as f:
        data = f.read()
        with open(name, "w") as new:
            new.write(str(torealnotes(data, combine, bychar, mode)))


def tochords(a,
             pitch=5,
             combine=0,
             interval_unit=0.5,
             period_unit=1,
             has_interval=0):
    if type(a[0]) != list:
        a = [a]
    if has_interval == 0:
        chordls = [
            chord([note(j, pitch)
                   for j in i], interval=interval_unit).period(period_unit)
            for i in a
        ]
    else:
        chordls = []
        for i in a:
            newchord = []
            N = len(i)
            newinterval = []
            for k in range(N):
                now = i[k]
                if now != 'interval':
                    newchord.append(note(now, pitch))
                    if k != N - 1 and i[k + 1] == 'interval':
                        newinterval.append(interval_unit + period_unit)
                    else:
                        newinterval.append(interval_unit)
            chordls.append(chord(newchord, interval=newinterval))
    if combine == 0:
        return chordls
    else:
        return chord([j for i in chordls for j in i],
                     interval=[j for i in chordls for j in i.interval])


def tochordsfile(path,
                 pitch=5,
                 combine=0,
                 interval_unit=0.5,
                 period_unit=1,
                 has_interval=0,
                 mode=0,
                 splitway=0,
                 combine1=0,
                 bychar=0):
    # mode == 0: open the real notes file and eval the nested by first checking if it is started with [[
    # mode == else: open the file written in 12notes language and translate to real notes
    # splitway == 0/1: corresponding to the mode == 0/1 in real notes translation
    with open(path) as f:
        data = f.read()
        if mode == 0:
            if data[:2] == '[[':
                data = eval(data)
                result = tochords(data, pitch, combine, interval_unit,
                                  period_unit, has_interval)
            else:
                result = 'not a valid real notes file'
        else:
            data = torealnotes(data, combine1, bychar, splitway)
            result = tochords(data, pitch, combine, interval_unit, period_unit,
                              has_interval)
    return result


# some examples
# a= getchord('C5','M7',2,0.5)
# play(a.on('C3',interval=0,duration=2)+a.on('B3',interval=0,duration=2)+a.on
# ('A3',interval=0,duration=2)+a.on('G3',interval=0,duration=2)+a.on('F3',
# interval=0,duration=2)+a.up(2,1).up(2,2).up(3,3).on('F#3',interval=0,
# duration=2)+getchord('G5','M7',duration=1,intervals=0.5,addition=
# perfect_octave).on('G3',interval=0,duration=2).period(12))
# play(((AM7[:-1] + AM7.reverse()).period(0.5) + (AM7[:-1] + AM7.reverse()).up().period(0.5))*3)

#Touhou main melody
#play((getchord_by_interval('D#5',[5,7,10,7,5],2,0.5)*3+getchord_by_interval('F5',[1,0,-4],2,0.5))*3,150)


def inversion_from(a, b, num=False, mode=0):
    N = len(b)
    for i in range(1, N):
        temp = b.inversion(i)
        if [x.name for x in temp.notes] == [y.name for y in a.notes]:
            return f'/{a[1].name}' if not num else f'{i} inversion'
    for j in range(1, N):
        temp = b.inversion_highest(j)
        if [x.name for x in temp.notes] == [y.name for y in a.notes]:
            return f'/{b[j].name}(top)' if not num else f'{j} inversion(highest)'
    return f'could not get chord {a.notes} from a single inversion of chord {b.notes}, you could try sort_from' if mode == 0 else None


def sort_from(a, b, getorder=False):
    names = [i.name for i in b]
    try:
        order = [names.index(j.name) + 1 for j in a]
        return f'{b.notes} sort as {order}' if not getorder else order
    except:
        return


def omitfrom(a, b, showls=False):
    if type(a) == chord:
        a = a.names()
    if type(b) == chord:
        b = b.names()
    omitnotes = list(set(b) - set(a))
    if showls:
        return omitnotes
    else:
        return f"omit {', '.join(omitnotes)}"


def changefrom(a, b, octave_a=False, octave_b=False, same_degree=True):
    # how a is changed from b (flat or sharp some notes of b to get a)
    # this is used only when two chords have the same number of notes
    # in the detect chord function
    if octave_a:
        a = a.inoctave()
    if octave_b:
        b = b.inoctave()
    if same_degree:
        b = b.down(12 * (b[1].num - a[1].num))
    N = min(len(a), len(b))
    anotes = [x.degree for x in a.notes]
    bnotes = [x.degree for x in b.notes]
    bnames = b.names()
    M = min(len(anotes), len(bnotes))
    changes = [(bnames[i], bnotes[i] - anotes[i]) for i in range(M)]
    changes = [x for x in changes if x[1] != 0]
    if any(abs(j[1]) != 1 for j in changes):
        changes = []
    else:
        changes = [f'b{j[0]}' if j[1] > 0 else f'#{j[0]}' for j in changes]
    return ', '.join(changes)


def contains(a, b):
    # if b contains a (notes), in other words,
    # all of a's notes is inside b's notes
    return set(a.names()) < set(b.names()) and len(a) < len(b)


def addfrom(a, b, default=True):
    # This function is used at the worst situation that no matches
    # from other chord transformations are found, and it is limited
    # to one note added.
    addnotes = omitfrom(b, a, True)
    if len(addnotes) == 1:
        if addnotes[0] == sorted(a.notes, key=lambda x: x.degree)[-1].name:
            return f'add {", ".join(addnotes)} on the top'
        else:
            return f'add {", ".join(addnotes)}'
    if default:
        return ''
    else:
        return f'add {", ".join(addnotes)}'


def inversion_way(a,
                  b,
                  inv_num=False,
                  chordtype=None,
                  only_msg=False,
                  ignore_sort_from=False):
    if samenotes(a, b):
        return f'{b[1].name}{chordtype}'
    if samenote_set(a, b):
        inversion_msg = inversion_from(
            a, b, mode=1) if not inv_num else inversion_from(
                a, b, num=True, mode=1)
        if inversion_msg is not None:
            if not only_msg:
                if chordtype is not None:
                    return f'{b[1].name}{chordtype}{inversion_msg}' if not inv_num else f'{b[1].name}{chordtype} {inversion_msg}'
                else:
                    return inversion_msg
            else:
                return inversion_msg
        else:
            if ignore_sort_from:
                return 'not good'
            sort_msg = sort_from(a, b, getorder=True)
            if sort_msg is not None:
                if not only_msg:
                    if chordtype is not None:
                        return f'{b[1].name}{chordtype} sort as {sort_msg}'
                    else:
                        return f'sort as {sort_msg}'
                else:
                    return f'sort as {sort_msg}'
            else:
                return f'a voicing of {b[1].name}{chordtype}'
    else:
        return 'not good'


def samenotes(a, b):
    return a.names() == b.names()


def samenote_set(a, b):
    return set(a.names()) == set(b.names())


def find_similarity(a,
                    b=None,
                    only_ratio=False,
                    fromchord_name=True,
                    getgoodchord=False,
                    listall=False,
                    ratio_and_chord=False,
                    ratio_chordname=False,
                    provide_name=None,
                    result_ratio=False,
                    ignore_sort_from=False,
                    change_from_first=False,
                    ignore_add_from=False,
                    same_note_special=True):
    result = ''
    if b is None:
        wholeTypes = chordTypes.keynames()
        selfname = a.names()
        rootnote = a[1]
        possible_chords = [(chd(rootnote, i), i) for i in wholeTypes]
        lengths = len(possible_chords)
        if same_note_special:
            ratios = [(1 if samenote_set(a, x[0]) else SequenceMatcher(
                None, selfname, x[0].names()).ratio(), x[1])
                      for x in possible_chords]
        else:
            ratios = [(SequenceMatcher(None, selfname,
                                       x[0].names()).ratio(), x[1])
                      for x in possible_chords]
        if ignore_add_from:
            alen = len(a)
            ratios_temp = [
                ratios[k] for k in range(len(ratios))
                if len(possible_chords[k][0]) >= alen
            ]
            if len(ratios_temp) != 0:
                ratios = ratios_temp
        else:
            if change_from_first:
                alen = len(a)
                ratios = [
                    ratios[k] for k in range(len(ratios))
                    if len(possible_chords[k][0]) == alen
                ]
        ratios.sort(key=lambda x: x[0], reverse=True)
        if listall:
            return ratios
        if only_ratio:
            return ratios[0]
        first = ratios[0]
        highest = first[0]
        chordfrom = possible_chords[wholeTypes.index(first[1])][0]
        if ratio_and_chord:
            if ratio_chordname:
                return first, chordfrom
            return highest, chordfrom
        if highest > 0.6:
            if change_from_first:
                result = find_similarity(a, chordfrom, fromchord_name=False)
                cff_ind = 0
                while result == 'not good':
                    cff_ind += 1
                    try:
                        first = ratios[cff_ind]
                    except:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = possible_chords[wholeTypes.index(
                            first[1])][0]
                        result = ''
                        break
                    highest = first[0]
                    chordfrom = possible_chords[wholeTypes.index(first[1])][0]
                    if highest > 0.6:
                        result = find_similarity(a,
                                                 chordfrom,
                                                 fromchord_name=False)
                    else:
                        first = ratios[0]
                        highest = first[0]
                        chordfrom = possible_chords[wholeTypes.index(
                            first[1])][0]
                        result = ''
                        break
            if ignore_sort_from:
                ignore_try = find_similarity(a,
                                             chordfrom,
                                             fromchord_name=False)
                ignore_ind = 0
                ratio_len = len(ratios)
                while 'sort' in ignore_try:
                    ignore_ind += 1
                    if ignore_ind < ratio_len:
                        if ratios[ignore_ind][0] > 0.6:
                            chordfrom = possible_chords[wholeTypes.index(
                                ratios[ignore_ind][1])][0]
                            ignore_try = find_similarity(a,
                                                         chordfrom,
                                                         fromchord_name=False)
                        else:
                            return 'not good'
                    else:
                        ignore_ind = 0
                        break
                first = ratios[ignore_ind]
                highest = first[0]
            if highest == 1:
                chordfrom_type = first[1]
                if samenotes(a, chordfrom):
                    result = f'{rootnote.name}{chordfrom_type}'
                else:
                    if samenote_set(a, chordfrom):
                        result = inversion_from(a, chordfrom, mode=1)
                        if result is None:
                            sort_message = sort_from(a,
                                                     chordfrom,
                                                     getorder=True)
                            if sort_message is None:
                                result = f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                            else:
                                result = f'{rootnote.name}{chordfrom_type} sort as {sort_message}'
                        else:
                            result = f'{rootnote.name}{chordfrom_type} {result}'
                    else:
                        return 'not good'
                if result_ratio:
                    return (highest, result) if not getgoodchord else (
                        (highest,
                         result), chordfrom, f'{chordfrom[1].name}{first[1]}')
                return result if not getgoodchord else (
                    result, chordfrom, f'{chordfrom[1].name}{first[1]}')
            else:
                if contains(a, chordfrom):
                    result = omitfrom(a, chordfrom)
                elif len(a) == len(chordfrom):
                    result = changefrom(a, chordfrom)
                elif (not ignore_add_from) and contains(chordfrom, a):
                    result = addfrom(a, chordfrom)
                if result == '':
                    if samenote_set(a, chordfrom):
                        result = inversion_from(a, chordfrom, mode=1)
                        if result is None:
                            sort_message = sort_from(a,
                                                     chordfrom,
                                                     getorder=True)
                            if sort_message is None:
                                return f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                            else:
                                result = f'sort as {sort_message}'
                    else:
                        return 'not good'

                if fromchord_name:
                    from_chord_names = f'{rootnote.name}{first[1]}'
                    result = f'{from_chord_names} {result}'
                if result_ratio:
                    return (highest,
                            result) if not getgoodchord else ((highest,
                                                               result),
                                                              chordfrom,
                                                              from_chord_names)
                return result if not getgoodchord else (result, chordfrom,
                                                        from_chord_names)

        else:
            return 'not good'
    else:
        if samenotes(a, b):
            if fromchord_name:
                if provide_name != None:
                    bname = b[1].name + provide_name
                else:
                    bname = detect(b)
                return bname if not getgoodchord else (bname, chordfrom, bname)
            else:
                return 'same'
        if only_ratio or listall:
            return SequenceMatcher(None, a.names(), b.names()).ratio()
        chordfrom = b
        if contains(a, chordfrom):
            result = omitfrom(a, chordfrom)
        elif len(a) == len(chordfrom):
            result = changefrom(a, chordfrom)
        elif (not ignore_add_from) and contains(chordfrom, a):
            result = addfrom(a, chordfrom)
        if result == '':
            if samenote_set(a, chordfrom):
                result = inversion_from(a, chordfrom, mode=1)
                if result is None:
                    sort_message = sort_from(a, chordfrom, getorder=True)
                    if sort_message is None:
                        return f'a voicing of the chord {rootnote.name}{chordfrom_type}'
                    else:
                        result = f'sort as {sort_message}'
            else:
                return 'not good'
        if fromchord_name:
            if provide_name != None:
                bname = b[1].name + provide_name
            else:
                bname = detect(b)
            if type(bname) == list:
                bname = bname[0]
            result = f'{bname} {result}'
        return result if not getgoodchord else (result, chordfrom, bname)


def detect_variation(a,
                     mode='chord',
                     inv_num=False,
                     rootpitch=5,
                     ignore_sort_from=False,
                     change_from_first=False,
                     original_first=False,
                     ignore_add_from=False,
                     same_note_special=True,
                     N=None):
    for each in range(1, N):
        each_current = a.inversion(each)
        each_detect = detect(each_current,
                             mode,
                             inv_num,
                             rootpitch,
                             ignore_sort_from,
                             change_from_first,
                             original_first,
                             ignore_add_from,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            #change_msg = inversion_way(a, each_current, inv_num)
            #if 'sort' in detect_msg and 'sort' in change_msg:
            #return f'{chord_name_str} {inversion_way(a, change_from_chord, inv_num)}'
            return f'{detect_msg} {inversion_way(a, each_current, inv_num)}'
    for each2 in range(1, N):
        each_current = a.inversion_highest(each2)
        each_detect = detect(each_current,
                             mode,
                             inv_num,
                             rootpitch,
                             ignore_sort_from,
                             change_from_first,
                             original_first,
                             ignore_add_from,
                             same_note_special,
                             whole_detect=False,
                             return_fromchord=True)
        if each_detect is not None:
            detect_msg, change_from_chord, chord_name_str = each_detect
            #change_msg = inversion_way(a, each_current, inv_num)
            #if 'sort' in detect_msg and 'sort' in change_msg:
            #return f'{chord_name_str} {inversion_way(a, change_from_chord, inv_num)}'
            return f'{detect_msg} {inversion_way(a, each_current, inv_num)}'


def detect_split(a, N=None):
    splitind = N // 2
    lower = detect(a.notes[:splitind])
    upper = detect(a.notes[splitind:])
    if type(upper) == list:
        upper = upper[0]
    if type(lower) == list:
        lower = lower[0]
    return f'[{upper}]/[{lower}]'


def interval_check(a, two_show_interval=True):
    if two_show_interval:
        TIMES, DIST = divmod((a.notes[1].degree - a.notes[0].degree), 12)
        if DIST == 0 and TIMES != 0:
            DIST = 12
        interval_name = INTERVAL[DIST][0]
        root_note_name = a[1].name
        if interval_name == 'perfect fifth':
            return f'{root_note_name}5 ({root_note_name} power chord)/ {root_note_name} with perfect fifth'
        return f'{root_note_name} with {interval_name}'
    else:
        if (a.notes[1].degree - a.notes[0].degree) % octave == 0:
            return f'{a.notes[0]} octave (or times of octave)'


def detect(a,
           mode='chord',
           inv_num=False,
           rootpitch=5,
           ignore_sort_from=False,
           change_from_first=False,
           original_first=False,
           ignore_add_from=False,
           same_note_special=True,
           whole_detect=True,
           return_fromchord=False,
           two_show_interval=True):
    # mode could be chord/scale
    if mode == 'chord':
        if type(a) != chord:
            a = chord(a, rootpitch=rootpitch)
        N = len(a)
        if N == 1:
            return f'note {a.notes[0]}'
        if N == 2:
            return interval_check(a, two_show_interval)
        a = a.standardize()
        N = len(a)
        if N == 1:
            return f'note {a.notes[0]}'
        if N == 2:
            return interval_check(a, two_show_interval)
        root = a[1].degree
        rootNote = a[1].name
        distance = tuple(i.degree - root for i in a[2:])
        findTypes = detectTypes[distance]
        if findTypes != 'not found':
            return [rootNote + i for i in findTypes]
        original_detect = find_similarity(a,
                                          result_ratio=True,
                                          ignore_sort_from=ignore_sort_from,
                                          change_from_first=change_from_first,
                                          ignore_add_from=ignore_add_from,
                                          same_note_special=same_note_special,
                                          getgoodchord=return_fromchord)
        if original_detect != 'not good':
            if return_fromchord:
                original_ratio, original_msg = original_detect[0]
            else:
                original_ratio, original_msg = original_detect
            if original_first:
                if original_ratio > 0.86 and all(x not in original_msg
                                                 for x in ['#', 'b']):
                    return original_msg if not return_fromchord else (
                        original_msg, original_detect[1], original_detect[2])
            if original_ratio == 1:
                return original_msg if not return_fromchord else (
                    original_msg, original_detect[1], original_detect[2])
        for i in range(1, N):
            current = chord(a.inversion(i).names())
            root = current[1].degree
            distance = tuple(i.degree - root for i in current[2:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_result = inversion_way(a, current, inv_num,
                                                 result1[0])
                if 'sort' in inversion_result:
                    continue
                else:
                    return inversion_result if not return_fromchord else (
                        inversion_result, current,
                        f'{current[1].name}{result1[0]}')
            else:
                current = current.inoctave()
                root = current[1].degree
                distance = tuple(i.degree - root for i in current[2:])
                result1 = detectTypes[distance]
                if result1 != 'not found':
                    inversion_result = inversion_way(a, current, inv_num,
                                                     result1[0])
                    if 'sort' in inversion_result:
                        continue
                    else:
                        return inversion_result if not return_fromchord else (
                            inversion_result, current,
                            f'{current[1].name}{result1[0]}')
        for i in range(1, N):
            current = chord(a.inversion_highest(i).names())
            root = current[1].degree
            distance = tuple(i.degree - root for i in current[2:])
            result1 = detectTypes[distance]
            if result1 != 'not found':
                inversion_high_result = inversion_way(a, current, inv_num,
                                                      result1[0])
                if 'sort' in inversion_high_result:
                    continue
                else:
                    return inversion_high_result if not return_fromchord else (
                        inversion_high_result, current,
                        f'{current[1].name}{result1[0]}')
            else:
                current = current.inoctave()
                root = current[1].degree
                distance = tuple(i.degree - root for i in current[2:])
                result1 = detectTypes[distance]
                if result1 != 'not found':
                    inversion_high_result = inversion_way(
                        a, current, inv_num, result1[0])
                    if 'sort' in inversion_high_result:
                        continue
                    else:
                        return inversion_high_result if not return_fromchord else (
                            inversion_high_result, current,
                            f'{current[1].name}{result1[0]}')
        # try to find if the chord is from a chord which omits some notes
        #if original_ratio > 0.6:
        #original_msg = find_similarity(a, chordfrom, provide_name = chordtype)
        #if original_msg != 'not good':
        #return original_msg
        inversion_final = True
        possibles = [(find_similarity(a.inversion(j),
                                      result_ratio=True,
                                      ignore_sort_from=ignore_sort_from,
                                      change_from_first=change_from_first,
                                      ignore_add_from=ignore_add_from,
                                      same_note_special=same_note_special,
                                      getgoodchord=True), j)
                     for j in range(1, N)]
        possibles = [x for x in possibles if x[0] != 'not good']
        if len(possibles) == 0:
            possibles = [(find_similarity(a.inversion_highest(j),
                                          result_ratio=True,
                                          ignore_sort_from=ignore_sort_from,
                                          change_from_first=change_from_first,
                                          ignore_add_from=ignore_add_from,
                                          same_note_special=same_note_special,
                                          getgoodchord=True), j)
                         for j in range(1, N)]
            possibles = [x for x in possibles if x[0] != 'not good']
            inversion_final = False
        if len(possibles) == 0:
            if original_detect != 'not good':
                return original_msg if not return_fromchord else (
                    original_msg, original_detect[1], original_detect[2])
            if not whole_detect:
                return
            else:
                detect_var = detect_variation(a, mode, inv_num, rootpitch,
                                              ignore_sort_from,
                                              change_from_first,
                                              original_first, ignore_add_from,
                                              same_note_special, N)
                if detect_var is None:
                    result_change = detect(a, mode, inv_num, rootpitch,
                                           ignore_sort_from,
                                           not change_from_first,
                                           original_first, ignore_add_from,
                                           same_note_special, False,
                                           return_fromchord)
                    if result_change is None:
                        return ''
                    else:
                        return result_change
                else:
                    return detect_var
        possibles.sort(key=lambda x: x[0][0][0], reverse=True)
        best = possibles[0][0]
        highest_ratio, highest_msg = best[0]
        if original_detect != 'not good':
            if original_ratio > 0.6 and (original_ratio >= highest_ratio
                                         or 'sort' in highest_msg):
                return original_msg if not return_fromchord else (
                    original_msg, original_detect[1], original_detect[2])
        if highest_ratio > 0.6:
            if inversion_final:
                current_invert = a.inversion(possibles[0][1])
            else:
                current_invert = a.inversion_highest(possibles[0][1])
            invfrom_current_invert = inversion_way(a, current_invert, inv_num)
            highest_msg = best[0][1]
            if 'sort' in highest_msg and 'sort' in invfrom_current_invert:
                invfrom_current_invert = inversion_way(a, best[1], inv_num)
                final_result = f'{best[2]} {invfrom_current_invert}'
            else:
                final_result = f'{highest_msg} {invfrom_current_invert}'
            return final_result if not return_fromchord else (final_result,
                                                              current_invert,
                                                              highest_msg)

        #return 'cannot detect the chord types'
        if not whole_detect:
            return
        else:
            detect_var = detect_variation(a, mode, inv_num, rootpitch,
                                          ignore_sort_from, change_from_first,
                                          original_first, ignore_add_from,
                                          same_note_special, N)
            if detect_var is None:
                result_change = detect(a, mode, inv_num, rootpitch,
                                       ignore_sort_from, not change_from_first,
                                       original_first, ignore_add_from,
                                       same_note_special, False,
                                       return_fromchord)
                if result_change is None:
                    return ''
                else:
                    return result_change
            else:
                return detect_var

    elif mode == 'scale':
        if type(a[0]) == int:
            try:
                scales = detectScale[tuple(a)][0]
            except:
                return 'cannot detect this scale'
        else:
            if type(a) in [chord, scale]:
                a = a.notes
            try:
                scales = detectScale[tuple(a[i].degree - a[i - 1].degree
                                           for i in range(1, len(a)))][0]
                return scales
            except:
                return 'cannot detect this scale'


def intervalof(a, cummulative=True, translate=False):
    if type(a) in [chord, scale]:
        a = a.notes
    return a.intervalof(cummulative, translate)


def sums(*chordls):
    if len(chordls) == 1:
        chordls = chordls[0]
        start = chordls[0]
        for i in chordls[1]:
            start += i
        return start
    else:
        return sums(list(chordls))


def random_composing(
    mode,
    length,
    difficulty='easy',
    init_notes=None,
    pattern=None,
    focus_notes=None,
    focus_ratio=0.7,
    avoid_dim_5=True,
    num=3,
    left_hand_velocity=70,
    right_hand_velocity=80,
    left_hand_meter=4,
    right_hand_meter=4,
):
    # Composing a piece of music randomly from a given mode (here means scale),
    # difficulty, number of start notes (or given notes) and an approximate length.
    # length is the total approximate total number of notes you want the music to be.
    if pattern is not None:
        pattern = [int(x) for x in pattern]
    standard = mode.notes[:-1]
    # pick is the sets of notes from the required scales which used to pick up notes for melody
    pick = [x.up(2 * octave) for x in standard]
    focused = False
    if focus_notes != None:
        focused = True
        focus_notes = [pick[i - 1] for i in focus_notes]
        remained_notes = [j for j in pick if j not in focus_notes]
        now_focus = 0
    # the chord part and melody part will be written separately,
    # but still with some relevations. (for example, avoiding dissonant intervals)
    # the draft of the piece of music would be generated first,
    # and then modify the details of the music (durations, intervals,
    # notes volume, periods and so on)
    basechord = mode.get_allchord(num=num)
    # count is the counter for the total number of notes in the piece
    count = 0
    patterncount = 0
    result = chord([])
    while count <= length:
        if pattern is None:
            newchordnotes = random.choice(basechord)
        else:
            newchordnotes = basechord[pattern[patterncount] - 1]
            patterncount += 1
            if patterncount == len(pattern):
                patterncount = 0
        newduration = 1  #random.choice([1,2])
        newinterval = 1  #random.choice([0.5,1])#random.choice([0,0.5,1])
        newchord = newchordnotes.set(newduration, newinterval)
        '''
        # check if current chord belongs to a kind of (closer to) major/minor
        check_chord_types = newchord[2].degree - newchord[1].degree
        if check_chord_types == 2:
            chord_types = 'sus2'        
        elif check_chord_types == 3:
            chord_types = 'minor'
        elif check_chord_types == 4:
            chord_types = 'major'
        elif check_chord_types == 5:
            chord_types = 'sus4'
        '''
        newchord_len = len(newchord)
        if newchord_len < left_hand_meter:
            choose_more = [x for x in mode if x not in newchord]
            for g in range(left_hand_meter - newchord_len):
                newchord += random.choice(choose_more)
        do_inversion = random.randint(0, 1)
        if do_inversion == 1:
            newchord = newchord.inversion_highest(
                random.randint(2, left_hand_meter - 1))
        for each in newchord.notes:
            each.volume = left_hand_velocity
        chord_notenames = newchord.names()
        chordinner = [x for x in pick if x.name in chord_notenames]
        while True:
            if focused:
                now_focus = random.choices([1, 0],
                                           [focus_ratio, 1 - focus_ratio])[0]
                if now_focus == 1:
                    firstmelody = random.choice(focus_notes)
                else:
                    firstmelody = random.choice(remained_notes)
            else:
                current = random.randint(0, 1)
                if current == 0:
                    # pick up melody notes outside chord inner notes
                    firstmelody = random.choice(pick)
                    # avoid to choose a melody note that appears a diminished fifth interval with the current chord
                    if avoid_dim_5:
                        while any((firstmelody.degree - x.degree) %
                                  diminished_fifth == 0
                                  for x in newchord.notes):
                            firstmelody = random.choice(pick)
                else:
                    # pick up melody notes from chord inner notes
                    firstmelody = random.choice(chordinner)
            firstmelody.volume = right_hand_velocity
            newmelody = [firstmelody]
            length_of_chord = sum(newchord.interval)
            intervals = [random.choice([0.5, 1])]
            firstmelody.duration = intervals[0]  #random.choice([0.5,1])
            while sum(intervals) <= length_of_chord:
                if focused:
                    now_focus = random.choices(
                        [1, 0], [focus_ratio, 1 - focus_ratio])[0]
                    if now_focus == 1:
                        currentmelody = random.choice(focus_notes)
                    else:
                        currentmelody = random.choice(remained_notes)
                else:
                    current = random.randint(0, 1)
                    if current == 0:
                        currentmelody = random.choice(pick)
                        if avoid_dim_5:
                            if any((currentmelody.degree - x.degree) %
                                   diminished_fifth == 0
                                   for x in newchord.notes):
                                continue
                    else:
                        currentmelody = random.choice(chordinner)
                currentmelody.volume = right_hand_velocity
                newinter = 0.5  #random.choice([0.5,1])
                intervals.append(newinter)
                currentmelody.duration = newinter  #random.choice([0.5,1])
                newmelody.append(currentmelody)

            distance = [
                abs(x.degree - y.degree) for x in newmelody for y in newmelody
            ]
            if diminished_fifth in distance:
                continue
            else:
                break
        newmelodyall = chord(newmelody, interval=intervals)
        while sum(newmelodyall.interval) > length_of_chord:
            newmelodyall.notes.pop()
            newmelodyall.interval.pop()
        newcombination = newchord.add(newmelodyall, mode='head')
        #choosemode = random.choice(['tail','head'])
        #if choosemode == 'head':
        #startime = random.choice([0,0.5,1])
        #newcombination = newchord.add(newmelodyall, mode = choosemode)
        #else:
        #newcombination = newchord.add(newmelodyall)
        result = result.add(newcombination)
        count += len(newcombination)
    return result


def fugue(mode,
          length,
          interval_bass=0.5,
          interval_melody=0.5,
          duration_bass=0.5,
          duration_melody=0.5):
    bassls = mode.notes[:-1]
    melodyls = [x.up(octave) for x in bassls]
    bassnotes = [random.choice(bassls) for j in range(length)]
    melodynotes = [random.choice(melodyls) for k in range(length)]
    bass = chord(bassnotes, duration_bass, interval_bass)
    melody = chord(melodynotes, duration_melody, interval_melody)
    return bass.add(melody, mode='head')


def perm(n, k=None):
    # return all of the permutations of the elements in x
    if k is None:
        k = len(n)
    if isinstance(n, int):
        n = list(range(1, n + 1))
    if isinstance(n, str):
        n = list(n)
    return eval(
        f'''[{f"[{', '.join([f'n[a{i}]' for i in range(k)])}]"} {''.join([f'for a{i} in range(len(n)) ' if i == 0 else f"for a{i} in range(len(n)) if a{i} not in [{', '.join([f'a{t}' for t in range(i)])}] " for i in range(k)])}]''',
        locals())


# examples:
# play([chord(x).set(1,1) for x in perm(chd('F','m9').names())], 400)
# play([(chord(x) + chord(x)[-3:]).set(1,1) for x in perm(chd('F','m9').names())], 300)
# play([(chord(x) + chord(x)[-3:]).set(1,1) for x in perm((chd('F','m13')%[1,2,4,5,7]).names())], 300)
