from couchdb import schema as sch
from couchdb.schema import  Schema
from gridrun import GridrunModel
from baserole import BaseroleModel, BaseroleInterface
from couchdb import client as client
import time

map_func_job = '''
def mapfun(doc):
    if 'base_type' in doc:
        if doc['base_type'] == 'BaseroleModel':
            if doc['sub_type'] == 'GridjobModel':
                yield doc['_id'],doc
    '''

map_func_author = '''
def mapfun(doc):
    if 'base_type' in doc:
        if doc['base_type'] == 'BaseroleModel':
            if doc['sub_type'] == 'GridjobModel':
                yield doc['author'],doc
    '''

map_func_children = '''
def mapfun(doc):
    if 'base_type' in doc:
        if doc['base_type'] == 'BaseroleModel':
            if doc['sub_type'] == 'GridjobModel':
                if doc['children']:
                    for job_id in doc['children']:
                        yield job_id, doc
                    else:
                        yield [],doc
    '''


map_func_author_status = '''
def mapfun(doc):
    if 'base_type' in doc:
        if doc['base_type'] == 'GridrunModel':
            for job_id in doc['owned_by']:
                yield (doc['author'], doc['status']), {'_id':job_id}
    '''

map_func_task_author_status = '''
def mapfun(doc):
    if 'base_type' in doc:
        if doc['base_type'] == 'BaseroleModel':
            if doc['sub_type'] == 'GridtaskModel':
                yield doc['author'], {'_id':doc['children']}
    '''

class GridjobModel(BaseroleModel):
    SUB_TYPE = 'GridjobModel'
    VIEW_PREFIX = 'GridjobModel'
    sub_type = sch.TextField(default=SUB_TYPE)    
    parser_name = sch.TextField()
    
    def __init__(self, *args):
        super(GridjobModel, self).__init__(*args)
        self._run_id = None
    
    def commit(self, db):
        self.store(db)
    
    def refresh(self, db):
        self = GridjobModel.load_job(db, self.id)
        return self
    
    @staticmethod
    def load_job(db, job_id):
        a_job = GridjobModel.load(db, job_id)
        view = GridrunModel.view_by_job(db, key=job_id)
        if len(view) == 0:
            DocumentError('Job %s does not have a run associated with it.'%(a_job.id))
        a_job._run_id = view.view.wrapper(view.rows[0]).id
        return a_job
    
    @staticmethod
    def view_by_job(db, **options):
        return GridjobModel.my_view(db, 'by_job', **options)
    
    @staticmethod
    def view_by_children(db, **options):
        return GridjobModel.my_view(db, 'by_children', **options)
    
    @staticmethod
    def view_by_author_status(db, **options):
        options['include_docs']=True
        return GridjobModel.my_view(db, 'by_author_status', **options)

    @staticmethod
    def view_by_task_author_status(db, **options):
        options['include_docs']=True
        return GridjobModel.my_view(db, 'by_task_author_status', **options)

    @classmethod
    def my_view(cls, db, viewname, **options):
        from couchdb.design import ViewDefinition
        viewnames = cls.sync_views(db, only_names=True)
        if viewname not in viewnames:
            CriticalError('View not in view name list.')
        a_view = super(cls, cls).view(db, '%s/%s'%(cls.VIEW_PREFIX, viewname), **options)
        #a_view=.view(db, 'all/%s'%viewname, **options)
        return a_view
    
    @classmethod
    def sync_views(cls, db,  only_names=False):
        from couchdb.design import ViewDefinition
        if only_names:
            viewnames=('by_job', 'by_author', 'by_children', 'by_author_status', 'by_task_author_status')
            return viewnames
        else:
            by_job = ViewDefinition(cls.VIEW_PREFIX, 'by_job', map_func_job, wrapper=cls, language='python')
            by_author = ViewDefinition(cls.VIEW_PREFIX, 'by_author', map_func_author, wrapper=cls, language='python')
            by_children = ViewDefinition(cls.VIEW_PREFIX, 'by_children', map_func_children, wrapper=None, language='python')
            by_author_status = ViewDefinition(cls.VIEW_PREFIX, 'by_author_status', map_func_author_status, wrapper=cls,\
                                             language='python') 
            by_task_author_status = ViewDefinition(cls.VIEW_PREFIX, 'by_task_author_status', map_func_task_author_status, \
                                                  wrapper=cls, language='python')
            views=[by_job, by_author, by_children, by_author_status, by_task_author_status]
            ViewDefinition.sync_many( db,  views)
        return views
    
