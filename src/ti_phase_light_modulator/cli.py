import argparse
import importlib.metadata
from . import __version__


def cli():
    
    parser = argparse.ArgumentParser(
        description=importlib.metadata.metadata(__package__).get('summary')
    )
    parser.set_defaults(func=lambda args: parser.print_help())
    parser.add_argument('-V', '--version', action='version', version=__version__)
    
    subparsers = parser.add_subparsers()
    
    display_parser = subparsers.add_parser(
        'display',
        help='Display images or directories of images fullscreen on external monitors'
    )
    display_parser.set_defaults(func=display)
    display_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to image or directory. If a directory path is provided, it will be scanned for image files (optionally recursively). If no path is provided, this command displays images from the current working directory.'
    )
    display_parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Scan path recursively for image files'
    )
    display_parser.add_argument(
        '--monitor', '-m',
        type=int,
        default=-1,
        help='Monitor index to use for image display'
    )
    
    args = parser.parse_args()
    args.func(args)


def display(args):
    from .display import ImageWindow, TIPLMDisplayException
    try:
        with ImageWindow(fullscreen=True, monitor=args.monitor) as win:
            win.load(args.path, args.recursive).run()
    except TIPLMDisplayException as e:
        print('Error:', e)
