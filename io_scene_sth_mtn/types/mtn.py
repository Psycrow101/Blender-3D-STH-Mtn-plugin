from os import SEEK_SET, SEEK_CUR
from dataclasses import dataclass
from typing import List
from . binary_utils import *


@dataclass
class Keyframe:
    time: int
    key_type: int
    tan_type: int
    tan1: float
    tan2: float
    val: float

    @classmethod
    def read(cls, fd, endian, key_type):
        v = read_uint16(fd, 1, endian)
        tan_type = v >> 14
        time = v & 0x3fff

        if tan_type > 1:
            tan1, val = read_float16(fd, 2, endian)
            tan2 = 0.0
        else:
            tan1, tan2, val = read_float16(fd, 3, endian)

        return cls(time=time,
            key_type=key_type,
            tan_type=tan_type,
            tan1=tan1,
            tan2=tan2,
            val=val)


    def write(self, fd, endian):
        write_uint16(fd, (self.time & 0x3fff) | (self.tan_type << 14), endian)
        if self.tan_type > 1:
            write_float16(fd, (self.tan1, self.val), endian)
        else:
            write_float16(fd, (self.tan1, self.tan2, self.val), endian)


@dataclass
class BoneMotion:
    bone_id: int
    keyframes: List[Keyframe]


@dataclass
class Mtn:
    model_name: str
    duration: int
    bone_motions: List[BoneMotion]

    @classmethod
    def read(cls, fd):
        magic = read_uint8(fd)
        endian = '<' if read_uint8(fd) == 0 else '>'
        fd.seek(0x6, SEEK_CUR)
        file_size = read_uint32(fd, 1, endian)
        fd.seek(0x6, SEEK_CUR)
        duration = read_uint16(fd, 1, endian)
        model_name = read_string(fd, 0x20)

        mtn = cls(model_name, duration, [])

        key_type = 3
        bone_id = 0
        bone_motion = BoneMotion(bone_id, [])

        while fd.tell() < file_size:
            if key_type >= 12:
                key_type = 0
                bone_id += 1
                mtn.bone_motions.append(bone_motion)
                bone_motion = BoneMotion(bone_id, [])

            struct_start = fd.tell()

            struct_len = read_uint32(fd, 1, endian)
            keyframes_num = read_uint16(fd, 1, endian)
            padding, strip = read_uint8(fd, 2)

            bone_motion.keyframes += [Keyframe.read(fd, endian, key_type) for _ in range(keyframes_num)]

            fd.seek(struct_start + struct_len, SEEK_SET)
            key_type += 1

        if bone_motion.keyframes:
            mtn.bone_motions.append(bone_motion)

        return mtn


    def write(self, fd, endian):
        write_uint8(fd, 0x4)
        write_uint8(fd, 0x1 if endian == '>' else 0x0)
        write_uint16(fd, 0x0, endian)
        write_uint32(fd, 0x0, endian)
        write_uint32(fd, 0x0, endian) # file_size fill later
        write_uint8(fd, (0xff, 0x07))
        write_uint16(fd, (0x0, 0x0), endian)
        write_uint16(fd, self.duration, endian)
        write_string(fd, self.model_name, 0x20)

        last_strip_addr = None
        for bone_motion in self.bone_motions:
            for keyframes in [[kf for kf in bone_motion.keyframes if kf.key_type == kt] for kt in range(12)]:
                keyframes_num = len(keyframes)
                if not keyframes_num:
                    continue

                struct_len = 8
                for kf in keyframes:
                    struct_len += 6 if kf.tan_type > 1 else 8
                padding = struct_len % 4
                struct_len += padding

                write_uint32(fd, struct_len, endian)
                write_uint16(fd, keyframes_num, endian)
                write_uint8(fd, padding)
                last_strip_addr = fd.tell()
                write_uint8(fd, 1)

                for kf in keyframes:
                    kf.write(fd, endian)
                fd.write(b'\x00' * padding)

        file_size = fd.tell()
        fd.seek(0x8, SEEK_SET)
        write_uint32(fd, file_size, endian)

        if last_strip_addr:
            fd.seek(last_strip_addr, SEEK_SET)
            write_uint8(fd, 0)


    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as fd:
            return cls.read(fd)


    def save(self, filepath, endian):
        with open(filepath, 'wb') as fd:
            return self.write(fd, endian)
