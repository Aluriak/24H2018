#!/bin/bash
DIR=$(dirname $0)
python3 "$DIR"/prod.py < /dev/stdin
