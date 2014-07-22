#! /bin/bash
#
PROG="$(basename $0)"

usage () {
cat <<EOF
Usage: $PROG PATH VERSION

Release the sources at PATH  as gc3pie-VERSION.
In detail, this does the following:
  - checks that there are no uncommitted changes
  - commits BRANCH to tags/VERSION
  - sets the '__version__' attribute in every module to VERSION;
  - updates the documentation
  - checks that ./setup.py can build the package
  - commits the sources to SVN
  - uploads the source package to PyPI

Options:

  --help, -h  Print this help text.

EOF
}


## helper functions
die () {
  rc="$1"
  shift
  (echo -n "$PROG: ERROR: ";
      if [ $# -gt 0 ]; then echo "$@"; else cat; fi) 1>&2
  exit $rc
}

have_command () {
  type "$1" >/dev/null 2>/dev/null
}

require_command () {
  if ! have_command "$1"; then
    die 1 "Could not find required command '$1' in system PATH. Aborting."
  fi
}

is_absolute_path () {
    expr match "$1" '/' >/dev/null 2>/dev/null
}


## environment check

require_command dot
require_command egrep
require_command getopt
require_command make
require_command pyreverse
require_command python
require_command svn

python -c 'import sphinx' \
    || die 1 "Cannot load required Python module 'sphinx'"

python -c 'import sphinx_pypi_upload' \
    || die 1 "Cannot load required Python module 'sphinx_pypi_upload'"


## parse command-line

maybe=""
debug=""

if [ "x$(getopt -T)" == 'x--' ]; then
    # old-style getopt, use compatibility syntax
    set -- $(getopt 'hnx' "$@")
else
    # GNU getopt
    set -- $(getopt --shell sh -l 'help,test,debug,just-print' -o 'hnx' -- "$@")
fi
while [ $# -gt 0 ]; do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --debug|-x) debug=yes ;;
        --just-print|--test|-n) maybe='echo' ;;
        --) shift; break ;;
    esac
    shift
done

eval branch=$1
if [ -z "$branch" ]; then
    echo 1>&2 "Missing 1st argument BRANCH"
    usage; exit 1;
fi
branch=$(echo $branch | sed -e 's|/*$||;')

eval version=$2
if [ -z "$version" ]; then
    echo 1>&2 "Missing 2nd argument VERSION"
    usage; exit 1;
fi


## main

if [ -n "$debug" ]; then
    set -x
fi

pushd $branch \
    || die 1 "Cannot change directory to branch '$branch'"

echo Checking that there are no uncommitted changes ...
svn_st=$(svn status --ignore-externals | egrep -v '^[IX?]')
if [ -n "$svn_st" ]; then
    die 1 "There are uncommitted changes in SVN tree (run 'svn status' to check); cannot continue."
fi

popd
echo Creating "$version" tag
$maybe svn cp $branch tags/$version
set +e

pushd tags/$version \
    || die 1 "Cannot change directory to tag tags/$version"


echo Setting the '__version__' attribute in every module to $version ...
set -e
find gc3pie -name '*.py' \
    | xargs egrep -l '^__version__ *=' \
    | xargs $maybe sed -i -r -e "s|__version__ *= *'[0-9a-z\\.\-]+ *|__version__ = '$version |;"
$maybe sed -i -r -e "s|version *= *[0-9a-z\\.\"'\-]+|version = '$version'|;" \
    gc3pie/setup.py
sed -i -e "s|release *= *[0-9a-z\\.\"'\-]+|release = '$version'|;" gc3pie/docs/conf.py
set +e


echo Updating HTML documentation ...
if ! (cd gc3pie/docs; $maybe make html); then
    die 1 "Could not update documentation."
fi


echo Checking that ./setup.py can build the package ...
if ! (cd gc3pie; ./setup.py sdist); then
    die 1 "Could not build the python package with './setup.py sdist'."
fi

echo Committing sources to SVN and creating "$version" tag ...
set -e
$maybe svn commit -m"Tagged branch '$branch' to 'tags/$version'"


echo Uploading source package to PyPI ...
(cd gc3pie; $maybe ./setup.py sdist upload)

echo Uploading documentation to PyPI ...
(cd gc3pie; $maybe ./setup.py upload_sphinx)
echo "All done: released '$branch' as GC3Pie '$version' ${maybe+(nah, joking...)}"
exit 0
