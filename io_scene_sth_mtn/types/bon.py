from mathutils import Euler, Vector
from os import SEEK_SET, SEEK_CUR
from dataclasses import dataclass
from typing import List, TypeVar
from . binary_utils import *

Bone = TypeVar('Bone')


@dataclass
class Bone:
    name: str
    tag: int
    pos: Vector
    rot: Euler
    scale: Vector
    flag: int
    split_id: int
    param_id: int
    child_offset: int
    sibling_offset: int
    offset: int
    parent: Bone = None

    @classmethod
    def read(cls, fd, endian):
        offset = fd.tell()
        tag = read_int32(fd, 1, endian)
        flag = read_uint16(fd, 1, endian)
        fd.seek(0x4, SEEK_CUR)
        split_id, param_id = read_uint8(fd, 2)
        fd.seek(0x4, SEEK_CUR)
        pos = Vector(read_float32(fd, 3, endian))
        fd.seek(0x4, SEEK_CUR)
        rot = Euler(read_float32(fd, 3, endian), 'XYZ')
        fd.seek(0x4, SEEK_CUR)
        scale = Vector(read_float32(fd, 3, endian))
        fd.seek(0x4, SEEK_CUR)
        fd.seek(0x8, SEEK_CUR)
        child_offset, sibling_offset = read_uint32(fd, 2, endian)
        name = read_string(fd, 0x20)
        return cls(name,
            tag,
            pos, rot, scale,
            flag,
            split_id, param_id,
            child_offset, sibling_offset,
            offset)


@dataclass
class Bon:
    model_name: str
    root_offset: float
    bones: List[Bone]

    @classmethod
    def read(cls, fd):
        fd.seek(0x1, SEEK_SET)
        endian = '<' if read_uint8(fd) == 0 else '>'
        fd.seek(0xa, SEEK_SET)
        bones_num = read_uint16(fd, 1, endian)
        root_offset = read_float32(fd, 1, endian)
        model_name = read_string(fd, 0x20)
        return cls(model_name,
            root_offset,
            [Bone.read(fd, endian) for _ in range(bones_num)])

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as fd:
            return cls.read(fd)


    def find_bone_parents(self):
        def find_bone(bone_offset) -> Bone:
            for b in self.bones:
                if b.offset == bone_offset:
                    return b
            return None

        for bone in self.bones:
            child_offset = bone.child_offset
            while child_offset > 0:
                child_bone = find_bone(child_offset)
                if not child_bone:
                    break
                child_bone.parent = bone
                child_offset = child_bone.sibling_offset
