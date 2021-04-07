import os
import pypandoc

from browsepy import datetime
from browsepy.file import abspath_to_urlpath, urlpath_to_abspath
from browsepy.plugin.text_digest.provider import ContentProvider
from . import Reject, celery, make_task_logger

logger = make_task_logger('ai.mccullough.celeritas.convert.pypandoc')
content_provider = ContentProvider('ai.mccullough.browsepy')
PANDOC_INPUT_FORMATS = [
    'commonmark',
    'docbook',
    'docx',
    'epub',
    'haddock',
    'html',
    'json',
    'latex',
    'markdown',
    'markdown_github',
    'markdown_mmd',
    'markdown_phpextra',
    'markdown_strict',
    'mediawiki',
    'native',
    'odt',
    'opml',
    'org',
    'rst',
    't2t',
    'textile',
    'twiki',
    ]
PANDOC_OUTPUT_FORMATS = [
    'asciidoc',
    'beamer',
    'commonmark',
    'context',
    'docbook',
    'docbook5',
    'docx',
    'dokuwiki',
    'dzslides',
    'epub',
    'epub3',
    'fb2',
    'haddock',
    'html',
    'html5',
    'icml',
    'json',
    'latex',
    'man',
    'markdown',
    'markdown_github',
    'markdown_mmd',
    'markdown_phpextra',
    'markdown_strict',
    'mediawiki',
    'native',
    'odt',
    'opendocument',
    'opml',
    'org',
    'plain',
    'revealjs',
    'rst',
    'rtf',
    's5',
    'slideous',
    'slidy',
    'tei',
    'texinfo',
    'textile',
    'zimwiki',
    ]
EXT_TO_FORMAT_MAP = {
    '.doc': 'docx',
    '.docx': 'docx',
    '.html': 'html',
    '.md': 'markdown',
    '.txt': 'plain',
    }


def default_config():
    return PandocConfig()


@celery.task(bind=True,
             name='convert.pypandoc',
             track_started=True,
             )
def convert_file(self, urlpath: str,
                 in_fmt: str = None,
                 out_ext: str = '.txt',
                 encoding: str = 'utf-8'):
    logger.info('Task received!')

    # region 1. Validate Pandoc input format
    if in_fmt and in_fmt not in PANDOC_INPUT_FORMATS:
        logger.warning(F'Input format {in_fmt} is not valid!')
        in_fmt = None

    basename = os.path.basename(urlpath)
    in_ext = basename[basename.index('.'):]
    if not in_fmt:
        guess_fmt = EXT_TO_FORMAT_MAP.get(in_ext)
        if guess_fmt not in PANDOC_INPUT_FORMATS:
            reason = ValueError(F'{guess_fmt} is not a valid input format!')
            logger.error(F'Error: {reason}')
            raise Reject(reason)
        else:
            in_fmt = guess_fmt
    # endregion

    # region 2. Validate Pandoc output format
    out_fmt = EXT_TO_FORMAT_MAP.get(out_ext)
    if not out_fmt or out_fmt not in PANDOC_OUTPUT_FORMATS:
        reason = ValueError(F'{out_fmt} is not a valid output format!')
        logger.error(F'Error: {reason}')
        raise Reject(reason)
    # endregion

    # region 3. Prepare output directory
    # TODO: Move '/var/www/browsepy/root' into config file
    infile = urlpath_to_abspath(urlpath, '/var/www/browsepy/root')
    logger.info(F'File Location: {infile}')
    outdir = os.path.join(os.path.dirname(infile),
                          'pandoc',
                          datetime.timestamp(),
                          )
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    logger.info(F'Output Directory Location: {outdir}')
    outfile = basename.replace(in_ext, out_ext)
    outpath = os.path.join(outdir, outfile)
    logger.info(F'Output File Location: {outpath}')
    # endregion

    # region 4. Prepare config
    config = default_config()
    config.align_output_file(suggested_file=outpath)
    # endregion

    # region 5. Convert File
    try:
        pypandoc.convert_file(infile, out_fmt, format=in_fmt,
                              extra_args=config.build_arguments(),
                              encoding=encoding,
                              outputfile=outpath)
        # TODO: Move '/var/www/browsepy/root' into config file
        return dict(
            parent=urlpath,
            child=abspath_to_urlpath(outpath, '/var/www/browsepy/root'),
        )
    except ValueError as ve:
        logger.error(F'Error: {ve}')
        raise Reject(ve)
    except RuntimeError as re:
        logger.error(F'Error: {re}')
        raise Reject(re)
    except OSError as ose:
        logger.error(F'Error: {ose}')
        raise Reject(ose)
    # endregion


class PandocConfig(object):
    """[Pandoc Options](https://pandoc.org/MANUAL.html#options)"""
    def __init__(self, smart: bool = True, standalone: bool = True):
        """

        :param smart:

        :param standalone:
          Produce output with an appropriate header and footer
          (e.g. a standalone HTML, LaTeX, TEI, or RTF file, not a fragment).
          This option is set automatically for pdf, epub, epub3, fb2, docx,
          and odt output. For native output, this option causes metadata to
          be included; otherwise, metadata is suppressed.
        """
        self.outfile = None
        self.smart = smart
        self.standalone = standalone

    def align_output_file(self, suggested_file):
        if not self.outfile:
            self.outfile = suggested_file

    def build_arguments(self):
        if not self.outfile:
            raise ValueError('No valid outfile has been supplied!')
        args = []
        if self.smart:
            args.append('--smart')
        if self.standalone:
            args.append('--standalone')
        return args
