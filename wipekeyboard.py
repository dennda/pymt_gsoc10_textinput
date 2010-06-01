from pymt import *


class MTWipeKeyboard(MTVKeyboard):
    def _is_letter(self, key):
        return key in self.layout.LETTERS

    def on_touch_down(self, touch):
        if not self._layout_widget.visible:
            x, y = self.to_local(*touch.pos)
            keyinfo = self.get_key_at_pos(x, y)
            # XXX Why should it be None?
            if keyinfo is not None and self._is_letter(keyinfo[0]):
                touch.userdata['collected_keys'] = [keyinfo]
                # What about the active_keys?
                return True
        return super(MTVKeyboard, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        collected = touch.userdata.get('collected_keys')
        if collected is None:
            # Touch started outside of the widget, ignore it.
            return

        x, y = self.to_local(*touch.pos)
        keyinfo = self.get_key_at_pos(x, y)
        if keyinfo and keyinfo != collected[-1] and self._is_letter(keyinfo[0]):
            # If several move events are fired if the touch is still
            # inside the same key, we don't want to collect it.
            collected.append(keyinfo)
            return True
        return super(MTVKeyboard, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        # is it possible that last on_touch_move.pos != on_touch_up.pos??
        collected = touch.userdata.get('collected_keys')
        if collected is not None:
            print "".join(keyinfo[0][0] for keyinfo in collected)
            return True


if __name__ == '__main__':
    wipe = MTWipeKeyboard()
    runTouchApp(wipe)
