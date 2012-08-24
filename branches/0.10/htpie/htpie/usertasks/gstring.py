import htpie

from htpie.lib import utils
from htpie.lib.exceptions import *
from htpie import enginemodel as model
from htpie import statemachine
from htpie.application import gamess
from htpie.usertasks import gsingle

from htpie.optimize import fire, lbfgs, neb

import numpy as np
import os
import copy

_app_tag_mapping = dict()
_app_tag_mapping['gamess']=gamess.GamessApplication

class States(statemachine.States):
    WAIT = u'STATE_WAIT'
    PROCESS = u'STATE_PROCESS'
    POSTPROCESS = u'STATE_POSTPROCESS'

class Transitions(statemachine.Transitions):
    pass

class GStringResult(model.EmbeddedDocument):
    gsingle = model.ListField(model.ReferenceField(gsingle.GSingle))
    
class GString(model.Task):
    result = model.ListField(model.EmbeddedDocumentField(GStringResult))
    neb = model.PickleField()
    opt = model.ListField(model.PickleField())
    
    def __str__(self):
        output = 'GString:\n'
        for a_result in self.result:
            for value in a_result.values():
                output +='Path:\n'
                for single in value:
                    output += '%s %s \n %s\n lock: %s\n'%(single.id, single.state, single.job, single['_lock'])
        return output
    
    def retry(self):
        if self.transition == Transitions.ERROR:
            try:
                self.acquire(120)
            except:
                raise
            else:
                self.transition = Transitions.PAUSED
                self.release()
        path = self.result[-1]
        children = path['gsingle']
        for child in children:
            try:
                child.retry()
            except:
                pass

    def kill(self):
        try:
            self.acquire(120)
        except:
            raise
        else:
            self.state = States.KILL
            self.release()
            htpie.log.debug('GString %s will be killed'%(self.id))
            path = self.result[-1]
            children = path['gsingle']
            for child in children:
                try:
                    child.kill()
                except:
                    pass
    
    def display(self, long_format=False):
        output = '%s %s %s %s\n'%(self.cls_name, self.id, self.state, self.transition)
        output += 'Task submitted: %s\n'%(self.create_d)
        output += 'Task last ran: %s\n'%(self.last_exec_d)
        output += 'Delta: %s\n'%(self.last_exec_d - self.create_d)
        if self.transition == Transitions.COMPLETE:
            pass

        def print_path(path):
            output = ''
            path = path['gsingle']
            for child in path:
                output += '%s %s %s %s\n'%(child.cls_name,  child.id, child.state, child.transition)
            return output
        
        if long_format:
            output += 'Child Tasks:\n'
            for i in xrange(len(self.result)):
                output += '-' * 80 + '\n'
                output += 'Path %d:\n'%(i)
                output += print_path(self.result[i])
        else:
            output += 'Last Ran Child Tasks:\n'
            output += 'Path %d:\n'%(len(self.result)-1)
            output += print_path(self.result[-1])
        return output


    @classmethod
    def create(cls, f_list,  app_tag, optimizer, requested_cores=16, requested_memory=2, requested_walltime=2):
        task = super(GString, cls,).create()
        task.app_tag = u'%s'%(app_tag)
        app = _app_tag_mapping[task.app_tag]
        
        a_neb = neb.NEB()
        l_opt = list()
        
        for a_file in f_list:
            task.attach_file(a_file, 'inputs')
        
        atoms_start, params_start = app.parse_input(f_list[0])
        atoms_end, params_end = app.parse_input(f_list[1])
        
        assert params_start == params_end,  'Start and finish need to have the same params.'
        path = neb.interpolate(atoms_start.get_positions(), atoms_end.get_positions())
        
        #Zero out the fire.v matrix
        optimizer.initialize(shape=atoms_start.get_positions().shape)
        
        for i in xrange(len(path)):
            mongo_pickle = model.PickleProxy()
            task.opt.append(mongo_pickle)
            task.opt[i].pickle = copy.deepcopy(optimizer)
        
        l_gsingle = GStringResult(gsingle=_convert_pos_to_jobs(app_tag, atoms_start, params_start, path, requested_cores, requested_memory, requested_walltime))
        task.result.append(l_gsingle)
        task.neb = model.PickleProxy()
        task.neb.pickle = a_neb
        
        task.transition = Transitions.PAUSED
        task.state = States.WAIT
        task.save()
        return task

