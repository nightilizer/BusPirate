#!/usr/bin/env python3
# coding=utf-8

"""
Bus Pirate scripting tool
"""

import sys
import os
import pathlib
import argparse
import time
import serial

from src.utils import *
from config import *

# Serial port
gSerial = serial.Serial()

def connect(port):
    global gSerial

    gSerial.port = port
    gSerial.baudrate = SERIAL_SPEED
    gSerial.timeout = SERIAL_TIMEOUT

    if(gSerial.isOpen()):
        gSerial.close()

    showMsg('Opening serial port')
    try:
        gSerial.open()
    except:
        pass

    if(gSerial.isOpen()):
        showOKMsg('Serial port open')
    else:
        showErrorMsg('ERROR opening serial port, exiting program')
        quit()

def send(command, keep = False):
    showSentMsg(command)
    serialCommand = command + '\n'
    gSerial.write(serialCommand.encode())

    startTime = time.time()
    lastRecTime = 0
    VVV=''

    while( (time.time() - startTime) < (SERIAL_RESPONSE_TIMEOUT/1000) ):
        line = gSerial.readline()
        if(line):
            line = line.decode()
            lastRecTime = time.time()
            showReceivedMsg(line)
            if "READ" in line and keep:
                VVV = line
        else:
            if lastRecTime:
                diff = (time.time() - lastRecTime) * 1000
                if diff > SERIAL_RESPONSE_END_SILENCE:
                    break
    else:
        showErrorMsg('Timeout waiting for response')
    if keep:
        #print(f"##### {VVV} ####")
        return VVV

def resetBoard():
    showMsg('Resetting board')
    send('#')
    delay(RESET_DELAY)

def sendScript(file):
    data = open(file, encoding='utf8')
    lines = [line.replace('\n', '').strip() for line in data]
    numLines = len(lines)
    showMsg('Sending script file ({0}) - {1} lines'.format(file, numLines))

    for line in lines:
        if line == '':
            delay(SCRIPT_BLANK_LINE_DELAY)
        elif line == '#':
            resetBoard()    # Correctly handle reset timeout
        else:
            send(line)

def sizeToAddr(size,org):
    if org:
        switcher = {
            46 : 128,
            56 : 256,
            66 : 512, }
    else:
        switcher = {
            46 : 64,
            56 : 128,
            66 : 256, }


    return switcher.get(size,"fail")


def read93(file, max, org ):
    data = open(file, "w")
    send("m7")
    send("1")
    send("1")
    send("2")
    send("W")
    for x in range(max):
        ret = send(f"[0b110;3 {x};8 r:0x1;16]",True)
        print(f"##### {ret} #### ")
        hhh=ret.split(' ')
        print(f"##### {hhh} #### ")
        sss=hhh[1]
        print(f"#####{sss}#### ")
        aaa=hex(x)
        data.write(f"{aaa} {sss}\n")


def write93(file, max, org ):
    data = open(file, "r")
    send("m7")
    send("1")
    send("1")
    send("2")
    send("W")
    send("[0b10011000000;11]")
    lines = [line.replace('\n', '').strip() for line in data]
    numLines = len(lines)
    for line in lines:
        print(f"## {line} ##\n")
        lll=line.split(' ');
        addr=lll[0]
        val=lll[1]
        print(f"addr={addr} val={val}\n")
        send(f"[0b101;3 {addr};8 {val};16]")
    


def main():
    showTitle('Bus Pirate scripting tool', line='*', color='blue+')
    programStartTime = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument('scriptFileName', nargs='?', help='set script file to use (default: {:s})'.format(SCRIPT_FILE), default=SCRIPT_FILE)
    parser.add_argument('-c', '--comPort', help='set COM port (default: {:s})'.format(SERIAL_PORT), default=SERIAL_PORT)
    parser.add_argument('-r', action='store_true', default=False)
    parser.add_argument('-w', action='store_true', default=False)
    parser.add_argument('-f', default="filename")
    parser.add_argument('-s', default=56,type=int)
    parser.add_argument('-o', action='store_true', default=False)

    args = parser.parse_args()


    showData('Script file', args.scriptFileName)
    showData('COM port', args.comPort)
    showData('r',args.r)
    showData('w',args.w)
    showData('f',args.f)
    showData('s',args.s)

    if args.r == False  and args.w == False:
        showErrorMsg('No Mode Set')
        quit()

    max=sizeToAddr(args.s, args.o)
    print(f"Max Addr is {max}")

    connect(args.comPort)

    if RESET_AT_STARTUP:
        resetBoard()

    #sendScript(args.scriptFileName)
    if args.r:
        read93(args.f, max, args.o)
    else: 
        write93(args.f, max, args.o)

    if RESET_AT_END:
        resetBoard()

    showMsg('Closing serial port')
    gSerial.close()


if __name__ == '__main__':
    try:
        main()
    except:
        print()
        print()
        print('----------------------------------------------')
        print('An error happened, execution interrupted:')
        print(sys.exc_info())
