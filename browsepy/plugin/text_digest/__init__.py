"""
Text Digest plugin

This plugin provides a digest functionality for text based files.
"""
from flask import (
    Blueprint,
    abort, flash,
    jsonify,
    request, redirect,
    render_template,
    session, url_for,
    )
from flask_mongoengine import MongoEngine
from mongoengine import NotUniqueError

from browsepy.file import (
    Node,
    )
from .celeritas import AsyncResult
from .celeritas.tasks.sleeper import sleeper
from .celeritas.tasks.convert import pdfminer, pypandoc
from wtforms import ValidationError

from . import migration
from .entity import (
    ApplicationPage,
    ConvertFileForm,
    DeferredTask,
    Authority, AuthorityForm,
    FileIndex, InsertFileForm,
    TextCorpus,
    )
from .ingestable import IngestableNode, IngestableFile, IngestableDirectory
from .logging import make_logger
from .provider import ContentProvider

logger = make_logger('ai.mccullough.browsepy.digest')
PLATFORM_AUTHORITY = 'ai.mccullough.browsepy'
db = MongoEngine()
content_provider = ContentProvider(PLATFORM_AUTHORITY)

digest = Blueprint(
    'text_digest',
    __name__,
    url_prefix='/digest',
    template_folder='templates',
    static_folder='static',
    )

# region -- Content Provider


@digest.route('/cp/authority/create', methods=('GET', 'POST'))
def create_authority():
    """Creates an Authority to group File URI's."""
    logger.info(F'{request.method}\t{request.path}')
    form = AuthorityForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            Authority(domain=form.domain.data).save()
            return redirect(url_for('browse'))
        except ValidationError as ve:
            print('Validation Error:', ve)
            return render_template(
                'authority/create_authority.digest.html',
                form=form,
                )
        except NotUniqueError as nue:
            print('Not Unique Error:', nue)
            return render_template(
                'authority/create_authority.digest.html',
                form=form,
                )
    return render_template(
        'authority/create_authority.digest.html',
        form=form,
        )


@digest.route('/cp/insert', defaults={'path': ''}, methods=('GET', 'POST'))
@digest.route('/cp/insert/<path:path>', methods=('GET', 'POST'))
def insert_node(path):
    """
    Insert a browsepy Node into the content provider.
    """
    logger.info(F'{request.method}\t{request.path}')
    node = Node.from_urlpath(path)
    if not node.is_file:
        abort(400)
    if not request.form:
        form = InsertFileForm(displayname=node.name)
    else:
        form = InsertFileForm(request.form)
    parent_node = node.parent
    parent_urlspec = None if not parent_node else parent_node.urlpath
    if request.method == 'POST' and form.validate():
        try:
            content_provider.insert(node, form.displayname.data)
            return redirect(url_for('browse', path=parent_urlspec))
        except ValidationError as ve:
            print('Validation Error:', ve)
            return render_template(
                'provider/insert_node.digest.html',
                file=node,
                form=form,
                back_dir=parent_urlspec,
                )
        except NotUniqueError as nue:
            print('Not Unique Error:', nue)
            return render_template(
                'provider/insert_node.digest.html',
                file=node,
                form=form,
                back_dir=parent_urlspec,
                )
    return render_template(
        'provider/insert_node.digest.html',
        file=node,
        form=form,
        back_dir=parent_urlspec,
        )


@digest.route('/cp/remove/<path:path>')
def remove_node(path):
    logger.info(F'{request.method}\t{request.path}')
    content_provider.delete(path)
    flash(F'Deleted index for {path}.', category='critical')
    return redirect(url_for('.files'))


@digest.route('/cp/register/<broker_id>', methods=['POST'])
def register_transformation(broker_id):
    logger.info(F'{request.method}\t{request.path}')
    task = AsyncResult(broker_id)
    if not task.successful():
        return jsonify(dict(
            broker_id=broker_id,
            data=dict(
                task_id=task.id,
                task_status=task.status,
                task_result=task.result,
                ),
            )), 400
    result = task.result
    logger.info(F'[Celeritas {broker_id}] Result: {result}')
    deferred = DeferredTask.objects(broker_id=broker_id).get_or_404()
    deferred.result = result
    deferred.save()
    child = Node.from_urlpath(result['child'])
    index = content_provider.register(result['parent'], child)
    return jsonify(dict(
            broker_id=broker_id,
            data=dict(
                file=index,
                ),
            )), 201

# endregion

# region -- Files


@digest.route('/files')
def files():
    """Handle files request, serve paginated listing of indexed files."""
    logger.info(F'{request.method}\t{request.path}')
    app_page = ApplicationPage.objects(title='File Index').get_or_404()
    current_page = request.args.get('p', 1, type=int)
    page_size = min(50, request.args.get('s', 10, type=int))
    paginated_files = FileIndex.objects.paginate(page=current_page,
                                                 per_page=page_size)
    return render_template(
        'files.digest.html',
        page=app_page,
        items_per_page=page_size,
        files=paginated_files,
        )

# endregion

# region -- File Converters


@digest.route('/convert/<path:path>')
def convert_file(path):
    logger.info(F'{request.method}\t{request.path}')
    file = FileIndex.objects(urlpath=path).get_or_404()
    app_page = ApplicationPage.objects(title='Convert File').get_or_404()
    form = ConvertFileForm()
    return render_template(
        'tasks/convert.celeritas.html',
        page=app_page,
        form=form,
        file=file
        )


