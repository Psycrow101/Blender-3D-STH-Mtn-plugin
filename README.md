# io_scene_sth_mtn

This plugin for Blender 3D allows you to import and export animations (`.mtn` or `.STHanim`) for Shadow the Hedgehog. Based on [Shadow-the-Hedgehog-.BON-MTN-import-export-tool](https://github.com/Shadowth117/Shadow-the-Hedgehog-.BON-MTN-import-export-tool).

Poorly tested and made just for fun. Keyframes are created on empty objects that transform the pose bones (it is not comfortable).

## How to import animation
1. Import DFF model into Blender
2. Make armature active
3. Import BON skeleton
4. Make _bon_root_ object active
5. Imort MTN animation

## Animation editing
If you want to make changes to export to MTN, you need to manipulate only the created objects from the BON collection. In other cases, you can remove the entire BON collection hierarchy and work directly on the armature bones. Make sure the "Bake action" option was enabled when importing so that the keyframes are applied to the armature bones.

## Requirements

* Blender 3D (2.81 and higher)
* [DragonFF](https://github.com/Parik27/DragonFF)
