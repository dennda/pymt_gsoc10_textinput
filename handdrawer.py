from pymt import *


class HandDrawer(MTWidget):
    def init(self):
        self.palm = None
        self.fingers = None
        self.knuckles = None
        self.touchfields = None

    def on_update(self):
        self.palm = self.fingers = self.knuckles = self.touchfields = None

        for touch in getCurrentTouches():
            if 'container' in touch.profile:
                self.palm = Vector(*touch.pos)
                self.fingers = [Vector(*touch.pos) for touch in touch.elements]
                # Hand found, break, don't return
                break
        else:
            # Executed if we didn't break out of the loop, i.e. no hand found.
            return

        self.fingers.sort()
        self.knuckles = [(f - self.palm) / 2 + self.palm for f in self.fingers]

        self.touchfields = []
        for f, k in zip(self.fingers, self.knuckles):
            self.touchfields.append([k + o * ((f - k) / 2) for o in range(1, 4)])


    def draw(self):
        if not (self.palm and self.fingers):
            return
        for finger in self.fingers:
            set_color(1, 0, 0)
            drawLine((finger.x, finger.y, self.palm.x, self.palm.y))
            set_color(0, 1, 0)
            drawCircle((finger.x, finger.y), 8)
        for knuckle in self.knuckles:
            set_color(1, 1, 0)
            drawCircle((knuckle.x, knuckle.y), 6)
        for touchfields in self.touchfields:
            set_color(0, 1, 1)
            for touchfield in touchfields:
                drawCircle((touchfield.x, touchfield.y), 12)
        for level in zip(*self.touchfields):
            drawLine(level)

        set_color(0, 0, 1)
        drawRectangle((self.palm.x, self.palm.y), (5, 5))


runTouchApp(HandDrawer())