@digest.route('/transform/<path:path>', methods=['POST'])
def transform_file(path):
    logger.info(F'{request.method} /digest/transform/{path}')
    form = ConvertFileForm(request.form)
    name = form.template.data.name
    broker_id = None
    if name == 'convert.pdfminer':
        broker_id = content_provider.convert(path,
                                             pdfminer.convert_pdf_to_html)
    elif name == 'convert.pypandoc':
        broker_id = content_provider.convert(path,
                                             pypandoc.convert_file)
    if broker_id:
        flash(F'Task {name} ({broker_id}) has been enqueued!',
              category='message')
    return redirect(url_for('.convert_file', path=path))

# endregion

# region -- Tasks


@digest.route('/tasks/<path:path>')
def tasks(path):
    logger.info(F'{request.method}\t{request.path}')
    file = FileIndex.objects(urlpath=path).get_or_404()
    app_page = ApplicationPage.objects(title='File Tasks').get_or_404()
    return render_template(
        'tasks/index.celeritas.html',
        page=app_page,
        file=file,
        )


@digest.route('/task/<broker_id>')
def task_status(broker_id):
    logger.info(F'{request.method}\t{request.path}')
    task = AsyncResult(broker_id)
    try:
        deferred = DeferredTask.objects(broker_id=broker_id).get_or_404()
        deferred.status = task.status
        deferred.save()
        return jsonify(dict(
            broker_id=broker_id,
            data=dict(
                task_id=task.id,
                task_status=task.status,
                task_result=task.result,
                ),
            )), 200
    except TypeError as te:
        logger.error(F'Error: {te}')
        return jsonify(dict(
            broker_id=broker_id,
            data=dict(
                task_status='NOT FOUND',
                task_result=None,
            ),
        )), 404


@digest.route('/task/sleeper', methods=('GET', 'POST'))
def task_sleeper():
    logger.info(F'{request.method}\t{request.path}')
    try:
        if request.method == 'POST':
            content = request.json
            delay = content.get('delay', 3)
            task = sleeper.delay(int(delay))
            return jsonify(dict(data=dict(task_id=task.id))), 202
    except Exception as ex:
        msg = F'Failed to launch sleeper: {ex}'
        logger.error(msg)
        flash(msg, category='error')
    app_page = ApplicationPage.objects(title='Sleeper').get_or_404()
    return render_template(
        'tasks/sleeper.celeritas.html',
        page=app_page,
        )

# endregion


def get_cookie_files_sorting(authority, default):
    # type: (str, str) -> str
    """
    Get sorting-cookie data for authority of current request.

    :param authority: authority for sorting attribute
    :param default: default sorting attribute
    :return: sorting property
    """
    if request:
        for cauthority, cprop in session.get('files:sort', ()):
            if authority == cauthority:
                return cprop
    return default


# def get_cookie_files_current_authority():
#     # type: (str, str) -> str
#     """
#     Get sorting-cookie data for authority of current request.
#
#     :param authority: authority for sorting attribute
#     :param default: default sorting attribute
#     :return: sorting property
#     """
#     if request:
#         for cauthority, cprop in session.get('files:sort', ()):
#             if authority == cauthority:
#                 return cprop
#     return default


def detect_ingest(directory):
    """Detect if directory node can be used as an ingestable target."""
    return directory.is_directory and directory.can_upload


def detect_insert_target(node):
    """Detect if the node is ingestable and does not exist in the db."""
    return (IngestableFile.detect(node)
            and not FileIndex.objects(urlpath=node.urlpath))


def detect_files(*args):
    """Detect if there are indexed files"""
    return len(FileIndex.objects) > 0


def register_arguments(manager):
    """
    Register arguments using given plugin manager.

    This method is called before `register_plugin`.

    :param manager: plugin manager
    :type manager: browsepy.manager.PluginManager
    """
    # Arguments are forwarded to argparse:ArgumentParser.add_argument,
    # https://docs.python.org/3.7/library/argparse.html#the-add-argument-method
    manager.register_argument(
        '--central-authority', metavar='WHOAMI', type=str,
        default=PLATFORM_AUTHORITY,
        help='MongoDB host connection parameter (default: %(default)s)',
        )
    manager.register_argument(
        '--mongodb-host', metavar='HOST', type=str, default='localhost',
        help='MongoDB host connection parameter (default: %(default)s)',
        )
    manager.register_argument(
        '--mongodb-port', metavar='PORT', type=int, default=27017,
        help='MongoDB port connection parameter (default: %(default)s)',
        )
    manager.register_argument(
        '--mongodb-collection', metavar='DB', type=str, default='browsepy',
        help='MongoDB database connection parameter (default: %(default)s)',
        )


def register_plugin(manager):
    """
    Register blueprints and actions using given plugin manager.

    :param manager: plugin manager
    :type manager: browsepy.manager.PluginManager
    """
    manager.register_blueprint(digest)
    manager.register_mimetype_function(IngestableFile.detect_mimetype)

    # add style tag
    manager.register_widget(
        place='styles',
        type='stylesheet',
        endpoint='text_digest.static',
        filename='css/browse.css',
        )

    # register header button
    manager.register_widget(
        place='header',
        type='button',
        href='text_digest.create_authority',
        text='Create File Authority',
        filter=detect_ingest,
        )
    manager.register_widget(
        place='header',
        type='button',
        href='text_digest.files',
        text='File Index',
        filter=detect_files,
        )

    # register action buttons
    manager.register_widget(
        place='entry-actions',
        css='insert',
        type='button',
        endpoint='text_digest.insert_node',
        filter=detect_insert_target,
        )

    db.init_app(manager.app)
    migration.run_migrations()
