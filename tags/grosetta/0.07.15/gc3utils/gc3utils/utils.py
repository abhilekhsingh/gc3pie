import sys
import os
import os.path
import commands
import logging
import logging.handlers
import tempfile
import getpass
import re
import time
import ConfigParser
import shutil
import getpass
#import smtplib
import subprocess
#from email.mime.text import MIMEText
sys.path.append('/opt/nordugrid/lib/python2.4/site-packages')
import warnings
warnings.simplefilter("ignore")
from arclib import *
from Exceptions import *
import Default
import gc3utils
from lockfile import FileLock
import shelve


    

# ================================================================
#
#                     Generic functions
#
# ================================================================

class defaultdict(dict):
    """
    A backport of `defaultdict` to Python 2.4
    See http://docs.python.org/library/collections.html
    """
    def __new__(cls, default_factory=None):
        return dict.__new__(cls)
    def __init__(self, default_factory):
        self.default_factory = default_factory
    def __missing__(self, key):
        try:
            return self.default_factory()
        except:
            raise KeyError("Key '%s' not in dictionary" % key)
    def __getitem__(self, key):
        if not dict.__contains__(self, key):
            dict.__setitem__(self, key, self.__missing__(key))
        return dict.__getitem__(self, key)


class Struct(dict):
    """
    A `dict`-like object, whose keys can be accessed with the usual
    '[...]' lookup syntax, or with the '.' get attribute syntax.

    Examples::

      >>> a = Struct()
      >>> a['x'] = 1
      >>> a.x
      1
      >>> a.y = 2
      >>> a['y']
      2

    Values can also be initially set by specifying them as keyword
    arguments to the constructor::

      >>> a = Struct(z=3)
      >>> a['z']
      3
      >>> a.z
      3
    """
    def __init__(self, initializer=None, **kw):
        if initializer is None:
            dict.__init__(self, **kw)
        else:
            dict.__init__(self, initializer, **kw)
    def __setattr__(self, key, val):
        self[key] = val
    def __getattr__(self, key):
        if self.has_key(key):
            return self[key]
        else:
            raise AttributeError, "No attribute '%s' on object %s" % (key, self)
    def __hasattr__(self, key):
        return self.has_key(key)


def progressive_number():
    """
    Return a positive integer, whose value is guaranteed to
    be monotonically increasing across different invocations
    of this function, and also across separate instances of the
    calling program.

    Example::

      >>> n = progressive_number()
      >>> m = progressive_number()
      >>> m > n
      True

    After every invocation of this function, the returned number
    is stored into the file ``~/.gc3/next_id.txt``.

    *Note:* as file-level locking is used to serialize access to the
    counter file, this function may block (default timeout: 30
    seconds) while trying to acquire the lock, or raise an exception
    if this fails.
    """
    # FIXME: should use global config value for directory
    id_filename = os.path.expanduser("~/.gc3/next_id.txt")
    # ``FileLock`` requires that the to-be-locked file exists; if it
    # does not, we create an empty one (and avoid overwriting any
    # content, in case another process is also writing to it).  There
    # is thus no race condition here, as we attempt to lock the file
    # anyway, and this will stop concurrent processes.
    if not os.path.exists(id_filename):
        open(id_filename, "a").close()
    lock = FileLock(id_filename, threaded=False) 
    lock.acquire(timeout=30) # XXX: can raise 'LockTimeout'
    id_file = open(id_filename, 'r+')
    id = int(id_file.read(8) or "0", 16)
    id +=1 
    id_file.seek(0)
    id_file.write("%08x -- DO NOT REMOVE OR ALTER THIS FILE: it is used internally by the gc3utils\n" % id)
    id_file.close()
    lock.release()
    return id


def create_unique_token():
    """
    Return a "unique job identifier" (a string).  Job identifiers are 
    temporally unique: no job identifier will (ever) be re-used,
    even in different invocations of the program.

    Currently, the unique job identifier has the form "job.XXX" where
    "XXX" is a decimal number.  
    """
    return "job.%d" % progressive_number()


def dirname(pathname):
    """
    Same as `os.path.dirname` but return `.` in case of path names with no directory component.
    """
    dirname = os.path.dirname(pathname)
    if not dirname:
        dirname = '.'
    # FIXME: figure out if this is a desirable outcome.  i.e. do we want dirname to be empty, or do a pwd and find out what the current dir is, or keep the "./".  I suppose this could make a difference to some of the behavior of the scripts, such as copying files around and such.
    return dirname


def check_jobdir(jobdir):
    """
    Perform various checks on the jobdir.
    Right now we just make sure it exists.  In the future it could include checks for:

    - are the files inside valid
    - etc.
    """

    if os.path.isdir(jobdir):
        return True
    else:
        return False


