import sys
import os

# Добавляем путь к проекту
path = '/home/Veronika6585/telegram-miniapp'
if path not in sys.path:
    sys.path.append(path)

# Меняем рабочую директорию
os.chdir(path)

from main import app

application = app