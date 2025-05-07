# Demonstrate the display module for showing images fullscreen on an external monitor

from ti_plm.display import ImageWindow

# The ImageWindow object is designed for use with context managers so setup/cleanup is handled automatically, even if an exception is thrown inside the context.
# Here we init our window to be fullscreen on monitor index -1 (the last monitor). Then we load all images in the current working directory recursively.
# Finally, calling run() kicks off the event loop which listens for keyboard events (arrow keys to advance image, ESC to exit).
# Glob patterns or individual image file names can also be passed to load().
with ImageWindow(fullscreen=True, monitor=-1) as win:
    
    # Load all images in the current working directory recursively.
    # Alternatively, win.load() accepts a file name, dir name, PIL.Image, or pygame.Surface to make it easy to load images from a variety of sources.
    win.load('.', recursive=True)
    
    # Calling win.run() will start the internal event loop and block until the window is closed or the ESC key is pressed.
    # Instead of calling win.run() here, you can set up your own event loop and iteratively call win.load() to update the display manually.
    win.run()