def _convert_pos_to_jobs(app_tag, atoms_start, params_start, path, requested_cores, requested_memory,  requested_walltime):
        count = 0
        app = _app_tag_mapping[app_tag]
        gsingle_path = list()
        for image in path:
            atoms_start.set_positions(image)
            
            dir = utils.generate_temp_dir()
            f_gimage = '%s/gimage_%d.inp'%(dir, count)
            app.write_input(f_gimage, atoms_start, params_start)
            fsm = gsingle.GSingle.create([f_gimage], app_tag, requested_cores, requested_memory, requested_walltime)
            gsingle_path.append(fsm)
            count += 1
        return gsingle_path

def _str_dict(dic):
        new_dic = {}
        for k, v in dic.items():
            new_dic[str(k)]=v
        return new_dic

class GStringStateMachine(statemachine.StateMachine):
    _cls_task = GString
    
    def __init__(self):
        super(GStringStateMachine, self).__init__()
        self.state_mapping.update({States.WAIT: self.handle_wait_state,                                                       
                                                      States.PROCESS: self.handle_process_state, 
                                                      States.POSTPROCESS: self.handle_postprocess_state, 
                                                      States.KILL: self.handle_kill_state, 
                                                    })

    def handle_wait_state(self):
        if self._wait_util_done():
            self.state = States.PROCESS

    def handle_process_state(self):
        children = self.task.result[-1]['gsingle']
        app = _app_tag_mapping[self.task.app_tag]
        a_neb = self.task.neb.pickle
        gc3_temp = _str_dict(children[0].gc3_temp)
        force_converge = .01
        
        f_list = self.task.open('inputs')
        atoms_start, params_start = app.parse_input(f_list[0])
        [f.close() for f in f_list]
        
        path_positions = list()
        path_energies = list()
        path_forces = list()
        for image in children:
            path_positions.append(image.coord.pickle)
            htpie.log.debug('id %s'%(image.id))
            htpie.log.debug('energy %s'%(image.result.energy))
            path_energies.append(image.result.energy[-1])
            path_forces.append(image.result.gradient[-1].pickle)
        
        a_neb.forces(path_positions, path_energies, path_forces)
        
        new_pos = list()
        l_opt = list()
        for a_opt in self.task.opt:
            l_opt.append(a_opt.pickle)
        
        for i in xrange(len(a_neb.path)):
            fmax = neb.vmag(a_neb.path[i].f)
            htpie.log.debug('GString %d %s max force %f'%(i, self.task.id, fmax))
        
        if fmax > force_converge:
            new_pos.append(a_neb.path[0].r)
            for i in xrange(1, len(a_neb.path) - 1):
                new_pos.append(l_opt[i].step(a_neb.path[i].r, a_neb.path[i].f))
                self.task.opt[i].pickle = l_opt[i]
                htpie.log.debug('Image force \n%s'%(a_neb.path[i].f))
            new_pos.append(a_neb.path[-1].r)
            
            for i in xrange(len( a_neb.path)):
                htpie.log.debug('GString %d position diff \n%s'%(i, a_neb.path[i].r - new_pos[i]))
            
            #We need the energy from the first and last position on the path, but we do not want to change them.
            #We therefore lock those positions and keep the old gsingle run for them
            path = _convert_pos_to_jobs(self.task.app_tag, atoms_start, params_start, new_pos[1:-1], **gc3_temp)
            path.insert(0, children[0])
            path.append(children[-1])
            
            l_gsingle = GStringResult(gsingle=path)
            self.task.result.append(l_gsingle)
            self.task.neb.pickle = a_neb
            self.state = States.WAIT
        else:
            self.state = States.POSTPROCESS
    
    def handle_postprocess_state(self):
        self.state = States.COMPLETE
        return True
    
    def handle_kill_state(self):
        return True

    def _wait_util_done(self):
        children =  self.task.result[-1]['gsingle']
        count = 0
        for child in children:
            if child.transition == Transitions.COMPLETE:
                count += 1
            elif child.transition == Transitions.ERROR:
                raise ChildNodeException('Child task %s errored.'%(child.id))
        
        if count == len(children):
            return True
        else:
            return False