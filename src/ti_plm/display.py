"""
This module provides structures to help display content on external monitors via HDMI/DP. It is based on pygame so
make sure you have installed the latest version in your python environment.
"""

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from glob import glob
import pathlib
import logging
import param

try:
    import pygame as pg
    from pygame._sdl2 import Window as PGWindow, Texture, Renderer
    from PIL.Image import Image
    from screeninfo.screeninfo import get_monitors
except ImportError as e:
    msg = '`ti_plm.display` module requires `pygame`, `pillow`, and `screeninfo` to be installed. Please install these with pip/conda and try again.'
    try:
        e.add_note(msg)
    except:
        e.msg = f'{e.msg}\n{msg}'
    raise e

from . import TIPLMException

log = logging.getLogger()

IMAGE_EXTENSIONS = ('.png', '.bmp', '.jpg', '.jpeg', '.tif', '.tiff')


class TIPLMDisplayException(TIPLMException):
    pass


class EventLoopExit(TIPLMDisplayException):
    pass


class EventLoop(param.Parameterized):

    fps = param.Integer(default=30, doc='Target FPS for event loop')
    
    enable_escape_exit = param.Boolean(default=True, doc='Enable/disable using the `ESC` key to exit the event loop.')
    
    init_callback = param.Callable(doc='Custom callback function that will be invoked before event loop starts.')
    
    loop_callback = param.Callable(doc='Custom callback function that will be invoked at the beginning of each loop.')
    
    keydown_callback = param.Callable(doc='Custom callback function that will be invoked when a key is pressed. The `key` value from the event object will be passed to the function.')
    
    exit_callback = param.Callable(doc='Custom callback function that will be invoked after event loop exits.')
    
    def __init__(self, **params):
        pg.init()
        self._clock = pg.time.Clock()
        super().__init__(**params)
    
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()
    
    def start(self):
        """Optionally overload this function in subclass"""
    
    def stop(self):
        """Optionally overload this function in subclass"""
    
    def update(self):
        """Optionally overload this function in subclass"""

    def draw(self):
        """Optionally overload this function in subclass"""
    
    def loop(self):
        """Run a single event loop, calling update() and draw() once"""
        
        if callable(self.loop_callback):
            self.loop_callback()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                raise EventLoopExit
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE and self.enable_escape_exit:
                    raise EventLoopExit
                if callable(self.keydown_callback):
                    self.keydown_callback(event.key)
                if hasattr(self, 'on_keydown'):
                    self.on_keydown(event.key)

        self.update()
        self.draw()
        self._clock.tick(self.fps)
    
    def run(self):
        """Run the event loop until something raises EventLoopExit.
        This will happen automatically if the pg.QUIT event is received or the ESC key is pressed.
        """
        
        if callable(self.init_callback):
            self.init_callback()
        
        while True:
            try:
                self.loop()
            except EventLoopExit:
                break
        
        if callable(self.exit_callback):
            self.exit_callback()
            

class Window(EventLoop):
    
    enable_fullscreen_toggle = param.Boolean(default=True, doc='Enable/disable fullscreen toggle using the `f` key.')
    
    hide_mouse_fullscreen = param.Boolean(default=True, doc='Whether or not to hide the mouse when the window is fullscreen.')
    
    fullscreen = param.Boolean(default=False, doc='Enable/disable fullscreen')
    
    monitor = param.Integer(default=-1, doc='Select the monitor index where the window should be. This can also be updated after the window is created to move the window programmatically.')
    
    def __init__(self, **params):
        # init monitors array and set bounds on monitor index param (to allow negative indexing)
        self._monitors = get_monitors()
        self.param.monitor.bounds = [-len(self._monitors), len(self._monitors) - 1]
        self._window = None
        self._renderer = None
        super().__init__(**params)
    
    @param.depends('fullscreen', 'monitor', watch=True)
    def _update_window(self):
        """Internal function that runs automatically any time fullscreen or monitor params are changed.
        
        It positions the window on the desired monitor and enables/disables fullscreen.
        """
        mon = self._monitors[self.monitor]
        self._window.position = mon.x, mon.y
        if self.fullscreen:
            self._window.set_fullscreen(True)
            if self.hide_mouse_fullscreen:
                pg.mouse.set_visible(False)
        else:
            self._window.set_windowed()
            pg.mouse.set_visible(True)
    
    def start(self):
        """Create pygame window"""
        super().start()
        if self._window is None:
            self._window = PGWindow(opengl=True, resizable=True)
            self._renderer = Renderer(self._window, vsync=True)
            self._update_window()
            self._window.focus()
    
    def stop(self):
        """Destroy pygame window"""
        if self._window is not None:
            self._window.destroy()
            self._renderer = None
        self._window = None
        super().stop()


