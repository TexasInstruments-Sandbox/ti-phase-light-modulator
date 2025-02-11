import pathlib

here = pathlib.Path(__file__).parent


def test_display():
    from ti_phase_light_modulator.display import ImageWindow

    with ImageWindow() as win:
        win.load(here / '../examples/bird_p67_7cm.png')
    
    with ImageWindow() as win:
        win.load(here / '../examples')
    