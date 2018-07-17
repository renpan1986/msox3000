#!/usr/bin/env python

# Copyright (c) 2018, Stephen Goadhouse <sgoadhouse@virginia.edu>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Neotion nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NEOTION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#-------------------------------------------------------------------------------
#  Handle several remote functions of Agilent/KeySight MSO3034A scope
#
# Using my new MSOX3000 Class

# pyvisa 1.6 (or higher) (http://pyvisa.sourceforge.net/)
# pyvisa-py 0.2 (https://pyvisa-py.readthedocs.io/en/latest/)
#
# NOTE: pyvisa-py replaces the need to install NI VISA libraries
# (which are crappily written and buggy!) Wohoo!
#
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import random
import sys
import argparse

from datetime import datetime
from msox3000 import MSOX3000


# Set to the IP address of the oscilloscope
#@@@#agilent_msox_3034a = 'TCPIP0::172.28.36.206::INSTR'
agilent_msox_3034a = 'TCPIP0::mx3034a-sdg1.phys.virginia.edu::INSTR'

def handleFilename(fname, ext, unique=True, timestamp=True):

    # If extension exists in fname, strip it and add it back later
    # after handle versioning
    ext = '.' + ext                       # don't pass in extension with leading '.'
    if (fname.endswith(ext)):
        fname = fname[:-len(ext)]

    # Make sure filename has no path components, nor ends in a '/'
    if (fname.endswith('/')):
        fname = fname[:-1]
        
    pn = fname.split('/')
    fname = pn[-1]
        
    # Assemble full pathname so files go to ~/Downloads    if (len(pp) > 1):
    pn = os.environ['HOME'] + "/Downloads"
    fn = pn + "/" + fname

    if (timestamp):
        # add timestamp suffix
        fn = fn + '-' + datetime.now().strftime("%Y%0m%0d-%0H%0M%0S")

    suffix = ''
    if (unique):
        # If given filename exists, try to find a unique one
        num = 0
        while(os.path.isfile(fn + suffix + ext)):
            num += 1
            suffix = "-{}".format(num)

    fn += suffix + ext

    return fn



