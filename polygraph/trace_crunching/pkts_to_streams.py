#!/usr/bin/env python
#      Polygraph (release 0.1)
#      Signature generation algorithms for polymorphic worms
#
#      Copyright (c) 2004-2005, Intel Corporation
#      All Rights Reserved
#
#  This software is distributed under the terms of the Eclipse Public
#  License, Version 1.0 which can be found in the file named LICENSE.
#  ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS SOFTWARE CONSTITUTES
#  RECIPIENT'S ACCEPTANCE OF THIS AGREEMENT

from __future__ import division
from __future__ import generators
import pcap
import sys
import string

def parse_ip4(hdr, offset):
    import struct
    rv = {}
    (version_plus_ihl, rv['tos'], rv['total_len'], rv['id'], flags_plus_offset, 
     rv['ttl'], rv['protocol'], rv['chksum'], rv['src'], rv['dst']) = \
    struct.unpack('>BBHHHBBHLL', hdr[offset:offset+20])
    rv['version'] = version_plus_ihl >> 4
    rv['ihl'] = version_plus_ihl & 0x0f
    rv['flags'] = flags_plus_offset >> 13
    rv['offset'] = flags_plus_offset & 0x1fff
    return rv

def parse_tcp(hdr, offset):
    import struct
    rv = {}
    (rv['src'], rv['dst'], rv['seq'], rv['ack_num'], offset_reserved,
     reserved_flags, rv['window'], rv['chksum'], rv['urgent_ptr']) = \
    struct.unpack('>HHLLBBHHH', hdr[offset:offset+20])
    rv['offset'] = offset_reserved >> 4
    rv['flags'] = reserved_flags & 0x3F
    return rv

def parse_udp(hdr, offset):
    import struct
    rv = {}
    (rv['src'], rv['dst'], rv['len'], rv['chksum']) = \
    struct.unpack('>HHHH', hdr[offset:offset+8])
    return rv

def _get_next_pkt(tracer, save_data):
    while True:
        (pktlen, raw_packet, ts) = tracer.next()
        if raw_packet == None:
            return None
        offset = 14
        ip4 = parse_ip4(raw_packet, offset)
        assert(ip4['version'] == 4)
        data_len = ip4['total_len'] - ip4['ihl']*4
        offset += ip4['ihl']*4
        if ip4['protocol'] == 6: # tcp
            tcp = parse_tcp(raw_packet, offset)
            offset += 4 * tcp['offset']
            data_len -= 4 * tcp['offset'] # subtract tcp header length
            src_port = tcp['src']
            dst_port = tcp['dst']
            type = "tcp"
            if tcp['flags'] & 4:
                status = "rst"
            elif tcp['flags'] & 1:
                status = "fin"
            else:
                status = "open"
        elif ip4['protocol'] == 17: # udp
            udp = parse_udp(raw_packet, offset)
            data_len -= 8 # subtract udp header length
            src_port = udp['src']
            dst_port = udp['dst']
            type = "udp"
            status = "udp"
        else: # not tcp or udp, grab the next packet instead
            continue
        break # got a tcp or udp packet, process and return

    # src ip, dst ip, src port, dst port
    connection = (ip4['src'], ip4['dst'], src_port, dst_port)
    pkt = {"connection": connection,
            "ts": [ts],
            "type": type,
            "status": status,
            "pkts": 1}

    if save_data:
        pkt["data"] = list(raw_packet[offset:offset+data_len])
    else:
        pkt["data"] = []

    return pkt

def print_stream(stream):
    """Print streams"""
    print "%s Connection: (%s)" % (stream["type"], stream["status"]), 
    print stream["connection"]
    print "Timestamps: ",
    print stream["ts"]
    print "Packet Count: ",
    print stream["pkts"]
    print "Data:\n" + stream["data"].__repr__()
#    print_stream.count -= 1
#    if print_stream.count <= 0:
#        raise IndexError
#print_stream.count = 10

def process_trace(trace_name, callback=print_stream, timeout=2000, filter=None,
                    save_data=True):
    """
    Process all the streams in the libpcap file

    trace_name is the name of the libpcap file to open and process.
    callback should take a stream as its only positional argument.
    timeout is the number of seconds without seeing a packet before
    considering a connection closed and processing the corresponding
    stream.

    The stream passed to callback is a dictionary with the following keys:
    connection: (src ip, dst ip, src port, dst port)
    data: string containing the reassembled stream
    ts: sequence of packet time stamps
    pkts: packet count

    callback may raise an IndexError exception to halt processing
    of the trace.
    """

    streams = [] # stream q - most recent at 0
    now = 0          # current time
    tracer = pcap.pcapObject() # libpcap trace object

    tracer.open_offline(trace_name)
    if filter:
        tracer.setfilter(filter, True, 0xffffff00L)

    while(True):
        pkt = _get_next_pkt(tracer, save_data)
        if(pkt == None):
            break

        now = pkt["ts"][-1]

        # process udp packets individually
        if(pkt["type"] == "udp"):
            pkt["data"] = "".join(pkt["data"])
            try: callback(pkt)
            except IndexError:
                return
            continue

        for i in xrange(len(streams)):
            stream = streams[i]
            if stream["connection"] == pkt["connection"]:
                # already have pkts in this connection.
                # update and process if connection is closed,
                # or put at beginning of q (if con still open)
                stream["data"].extend(pkt["data"])
                stream["status"] = pkt["status"]
                stream["ts"].append(pkt["ts"][-1])
                stream["pkts"] += 1
                del(streams[i])
                if stream["status"] == "fin" or stream["status"] == "rst":
                    stream["data"] = "".join(stream["data"])
                    try: callback(stream)
                    except IndexError:
                        return
                else:
                    streams.insert(0, stream)
                break
        else:
            # new connection. insert into q if data length > 0
            if len(pkt["data"]) > 0:
                streams.insert(0, pkt)

        # process any timed out connections
        while len(streams) > 0 and now - streams[-1]["ts"][-1] > timeout:
            # remove from q
            stream = streams[-1]
            del(streams[-1])
            stream["status"] = "timeout"
            stream["data"] = "".join(stream["data"])
            try: callback(stream)
            except IndexError:
                return

    # no more packets- finish processing streams
    while len(streams) > 0:
        # remove from q
        stream = streams[-1]
        del(streams[-1])
        stream["data"] = "".join(stream["data"])
        try: callback(stream)
        except IndexError:
            return

if __name__ == "__main__":
    assert len(sys.argv) > 1
    for fname in sys.argv[1:]:
        process_trace(fname)
