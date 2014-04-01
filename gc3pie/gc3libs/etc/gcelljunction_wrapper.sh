#!/bin/bash
#
# gcelljunction_wrapper.sh -- base wrapper script for executing
# 'tricellular_junctions' MATLAB code
#
# Authors: Riccardo Murri <riccardo.murri@uzh.ch>,
#          Sergio Maffioletti <sergio.maffioletti@gc3.uzh.ch>
#
# Copyright (c) 2013-2014 GC3, University of Zurich, http://www.gc3.uzh.ch/
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
me=$(basename "$0")

## defaults

exe="$HOME/bin/tricellular_junctions"
mcr_root=/usr/local/MATLAB/R2012a


## helper functions

function die () {
    rc="$1"
    shift
    (echo -n "$me: ERROR: ";
        if [ $# -gt 0 ]; then echo "$@"; else cat; fi) 1>&2
    exit $rc
}


## usage info

usage () {
    cat <<__EOF__
Usage:
  $me [options] SIM_NO

Run the 'tricellular_junctions' code with parameter set SIM_NO.

Options:
  -x EXE	Path to alternate 'tricellular_junctions' binary executable (default: '$exe')
  -m PATH       Path to alternate MATLAB installation directory (default: '$mcr_root')
  -d            Enable debugging logging

__EOF__
}


## parse command-line

# since SIM_NO might be the number `-1` or `-2`, we need to prevent
# `getopt` from treating it as an option, so stop parsing at the first
# non-option argument
export POSIXLY_CORRECT=1

short_opts='dhm:x:'
long_opts='debug,executable:,matlab-root:,help'

if [ "x$(getopt -T)" != 'x--' ]; then
    # GNU getopt
    args=$(getopt --name "$me" --shell sh -l "$long_opts" -o "$short_opts" -- "$@")
    if [ $? -ne 0 ]; then
        die 1 "Type '$me --help' to get usage information."
    fi
    # use 'eval' to remove getopt quoting
    eval set -- $args
else
    # old-style getopt, use compatibility syntax
    args=$(getopt "$short_opts" "$@")
    if [ $? -ne 0 ]; then
        die 1 "Type '$me --help' to get usage information."
    fi
    set -- $args
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --executable|-x)  exe="$2"; shift ;;
        --matlab-root|-m) mcr_root="$2"; shift ;;
        --debug|-d)       set -x ;;
        --help|-h)        usage; exit 0 ;;
        --)               shift; break ;;
    esac
    shift
done

unset POSIXLY_CORRECT


# sanity check: the SIM_NO argument has to be present
if [ $# -lt 1 ]; then
    die 1 "Missing required argument SIM_NO. Type '$me --help' to get usage help."
fi


echo "=== Starting at `date '+%Y-%m-%d %H:%M:%S'`"

# echo configuration
echo -n "=== checking exe: ${exe} -- "
if [ -r ${exe} ]; then
    echo -n "present, "
else
    echo "NOT FOUND"
    exit 127 # Command not found
fi
if [ -x ${exe} ]; then
    echo "executable"
else
    echo "NOT EXECUTABLE"
    exit 126
fi


# run script
echo "=== Running: ${exe} $@"
# XXX: this is already done by the wrapper script `run_....sh`
# generated by the MatLab compiler, so we should rely on that and not
# duplicate code here.
LD_LIBRARY_PATH=.:${mcr_root}/runtime/glnxa64
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${mcr_root}/bin/glnxa64
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${mcr_root}/sys/os/glnxa64
mcr_jre=${mcr_root}/sys/java/jre/glnxa64/jre/lib/amd64
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${mcr_jre}/native_threads
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${mcr_jre}/server
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${mcr_jre}/client
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${mcr_jre}
export LD_LIBRARY_PATH
XAPPLRESDIR=${mcr_root}/X11/app-defaults
export XAPPLRESDIR
${exe} "$@"
rc=$?

echo "=== Simulation ended with exit code $rc"

# Prepare result
echo "=== Done at `date '+%Y-%m-%d %H:%M:%S'`."

exit $rc
