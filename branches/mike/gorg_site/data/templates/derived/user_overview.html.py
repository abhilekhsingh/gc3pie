from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1268752627.9920981
_template_filename='/home/mmonroe/apps/gorg/gorg_site/gorg_site/templates/derived/user_overview.html'
_template_uri='/derived/user_overview.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
from webhelpers.html import escape
_exports = ['heading', 'title']


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
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n')
        # SOURCE LINE 2
        __M_writer(u'\n')
        # SOURCE LINE 3
        __M_writer(u'\n\n\n')
        # SOURCE LINE 6
        __M_writer(escape(h.link_to(
	'View your tasks',
	h.url_for(
	    controller=u'gridtask',
	    action='view_user_task_overview',
	)
)))
        # SOURCE LINE 12
        __M_writer(u'<br>\n')
        # SOURCE LINE 13
        __M_writer(escape(h.link_to(
	'View your jobs',
	h.url_for(
	    controller=u'gridjob',
	    action='view_user_job_overview',
	)
)))
        # SOURCE LINE 19
        __M_writer(u'\n')
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