def main():

    parser = argparse.ArgumentParser(description='Access Agilent/KeySight MSO3034A scope')
    parser.add_argument('--hardcopy', '-y', metavar='outfile.png', help='grab hardcopy of scope screen and output to named file as a PNG image')
    parser.add_argument('--waveform', '-w', nargs=2, metavar=('channel', 'outfile.csv'), action='append', help='grab waveform data of channel and output to named file as a CSV file')
    parser.add_argument('--setup_save', '-s', metavar='outfile.stp', help='save the current setup of the oscilloscope into the named file')
    parser.add_argument('--setup_load', '-l', metavar='infile.stp', help='load the current setup of the oscilloscope from the named file')
    parser.add_argument('--statistics', '-t', action='store_true', help='dump to the output the current displayed measurements')
    parser.add_argument('--autoscale', '-a',  nargs=1, action='append', metavar='channel', type=int, choices=range(1,MSOX3000.maxChannel+1),
                            help='cause selected channel to autoscale')
    parser.add_argument('--dvm', '-d', nargs=1, action='append', metavar='channel', type=int, choices=range(1,MSOX3000.maxChannel+1),
                            help='measure and output the DVM readings of selected channel')
    parser.add_argument('--measure', '-m', nargs=1, action='append', metavar='channel', type=int, choices=range(1,MSOX3000.maxChannel+1),
                            help='measure and output the selected channel')

    args = parser.parse_args()

    ## Connect to the Oscilloscope
    scope = MSOX3000(agilent_msox_3034a)
    scope.open()

    print(scope.idn())

    if (args.hardcopy):
        fn = handleFilename(args.hardcopy, 'png')
        
        scope.hardcopy(fn)
        print("Hardcopy Output file: %s" % fn )

    if (args.waveform):
        for nxt in args.waveform:
            # check the channel
            try:
                channel = int(nxt[0])
                if (channel >= 1 and channel <= MSOX3000.maxChannel):
                    fn = handleFilename(nxt[1], 'csv')
                    #@@@#dataLen = scope.waveform(fn, channel, points=100)
                    dataLen = scope.waveform(fn, channel)
                    print("Waveform Output of Channel {} in {} points to file {}".format(channel,dataLen,fn))
                else:
                    print('INVALID Channel Number: {}  SKIPPING!'.format(channel))
            except Exception:
                    print('INVALID Channel Number: "{}"  SKIPPING!'.format(nxt[0]))
                        
    if (args.dvm):
        for lst in args.dvm:
            chan = lst[0]
            acrms = scope.measureDVMacrms(chan)
            dc = scope.measureDVMdc(chan)
            dcrms = scope.measureDVMdcrms(chan)
            freq = scope.measureDVMfreq(chan)

            if (acrms >= MSOX3000.OverRange):
                acrms = 'INVALID '
            if (dc >= MSOX3000.OverRange):
                dc = 'INVALID '
            if (dcrms >= MSOX3000.OverRange):
                dcrms = 'INVALID '
            if (freq >= MSOX3000.OverRange):
                freq = 'INVALID '
            
            print("Ch.{}: {: 7.5f}V ACRMS".format(chan,acrms))
            print("Ch.{}: {: 7.5f}V DC".format(chan,dc))
            print("Ch.{}: {: 7.5f}V DCRMS".format(chan,dcrms))
            print("Ch.{}: {}Hz FREQ".format(chan,freq))

    if (args.statistics):
        print(scope.measureStatistics())
            
    if (args.measure):
        for lst in args.measure:
            chan = lst[0]

            print('\nNOTE: If returned value is >= {}, then it is to be considered INVALID'.format(MSOX3000.OverRange))
            print('\nMeasurements for Ch. {}:'.format(chan))
            print(scope.measureBitRate(chan))
            print(scope.measureBurstWidth(chan))
            print(scope.measureCounterFrequency(chan))
            print(scope.measureFrequency(chan))
            print(scope.measurePeriod(chan))
            print(scope.measurePosDutyCycle(chan))
            print(scope.measureNegDutyCycle(chan))
            print(scope.measureFallTime(chan))
            print(scope.measureFallEdgeCount(chan))
            print(scope.measureFallPulseCount(chan))
            print(scope.measureNegPulseWidth(chan))
            print(scope.measurePosPulseWidth(chan))
            print(scope.measureRiseTime(chan))
            print(scope.measureRiseEdgeCount(chan))
            print(scope.measureRisePulseCount(chan))
            print(scope.measureOvershoot(chan))
            print(scope.measurePreshoot(chan))
            print()
            print(scope.measureVoltAmplitude(chan))
            print(scope.measureVoltTop(chan))
            print(scope.measureVoltBase(chan))
            print(scope.measureVoltMax(chan))
            print(scope.measureVoltAverage(chan))
            print(scope.measureVoltMin(chan))
            print(scope.measureVoltPP(chan))
            print(scope.measureVoltRMS(chan))

                                    
    if (args.setup_save):
        fn = handleFilename(args.setup_save, 'stp')
        
        dataLen = scope.setupSave(fn)
        print("Oscilloscope Setup bytes saved: {} to '{}'".format(dataLen,fn) )

    if (args.setup_load):
        fn = handleFilename(args.setup_load, 'stp', unique=False, timestamp=False)

        if(not os.path.isfile(fn)):
            print('INVALID filename "{}" - must be exact and exist!'.format(fn))
        else:
            dataLen = scope.setupLoad(fn)
            print("Oscilloscope Setup bytes loaded: {} from '{}'".format(dataLen,fn) )

    if (args.autoscale):
        for chan in args.autoscale:
            scope.setupAutoscale(chan[0])
                                    
    # a simple test of enabling/disabling the channels
    if False:
        wait = 0.5 # just so can see if happen
        for chan in range(1,5):
            scope.outputOn(chan,wait)

            for chanEn in range(1,5):
                if (scope.isOutputOn(chanEn)):
                    print("Channel {} is ON.".format(chanEn))
                else:
                    print("Channel {} is off.".format(chanEn))
            print()

        for chan in range(1,5):
            scope.outputOff(chan,wait)

            for chanEn in range(1,5):
                if (scope.isOutputOn(chanEn)):
                    print("Channel {} is ON.".format(chanEn))
                else:
                    print("Channel {} is off.".format(chanEn))
            print()

        scope.outputOnAll(wait)
        for chanEn in range(1,5):
            if (scope.isOutputOn(chanEn)):
                print("Channel {} is ON.".format(chanEn))
            else:
                print("Channel {} is off.".format(chanEn))
        print()

        scope.outputOffAll(wait)
        for chanEn in range(1,5):
            if (scope.isOutputOn(chanEn)):
                print("Channel {} is ON.".format(chanEn))
            else:
                print("Channel {} is off.".format(chanEn))
        print()



    print('Done')
    scope.close()


if __name__ == '__main__':
    main()
