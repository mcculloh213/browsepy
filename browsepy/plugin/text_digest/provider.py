from contextlib import contextmanager

from .celeritas import AsyncResult
from .entity import (
    Authority, AsyncTask, DeferredTask,
    FileIndex, TextCorpus, Widget,
    )
from .ingestable import File


class ContentProvider(object):
    """A URI Content Provider that allows for 'safe' file handling."""

    @property
    def central_authority(self) -> str:
        return self._authority

    @central_authority.setter
    def central_authority(self, value):
        self._authority = value

    def __init__(self, authority: str):
        self._authority = authority

    @contextmanager
    def open(self, abspath, method='r'):
        fp = open(abspath, method)
        try:
            yield fp
        finally:
            fp.close()

    def insert(self, node, display_name):
        # type: (File, str) -> str
        """
        Inserts the node into the database, creating and storing a FileIndex.

        :param node: the browsepy Node to insert
        :param display_name: the display name of the node

        :returns: the id of the new FileIndex.
        """
        fileptr = FileIndex(
            filename=node.name,
            displayname=display_name,
            urlpath=node.urlpath,
            matpath=','.join(('/' + node.parent.urlpath).split('/')) + ',',
            mimetype=node.mimetype,
            uri=ContentProvider.get_uri_for_node(self._authority, node),
            tasks=[],
            widgets=ContentProvider.get_default_file_widgets(node,
                                                             display_name),
            ).save()
        return str(fileptr.id)

    def register(self, parent, child):
        # type: (str, File) -> str
        parent_fp = FileIndex.objects(urlpath=parent).get_or_404()
        transform_fp = FileIndex(
            filename=child.name,
            displayname=parent_fp.displayname,
            urlpath=child.urlpath,
            matpath=','.join(('/' + child.parent.urlpath).split('/')) + ',',
            mimetype=child.mimetype,
            uri=ContentProvider.get_uri_for_node(self._authority, child),
            tasks=[],
            widgets=ContentProvider.get_default_file_widgets(child,
                                                             parent_fp.displayname),
            ).save()
        parent_fp.transformations.append(transform_fp)
        parent_fp.save()
        return str(transform_fp.id)

    @staticmethod
    def convert(urlpath, task):
        fileptr = FileIndex.objects(urlpath=urlpath).get_or_404()
        template = AsyncTask.objects(name=task.name).get_or_404()
        arguments = template.parameters
        arguments[0].value = urlpath
        request = task.delay(urlpath)
        dt = DeferredTask(
            broker_id=request.id,
            template=template,
            arguments=arguments,
            status=request.status
        ).save()
        fileptr.tasks.append(dt)
        fileptr.save()
        return str(dt.id)

    def update(self):
        pass

    @staticmethod
    def delete(urlpath):
        fileptr = FileIndex.objects(urlpath=urlpath).get_or_404()
        fid = str(fileptr.id)
        fileptr.delete()
        return fid

    @classmethod
    def get_uri_for_node(cls, authority, node):
        """
        Gets the associated file URI for the node.

        :param authority: the authority requesting the node
        :param node: the browsepy Node
        """
        return F'file://{authority}/{node.urlpath}'

    @classmethod
    def get_default_file_widgets(cls, node, name):
        """"""
        return [
            Widget.create_button('entry-actions',
                                 endpoint='text_digest.tasks',
                                 icon='tasks',
                                 tooltip={
                                     'data-toggle': 'tooltip',
                                     'data-title': 'Tasks',
                                     'style': 'cursor:pointer;font-size:1.4em',
                                     'title': 'Tasks',
                                    },
                                 **dict(path=node.urlpath),
                                 ),
            Widget.create_button('entry-actions',
                                 endpoint='text_digest.convert_file',
                                 icon='filter',
                                 tooltip={
                                     'data-toggle': 'tooltip',
                                     'data-title': 'Convert',
                                     'style': 'cursor:pointer;font-size:1.4em',
                                     'title': 'Convert',
                                    },
                                 **dict(path=node.urlpath),
                                 ),
            Widget.create_button('entry-actions',
                                 href='text_digest.files',
                                 icon='equalizer',
                                 tooltip={
                                     'data-toggle': 'tooltip',
                                     'data-title': 'Data',
                                     'style': 'cursor:pointer;font-size:1.4em',
                                     'title': 'Data',
                                    },
                                 ),
            Widget.create_button('entry-actions',
                                 endpoint='text_digest.remove_node',
                                 icon='remove',
                                 tooltip={
                                     'data-toggle': 'tooltip',
                                     'data-title': 'Remove',
                                     'style': 'cursor:pointer;font-size:1.4em',
                                     'title': 'Remove',
                                    },
                                 **dict(path=node.urlpath),
                                 ),
            Widget.create_link('entry-link',
                               endpoint='open',
                               text=name,
                               **dict(path=node.urlpath))
        ]
