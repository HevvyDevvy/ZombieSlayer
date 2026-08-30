import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from gui import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def load_stylesheet(app: QApplication) -> None:
    qss_path = Path(__file__).resolve().parent / "gui" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Zombie Slayer")
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
