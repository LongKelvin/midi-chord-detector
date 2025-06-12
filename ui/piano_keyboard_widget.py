# --- PianoKeyWidget (can be in a new file or same UI file) ---
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPolygonF
from PyQt6.QtCore import Qt, QPointF, pyqtSignal

class PianoKeyWidget(QWidget):
    key_pressed_signal = pyqtSignal(int, bool) # midi_note, is_on

    def __init__(self, midi_note: int, is_black: bool, parent=None):
        super().__init__(parent)
        self.midi_note = midi_note
        self.is_black = is_black
        self.is_pressed = False

        self.setMinimumSize(10, 30) # Ensure it's visible

        # Colors (can be customized further via QSS or properties)
        self.color_white_key = QColor("#FFFFFF")
        self.color_black_key = QColor("#222222")
        self.color_pressed_white = QColor("#AED6F1") # Light blue for pressed white
        self.color_pressed_black = QColor("#5DADE2") # Brighter blue for pressed black
        self.color_border = QColor("#000000")

    def set_pressed(self, pressed: bool):
        if self.is_pressed != pressed:
            self.is_pressed = pressed
            self.update() # Trigger a repaint
            # self.key_pressed_signal.emit(self.midi_note, pressed) # If key itself emits

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect() # Gets the widget's current geometry

        if self.is_black:
            key_color = self.color_pressed_black if self.is_pressed else self.color_black_key
        else:
            key_color = self.color_pressed_white if self.is_pressed else self.color_white_key

        painter.setBrush(QBrush(key_color))
        painter.setPen(QPen(self.color_border, 1)) # Border for all keys
        painter.drawRect(rect)

        # Optional: Add note name text (might be too small on individual keys)
        # if not self.is_black and self.height() > 50: # Only for larger white keys
        #     font = painter.font()
        #     font.setPointSize(max(6, int(self.height() / 12)))
        #     painter.setFont(font)
        #     note_name = ChordTheory.midi_to_pitch_class_name(self.midi_note)
        #     octave = self.midi_note // 12 -1
        #     painter.setPen(self.color_black_key if not self.is_pressed else self.color_white_key)
        #     painter.drawText(rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, f"{note_name}{octave}")


    # Allow clicking on keys for testing (optional)
    def mousePressEvent(self, event):
        self.set_pressed(True)
        # In a real app, this might also trigger a sound or send a MIDI message out
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.set_pressed(False)
        super().mouseReleaseEvent(event)