from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1270130988.6457491
_template_filename='/home/mmonroe/apps/gorg/gorg_site/gorg_site/templates/derived/user_tasks.html'
_template_uri='/derived/user_tasks.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
from webhelpers.html import escape
_exports = ['buildrow', 'heading', 'title']


def _mako_get_namespace(context, name):
    try:
        return context.namespaces[(__name__, name)]
    except KeyError:
        _mako_generate_namespaces(context)
        return context.namespaces[(__name__, name)]
def _mako_generate_namespaces(context):
    pass
def _mako_inherit(template, context):
    _mako_generate_namespaces(context)
    return runtime._inherit_from(context, '/base/index.html', _template_uri)
def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        h = context.get('h', UNDEFINED)
        c = context.get('c', UNDEFINED)
        def buildrow(a_task,odd=True):
            return render_buildrow(context.locals_(__M_locals),a_task,odd)
        len = context.get('len', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n')
        # SOURCE LINE 2
        __M_writer(u'\n')
        # SOURCE LINE 3
        __M_writer(u'\n\n')
        # SOURCE LINE 29
        __M_writer(u'\n\n')
        # SOURCE LINE 31
        if len(c.paginator):
            # SOURCE LINE 32
            __M_writer(u'<p>')
            __M_writer(escape( c.paginator.pager('$link_first $link_previous $first_item to $last_item of $item_count $link_next $link_last') ))
            __M_writer(u'</p>\n<table class="paginator"><tr><th>Task ID</th><th>Task Title</th><th>Job Count</th><th>Posted</th></tr>\n')
            # SOURCE LINE 34
            counter=0 
            
            __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin()[__M_key]) for __M_key in ['counter'] if __M_key in __M_locals_builtin()]))
            __M_writer(u'\n')
            # SOURCE LINE 35
            for item in c.paginator:
                # SOURCE LINE 36
                __M_writer(u'    ')
                __M_writer(escape(buildrow(item, counter%2)))
                __M_writer(u'\n    ')
                # SOURCE LINE 37
                counter += 1 
                
                __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin()[__M_key]) for __M_key in ['counter'] if __M_key in __M_locals_builtin()]))
                __M_writer(u'\n')
            # SOURCE LINE 39
            __M_writer(u'</table>\n<p>')
            # SOURCE LINE 40
            __M_writer(escape( c.paginator.pager('~2~') ))
            __M_writer(u'</p>\n')
            # SOURCE LINE 41
        else:
            # SOURCE LINE 42
            __M_writer(u'<p>\n    No pages have yet been created.\n    <a href="')
            # SOURCE LINE 44
            __M_writer(escape(h.url_for(controller='page', action='new')))
            __M_writer(u'">Add one</a>.\n</p>\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_buildrow(context,a_task,odd=True):
    context.caller_stack._push_frame()
    try:
        h = context.get('h', UNDEFINED)
        len = context.get('len', UNDEFINED)
        unicode = context.get('unicode', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 5
        __M_writer(u'\n')
        # SOURCE LINE 6
        if odd:
            # SOURCE LINE 7
            __M_writer(u'        <tr class="odd">\n')
            # SOURCE LINE 8
        else:
            # SOURCE LINE 9
            __M_writer(u'        <tr class="even">\n')
        # SOURCE LINE 11
        __M_writer(u'        <td valign="top">\n            ')
        # SOURCE LINE 12
        __M_writer(escape(h.link_to(
                a_task.id,
                h.url_for(
                    controller=u'gridtask',
                    action='view_task',
                    id=unicode(a_task.id)
                )
            )))
        # SOURCE LINE 19
        __M_writer(u'\n        </td>\n        <td valign="top">\n            ')
        # SOURCE LINE 22
        __M_writer(escape(a_task.title))
        __M_writer(u'\n        </td>\n        <td valign="top">\n            ')
        # SOURCE LINE 25
        __M_writer(escape(len(a_task.children)))
        __M_writer(u'\n        </td>\n        <td valign="top">')
        # SOURCE LINE 27
        __M_writer(escape(a_task.dat.strftime('%c')))
        __M_writer(u'</td>\n        </tr>\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_heading(context):
    context.caller_stack._push_frame()
    try:
        c = context.get('c', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 3
        __M_writer(u'<h1>')
        __M_writer(escape(c.heading or c.title))
        __M_writer(u'</h1>')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_title(context):
    context.caller_stack._push_frame()
    try:
        c = context.get('c', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 2
        __M_writer(escape(c.title))
        return ''
    finally:
        context.caller_stack._pop_frame()


