class COLOR:
    GRAY = "#7A7A7A"
    BRIGHT = "#212335"
    MIDIUM = "#1A1C2E"
    DARK = "#101224"
    BUTTON = "#F5F3C2"
    BUTTON_DSIABLED = "#999682"
    BUTTON_AUTOGENERATE = "#F5B5B5"


MAIN_STYLESHEET = """
        QWidget {
            color: white;
            background-color: """ + COLOR.BRIGHT + """;
        }
        QTextEdit {
            background-color: """ + COLOR.DARK + """;
        }
        QLineEdit {
            background-color: """ + COLOR.DARK + """;
            border: 1px solid """ + COLOR.GRAY + """;
        }
        QComboBox {
            background-color: """ + COLOR.DARK + """;
            border: 1px solid """ + COLOR.GRAY + """;
        }
        QComboBox QAbstractItemView {
            border: 2px solid """ + COLOR.GRAY + """;
            selection-background-color: black;
        }
        QPushButton {
            color:black;
            background-color: """ + COLOR.BUTTON + """;
        }
        QPushButton:disabled {
            background-color: """ + COLOR.BUTTON_DSIABLED + """;
        }
        QSplitter::handle {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(0, 0, 0, 0),
            stop:0.1 rgba(0, 0, 0, 0),
            stop:0.1001 rgba(255, 255, 255, 255),
            stop:0.2 rgba(255, 255, 255, 255),
            stop:0.2001 rgba(0, 0, 0, 0),
            stop:0.8 rgba(0, 0, 0, 0),
            stop:0.8001 rgba(255, 255, 255, 255),
            stop:0.9 rgba(255, 255, 255, 255),
            stop:0.9001 rgba(0, 0, 0, 0));
            image: url(:/images/splitter.png);
         }
    """
