import os
import sys
import base64
import struct
import math
import random

from requests_toolbelt.multipart.encoder import MultipartEncoder

DIGIT = '0123456789'

def take_while_in(string, i, alphabet):
    took = ''
    while i < len(string) and string[i] in alphabet:
        took += string[i]
        i += 1
    return i, took

CONVERT_TO_MP3 = True

def pack2(n):
    return struct.pack('<H', n)

def pack4(n):
    return struct.pack('<I', n)

NOTES = ['c', 'c+', 'd', 'd+', 'e', 'f', 'f+', 'g', 'g+', 'a', 'a+', 'b']
MAX_LENGTH = 10000
MAX_DEPTH = 3

def normalize_note(note):
    if note.endswith('+'):
        i = NOTES.index(note[:-1])
        return NOTES[(i + 1) % len(NOTES)]
    elif note.endswith('-'):
        i = NOTES.index(note[:-1])
        return NOTES[(i - 1) % len(NOTES)]
    else:
        return note

def frequency_for(octave, note):
    base = 55.0
    note_diff = NOTES.index(note) - NOTES.index('a') 
    return base * 2 ** (octave + float(note_diff) / 12)

def duration_for(tempo, duration):
    # tempo: quarter notes per minute
    return (4.0 / duration) * (60.0 / tempo)

def wav_to_ogg(wav_data):
    # XXX: hack :-)
    f = open('_tmp_.wav', 'w')
    f.write(wav_data)
    f.close()
    os.system('oggenc _tmp_.wav')

