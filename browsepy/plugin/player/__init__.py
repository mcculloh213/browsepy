"""
Player plugin.

This plugin is both functional and simple enough to serve as example for:
- Blueprint registration.
- Widget with filtering function.
- Custom file nodes.
- Sorting cookie retrieval and usage.

"""
from flask import Blueprint, abort
from browsepy import get_cookie_browse_sorting, browse_sortkey_reverse
from browsepy.stream import stream_template

from .playable import PlayableNode, PlayableDirectory, PlayableFile


player = Blueprint(
    'player',
    __name__,
    url_prefix='/play',
    template_folder='templates',
    static_folder='static',
    )


@player.route('/', defaults={'path': ''})
@player.route('/<path:path>')
def play(path):
    """
    Handle player requests.

    :param path: path to directory
    :type path: str
    :returns: flask.Response
    """
    sort_property = get_cookie_browse_sorting(path, 'text')
    sort_fnc, sort_reverse = browse_sortkey_reverse(sort_property)
    node = PlayableNode.from_urlpath(path)
    if node.is_playable and not node.is_excluded:
        return stream_template(
            'audio.player.html',
            file=node,
            sort_property=sort_property,
            sort_fnc=sort_fnc,
            sort_reverse=sort_reverse,
            playlist=node.playable_list,
            )
    abort(404)


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
        '--player-directory-play', action='store_true',
        help='enable directories as playlist'
        )


def register_plugin(manager):
    """
    Register blueprints and actions using given plugin manager.

    :param manager: plugin manager
    :type manager: browsepy.manager.PluginManager
    """
    manager.register_blueprint(player)
    manager.register_mimetype_function(PlayableFile.detect_mimetype)

    # add style tag
    manager.register_widget(
        place='styles',
        type='stylesheet',
        endpoint='player.static',
        filename='css/browse.css'
        )

    # register link actions
    manager.register_widget(
        place='entry-link',
        type='link',
        endpoint='player.play',
        filter=PlayableFile.detect,
        )

    # register action buttons
    manager.register_widget(
        place='entry-actions',
        css='play',
        type='button',
        endpoint='player.play',
        filter=PlayableFile.detect,
        )

    # check argument (see `register_arguments`) before registering
    if manager.get_argument('player_directory_play'):
        # register header button
        manager.register_widget(
            place='header',
            type='button',
            endpoint='player.play',
            text='Play directory',
            filter=PlayableDirectory.detect,
            )
