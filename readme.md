# Motion Transfer

## Introduction

Motion Transfer is a Blender addon which enables an average user to easily transfer animations between similar rigs that have different bone orientations.

## Installation


1. Download this repository as a zip
[Download 2.8+](https://github.com/hampta/Motion-Transfer/archive/refs/heads/master.zip)
[Download 2.79](https://github.com/hampta/Motion-Transfer/archive/refs/heads/2.79.zip)
2. Install and open Blender, preferably 2.79 or later.
2. Go to User Preferences, and then Addons.
3. Using the "install from file" dialogue, pick the zip you downloaded.
4. Make sure the checkbox to enable it is checked
5. Save user preferences

## Tutorial

1. Align the T-Poses:
	* Pose your transfer target to match the T-Pose of your source
	* Apply armature modifiers on your target objects where necessary
	* Apply said pose as a reference
2. Select the source armature
3. Select the target armature
4. Using the spacebar search menu, run Motion Transfer
5. Tweak your parameters.  If your bone names don't match, you can use a position based search to select the nearest bone in a given radius, excluding the blacklist.
6. Run, give it some time, and enjoy!