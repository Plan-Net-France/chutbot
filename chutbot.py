#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import signal, sys, audioop, argparse, alsaaudio, random, time
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from os import path
try:
    from os import scandir
except ImportError:
    from scandir import scandir
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

sampleRate = 44100
channels = 1
bitPerSamples = 16
periodSize = 800
configFile = None
configLoaded = False

class ChutBot:
    _file = ''
    _folder = ''
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
    _bipFile = ''
    _bipFileData = None
    _frequency = 10
    _random = False
    _lastDebugWidth = 0
    _lastDebugEndLine = False
    _lastDebugReturn = False

    def __init__(self, configParser):
        self._debug = configParser.getint('global', 'verbose') > 0
        self._file = str(configParser.get('resources', 'file'))
        self._folder = str(configParser.get('resources', 'folder'))
        self._random = configParser.getboolean('resources', 'random')
        self._bipFile = str(configParser.get('startup', 'bipfile'))
        self._warmup = configParser.getint('startup', 'warmup')
        self._volume = configParser.getfloat('detection', 'volume')
        self._frequency = configParser.getint('detection', 'frequency')
        self._repeat = configParser.getint('detection', 'repeat')
        self._clear = configParser.getint('detection', 'clear')
        self.debug(self._file, self._folder, self._random, self._bipFile, self._warmup, self._volume, self._frequency, self._repeat, self._clear, sep=', ')
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
        return {
            'data': segment.raw_data[0:totalFrameCount * bitPerSamples / 8 * 2],
            'name': path.basename(file)
        }

    def _loadFolder(self, folder):
        audioFiles = []
        it = scandir(folder)
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file():
                try:
                    self.debug('Loading file %s… ' % entry.name, end='', flush= True)
                    audioFiles.append(self._loadFile(entry.path))
                    self.debug('Done')
                except CouldntDecodeError:
                    self.debug('Failed')
        return audioFiles

    def _loadFiles(self, file, folder):
        global bitPerSamples, sampleRate, periodSize
        if file != '':
            try:
                self.debug('Loading %s… ' % file, end='', flush= True)
                self._audioFiles = [self._loadFile(file)]
                self.debug('Done.')
            except CouldntDecodeError:
                print('Error loading file %s.' % file, file= sys.stderr)
                sys.exit(-100)
        if folder != '':
            self.debug('Loading files in %s…' % folder)
            self._audioFiles = self._loadFolder(folder)
            self.debug('Files loaded.')
        if len(self._audioFiles) == 0:
            print('No file to load. Check your arguments. Use -h for help.', file= sys.stderr)
            sys.exit(-99)

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

    def _playBip(self):
        global bitPerSamples, sampleRate, periodSize
        if self._bipFile != '':
            try:
                self.debug('Loading bip %s… ' % self._bipFile, end='', flush= True)
                self._bipFileData = self._loadFile(self._bipFile)
                self.debug('Done.')
                self.debug('Playing bip… ', end='', flush= True)
                self._audioOutput.write(self._bipFileData['data'])
                self.debug('Done.')
            except CouldntDecodeError:
                print('Error loading bip file %s.' % self._bipFile, file= sys.stderr)

    def _readLoop(self):
        global bitPerSamples, sampleRate, periodSize
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
        period = periodSize / sampleRate
        nextTime = time.time()
        self.debug("Warming up…", end= '', flush= True)
        while not self._stop:
            incoming = False
            now = time.time()
            if nextTime > now:
                time.sleep(nextTime - now)
            nextTime = time.time() + period
            frames, data = self._audioInput.read()
            if frames > 0:
                if silentFrames > 0:
                    silentFrames -= frames
                else:
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

    def initialize(self):
        self._loadFiles(self._file, self._folder)

    def run(self):
        self._playBip()
        self._readLoop()

    def stop(self):
        self._stop = True

    def isStopping(self):
        return self._stop

    @classmethod
    def _initArgumentParser(cls, makeNonRequired=False):
        parser = argparse.ArgumentParser(description="The Chut Bot. It plays a sound when there is too munch ambiant noise.")
        parser.add_argument('--config', type=str, help='Configuration file to use. With INI format. See example.ini.', metavar='file')
        group = parser.add_mutually_exclusive_group(required=not makeNonRequired)
        group.add_argument('file', nargs='?', default='', help='Sound file to play when volume threshold is reached.')
        group.add_argument('-F', '--folder', default='', help='Folder where sound files to play randomly when threshold is reached are put.', metavar='folder')
        parser.add_argument('--random', action='store_true', help='Activate playing the files randomly.')
        group = parser.add_argument_group('Startup', 'Startup behaviour. Adjust here the behaviour when the bot is ready.')
        group.add_argument('-b', '--bipfile', default='', help='Sound file played on startup.', metavar='file')
        group.add_argument('-w', '--warmup', type=int, default=2000, help='Duration in milliseconds at start in which the device is silent.', metavar='duration')
        group = parser.add_argument_group('Detection', 'Detection behaviour. Adjust the threshold parameters.')
        group.add_argument('-t', '--volume', type=float, default=-15, help='Threshold volume in decibel, relative to max volume (0dB). Value is expected to be negative.', metavar='dB')
        group.add_argument('-f', '--frequency', type=int, default=10, help='Frequency of threshold computation in Hz, between 1 and 55.', metavar='Hz')
        group.add_argument('-r', '--repeat', type=int, default=10, help='Number of times the threshold must be reached continously before triggering the playback.', metavar='times')
        group.add_argument('-c', '--clear', type=int, default=5000, help='Duration in milliseconds after the playback in which the device will be silent.', metavar='duration')
        parser.add_argument('-v', '--verbose', action='count', help='Display program state.')
        return parser

    @classmethod
    def _checkArguments(cls, arguments, argumentsParser):
        if arguments.volume > 0:
            argumentsParser.error('argument -t/--volume: should be a negative decimal number in decibel.')
            sys.exit(-1)
        if arguments.repeat <= 0:
            argumentsParser.error('argument -r/--repeat: should be a positive integer.')
            sys.exit(-2)
        if arguments.clear < 0:
            argumentsParser.error('argument -c/--clear: should be a positive integer in milliseconds.')
            sys.exit(-3)
        if arguments.warmup < 0:
            argumentsParser.error('argument -w/--warmup: should be a positive integer in milliseconds.')
            sys.exit(-4)
        if arguments.frequency <= 0 or arguments.frequency > 55:
            argumentsParser.error('argument -f/--frequency: Should be an integer in Hz between 1 and 55.')
            sys.exit(-5)

    @classmethod
    def _initConfigParser(cls):
        parser = configparser.RawConfigParser({
            'resources': {
                'file': '',
                'folder': '',
                'random': str(False)
            },
            'startup': {
                'bipfile': '',
                'warmup': str(2000)
            },
            'detection': {
                'volume': str(-15),
                'frequency': str(10),
                'repeat': str(10),
                'clear': str(5000)
            },
        })
        parser.add_section('global')
        parser.set('global', 'verbose', '0')
        parser.add_section('resources')
        parser.set('resources', 'file', '')
        parser.set('resources', 'folder', '')
        parser.set('resources', 'random', str(False))
        parser.add_section('startup')
        parser.set('startup', 'bipfile', '')
        parser.set('startup', 'warmup', str(2000))
        parser.add_section('detection')
        parser.set('detection', 'volume', str(-15))
        parser.set('detection', 'frequency', str(10))
        parser.set('detection', 'repeat', str(10))
        parser.set('detection', 'clear', str(5000))
        return parser

    @classmethod
    def _loadConfig(cls, configParser, arguments=None):
        global configFile, configLoaded
        locations = ['/etc/chutbot/config.ini', '~/.chutbot.ini']
        locations = [path.expanduser(p) for p in locations]
        newConfigFile = None
        if arguments != None:
            newConfigFile = arguments.config
        else:
            newConfigFile = configFile
        if newConfigFile != None:
            if not path.isfile(newConfigFile):
                cls._initArgumentParser().error('argument --config: the file do no exists')
                sys.exit(-97)
            locations.append(newConfigFile)
        read = configParser.read(locations)
        if newConfigFile != None:
            if not newConfigFile in read:
                cls._initArgumentParser().error('argument --config: the file could not be loaded')
                sys.exit(-96)
        if len(read) == 0:
            cls._initArgumentParser().error('could not load any configuration')
            sys.exit(-95)
        if arguments != None:
            configFile = newConfigFile
        configLoaded = True
        if arguments != None and arguments.verbose > 0:
            configParser.set('global', 'verbose', str(arguments.verbose))

    @classmethod
    def _defineArgumentsAsConfig(cls, configParser, arguments):
        configParser.set('global', 'verbose', arguments.verbose)
        configParser.set('resources', 'file', arguments.file)
        configParser.set('resources', 'folder', arguments.folder)
        configParser.set('resources', 'random', str(arguments.random))
        configParser.set('startup', 'bipfile', arguments.bipfile)
        configParser.set('startup', 'warmup', str(arguments.warmup))
        configParser.set('detection', 'volume', str(arguments.volume))
        configParser.set('detection', 'frequency', str(arguments.frequency))
        configParser.set('detection', 'repeat', str(arguments.repeat))
        configParser.set('detection', 'clear', str(arguments.clear))

    @classmethod
    def start(cls):
        configParser = cls._initConfigParser()
        argumentsParser = cls._initArgumentParser()
        from sys import argv
        if len(argv) > 1 and '--config' in argv:
            if len(argv) == 3 or (len(argv) == 4 and '-v' in argv):
                cls._loadConfig(configParser, cls._initArgumentParser(True).parse_args())
            else:
                argumentsParser.error('the argument --config cannot be used with any other argument except -v/--verbose')
                sys.exit(-98)
        else:
            if len(argv) == 1:
                cls._loadConfig(configParser)
            else:
                arguments = argumentsParser.parse_args()
                cls._checkArguments(arguments, argumentsParser)
                cls._defineArgumentsAsConfig(configParser, arguments)
        chutbot = cls(configParser)
        chutbot.initialize()

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