class SoundGenerator(object):

    def __init__(self, samples_per_second):
        self.samples_per_second = samples_per_second
        self.bytes_per_sample = 1
        self.channel = 1 # mono
        self.format = 1  # PCM

        self._compiled_sounds = []
        self._sound_table = {}

        self.tempo = 120             # quarter notes per minute
        self.octave = 4              # 0-6
        self.note_length = 4
        self.proportion = 7.0 / 8    # normal
        self.volume = 7

    def urlencoded_audio(self, samples):
        raw = ''.join(map(chr, samples))
        wav = ''
        wav += 'WAVE'
        wav += 'fmt '
        wav += pack4(0x10)
        wav += pack2(self.format)
        wav += pack2(self.channel)
        wav += pack4(self.samples_per_second)
        wav += pack4(self.samples_per_second * self.bytes_per_sample)
        wav += pack2(self.bytes_per_sample)
        wav += pack2(8 * self.bytes_per_sample)
        wav += 'data'
        wav += pack4(len(raw) + 2)
        wav += raw
        riff = 'RIFF' + pack4(len(wav)) + wav
        if CONVERT_TO_MP3:
            fmt = 'mp3'
            data = wav_to_mp3(riff)
        else:
            fmt = 'wav'
            data = riff
        return 'data:audio/' + fmt + ';base64,' + base64.encodestring(data).replace('\n', '')

    def make_ogg(self, string):
        #samples = self.melody(string)
        #samples = self.complex_melody(string)
        samples = self.grammargen_melody(string)
        raw = ''.join(map(chr, samples))
        wav = ''
        wav += 'WAVE'
        wav += 'fmt '
        wav += pack4(0x10)
        wav += pack2(self.format)
        wav += pack2(self.channel)
        wav += pack4(self.samples_per_second)
        wav += pack4(self.samples_per_second * self.bytes_per_sample)
        wav += pack2(self.bytes_per_sample)
        wav += pack2(8 * self.bytes_per_sample)
        wav += 'data'
        wav += pack4(len(raw) + 2)
        wav += raw
        riff = 'RIFF' + pack4(len(wav)) + wav
        wav_to_ogg(riff)

    def sine_sq_wave(self, dur_s, freq_hz, amplitude):
        freq_hz = float(freq_hz)
        dur_samples = int(self.samples_per_second * dur_s)
        samples = []
        for i in range(dur_samples):
            s = abs(math.sin(float(i) * (freq_hz / self.samples_per_second) * 2 * math.pi))
            #s = s * s
            #samples.append(128 + int(127 * s))
            samples.append(max(0, min(255, int(255 * self.volume * s))))
        return samples

    def sine_sq_wave_envelope(self, dur_s, freq_hz, amplitude, p1, p2):
        #
        # 0   p1______p2   1
        #   /           \
        #  /             \
        #
        freq_hz = float(freq_hz)
        dur_samples = int(self.samples_per_second * dur_s)
        samples = []
        for i in range(dur_samples):
            s = abs(math.sin(float(i) * (freq_hz / self.samples_per_second) * 2 * math.pi))
            #s = s * s
            #samples.append(128 + int(127 * s))
            if float(i) / dur_samples < p1:
                env = (float(i) / dur_samples) / p1
            elif float(i) / dur_samples > p2:
                env = ((dur_samples - float(i)) / dur_samples) / (1 - p2)
            else:
                env = 1.0
            samples.append(max(0, min(255, int(255 * amplitude * env * s))))
        return samples

    def silence(self, dur_s):
        dur_samples = int(self.samples_per_second * dur_s)
        samples = []
        for i in range(dur_samples):
            samples.append(0)
        return samples

    def parse(self, string, i):
        if i < len(string) and string[i] in DIGIT:
            i, n = take_while_in(string, i, DIGIT)
            if i < len(string) and string[i] == '*':
                i, part = self.parse(string, i + 1)
                return i, ['REP', int(n), part]
            else:
                return i, ['SEQ']
        elif i < len(string) and string[i] == '!':
            i, lst = self.parse_list(string, i + 1)
            return i, ['RAND'] + lst
        elif i < len(string) and string[i] == '\\':
            i, lst = self.parse_list(string, i + 1)
            return i, ['REV'] + lst
        elif i < len(string) and string[i] == '|':
            i, lst = self.parse_list(string, i + 1)
            return i, ['PAR'] + lst
        elif i < len(string) and string[i] in ':_':
            i, lst = self.parse_list(string, i + 1)
            return i, ['SEQ'] + lst
        elif i < len(string) and string[i] == '(':
            i, lst = self.parse_list(string, i + 1)
            if i < len(string) and string[i] == ')':
                return i + 1, ['SEQ'] + lst
            else:
                return i, ['SEQ'] + lst
        else: 
            res = ''
            while i < len(string) and string[i] != ')':
                res += string[i]
                i += 1
            return i, res

    def parse_list(self, string, i):
        lst = []
        while i < len(string) and string[i] != ')':
            i, part = self.parse(string, i)
            lst.append(part)
        return i, lst

    def grammargen(self, grammar, string, length=0, depth=0):
        if length > 2 * MAX_LENGTH or depth > 2 * MAX_DEPTH:
            return ''
        res = ''
        for x in string:
            if x in grammar:
                if length >= MAX_LENGTH or depth >= MAX_DEPTH:
                    base = grammar[x]['base']
                    if len(base) == 0:
                        base = ['']
                    res += self.grammargen(grammar, random.choice(base), length=length + len(res), depth=depth + 1)
                else:
                    recursive = grammar[x]['recursive']
                    if len(recursive) == 0:
                        recursive = grammar[x]['base']
                    if len(recursive) == 0:
                        recursive = ['']
                    res += self.grammargen(grammar, random.choice(recursive), length=length + len(res), depth=depth + 1)
            else:
                res += x
        return res

    def grammargen_melody(self, string):
        prods = string.split(';')
        start = prods[0]
        d = {}
        for prod in prods:
            prod = prod.strip(' \t\r\n').split('=')
            name = prod[0].strip(' \t\r\n')
            if len(prod) == 1 or name == '': continue
            right = '->'.join(prod[1:]).split('/')
            
            recursive = []
            base = []
            lst = recursive
            for x in right:
                if x.strip(' \t\r\n') == '':
                    lst = base
                else:
                    lst.append(x)
            d[name] = {'recursive': recursive, 'base': base}
        melody = self.grammargen(d, start)
        return self.complex_melody(melody)

    def complex_melody(self, string):
        _, tree = self.parse(string, 0)
        melody = self.build_complex_melody(tree)
        return melody

    def build_complex_melody(self, tree):
        if isinstance(tree, str) or isinstance(tree, unicode):
            return self.melody(tree)
        elif tree[0] == 'SEQ':
            parts = []
            accum = ''
            for t in tree[1:]:
                if isinstance(t, str) or isinstance(t, unicode):
                    accum += t
                else:
                    parts.append(accum)
                    accum = ''
                    parts.append(t)
            if accum != '':
                parts.append(accum)
            result = []
            for part in parts:
                if isinstance(part, str) or isinstance(part, unicode):
                    result.extend(self.melody(part))
                else:
                    result.extend(self.build_complex_melody(part))
            return result
        elif tree[0] == 'PAR':
            parts = []
            mx = 0
            for t in tree[1:]:
                part = self.build_complex_melody(t)
                parts.append(part)
                mx = max(mx, len(part))
            result = [[] for i in range(mx)]
            for part in parts:
                for i in range(len(part)): 
                    result[i].append(part[i])
            for i in range(len(result)):
                result[i] = int(float(sum(result[i])) / len(result[i]))
            return result
        elif tree[0] == 'RAND':
            t = random.choice(tree[1:])
            return self.build_complex_melody(t)
        elif tree[0] == 'REV':
            samples = self.build_complex_melody(tree[1])
            return list(samples[::-1])
        elif tree[0] == 'REP':
            part = self.build_complex_melody(tree[2])
            result = []
            for i in range(tree[1]):
                result.extend(part)
            return result
        else:
            return []

    def melody(self, string):
        samples = []

        i = 0
        while i < len(string):
            if string[i] in 'cdefgabp':
                note = string[i]
                i += 1
                if note != 'p' and i < len(string) and string[i] in '+-':
                    note += string[i]
                    i += 1
                note = normalize_note(note)
                this_note_length = self.note_length
                if i < len(string) and string[i] in DIGIT:
                    i, this_note_length_string = take_while_in(string, i, DIGIT)
                    this_note_length = int(this_note_length_string)

                dur = duration_for(self.tempo, this_note_length)

                while i < len(string) and string[i] == '.':
                    dur = dur * 1.5
                    i += 1

                if note == 'p':
                    samples.extend(self.silence(dur))
                else:
                    vol = 1 / (2 ** (8.0 - self.volume))
                    p1 = (1 - self.proportion) / 3
                    p2 = 1 - 2 * (1 - self.proportion) / 3
                    samples.extend(self.sine_sq_wave_envelope(dur, frequency_for(self.octave, note), vol, p1, p2))
                    #samples.extend(self.silence((1 - self.proportion) * dur))
            elif string[i] in 't':
                i += 1
                if i < len(string) and string[i] in DIGIT:
                    i, tempo_string = take_while_in(string, i, DIGIT)
                    self.tempo = int(tempo_string)
            elif string[i:i+2] == 'l+':
                i += 2
                self.note_length = min(64, self.note_length * 2)
            elif string[i:i+2] == 'l-':
                i += 2
                self.note_length = max(1, self.note_length / 2)
            elif string[i] in 'l':
                i += 1
                if not (i < len(string) and string[i] in DIGIT):
                    raise Exception('PLAY: L(ength) expected a number: "%s"' % (string,))
                i, note_length_string = take_while_in(string, i, DIGIT)
                self.note_length = int(note_length_string)
            elif string[i:i+2] == 'o+':
                i += 2
                self.octave = (self.octave - 1) % 6
            elif string[i:i+2] == 'o-':
                i += 2
                self.octave = (self.octave + 1) % 6
            elif string[i] in 'o':
                i += 1
                if not (i < len(string) and string[i] in DIGIT):
                    raise Exception('PLAY: O(ctave) expected a number 1-8: "%s"' % (string,))
                i, octave_string = take_while_in(string, i, DIGIT)
                self.octave = int(octave_string)
            elif string[i:i+2] == 'v+':
                i += 2
                self.volume = min(8, self.volume + 1)
            elif string[i:i+2] == 'v-':
                i += 2
                self.volume = max(1, self.volume - 1)
            elif string[i] in 'v':
                i += 1
                if not (i < len(string) and string[i] in DIGIT):
                    raise Exception('PLAY: V(olume) expected a number 1-8: "%s"' % (string,))
                i, volume_string = take_while_in(string, i, DIGIT)
                self.volume = int(volume_string)
            elif string[i] in 'm':
                i += 1
                if not (i < len(string) and string[i] in 'snlbf'):
                    raise Exception('PLAY: M(ode) expected a letter: S(taccato)/N(ormal)/L(ong)/F(oreground)/B(ackground)"' % (string,))
                mode = string[i]
                if mode == 's':
                    self.proportion = 3.0 / 4
                elif mode == 'n':
                    self.proportion = 7.0 / 8
                elif mode == 'l':
                    self.proportion = 1.0

                if mode in 'bf':
                    print('Warning: foreground/background mode for PLAY not implemented')

                i += 1
            elif string[i] == ' ':
                i += 1
            else:
                raise Exception('Unknown directives for PLAY: "%s"' % (string,))
        return samples

    def compile_sound(self, sound):
        if sound in self._sound_table:
            return self._sound_table[sound]
        else:
            if isinstance(sound, tuple):
                (dur_s, freq_hz) = sound
                sound_samples = self.sine_sq_wave(dur_s, freq_hz, 1)
            else:
                sound_samples = self.melody(sound)
            sound_id = len(self._compiled_sounds)
            self._compiled_sounds.append((sound_id, self._sound_definition(sound_samples)))
            self._sound_table[sound] = sound_id
            return sound_id

    def sounds(self):
        return self._compiled_sounds

    def _sound_definition(self, samples):
        return 'new Audio("' + self.urlencoded_audio(samples) + '")'

def play(string):
    return SoundGenerator(84100).make_ogg(string)

if __name__ == '__main__':
    s = SoundGenerator(84100)
    print(s.parse('(a)', 0))
