from browsepy.plugin.text_digest.logging import make_logger

from .entity import (
    ApplicationPage, Widget,
    AsyncTask, TaskParameter
    )

# create logger
logger = make_logger('ai.mccullough.browsepy.digest.migration')


def _application_page_exists(title) -> bool:
    return ApplicationPage.objects(title=title).count() != 0


def _async_task_exists(name) -> bool:
    return AsyncTask.objects(name=name).count() != 0


def _insert_page_file_index():
    page = ApplicationPage(
        title='File Index',
        widgets=[
            Widget.create_button(
                'header',
                href='browse',
                text='Browse Files',
                ),
            Widget.create_button(
                'header',
                href='text_digest.create_authority',
                text='Create File Authority',
                ),
            Widget.create_button(
                'header',
                href='text_digest.task_sleeper',
                text='Celery Test',
                ),
        ],
        ).save()
    logger.info(F'Inserted File Index ({page.id})')
    return page.id


def _insert_page_task_sleeper():
    page = ApplicationPage(
        title='Sleeper',
        widgets=[
            Widget.create_button(
                'header',
                href='text_digest.files',
                text='File Index',
            ),
        ],
        ).save()
    logger.info(F'Inserted Sleeper ({page.id})')
    return page.id


def _insert_page_convert_file():
    page = ApplicationPage(
        title='Convert File',
        widgets=[
            Widget.create_button(
                'header',
                href='browse',
                text='Browse Files',
                ),
            Widget.create_button(
                'header',
                href='text_digest.files',
                text='File Index',
                ),
            ],
        ).save()
    logger.info(F'Inserted Convert File ({page.id})')
    return page.id


def _insert_page_file_tasks():
    page = ApplicationPage(
        title='File Tasks',
        widgets=[
            Widget.create_button(
                'header',
                href='browse',
                text='Browse Files',
                ),
            Widget.create_button(
                'header',
                href='text_digest.files',
                text='File Index',
                ),
            ],
        ).save()
    logger.info(F'Inserted File Tasks ({page.id})')
    return page.id


def _insert_task_convert_pdfminer():
    task = AsyncTask(
        name='convert.pdfminer',
        description='Converts a PDF to HTML using PDFMiner.six',
        parameters=[
            TaskParameter(
                name='urlpath',
                type=str.__name__,
                description='The platform URL path of the file to convert.',
                ),
            TaskParameter(
                name='out_type',
                type=str.__name__,
                description='One of { .htm, .html, .xml, .tag }',
                default_value='.html',
                is_required=False,
                ),
            ],
        ).save()
    logger.info(F'Inserted convert.pdfminer ({task.id})')
    return task.id


def _insert_task_convert_pypandoc():
    task = AsyncTask(
        name='convert.pypandoc',
        description='Converts a file to another usable type using Pandoc.',
        parameters=[
            TaskParameter(
                name='urlpath',
                type=str.__name__,
                description='The platform URL path of the file to convert.',
                ),
            TaskParameter(
                name='in_fmt',
                type=str.__name__,
                description=('The format of the input file. '
                             'If not provided, the format will try '
                             'to be guessed by the file extension.'),
                default_value=None,
                is_required=False,
                ),
            TaskParameter(
                name='out_ext',
                type=str.__name__,
                description='The desired file extension for the output file.',
                default_value='.txt',
                is_required=False,
                ),
            TaskParameter(
                name='encoding',
                type=str.__name__,
                description='The encoding of the file or the input bytes.',
                default_value='utf-8',
                is_required=False,
                ),
            ],
        ).save()
    logger.info(F'Inserted convert.pypandoc ({task.id})')
    return task.id

MIGRATIONS = {
    'pages': {
        'File Index': _insert_page_file_index,
        'Sleeper': _insert_page_task_sleeper,
        'Convert File': _insert_page_convert_file,
        'File Tasks': _insert_page_file_tasks,
    },
    'tasks': {
        'convert.pdfminer': _insert_task_convert_pdfminer,
        'convert.pypandoc': _insert_task_convert_pypandoc,
    }
}


def run_migrations():
    logger.info('----- Executing MongoDB Migrations -----')
    pages = MIGRATIONS.get('pages')
    for title, fnc in pages.items():
        if not _application_page_exists(title):
            logger.warning(F'Page {title} not found!')
            if not fnc():
                msg = F'Migration failed! Application Page: {title}'
                logger.error(msg)
                raise RuntimeError(msg)
        else:
            logger.info(F'No changes applied to Application Page {title}!')
    tasks = MIGRATIONS.get('tasks')
    for name, fnc in tasks.items():
        if not _async_task_exists(name):
            logger.warning(F'Async Task {name} not found!')
            if not fnc():
                msg = F'Migration failed! Async Task: {name}'
                logger.error(msg)
                raise RuntimeError(msg)
        else:
            logger.info(F'No changes applied to Async Task {name}!')
    logger.info('----- Completed MongoDB Migrations -----')
