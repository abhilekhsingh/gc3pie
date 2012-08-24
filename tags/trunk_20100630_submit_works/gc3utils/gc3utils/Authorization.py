import Default
import utils
import sys
import os
import Exceptions

import gc3utils


class Auth(object):
    def __init__(self,auto_enable=True):
        self.auto_enable=True
        self.__auths = { }

    def get(self,auth_type):
        if not self.__auths.has_key(auth_type):
            if auth_type is Default.SMSCG_AUTHENTICATION:
                a = ArcAuth()
            elif auth_type is Default.SSH_AUTHENTICATION:
                a = SshAuth()
            elif auth_type is Default.NONE_AUTHENTICATION:
                a = NoneAuth()
            else:
                raise Exception("Invalid auth_type in Auth()")

            if not a.check():
                if self.auto_enable:
                    try:
                        a.enable()
                    except Exception, x:
                        a = x
                else:
                    a = Exceptions.AuthenticationException()
            self.__auths[auth_type] = a

        a = self.__auths[auth_type]
        if isinstance(a, Exception):
            raise a
        return a

class ArcAuth(object):
                
    def check(self):
        gc3utils.log.debug('Checking authentication: GRID')
        try:
            if (utils.check_grid_authentication()) and (utils.check_user_certificate()):
                return True
        except:
            gc3utils.log.error('Authentication Error: %s', sys.exc_info()[1])
        
        return False
     
    def enable(self):
        try:
            # Get AAI username
            _aaiUserName = None
                
            Default.AAI_CREDENTIAL_REPO = os.path.expandvars(Default.AAI_CREDENTIAL_REPO)
            gc3utils.log.debug('checking AAI credential file [ %s ]',Default.AAI_CREDENTIAL_REPO)
            try: 
                _fileHandle = open(Default.AAI_CREDENTIAL_REPO,'r')
                _aaiUserName = _fileHandle.read()
                _fileHandle.close()
                _aaiUserName = _aaiUserName.rstrip("\n")
                gc3utils.log.debug('_aaiUserName: %s',_aaiUserName)
            except IOError:
                gc3utils.log.error('Failed opening AAI credential file') 

            # Renew credential
            return utils.renew_grid_credential(_aaiUserName)

        except:
            gc3utils.log.critical('Failed renewing grid credential [%s]',sys.exc_info()[1])
            # return False
            raise Exceptions.AuthenticationException('failed renewing GRID credential')


class SshAuth(object):
    def check(self):
        return True
    def enable(self):
        return True


class NoneAuth(object):
    def check(self):
        return True

    def enable(self):
        return True

    
    
    
        