def check_qgms_version(minimum_version):
    """
    This will check that the qgms script is an acceptably new version.
    This function could also be exanded to make sure gamess is installed and working, and if not recompile it first.
    """
    # todo: fill out this function.
    # todo: add checks to verify gamess is working?

    current_version = 0.1

    # todo: write some function that goes out and determines version

    if minimum_version < current_version:
        gc3utils.log.error('qgms script version is too old.  Please update it and resubmit.')
        return False

    return True


def deploy_configuration_file(filename, template_filename=None):
    """
    Ensure that configuration file `filename` exists; possibly
    copying it from the specified `template_filename`.

    Return `True` if a file with the specified name exists in the 
    configuration directory.  If not, try to copy the template file
    over and then return `False`; in case the copy operations fails, 
    a `NoConfigurationFile` exception is raised.

    If parameter `filename` is not an absolute path, it is interpreted
    as relative to `gc3utils.Default.RCDIR`; if `template_filename` is
    `None`, then it is assumed to be the same as `filename`.
    """
    if template_filename is None:
        template_filename = os.path.basename(filename)
    if not os.path.isabs(filename):
        filename = os.path.join(Default.RCDIR, filename)
    if os.path.exists(filename):
        return True
    else:
        try:
            # copy sample config file 
            if not os.path.exists(dirname(filename)):
                os.makedirs(dirname(filename))
            from pkg_resources import Requirement, resource_filename
            sample_config = resource_filename(Requirement.parse("gc3utils"), 
                                              "gc3utils/etc/" + template_filename)
            import shutil
            shutil.copyfile(sample_config, filename)
            return False
        except IOError, x:
            gc3utils.log.critical("CRITICAL ERROR: Failed copying configuration file: %s" % x)
            raise NoConfigurationFile("No configuration file '%s' was found, and an attempt to create it failed. Aborting." % filename)
        except ImportError:
            raise NoConfigurationFile("No configuration file '%s' was found. Aborting." % filename)


def from_template(template, **kw):
    """
    Return the contents of `template`, substituting all occurrences
    of Python formatting directives '%(key)s' with the corresponding values 
    taken from dictionary `kw`.

    If `template` is an object providing a `read()` method, that is
    used to gather the template contents; else, if a file named
    `template` exists, the template contents are read from it;
    otherwise, `template` is treated like a string providing the
    template contents itself.
    """
    if hasattr(template, 'read') and callable(template.read):
        template_contents = template.read()
    elif os.path.exists(template):
        template_file = file(template, 'r')
        template_contents = template_file.read()
        template_file.close()
    else:
        # treat `template` as a string
        template_contents = template
    # substitute `kw` into `t` and return it
    return (template_contents % kw)


def to_bytes(s):
    """
    Convert string `s` to an integer number of bytes.  Suffixes like
    'KB', 'MB', 'GB' (up to 'YB'), with or without the trailing 'B',
    are allowed and properly accounted for.  Case is ignored in
    suffixes.

    Examples::

      >>> to_bytes('12')
      12
      >>> to_bytes('12B')
      12
      >>> to_bytes('12KB')
      12000
      >>> to_bytes('1G')
      1000000000

    Binary units 'KiB', 'MiB' etc. are also accepted:

      >>> to_bytes('1KiB')
      1024
      >>> to_bytes('1MiB')
      1048576

    """
    last = -1
    unit = s[last].lower()
    if unit.isdigit():
        # `s` is a integral number
        return int(s)
    if unit == 'b':
        # ignore the the 'b' or 'B' suffix
        last -= 1
        unit = s[last].lower()
    if unit == 'i':
        k = 1024
        last -= 1
        unit = s[last].lower()
    else:
        k = 1000
    # convert the substring of `s` that does not include the suffix
    if unit.isdigit():
        return int(s[0:(last+1)])
    if unit == 'k':
        return int(float(s[0:last])*k)
    if unit == 'm':
        return int(float(s[0:last])*k*k)
    if unit == 'g':
        return int(float(s[0:last])*k*k*k)
    if unit == 't':
        return int(float(s[0:last])*k*k*k*k)
    if unit == 'p':
        return int(float(s[0:last])*k*k*k*k*k)
    if unit == 'e':
        return int(float(s[0:last])*k*k*k*k*k*k)
    if unit == 'z':
        return int(float(s[0:last])*k*k*k*k*k*k*k)
    if unit == 'y':
        return int(float(s[0:last])*k*k*k*k*k*k*k*k)

 
# === Configuration File
def import_config(config_file_location, auto_enable_auth=True):
    (default_val,resources_vals) = read_config(config_file_location)
    return (get_defaults(default_val),
            get_resources(resources_vals),
            auto_enable_auth)

