import pathlib

here = pathlib.Path(__file__).parent


def test_display():
    try:
        from ti_plm.display import ImageWindow
    except ImportError:
        print('Skipping test_display: ti_plm installed without `display` module support')
        return

    with ImageWindow() as win:
        win.load(here / '../examples/bird_p67_7cm.png')
    
    with ImageWindow() as win:
        win.load(here / '../examples')
    