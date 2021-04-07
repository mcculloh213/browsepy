import os
import pdfminer.high_level
from pdfminer.layout import LAParams

from browsepy import datetime
from browsepy.file import abspath_to_urlpath, urlpath_to_abspath
from browsepy.plugin.text_digest.provider import ContentProvider
from . import Reject, celery, make_task_logger

logger = make_task_logger('ai.mccullough.celeritas.convert.pdfminer')
content_provider = ContentProvider('ai.mccullough.browsepy')
OUTPUT_TYPES = (('.htm', 'html'),
                ('.html', 'html'),
                ('.xml', 'xml'),
                ('.tag', 'tag'))


def default_config():
    return PDFMinerConfig()


@celery.task(bind=True,
             name='convert.pdfminer',
             track_started=True,
             )
def convert_pdf_to_html(self, urlpath: str,
                        out_type: str = '.html'):
    logger.info('Task received!')

    if not urlpath.endswith('.pdf'):
        reason = ValueError(F'{urlpath} is not a PDF!')
        logger.error(F'Error: {reason}')
        raise Reject(reason)

    config = default_config()
    logger.info(F'Converting {urlpath} using PDFMiner.')
    basename = os.path.basename(urlpath)
    logger.info(F'Basename: {basename}')
    # TODO: Move '/var/www/browsepy/root' into config file
    infile = urlpath_to_abspath(urlpath, '/var/www/browsepy/root')
    logger.info(F'File Location: {infile}')
    outdir = os.path.join(os.path.dirname(infile),
                          'pdfminer',
                          datetime.timestamp(),
                          )
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    logger.info(F'Output Directory Location: {outdir}')
    config.align_output_dir(outdir)
    outfile = os.path.join(outdir, basename.replace('.pdf', out_type))
    logger.info(F'Output File Location: {outfile}')
    config.align_output_file(outfile)

    try:
        params = config.build_extract_args()
        with content_provider.open(outfile, 'wb') as outfp:
            with content_provider.open(infile, 'rb') as fp:
                pdfminer.high_level.extract_text_to_fp(fp, outfp, **params)
        # TODO: Move '/var/www/browsepy/root' into config file
        return dict(
            parent=urlpath,
            child=abspath_to_urlpath(outfile, '/var/www/browsepy/root'),
            )
    except ValueError as ve:
        logger.error(F'Error: {ve}')
        raise Reject(ve)


class PDFMinerConfig(object):
    """

    """
    def __init__(self,
                 no_laparams=False, all_texts=None, detect_vertical=None,
                 word_margin=None, char_margin=None, line_margin=None,
                 boxes_flow=None, output_type='text', codec='utf-8',
                 strip_control=False, maxpages=0, page_numbers=None,
                 password="", scale=1.0, rotation=0, layoutmode='normal',
                 output_dir=None, debug=False, disable_caching=False,
                 **kwargs,
                 ):
        self.outfile = '-'
        self.no_laparams = no_laparams
        self.all_texts = all_texts
        self.detect_vertical = detect_vertical
        self.word_margin = word_margin
        self.char_margin = char_margin
        self.line_margin = line_margin
        self.boxes_flow = boxes_flow
        self.output_type = output_type
        self.codec = codec
        self.strip_control = strip_control
        self.maxpages = maxpages
        self.page_numbers = page_numbers
        self.password = password
        self.scale = scale
        self.rotation = rotation
        self.layoutmode = layoutmode
        self.output_dir = output_dir
        self.debug = debug
        self.disable_caching = disable_caching
        self.kwargs = kwargs

    def align_output_dir(self, suggested_dir):
        if not self.output_dir:
            self.output_dir = suggested_dir
            logger.info(F'Aligned output directory: {self.output_dir}')

    def align_output_file(self, suggested_file):
        if self.outfile == '-':
            temp = self.outfile
            self.outfile = suggested_file
            if not self._resolve_output_type():
                self.outfile = temp
                logger.warn(F'Failed to align output file: No output types '
                            F'match {suggested_file}')
            else:
                logger.info(F'Aligned output file: {self.outfile}')

    def build_extract_args(self):
        if self.outfile == '-':
            raise ValueError('No valid outfile has been supplied!')
        return dict(
            output_type=self.output_type,
            codec=self.codec,
            laparams=self._create_layout_arguments(),
            maxpages=self.maxpages,
            page_numbers=self.page_numbers,
            password=self.password,
            scale=self.scale,
            rotation=self.rotation,
            layoutmode=self.layoutmode,
            output_dir=self.output_dir,
            strip_control=self.strip_control,
            debug=self.debug,
            disable_caching=self.disable_caching,
            **self.kwargs
            )

    def _create_layout_arguments(self):
        if not self.no_laparams:
            laparams = LAParams()
            for param in ('all_texts', 'detect_vertical', 'word_margin',
                          'char_margin', 'line_margin', 'boxes_flow'):
                paramv = locals().get(param, None)
                if paramv is not None:
                    setattr(laparams, param, paramv)
        else:
            laparams = None
        return laparams

    def _resolve_output_type(self):
        """
        :returns: True if the output type was resolved, False o.w.
        """
        if self.output_type == 'text' and self.outfile != '-':
            for override, alttype in OUTPUT_TYPES:
                if self.outfile.endswith(override):
                    self.output_type = alttype
                    return True
        return False
