#!/usr/bin/env python
import snap7
import struct
import sys, getopt

HOST = ''       # IP Address
PORT = 102      #
MODE = ''       # Read / Write
ADDRESS = ''    # Offset in bits
NUMBER = ''     # Number of bits that are going to be read/written
DATA = ''       # Data to be written

GREEN = "\033[32;1m"
RED = "\033[31;1m"
CRESET = "\033[0m"

try:
    opts, args = getopt.getopt(sys.argv[1:],"ha:m:n:d:",["address","mode","number","data"])
except getopt.GetoptError:
    print (RED + "[-]" + CRESET +" Usage: s7comm.py -a <address> -m <mode> -n <number> -d <data> ip_address\n\
    -a\tAddress from which data will be read/written\n\
    -m\t[r|w] Chosen mode of the program, whether you want to read or write on the PLC\n\
    -n\tNumber of data you want to read/write\n\
    -d\tData in binary to write (e.g. 1001)") 
    sys.exit(2)
if len(sys.argv) == 1:
    print (RED + "[-]" + CRESET +" Usage: s7comm.py -a <address> -m <mode> -n <number> -d <data> ip_address\n\
    -a\tAddress from which data will be read/written\n\
    -m\t[r|w] Chosen mode of the program, whether you want to read or write on the PLC\n\
    -n\tNumber of data you want to read/write\n\
    -d\tData in binary to write (e.g. 1001)")
    sys.exit(1)
for opt, arg in opts:
    if opt == '-h' or len(sys.argv) < 8:
        print (RED + "[-]" + CRESET + " Usage: s7comm.py -a <address> -m <mode> -n <number> -d <data> ip_address\n\
    -a\tAddress from which data will be read/written\n\
    -m\t[r|w] Chosen mode of the program, whether you want to read or write on the PLC\n\
    -n\tNumber of data you want to read/write\n\
    -d\tData in binary to write (e.g. 1001)")
        sys.exit()
    elif opt in ("-a", "--address"):
        ADDRESS = arg
    elif opt in ("-m", "--mode"):
        if arg == "r" or arg == "w":
            MODE = arg
        else:
            print RED + "[-]" + CRESET +" There are only two modes: read (r) or write (w)"
            sys.exit()
    elif opt in ("-n", "--number"):
        NUMBER = arg
    elif opt in ("-d", "--data"):
        for i in arg:
            if i != '0' and i != '1':
                print RED + "[-]" + CRESET + " Data to be written shall only contain 0s and 1s"
                sys.exit(3)
        DATA = arg
        if len(DATA) != int(NUMBER):
            print RED + "[-]" + CRESET + " The number of bits to write, specified in [-n], is different from the size of the data given in [-d]"
            sys.exit(4)

HOST = sys.argv[len(sys.argv)-1]

s7 = snap7.client.Client()
s7.connect(HOST, 0, 1)

if MODE == "r":
    result = []
    output = []
    start = int(ADDRESS)/8
    offset = int(ADDRESS) % 8   # Where the start address is located in the byte
    offset_bis = 8-offset       # How many bits are going to be read in the first byte
    new_number = int(NUMBER)-offset_bis # New number to calculate the remaining bytes that need to be read
    if new_number <= 0:
        size = 1
    else:
        size = (new_number-1)/8 + 2
    s = s7.read_area(snap7.types.areas['PA'], 0, start, size)
    result = [bits[::-1] for bits in ['0' * (8-len(bin(x)[2:])) + bin(x)[2:] for x in s ]] 
    for k in range(offset,min(8,offset+int(NUMBER))):
        output.append(result[0][k]) # to write the bits value of the first byte 
    if 8 < offset+int(NUMBER):
        size_result = len(result)
        for l in range(1,size_result):
            for m in range(0,8):
                output.append(result[l][m]) # all the remaining bytes
    print '===Outputs==='
    for j in range(0,int(NUMBER)):
        print "Output " + str(int(ADDRESS) + j) + " : " + output[j]

elif MODE == "w":
    if len(DATA) == 0:
        print RED + "[-]" + CRESET + " [-d] parameter misused or absent"
        sys.exit(3)
    to_be_written = []
    data = []
    start = int(ADDRESS)/8
    offset = int(ADDRESS) % 8   # Where the start address is located in the byte
    offset_bis = 8-offset       # How many bits are going to be read in the first byte
    new_number = int(NUMBER)-offset_bis # New number to calculate the remaining bytes that need to be read
    if new_number <= 0:
        size = 1
    else:
        size = (new_number-1)/8 + 2
    to_be_written.append(DATA[:offset_bis])
    to_be_written += [ DATA[i + offset_bis : i + offset_bis + 8] for i in range(0, len(DATA) - offset_bis, 8) ]
    s = s7.read_area(snap7.types.areas['PA'], 0, start, size)
    read_values = [bits[::-1] for bits in ['0' * (8-len(bin(x)[2:])) + bin(x)[2:] for x in s ]] 
    if offset != 0: 
        data.append(read_values[0][:offset])
    data += to_be_written[::] 
    if new_number % 8 != 0:
        data.append(read_values[size-1][new_number % 8:])
    if len(data[0]) != 8:
        data[0:2] = [''.join(data[0:2])]
    if len(data[-1]) != 8:
        data[len(data)-2:len(data)] = [''.join(data[len(data)-2:len(data)])]
    data1 = [int(byte[::-1],2) for byte in data] 
    data = bytearray(data1)
    s = s7.write_area(snap7.types.areas['PA'], 0, start, data)    
    print GREEN + "[+] " + CRESET  + DATA + " has been written correctly from address " + ADDRESS 
