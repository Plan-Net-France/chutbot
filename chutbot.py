#!/usr/bin/env python

from __future__ import print_function
import signal, numpy, sys, audioop
from pydub import AudioSegment
import alsaaudio
import scipy.io.wavfile as wavfile

sampleRate = 44100
channels = 1
bitPerSamples = 16
audioInput = None
allData = []

def _signal_handler(signal, frame):
    wavfile.write("output.wav", sampleRate, numpy.int16(allData))  # write final buffer to wav file
    print('You pressed Ctrl+C!')
    sys.exit(0)
signal.signal(signal.SIGINT, _signal_handler)

def _initialize():
    global audioInput
    audioInput = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL)
    audioInput.setchannels(1)
    audioInput.setrate(sampleRate)
    audioInput.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    audioInput.setperiodsize(800)

def _readLoop():
    global audioInput, allData, bitPerSamples
    sampleLength = bitPerSamples / 8
    count = 0
    chars = "-\\|/"
    totalFrames = 0
    while 1:
        frames, data = audioInput.read()
        if frames > 0:
            for i in range(frames):
                allData.append(audioop.getsample(data, sampleLength, i))
            totalFrames += frames
            print("%s %d\t" % (chars[count], totalFrames), end= "\r")
        if frames < 0:
            print("%s Overrun\t" % (chars[count]), end= "\r")
        sys.stdout.flush()
        count += 1
        count %= 4

def main():
    _initialize()
    _readLoop()

if __name__ == "__main__":
    main()
