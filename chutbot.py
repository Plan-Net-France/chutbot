#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import signal, sys, audioop, argparse, alsaaudio, random
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from os import path
try:
    from os import scandir
except ImportError:
    from scandir import scandir

sampleRate = 44100
channels = 1
bitPerSamples = 16
periodSize = 800

class ChutBot:
    _audioInput = None
    _audioOutput = None
    _audioFiles = []
    _volume = 0
    _repeat = 0
    _clear = 0
    _stop = False
    _debug = False
    _state = 0
    _warmup = 0
    _beepFile = None
    _frequency = 10
    _random = False
    _lastDebugWidth = 0
    _lastDebugEndLine = False
    _lastDebugReturn = False

    def __init__(self, arguments):
        self._volume = arguments.volume
        self._debug = arguments.verbose > 0
        self._repeat = arguments.repeat
        self._clear = arguments.clear
        self._warmup = arguments.warmup
        self._beepFile = arguments.beepfile
        self._frequency = arguments.frequency
        self._random = arguments.random
        self._loadFiles(arguments.file, arguments.folder)
        self._initializeAudio()

    def debug(self, *values, **kwargs):
        if (self._debug):
            flush = False
            if 'flush' in kwargs:
                flush = kwargs['flush']
                del kwargs['flush']
            file = kwargs['file'] if 'file' in kwargs else sys.stdout
            if self._lastDebugWidth and (self._lastDebugReturn or str(values[0])[0] == '\r'):
                print('\r' + (' ' * self._lastDebugWidth), end= '', file= file)
                self._lastDebugWidth = 0
                self._lastDebugReturn = 0
            if self._lastDebugEndLine:
                self._lastDebugEndLine = False
                self._lastDebugWidth = 0
            print(*values, **kwargs)
            allText = (kwargs['sep'] if 'sep' in kwargs else ' ').join([str(val) for val in values])
            text = allText.split('\n').pop().split('\r').pop()
            if allText.find('\r') >= 0 or allText.find('\n') >= 0:
                self._lastDebugWidth = 0
            self._lastDebugWidth += len(text)
            if (kwargs['end'] if 'end' in kwargs else '\n') == '\n' or allText[len(allText) - 1] == '\n':
                self._lastDebugEndLine = True
            if flush:
                file.flush()

    def _loadFile(self, file):
        segment = AudioSegment.from_file(file) \
            .set_sample_width(bitPerSamples / 8) \
            .set_channels(2) \
            .set_frame_rate(sampleRate)
        totalFrameCount = int(segment.frame_count())
        if segment.frame_count() % periodSize != 0:
            segment = segment + AudioSegment.silent(duration= 1000, frame_rate= sampleRate)
            totalFrameCount = totalFrameCount - (totalFrameCount % periodSize) + periodSize
        self._audioFiles.append({
            'data': segment.raw_data[0:totalFrameCount * bitPerSamples / 8 * 2],
            'name': path.basename(file)
        })

    def _loadFolder(self, folder):
        it = scandir(folder)
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file():
                try:
                    self.debug('Loading file %s… ' % entry.name, end='', flush= True)
                    self._loadFile(entry.path)
                    self.debug('Done')
                except CouldntDecodeError:
                    self.debug('Failed')

    def _loadFiles(self, file, folder):
        global bitPerSamples, sampleRate, periodSize
        if file != None:
            try:
                self.debug('Loading %s… ' % file, end='', flush= True)
                self._loadFile(file)
                self.debug('Done.')
            except CouldntDecodeError:
                print('Error loading file %s.' % file, file= sys.stderr)
                sys.exit(100)
        if folder != None:
            self.debug('Loading files in %s…' % folder)
            self._loadFolder(folder)
            self.debug('Files loaded.')
        if len(self._audioFiles) == 0:
            print('No file to load. Check your arguments. Use -h for help.', file= sys.stderr)
            sys.exit(99)

    def _initializeAudio(self):
        global sampleRate, periodSize
        self._audioInput = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)
        self._audioInput.setchannels(1)
        self._audioInput.setrate(sampleRate)
        self._audioInput.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self._audioInput.setperiodsize(periodSize)
        self._audioOutput = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NORMAL)
        self._audioOutput.setchannels(2)
        self._audioOutput.setrate(sampleRate)
        self._audioOutput.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self._audioOutput.setperiodsize(periodSize)

    def _readLoop(self):
        global bitPerSamples, sampleRate
        sampleLength = bitPerSamples / 8
        count = 0
        chars = "-\\|/"
        buffer = ""
        samplingSize = (sampleRate * sampleLength) // self._frequency
        silentFrames = (sampleRate * sampleLength) * self._warmup // 1000
        lastDb = 0
        times = 0
        lenFiles = len(self._audioFiles)
        maxFile = lenFiles - 1
        current = random.randint(0, maxFile) if self._random else 0
        self.debug("Warming up…", end= '', flush= True)
        while not self._stop:
            incoming = False
            frames, data = self._audioInput.read()
            if frames > 0:
                if silentFrames > 0:
                    silentFrames -= frames
                if silentFrames < 0:
                    buffer = data[-silentFrames*sampleLength:(frames + silentFrames)*sampleLength]
                    silentFrames = 0
                else:
                    buffer += data[0:frames*sampleLength]
                incoming = len(buffer) >= samplingSize
                while len(buffer) >= samplingSize:
                    sample = AudioSegment(buffer[0:samplingSize], sample_width= sampleLength, frame_rate= sampleRate, channels= 1)
                    lastDb = sample.dBFS
                    buffer = buffer[samplingSize:]
                    if lastDb > self._volume:
                        times += 1
                        if times == self._repeat:
                            self.debug("\rThreshold ! %s" % self._audioFiles[current]['name'], end='', flush= True)
                            self._audioOutput.write(self._audioFiles[current]['data'])
                            if self._random:
                                current = random.randint(0, maxFile)
                            else:
                                current = (current + 1) % lenFiles
                            buffer = ''
                            silentFrames = (sampleRate * sampleLength) * self._clear // 1000
                            self.debug('\rSilence…', end='', flush=True)
                            times = 0
                    else:
                        if times > 0:
                            times -= 1
            if self._debug and incoming:
                if silentFrames == 0:
                    self.debug("\r%s %d dB (%d)" % (chars[count], lastDb, times), end= '', flush= True)
                count += 1
                count %= 4

    def run(self):
        self._readLoop()

    def stop(self):
        self._stop = True

    def isStopping(self):
        return self._stop

    @classmethod
    def _parse_arguments(cls):
        parser = argparse.ArgumentParser(description="The Chut Bot. It plays a sound when there is too munch ambiant noise.")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('file', nargs='?', const=None, help='WAV file to play when volume threshold is reached.')
        group.add_argument('-F', '--folder', help='Folder where WAV files to play randomly when threshold is reached are put.', metavar='folder')
        parser.add_argument('--random', action='store_true', help='Activate playing the files randomly.')
        group = parser.add_argument_group('Startup', 'Startup behaviour. Adjust here the behaviour when the bot is ready.')
        group.add_argument('-b', '--beepfile', help='WAV file played on startup.', metavar='file')
        group.add_argument('-w', '--warmup', type=int, default=2000, help='Duration in milliseconds at start in which the device is silent.', metavar='duration')
        group = parser.add_argument_group('Detection', 'Detection behaviour. Adjust the threshold parameters.')
        group.add_argument('-t', '--volume', type=int, default=-15, help='Threshold volume in decibel, relative to max volume (0dB). Value is expected to be negative.', metavar='dB')
        group.add_argument('-f', '--frequency', type=int, default=10, help='Frequency of threshold computation in Hz, between 1 and 55.', metavar='Hz')
        group.add_argument('-r', '--repeat', type=int, default=10, help='Number of time the threshold must be reached continously before triggering the playback.', metavar='times')
        group.add_argument('-c', '--clear', type=int, default=5000, help='Duration in milliseconds after the playback in which the device will be silent.', metavar='duration')
        parser.add_argument('-v', '--verbose', action='count', help='Display program state.')
        return parser.parse_args()

    @classmethod
    def checkArguments(cls, arguments):
        if arguments.volume > 0:
            print('Invalid volume. Should be a negative integer in decibel.', file= sys.stderr)
            sys.exit(1)
        if arguments.repeat <= 0:
            print('Invalid repeat. Should be a positive integer.', file= sys.stderr)
            sys.exit(2)
        if arguments.clear < 0:
            print('Invalid clear. Should be a positive integer in milliseconds.', file= sys.stderr)
            sys.exit(3)
        if arguments.warmup < 0:
            print('Invalid warmup. Should be a positive integer in milliseconds.', file= sys.stderr)
            sys.exit(4)
        if arguments.frequency <= 0 or arguments.frequency > 55:
            print('Invalid frequency. Should be an integer in Hz between 1 and 55.', file= sys.stderr)
            sys.exit(5)

    @classmethod
    def start(cls):
        arguments = cls._parse_arguments()
        cls.checkArguments(arguments)
        chutbot = cls(arguments)

        def _signal_handler(sig, frame):
            if (not chutbot.isStopping()):
                if sig == signal.SIGINT:
                    print('You pressed Ctrl+C!', file= sys.stderr)
                chutbot.stop()

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        chutbot.run()

if __name__ == "__main__":
    ChutBot.start()
