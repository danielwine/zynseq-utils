#!/usr/bin/env bash

# rsync -azPr --exclude="node_modules" --delete-after . performer@performer.local:~/performer/
rsync -azPr --exclude="node_modules" --delete-after . root@zynthian.local:~/zynseq-utils/
