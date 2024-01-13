# ZynSeq utils

ZynSeq utils are Python modules in order to facilitate remote / experimental sequencing (on Linux) for the Zynthian open synth platform. It uses the 'zynseq' C++ library written by Brian Walton.

It supports phrase extraction from renoise files (xrns) and zynthian snapshot (zss) imports and exports.

## Installing dependencies

`source requirements.sh`
`pip install -r requirements.txt`

This compiles the zynseq library and installs basic dependencies.
Change the configuration according to your needs (core/config.py).

## Renoise bridge

### Usage

If no arguments are given, it will constantly monitor the changes in the standard XRNS folder (preconfigured in config.py):

`python bridge.py`

Example to manually convert and upload a project
(imports phrases from test.xrns and uploads a ZSS to zynthian):

`python bridge.py test.xrns --upload 002`

## Interactive CLI

Experimental command line interface for managing zss and xrns files.

### Usage

`python cli.py`
`python cli.py --simple`

### Notes

To use audio playback, we need to install LinuxSampler too and copy the necessary sound samples into the folder defined in config (PATH_SAMPLES)
