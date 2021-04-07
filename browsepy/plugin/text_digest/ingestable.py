"""Ingestable file classes."""

from browsepy.compat import cached_property
from browsepy.file import Node, File, Directory


class IngestableNode(Node):
    """Base class for ingestable nodes."""

    @cached_property
    def title(self):
        """Get ingestable filename."""
        return self.name

    @cached_property
    def is_ingestable(self):
        # type: () -> bool
        """
        Get if node is ingestable.

        :returns: True if node is ingestable, False otherwise
        """
        return self.detect(self)

    @classmethod
    def detect(cls, node, fast=False):
        """Check if class supports node."""
        kls = cls.directory_class if node.is_directory else cls.file_class
        return kls.detect(node)


@IngestableNode.register_file_class
class IngestableFile(IngestableNode, File):
    """Generic node for filenames with extension."""

    ingestable_extensions = {
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'htm': 'text/html',
        'html': 'text/html',
        'md': 'text/markdown',
        'pdf': 'application/pdf',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'rtf': 'application/rtf',
        'txt': 'text/plain',
    }

    @cached_property
    def mimetype(self):
        """Get mimetype."""
        return self.detect_mimetype(self.path)

    @cached_property
    def extension(self):
        """Get filename extension."""
        return self.detect_extension(self.path)

    @classmethod
    def detect(cls, node, fast=False):
        """Get whether file is ingestable."""
        return (
            (fast or node.is_file) and
            cls.detect_extension(node.path) in cls.ingestable_extensions
        )

    @classmethod
    def detect_extension(cls, path):
        """Detect extension from given path."""
        for extension in cls.ingestable_extensions:
            if path.endswith('.%s' % extension):
                return extension
        return None

    @classmethod
    def detect_mimetype(cls, path):
        """Detect mimetype by its extension."""
        mime = cls.ingestable_extensions.get(
            cls.detect_extension(path),
            None
            )
        return mime


@IngestableNode.register_directory_class
class IngestableDirectory(IngestableNode, Directory):
    """Ingestable directory node."""

    @classmethod
    def detect(cls, node, fast=False):
        """Detect if the given node contains ingestable files."""
        return (
            node.is_directory and
            any(IngestableFile.detect(n, fast=True) for n in node._listdir())
        )
