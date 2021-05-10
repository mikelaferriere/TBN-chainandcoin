#!/usr/bin/env python3
"""
https://ethereum-classic-guide.readthedocs.io/en/latest/docs/appendices/recursive_length_prefix.html
"""

import math

N_BITS_PER_BYTE = 8

def n_bytes(integer):
    """
    Finds the numbers of bytes needed to represent integers.
    """

    return math.ceil(integer.bit_length() / N_BITS_PER_BYTE)

def get_len(input, extra):
    """
    Finds the lengths of the longest inputs using the given extra values.
    """

    n_bytes = input[0] - extra

    return 1 + n_bytes + int.from_bytes(input[2:2 + n_bytes], "big")

def rlp_encode(input):
    """
    Recursive Length Prefix encodes inputs.
    """

    if isinstance(input, bytes):
        body = input
        if   (len(body) == 1) and (body[0] < 128):
            header = bytes([])
        elif len(body) < 56:
            header = bytes([len(body) + 128])
        else:
            len_   = len(body)
            len_   = len_.to_bytes(n_bytes(len_), "big")
            header = bytes([len(len_) + 183]) + len_
        result = header + body
    else:
        body = bytes([])
        for e in input:
            body += rlp_encode(e)
        if len(body) < 56:
            header = bytes([len(body) + 192])
        else:
            len_   = len(body)
            len_   = len_.to_bytes(n_bytes(len_), "big")
            header = bytes([len(len_) + 247]) + len_
        result = header + body

    return result

def rlp_decode(input):
    """
    Recursive Length Prefix decodes inputs.
    """

    if input[0] < 128:
        result = input
    elif input[0] < 184:
        result = input[1:]
    elif input[0] < 192:
        result = input[1 + (input[0] - 183):]
    else:
        result = []
        if input[0] < 248:
            input = input[1:]
        else:
            input = input[1 + (input[0] - 247):]
        while input:
            if   input[0] < 128:
                len_ = 1
            elif input[0] < 184:
                len_ = 1 + (input[0] - 128)
            elif input[0] < 192:
                len_ = get_len(input, 183)
            elif input[0] < 248:
                len_ = 1 + (input[0] - 192)
            else:
                len_ = get_len(input, 247)
            result.append(rlp_decode(input[:len_]))
            input = input[len_:]

    return result
