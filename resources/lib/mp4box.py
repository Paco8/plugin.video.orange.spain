#!/usr/bin/env python
# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division
import json
import io

def bytes_to_int(byte_array):
    if isinstance(byte_array, str):  # Python 2
        return int(byte_array.encode('hex'), 16)
    else:  # Python 3
        return int.from_bytes(byte_array, byteorder='big', signed=False)


def read_box(data):
    # Lee el tamaño y el tipo de caja
    size_bytes = data.read(4)
    type_bytes = data.read(4)

    if len(size_bytes) < 4 or len(type_bytes) < 4:
        return None, None

    # Convierte el tamaño de bytes a entero sin signo
    size = bytes_to_int(size_bytes)

    # Convierte el tipo de bytes a cadena
    box_type = type_bytes.decode('utf-8')

    return size, box_type


def parse_moof(data):
    box_info = {}

    while True:
        # Lee el tamaño y el tipo de la siguiente caja
        size, box_type = read_box(data)

        if size is None or box_type is None:
            break

        if box_type == "moof":
            box_info[box_type] = parse_moof(data)  # Analiza las cajas dentro de "moof"
        elif box_type == "mfhd":
            # Lee la información específica de la caja "mfhd"
            version = ord(data.read(1))
            flags = data.read(3)
            sequence_number = bytes_to_int(data.read(4))

            box_info[box_type] = {
                "version": version,
                "flags": flags.decode('utf-8'),
                "sequence_number": sequence_number
            }
        else:
            box_info[box_type] = str(size)

        # Mueve el puntero al siguiente inicio de caja
        data.seek(size - 8, io.SEEK_CUR)

    return box_info


def parse_box(data):
    # Crea un objeto de flujo de datos a partir de los datos en la variable
    data_stream = io.BytesIO(data)

    # Analiza los datos del flujo
    return parse_moof(data_stream)

