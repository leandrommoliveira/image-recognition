import sys
import pytesseract
import clipboard

from PIL import Image
from PyQt4 import QtCore, QtGui
from io import StringIO
from subprocess import getoutput
from Xlib import X, display, Xutil

class XSelect:
    def __init__(self, display):
        # X display
        self.d = display

        # Screen
        self.screen = self.d.screen()

        # Draw on the root window (desktop surface)
        self.window = self.screen.root
        self.result = None

        # If only I could get this working...
        #cursor = xobject.cursor.Cursor(self.d, Xcursorfont.crosshair)
        #cursor = self.d.create_resource_object('cursor', Xcursorfont.X_cursor)
        cursor = X.NONE

        self.window.grab_pointer(1, X.PointerMotionMask|X.ButtonReleaseMask|X.ButtonPressMask,
                X.GrabModeAsync, X.GrabModeAsync, X.NONE, cursor, X.CurrentTime)

        self.window.grab_keyboard(1, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)

        colormap = self.screen.default_colormap
        color = colormap.alloc_color(0, 0, 0)
        # Xor it because we'll draw with X.GXxor function
        xor_color = color.pixel ^ 0xffffff

        self.gc = self.window.create_gc(
            line_width = 1,
            line_style = X.LineSolid,
            fill_style = X.FillOpaqueStippled,
            fill_rule  = X.WindingRule,
            cap_style  = X.CapButt,
            join_style = X.JoinMiter,
            foreground = xor_color,
            background = self.screen.black_pixel,
            function = X.GXxor,
            graphics_exposures = False,
            subwindow_mode = X.IncludeInferiors,
        )

        done    = False
        started = False
        start   = dict(x=0, y=0)
        end     = dict(x=0, y=0)
        last    = None
        drawlimit = 10
        i = 0

        while done == False:
            e = self.d.next_event()

            # Window has been destroyed, quit
            if e.type == X.DestroyNotify:
                sys.exit(0)

            # Mouse button press
            elif e.type == X.ButtonPress:
                # Left mouse button?
                if e.detail == 1:
                    start = dict(x=e.root_x, y=e.root_y)
                    started = True

                # Right mouse button?
                elif e.detail == 3:
                    sys.exit(0)

            # Mouse button release
            elif e.type == X.ButtonRelease:
                end = dict(x=e.root_x, y=e.root_y)
                if last:
                    self.draw_rectangle(start, last)
                done = True
                pass

            # Mouse movement
            elif e.type == X.MotionNotify and started:
                i = i + 1
                if i % drawlimit != 0:
                    continue

                if last:
                    self.draw_rectangle(start, last)
                    last = None

                last = dict(x=e.root_x, y=e.root_y)
                self.draw_rectangle(start, last)
                pass

            # Keyboard key
            elif e.type == X.KeyPress:
                sys.exit(0)

        self.d.flush()

        coords = self.get_coords(start, end)
        if coords['width'] <= 1 or coords['height'] <= 1:
            sys.exit(0)
        else:
            self.result = "%d %d %d %d" % (coords['start']['x'], coords['start']['y'], coords['width'], coords['height'])

    def get_coords(self, start, end):
        safe_start = dict(x=0, y=0)
        safe_end   = dict(x=0, y=0)

        if start['x'] > end['x']:
            safe_start['x'] = end['x']
            safe_end['x']   = start['x']
        else:
            safe_start['x'] = start['x']
            safe_end['x']   = end['x']

        if start['y'] > end['y']:
            safe_start['y'] = end['y']
            safe_end['y']   = start['y']
        else:
            safe_start['y'] = start['y']
            safe_end['y']   = end['y']

        return {
            'start': {
                'x': safe_start['x'],
                'y': safe_start['y'],
            },
            'end': {
                'x': safe_end['x'],
                'y': safe_end['y'],
            },
            'width' : safe_end['x'] - safe_start['x'],
            'height': safe_end['y'] - safe_start['y'],
        }

    def draw_rectangle(self, start, end):
        coords = self.get_coords(start, end)
        self.window.rectangle(self.gc,
            coords['start']['x'],
            coords['start']['y'],
            coords['end']['x'] - coords['start']['x'],
            coords['end']['y'] - coords['start']['y']
        )


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    stdout = sys.stdout
    sys.stdout = StringIO()
    d = display.Display()
    sys.stdout = stdout

    resArea = None
    while not resArea or resArea == '0 0 0 0':
        resArea = XSelect(d)

    area = xo, yo, x, y = resArea.result.split()
    pixMap = QtGui.QPixmap.grabWindow(QtGui.QApplication.desktop().winId())
    qi = pixMap.toImage()
    qi = qi.copy(int(area[0]), int(area[1]), int(area[2]), int(area[3]))
    pixMap = QtGui.QPixmap.fromImage(qi)
    pixMap.save('/tmp/print_temp.png', 'png')

    text = pytesseract.image_to_string(Image.open('/tmp/print_temp.png'))
    clipboard.copy(text)
    print(text)