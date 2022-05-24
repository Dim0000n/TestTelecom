import wx
from Classes import mainFrame

if __name__ == "__main__":
    app = wx.App(False)         # запускаем приложение
    frame = mainFrame('TestTelecom', (600,400))         # создаем фрейм
    app.MainLoop()              # запускаем луп