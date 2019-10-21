#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import signal, numpy, sys, audioop, argparse, alsaaudio
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.playback import play
import scipy.io.wavfile as wavfile

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

    def __init__(self, arguments):
        self._loadFiles(arguments.file, arguments.folder)
        self._initializeAudio()
        self._volume = arguments.volume
        self._debug = arguments.verbose > 0
        self._repeat = arguments.repeat
        self._clear = arguments.clear
        self._warmup = arguments.warmup
        self._beepFile = arguments.beepfile
        self._frequency = arguments.frequency

    def _loadFile(self, file):
        segment = AudioSegment.from_file(file, format="wav") \
            .set_sample_width(bitPerSamples / 8) \
            .set_channels(2) \
            .set_frame_rate(sampleRate)
        totalFrameCount = int(segment.frame_count())
        if segment.frame_count() % periodSize != 0:
            segment = segment + AudioSegment.silent(duration=1000, frame_rate=sampleRate)
            totalFrameCount = totalFrameCount - (totalFrameCount % periodSize) + periodSize
        self._audioFiles.append(segment.raw_data[0:totalFrameCount * bitPerSamples / 8 * 2])

    def _loadFiles(self, file, folder):
        global bitPerSamples, sampleRate, periodSize
        if file != None:
            try:
                if self._debug:
                    print('Loading %s… ', end='')
                segment = AudioSegment.from_file(file, format="wav") \
                    .set_sample_width(bitPerSamples / 8) \
                    .set_channels(2) \
                    .set_frame_rate(sampleRate)
                totalFrameCount = int(segment.frame_count())
                if segment.frame_count() % periodSize != 0:
                    segment = segment + AudioSegment.silent(duration=1000, frame_rate=sampleRate)
                    totalFrameCount = totalFrameCount - (totalFrameCount % periodSize) + periodSize
                self._audioFiles.append(segment.raw_data[0:totalFrameCount * bitPerSamples / 8 * 2])
                if self._debug:
                    print('Done')
            except CouldntDecodeError:
                sys.stderr.write('Error loading file %s.\n' % file)
                sys.exit(100)
        if len(self._audioFiles) == 0:
            sys.stderr.write('No file to load. Check your arguments. Use -h for help.\n')
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
        if self._debug:
            print("Warming up… ", end='')
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
                            if self._debug:
                                print("\rThreshold !                  ", end='')
                                sys.stdout.flush()
                            self._audioOutput.write(self._audioFiles[0])
                            buffer = ''
                            silentFrames = (sampleRate * sampleLength) * self._clear // 1000
                            if self._debug:
                                print('\rSilence…', end='')
                    else:
                        if times > 0:
                            times -= 1
            if self._debug and incoming:
                if silentFrames == 0:
                    print("\r%s %d dB (%d)  " % (chars[count], lastDb, times), end= '')
                sys.stdout.flush()
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
        parser.add_argument('file', nargs='?', const=None, help='WAV file to play when volume threshold is reached.')
        parser.add_argument('-F', '--folder', help='Folder where WAV files to play randomly when threshold is reached are put.')
        parser.add_argument('-b', '--beepfile', help='WAV file played on startup.')
        parser.add_argument('-w', '--warmup', type=int, default=2000, help='Duration in milliseconds at start in which the device is silent.')
        parser.add_argument('-t', '--volume', type=int, default=-15, help='Threshold volume in decibel, relative to max volume (0dB). Value is expected to be negative.')
        parser.add_argument('-f', '--frequency', type=int, default=10, help='Frequency of threshold computation in Hz, between 1 and 55.')
        parser.add_argument('-r', '--repeat', type=int, default=10, help='Number of time the threshold must be reached continously before triggering the playback.')
        parser.add_argument('-c', '--clear', type=int, default=5000, help='Duration in milliseconds after the playback in which the device will be silent.')
        parser.add_argument('-v', '--verbose', action='count', help='Display program state.')
        return parser.parse_args()

    @classmethod
    def checkArguments(cls, arguments):
        if arguments.volume > 0:
            sys.stderr.write('Invalid volume. Should be a negative integer in decibel.\n')
            sys.exit(1)
        if arguments.repeat <= 0:
            sys.stderr.write('Invalid repeat. Should be a positive integer.\n')
            sys.exit(2)
        if arguments.clear < 0:
            sys.stderr.write('Invalid clear. Should be a positive integer in milliseconds.')
            sys.exit(3)
        if arguments.warmup < 0:
            sys.stderr.write('Invalid warmup. Should be a positive integer in milliseconds.')
            sys.exit(4)
        if arguments.frequency <= 0 or arguments.frequency > 55:
            sys.stderr.write('Invalid frequency. Should be an integer in Hz between 1 and 55.')
            sys.exit(5)

    @classmethod
    def start(cls):
        arguments = cls._parse_arguments()
        cls.checkArguments(arguments)
        chutbot = cls(arguments)

        def _signal_handler(signal, frame):
            if (not chutbot.isStopping()):
                print('You pressed Ctrl+C!')
                chutbot.stop()

        signal.signal(signal.SIGINT, _signal_handler)
        chutbot.run()

if __name__ == "__main__":
    ChutBot.start()
