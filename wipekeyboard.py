from pymt import *


class MTWipeKeyboard(MTSpellVKeyboard):
    def __init__(self, **kwargs):
        super(MTWipeKeyboard, self).__init__(**kwargs)
        # XXX
        self._lines = []
        self.label = MTLabel(label="", pos=(300, 300))
        self.add_widget(self.label)

    def draw(self):
        # XXX
        super(MTWipeKeyboard, self).draw()
        set_color(1, 0, 0, 0.8)
        if self._lines:
            drawLine(self._lines, width=5.)

    def _is_letter(self, key):
        return key in self.layout.LETTERS

    def on_touch_down(self, touch):
        self._lines = []
        if not self._layout_widget.visible:
            x, y = self.to_local(*touch.pos)
            keyinfo = self.get_key_at_pos(x, y)
            # XXX Why should it be None?
            if keyinfo is not None and self._is_letter(keyinfo[0]):
                self._clear_suggestions()
                # Memorize the position that the touch entered and left the key
                touch.userdata['collected_keys'] = [(keyinfo, [x, y, x, y])]
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
        if not keyinfo:
            return # XXX super?
        # If several move events are fired if the touch is still
        # inside the same key, we want to overwrite the last actual
        # touch position inside the key...
        if keyinfo == collected[-1][0]:
            collected[-1][1][2] = x
            collected[-1][1][3] = y
            return True
        # ...but we don't want to collect the key itself again.
        else:
            if self._is_letter(keyinfo[0]):
                collected.append((keyinfo, [x, y, x, y]))
                return True
        return super(MTVKeyboard, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        # XXX is it possible that last on_touch_move.pos != on_touch_up.pos??
        collected = touch.userdata.get('collected_keys')
        if collected is not None:
            print "".join(keyinfo[0][0][0] for keyinfo in collected)
            word = self.analyze_collected_keys(collected)
            print 'WINNER:', word
            self.label.label = word
            return True

    def analyze_collected_keys(self, keys):
        chars = [key[0][0][0] for key in keys]
        print chars
        if len(keys) == 1:
            word = chars[0]
        elif len(keys) == 2:
            word = "".join(chars)
        else:
            # Pretty sure the word starts with the first key that was touched.
            word = chars[0]
            positions = [key[1] for key in keys]
            self._lines = positions
            # The vectors between two keys. From old key to new key.
            # TODO Improve calculation below.
            vectors = []
            for index, pos in enumerate(positions[1:]):
                last_pos = positions[index]
                dx = pos[0] - last_pos[0]
                dy = pos[1] - last_pos[1]
                vectors.append(Vector(dx, dy))
            print 'vectors', vectors
            angles = []
            for index, vec in enumerate(vectors[1:]):
                last_vec = vectors[index]
                angle = last_vec.angle(vec)
                angles.append(angle)
            print 'angles', angles
            for index, angle in enumerate(angles):
                # XXX Find a proper threshold
                if abs(angle) > 30:
                    word = "".join((word, chars[index+1]))
                else:
                    print 'suppressed', chars[index+1]

            # Pretty sure the word ends with the last key that was touched.
            word = "".join((word, chars[-1]))
            print "ANGULAR:", word

        spell = self.spelling
        suggestions = spell.suggest(word)[:10]
        if spell.check(word):
            for suggestion in suggestions:
                self._add_suggestion(suggestion)
            return word
        else:
            for suggestion in suggestions[1:]:
                self._add_suggestion(suggestion)
            return suggestions[0] if suggestions else word



if __name__ == '__main__':
    wipe = MTWipeKeyboard()
    runTouchApp(wipe)
