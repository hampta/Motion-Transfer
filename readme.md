# Motion Transfer

## Introduction

Motion Transfer is a Blender addon which enables an average user to easily transfer animations between similar rigs that have different bone orientations.

## Installation

1. Download this repository as a zip
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
2. Make sure the bone names match -- currently, this is how the addon knows that to transfer.  In the future, I hope to add autodetection.
3. Select the source armature
4. Select the target armature
5. Using the spacebar search menu, run Motion Transfer