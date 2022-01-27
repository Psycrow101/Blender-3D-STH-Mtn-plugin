import struct


def read_uint8(fd, num=1):
    res = struct.unpack('%dB' % num, fd.read(1 * num))
    return res if num > 1 else res[0]


def read_uint16(fd, num=1, en='<'):
    res = struct.unpack('%s%dH' % (en, num), fd.read(2 * num))
    return res if num > 1 else res[0]


def read_float16(fd, num=1, en='<'):
    res = struct.unpack('%s%de' % (en, num), fd.read(2 * num))
    return res if num > 1 else res[0]


def read_uint32(fd, num=1, en='<'):
    res = struct.unpack('%s%dI' % (en, num), fd.read(4 * num))
    return res if num > 1 else res[0]


def read_float32(fd, num=1, en='<'):
    res = struct.unpack('%s%df' % (en, num), fd.read(4 * num))
    return res if num > 1 else res[0]


def read_string(fd, strlen=0):
    if strlen == 0:
        strlen = 1
        start = fd.tell()
        while fd.read(1) != b'\x00':
            strlen += 1
        fd.seek(start)

    return fd.read(strlen).replace(b'\x00', b'').decode('utf-8')


def _write_val(fd, vals, t, en='<'):
    data = vals if hasattr(vals, '__len__') else (vals, )
    data = struct.pack('%s%d%s' % (en, len(data), t), *data)
    fd.write(data)


def write_uint8(fd, vals):
    _write_val(fd, vals, 'B')


def write_uint16(fd, vals, en='<'):
    _write_val(fd, vals, 'H', en)


def write_float16(fd, vals, en='<'):
    _write_val(fd, vals, 'e', en)


def write_uint32(fd, vals, en='<'):
    _write_val(fd, vals, 'I', en)


def write_string(fd, val, strlen=0):
    if strlen > 0:
        nulls = strlen - len(val)
    else:
        nulls = 1
    fd.write(val.encode('utf-8') + b'\x00' * nulls)