def get_defaults(defaults):
    # Create an default object for the defaults
    # defaults is a list[] of values
    try:
        # Create default values
        default = gc3utils.Default.Default(defaults)
    except:
        gc3utils.log.critical('Failed loading default values')
        raise
        
    return default
    

def get_resources(resources_list):
    # build Resource objects from the list returned from read_config
    #        and match with selectd_resource from comand line
    #        (optional) if not options.resource_name is None:
    resources = []
    
    try:
        for resource in resources_list:
            gc3utils.log.debug('creating instance of Resource object... ')

            try:
                tmpres = gc3utils.Resource.Resource(resource)
            except:
                gc3utils.log.error("rejecting resource '%s'",resource['name'])
                #                gc3utils.log.warning("Resource '%s' failed validity test - rejecting it.",
                #                                     resource['name'])

                continue
#            tmpres = gc3utils.Resource.Resource()
                
#            tmpres.update(resource)
            #            for items in resource:
            #                gc3utils.log.debug('Updating with %s %s',items,resource[items])
            #                tmpres.insert(items,resource[items])
            
            gc3utils.log.debug('Checking resource type %s',resource['type'])
            if resource['type'] == 'arc':
                tmpres.type = gc3utils.Default.ARC_LRMS
            elif resource['type'] == 'ssh_sge':
                tmpres.type = gc3utils.Default.SGE_LRMS
            else:
                gc3utils.log.error('No valid resource type %s',resource['type'])
                continue
            
            gc3utils.log.debug('checking validity with %s',str(tmpres.is_valid()))
            
            resources.append(tmpres)
    except:
        gc3utils.log.critical('failed creating Resource list')
        raise
    
    return resources

                                
def read_config(config_file_location):
    """
    Read configuration file.
    """

    resource_list = []
    defaults = {}

#    print 'mike_debug 100'
#    print config_file_location

    _configFileLocation = os.path.expandvars(config_file_location)
    if not deploy_configuration_file(_configFileLocation, "gc3utils.conf.example"):
        # warn user
        raise NoConfigurationFile("No configuration file '%s' was found; a sample one has been copied in that location; please edit it and define resources before you try running gc3utils commands again." % _configFileLocation)

    # Config File exists; read it
    config = ConfigParser.ConfigParser()
    try:
        config_file = open(_configFileLocation)
        config.readfp(config_file)
    except:
        raise NoConfigurationFile("Configuration file '%s' is unreadable or malformed. Aborting." 
                                  % _configFileLocation)

    defaults = config.defaults()

    _resources = config.sections()
    for _resource in _resources:
        _option_list = config.options(_resource)
        _resource_options = {}
        for _option in _option_list:
            _resource_options[_option] = config.get(_resource,_option)
        _resource_options['name'] = _resource
        resource_list.append(_resource_options)

    gc3utils.log.debug('readConfig resource_list length of [ %d ]',len(resource_list))
    return [defaults,resource_list]

def obtain_file_lock(joblist_location, joblist_lock):
    """
    Lock a file.
    """

    # Obtain lock
    lock_obtained = False
    retries = 3
    default_wait_time = 1


    # if joblist_location does not exist, create it
    if not os.path.exists(joblist_location):
        open(joblist_location, 'w').close()
        gc3utils.log.debug(joblist_location + ' did not exist.  created it.')


    gc3utils.log.debug('trying creating lock for %s in %s',joblist_location,joblist_lock)    

    while lock_obtained == False:
        if ( retries > 0 ):
            try:
                os.link(joblist_location,joblist_lock)
                lock_obtained = True
                break
            except OSError:
                # lock already created; wait
                gc3utils.log.debug('Lock already created; retry later [ %d ]',retries)
                time.sleep(default_wait_time)
                retries = retries - 1
            except:
                gc3utils.log.error('failed obtaining lock due to %s',sys.exc_info()[1])
                raise
        else:
            gc3utils.log.error('could not obtain lock for updating list of jobs')
            break

    return lock_obtained

def release_file_lock(joblist_lock):
    """
    Release locked file.
    """

    try:
        os.remove(joblist_lock)
        return True
    except:
        gc3utils.log.debug('Failed removing lock due to %s',sys.exc_info()[1])
        return False

#def send_email(_to,_from,_subject,_msg):
#    try:
#        _message = MIMEText(_msg)
#        _message['Subject'] = _subject
#        _message['From'] = _from
#        _message['To'] = _to
        
#        s = smtplib.SMTP()
#        s.connect()
#        s.sendmail(_from,[_to],_message.as_string())
#        s.quit()
        
#    except:
#        logging.error('Failed sending email [ %s ]',sys.exc_info()[1])


if __name__ == '__main__':
    import doctest
    doctest.testmod()