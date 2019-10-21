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
audioInput = None
audioOutput = None
measurementFrequency = 10
defaultThresholdDb = -15
audioFiles = []
periodSize = 800

def _signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)
signal.signal(signal.SIGINT, _signal_handler)

def _parse_arguments():
    global defaultThresholdDb
    parser = argparse.ArgumentParser(description="Chut Bot")
    parser.add_argument('file', nargs='?', const=None, help='The WAV file to play when threshold is reached.')
    parser.add_argument('-t', '--threshold', type=int, default=defaultThresholdDb, help='The decibel threshold, relative to max volume. Value is expected to be negative.')
    parser.add_argument('-f', '--folder', help='The location where WAV files to play randomly when threshold is reached.')
    return parser.parse_args()

def _loadFiles(file, folder):
    global audioFiles, bitPerSamples, sampleRate, periodSize
    if file != None:
        try:
            print('Loading %s… ', end='')
            segment = AudioSegment.from_file(file, format="wav") \
                .set_sample_width(bitPerSamples / 8) \
                .set_channels(2) \
                .set_frame_rate(sampleRate)
            totalFrameCount = int(segment.frame_count())
            if segment.frame_count() % periodSize != 0:
                segment = segment + AudioSegment.silent(duration=1000, frame_rate=sampleRate)
                totalFrameCount = totalFrameCount - (totalFrameCount % periodSize) + periodSize
            audioFiles.append(segment.raw_data[0:totalFrameCount * bitPerSamples / 8 * 2])
            print('Done')
        except CouldntDecodeError:
            sys.stderr.write('Error loading file %s.\n' % file)
            sys.exit(1)
    if len(audioFiles) == 0:
        sys.stderr.write('No file to load. Check your arguments.\n')
        sys.exit(4)

def _initialize():
    global audioInput, audioOutput, periodSize
    audioInput = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)
    audioInput.setchannels(1)
    audioInput.setrate(sampleRate)
    audioInput.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    audioInput.setperiodsize(periodSize)
    audioOutput = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NORMAL)
    audioOutput.setchannels(2)
    audioOutput.setrate(sampleRate)
    audioOutput.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    audioOutput.setperiodsize(periodSize)

def _readLoop(threshold):
    global audioInput, audioOutput, bitPerSamples, sampleRate, measurementFrequency, audioFiles
    sampleLength = bitPerSamples / 8
    count = 0
    chars = "-\\|/"
    totalFrames = 0
    buffer = ""
    samplingSize = (sampleRate * sampleLength) / measurementFrequency
    minimumFrames = (sampleRate * sampleLength) * 5 # 5 seconds minimum
    startup = True
    lastDb = 0
    print("Warming up… ", end='')
    while 1:
        frames, data = audioInput.read()
        if frames > 0:
            buffer += data[0:frames*sampleLength]
            totalFrames += frames
            if len(buffer) >= samplingSize:
                sample = AudioSegment(buffer[0:samplingSize], sample_width= sampleLength, frame_rate= sampleRate, channels= 1)
                lastDb = sample.dBFS
                buffer = buffer[samplingSize:]
                if startup and totalFrames >= minimumFrames:
                    print('Done')
                    startup = False
                if lastDb > threshold and totalFrames >= minimumFrames:
                    print("\rThreshold !    ")
                    sys.stdout.flush()
                    audioOutput.write(audioFiles[0])
            if not startup:
                print("\r%s %d dB    " % (chars[count], lastDb), end= '')
        if frames < 0:
            print("\rOverrun        ")
        sys.stdout.flush()
        count += 1
        count %= 4

def main():
    arguments = _parse_arguments()
    if arguments.threshold > 0:
        sys.stderr.write('Invalid threshold. Should be negative.\n')
        sys.exit(2)
    _loadFiles(arguments.file, arguments.folder)
    _initialize()
    _readLoop(arguments.threshold)

if __name__ == "__main__":
    main()
