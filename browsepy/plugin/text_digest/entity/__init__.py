import mongoengine as me

from datetime import datetime, timezone as tz
from functools import wraps
from flask_mongoengine import Document
from flask_mongoengine.wtf import model_form
from typing import Optional, Union

from browsepy.compat import cached_property


def connect(db: str,
            host: str = 'localhost',
            port: Union[str, int] = 27017,
            default: Optional[str] = 'browsepy',
            alias: Optional[str] = None,
            disconnect_on_return: bool = False):
    def connect_decorator(func):
        if default and alias:
            try:
                me.connect(db=default, host=host, port=port)
            except me.ConnectionFailure as cfe:
                print('[Database] Error:', cfe)
            finally:
                me.connect(db=db, host=host, port=port, alias=alias)
        else:
            me.connect(db=db, host=host, port=port)

        @wraps(func)
        def connect_wrapper(*args, **kwargs):
            _out = func(*args, **kwargs)
            if disconnect_on_return and default and alias:
                me.disconnect(alias=alias)
            return _out
        return connect_wrapper
    return connect_decorator


class Authority(Document):
    domain = me.StringField(required=True, unique=True,
                            min_length=8, max_length=64)
    created = me.DateTimeField(default=datetime.now(tz.utc))


AuthorityForm = model_form(Authority, only=['domain'],
                           field_args={'domain': {'label': 'Domain'}})


WIDGET_TYPES = ['button', 'link', 'script', 'stylesheet', 'upload', 'html']
WIDGET_PLACES = ['entry-actions', 'entry-link',
                 'styles', 'head', 'scripts', 'header', 'footer']


class TaskParameter(me.EmbeddedDocument):
    name = me.StringField(required=True)
    type = me.StringField(required=True)
    value = me.DynamicField(required=False)
    description = me.StringField(default='NO DESCRIPTION')
    default_value = me.DynamicField(default=None, null=True)
    is_required = me.BooleanField(default=True)
    is_kwarg = me.BooleanField(default=False)


class AsyncTask(Document):
    name = me.StringField(required=True, unique=True)
    description = me.StringField(default='NO DESCRIPTION')
    parameters = me.EmbeddedDocumentListField(TaskParameter)


class DeferredTask(Document):
    broker_id = me.StringField(primary_key=True)
    template = me.ReferenceField(AsyncTask, reverse_delete_rule=me.CASCADE)
    arguments = me.EmbeddedDocumentListField(TaskParameter)
    status = me.StringField(default='PENDING')
    result = me.DynamicField(default=None, null=True)
    created = me.DateTimeField(default=datetime.now(tz.utc))

    @staticmethod
    def template_label_modifier(obj):
        return obj.name


ConvertFileForm = model_form(DeferredTask, only=['template'],
                             field_args={'template': {
                                  'allow_blank': False,
                                  'label': 'Methods',
                                  'label_attr': 'name',
                              }})


class Widget(me.EmbeddedDocument):
    type = me.StringField(required=True, choices=WIDGET_TYPES)
    place = me.StringField(required=True, choices=WIDGET_PLACES)
    endpoint = me.StringField(default=None, null=True)
    endpoint_params = me.DictField(default={})
    href = me.StringField(default=None, null=True)
    icon = me.StringField(default=None, null=True)
    text = me.StringField(default=None, null=True)
    tooltip = me.DictField(default={})
    css = me.StringField(default=None, null=True)
    src = me.StringField(default=None, null=True)
    filename = me.StringField(default=None, null=True)
    action = me.StringField(default=None, null=True)
    html = me.StringField(default=None, null=True)

    @classmethod
    def create_button(cls, place, endpoint=None,
                      href=None, icon=None, css=None,
                      text=None, tooltip=None,
                      **kwargs):
        tooltip_params = tooltip or {}
        return cls(
            type='button',
            place=place,
            endpoint=endpoint,
            endpoint_params=dict(**kwargs),
            href=href,
            icon=icon,
            text=text,
            tooltip=tooltip_params,
            css=css,
            )

    @classmethod
    def create_link(cls, place, endpoint=None,
                    href=None, icon=None,
                    css=None, text=None,
                    **kwargs):
        return cls(
            type='link',
            place=place,
            endpoint=endpoint,
            endpoint_params=dict(**kwargs),
            href=href,
            icon=icon,
            text=text,
            css=css,
            )

    @classmethod
    def create_script(cls):
        return cls(
            type='script',
            )

    @classmethod
    def create_stylesheet(cls):
        return cls(
            type='stylesheet',
            )

    @classmethod
    def create_upload(cls):
        return cls(
            type='upload',
            )

    @classmethod
    def create_html(cls):
        return cls(
            type='html',
            )


class FileIndex(Document):
    filename = me.StringField(required=True)
    displayname = me.StringField(required=True, max_length=128)
    urlpath = me.StringField(required=True, unique=True)
    matpath = me.StringField(required=True)
    mimetype = me.StringField(required=True)
    uri = me.StringField(required=True)
    transformations = me.ListField(
        me.ReferenceField('self', reverse_delete_rule=me.CASCADE))
    tasks = me.ListField(
        me.ReferenceField(DeferredTask, reverse_delete_rule=me.CASCADE))
    widgets = me.EmbeddedDocumentListField(Widget)
    created = me.DateTimeField(default=datetime.now(tz.utc))
    updated = me.DateTimeField(default=datetime.now(tz.utc))

    @cached_property
    def link(self):
        """
        Get last widget with place `entry-link`.

        :returns: widget on entry-link (ideally a link one)
        :rtype: namedtuple instance
        """
        link = None
        for widget in self.widgets:
            if widget.place == 'entry-link':
                link = widget
        return link


InsertFileForm = model_form(FileIndex, only=['displayname'],
                            field_args={'displayname': {
                                'label': 'Display Name'
                            }})


class TextDigest(Document):
    method = me.StringField(reqired=True)
    outputs = me.StringField(required=True)


class TextCorpus(Document):
    authority = me.ReferenceField(Authority, required=True,
                                  reverse_delete_rule=me.DENY)
    files = me.ListField(me.ReferenceField(FileIndex,
                                           reverse_delete_rule=me.CASCADE))
    created = me.DateTimeField(default=datetime.now(tz.utc))
    updated = me.DateTimeField(default=datetime.now(tz.utc))


class ApplicationPage(Document):
    title = me.StringField(required=True, unique=True)
    widgets = me.EmbeddedDocumentListField(Widget)
