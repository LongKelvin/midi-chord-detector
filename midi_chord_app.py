import sys
from PyQt6.QtWidgets import (
    QApplication
)

from ui.main_window import ChordAppMainWindow



if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    
    # Load and apply a QSS stylesheet for a more modern look (optional)
    # You can create a "style.qss" file or embed it.
    # try:
    #     with open("style.qss", "r") as f:
    #         app.setStyleSheet(f.read())
    # except FileNotFoundError:
    #     print("style.qss not found, using default styles.")

    main_window = ChordAppMainWindow()
    main_window.show()
    sys.exit(app.exec())