class ImageWindow(Window):
    
    index = param.Integer(doc='Image index to display')
    
    def __init__(self, **params):
        self._imgs = []
        super().__init__(**params)
    
    def load(self, img: str | pathlib.Path | Image | pg.Surface, recursive: bool = False):
        """Load an image or series of images for displaying in this window. Image are appended to the 
        current list of images. Call .clear() to remove all images from the list.

        Args:
            img (str | pathlib.Path | Image | pg.Surface): Input image path, glob string, PIL Image, or pygame Surface
            recursive (bool, optional): Whether or not recursive globing is used on input glob string. Defaults to False.

        Raises:
            TIPLMDisplayException: Error loading requested image(s)
        """
        if isinstance(img, (str, pathlib.Path)):
            p = pathlib.Path(img)
            if p.is_dir():
                paths = list((p.rglob if recursive else p.glob)('*'))
            else:
                paths = [pathlib.Path(p) for p in glob(str(img), recursive=recursive)]
            self._imgs.extend([p for p in paths if p.suffix.lower() in IMAGE_EXTENSIONS])
            if len(self._imgs) == 0:
                raise TIPLMDisplayException(f'No images found for input path "{img}"')
        elif isinstance(img, Image):
            if img.mode != 'RGB':
                img = img.convert('RGB')
            self._imgs.append(pg.image.frombytes(img.tobytes(), img.size, img.mode))
        elif isinstance(img, pg.Surface):
            self._imgs.append(img)
        else:
            raise TIPLMDisplayException('Error loading image. Type must be str, pathlib.Path, PIL.Image.Image, or pg.Surface.')
        
        # Reset index to 0, but discard event because we'll manually trigger it later. This ensures event is triggered even if index is already 0.
        with param.discard_events(self):
            self.index = 0
        
        # Manually trigger index param to update texture
        self.param.trigger('index')
        
        return self
    
    def clear(self):
        """Clear image list. This will also clear the image window."""
        self._imgs.clear()
        with param.discard_events(self):
            self.index = 0
        self.param.trigger('index')
    
    @param.depends('index', watch=True)
    def _update_texture(self):
        """Update texture and render image defined by `index` param
        """
        self._renderer.clear()
        
        if len(self._imgs) > 0:
            img = self._imgs[self.index % len(self._imgs)]
        
            if isinstance(img, (str, pathlib.Path)):
                img = pg.image.load(img)
        
            tex = Texture.from_surface(self._renderer, img)
            self._renderer.blit(tex, tex.get_rect())
            
        self._renderer.present()

    def next(self):
        """Display next image if multiple images have been loaded"""
        if len(self._imgs) > 0:
            self.index = (self.index + 1) % len(self._imgs)
        return self
    
    def previous(self):
        """Display previous image if multiple images have been loaded"""
        if len(self._imgs) > 0:
            self.index = (self.index - 1) % len(self._imgs)
        return self
    
    def on_keydown(self, key):
        """Handle keydown event to trigger next/previous image"""
        if key == pg.K_TAB or key == pg.K_RIGHT or key == pg.K_SPACE:
            self.next()
        elif key == pg.K_LEFT:
            self.previous()