class JobInterface(BaseroleInterface):
    
    def create(self, title,  parser_name, files_to_run, application_to_run='gamess', 
                        selected_resource='ocikbpra',  cores=2, memory=1, walltime=-1):
        self.controlled = GridjobModel().create(self.db.username, title)
        a_run = GridrunModel()
        a_run = a_run.create( self.db, files_to_run, self.controlled, application_to_run, 
                        selected_resource,  cores, memory, walltime)
        self.controlled._run_id = a_run.id
        self.parser = parser_name
        self.controlled.commit(self.db)
        return self
    
    def load(self, id):
        self.controlled=GridjobModel.load_job(self.db, id)
        return self
    
    def add_parent(self, parent):
        parent.add_child(self)
    
    def task():
        def fget(self):
            from gridtask import GridtaskModel, TaskInterface
            self.controlled.refresh(self.db)
            view = GridtaskModel.view_by_children(self.db)
            task_id = view[self.controlled.id].rows[0].id
            a_task=TaskInterface(self.db).load(task_id)
            return a_task
        return locals()
    task = property(**task())

    def parents():            
        def fget(self):
            job_list = list()
            view = GridjobModel.view_by_children(self.db)
            for a_parent in view[self.controlled.id]:
                job_list.append(a_parent)
            return tuple(job_list)
        return locals()
    parents = property(**parents())
    
    def run():
        def fget(self):
            return GridrunModel.load(self.db, self.controlled._run_id)
        return locals()
    run = property(**run())

    def status():
        def fget(self):
            a_run = self.run
            return a_run.status
        def fset(self, status):
            a_run = self.run
            a_run.status = status
            a_run.commit(self.db)
        return locals()
    status = property(**status())

    def wait(self, target_status=GridrunModel.POSSIBLE_STATUS['DONE'], timeout=60, check_freq=10):
        from time import sleep
        if timeout == 'INFINITE':
            timeout = sys.maxint
        if check_freq > timeout:
            check_freq = timeout
        starting_time = time.time()
        while True:
            my_status = self.status
            assert my_status != GridrunModel.POSSIBLE_STATUS['ERROR'], 'Job %s returned an error.'%self.id
            if starting_time + timeout < time.time() or my_status == target_status:
                break
            else:
                time.sleep(check_freq)
        if my_status == target_status:
            # We did not timeout 
            return True
        else:
            # Timed or errored out
            return False

    def attachments():
        def fget(self):
            f_dict = super(JobInterface, self).attachments
            f_dict.update(self.run.attachments_to_files(self.db))
            return f_dict
        return locals()
    attachments = property(**attachments())

    def run_id():        
        def fget(self):
            return self.controlled._run_id
        return locals()
    run_id = property(**run_id())
    
    def run_params():        
        def fget(self):
            return self.run.run_params
        return locals()
    run_params = property(**run_params())
    
    def job():        
        def fget(self):
            return self.controlled
        def fset(self, a_job):
            self.controlled = a_job
        return locals()
    job = property(**job())

    def parser():        
        def fget(self):
            return self.controlled.parser_name
        def fset(self, parser_name):
            self.controlled.parser_name = parser_name
            self.controlled.commit(self.db)
        return locals()
    parser = property(**parser())

    def parsed():
        def fget(self):
            import cPickle as pickle
            f_parsed = self.get_attachment('parsed')
            if f_parsed:
                parsed = pickle.load(f_parsed)
                f_parsed.close()
                return parsed
        def fset(self, parsed):
            import cPickle as pickle
            import cStringIO as StringIO
            pkl = StringIO.StringIO(pickle.dumps(parsed))
            self.put_attachment(pkl,'parsed')
        return locals()
    parsed = property(**parsed())

