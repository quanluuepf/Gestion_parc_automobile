import sys
import os

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import init_db, get_connection
from src.ui.dashboard import DashboardApp

def main():
    init_db()
    app = DashboardApp()
    app.run()

if __name__ == '__main__':
    main()
