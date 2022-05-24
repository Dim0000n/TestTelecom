import wx           # фремворк для GUI
import socket       # библиотека для создание TCP подключения
import re           # библиотека регулярных выражений
import datetime     # для записи текущей даты и времени в лог
from threading import Thread        # импорт класса потоков
from pubsub import pub              # для общения между потоками


class sockThread(Thread):

    '''
    Класс sockThread реализует принятие данных через TCP протокол в отдельном потоке, наследует Thread
    '''

    def __init__(self): # конструктор

        super().__init__() #конструктор суперкласса

        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)  # инициализация сокета AF_NET  - семейство адресов IPv4, SOCK_STREAM - использование протокола TCP
        # Setup TCP socket
        self.socket.bind(('127.0.0.1', 8888)) # биндим сокет на localhost на порт 8888
        self.socket.listen(5)        # очередь максимум из 5 клиентов
        self.setDaemon(True)         #deamon-поток
        self.start()


    # реализация метода run
    def run(self):

        while True:             # бесконечный цикл пиема данных
            try:
                self.socket.settimeout(None)            # бесконечное ожидание подключение
                client, addr = self.socket.accept()     # рукопожатие

            except socket.error:                        # обработка исключений
                break

            else:
                received = client.recv(1024)            # принимаем пакет
                try:
                    answer = received.decode('utf-8')  # попытка декодировать пакет в utf-8

                except:
                    '''
                    В случае с telnet клиентом, таким как putty, первый пакет является служебным, его кодировка не utf-8
                    А второй пакет содержит переданное пользователем сообщение
                    '''
                    try:
                        client.settimeout(60)               # выставление таймаута 60 секунд для клиента
                        received = client.recv(1024)        # получение пакета
                        answer = received.decode('utf-8')   # декодирование пакета
                    except:
                        pass                                # в случае исключения

                client.close()  # закрываем соединение с клиентом


                result, willShow = self.__prepareDataToWrite(answer) #подготовка пакета к записи


                if len(result) != 0:                # если ответ не пустой
                    with open('log.txt','a') as f:  # открытие файла лога на дозапись
                        now = datetime.datetime.now()                           # получение текущих даты и времени
                        f.write(now.strftime("%d-%m-%Y %H:%M:%S") + " " + result + "\n")     # запись лога

                if not willShow:                    # если запись не отображается
                    result=""                       # обнуляем результирующую переменную для удаления предыдущей записи из ui

                wx.CallAfter(pub.sendMessage,"update", msg=result) #отправляем соообщение в ui через объект pubsub



        # shutdown the socket
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass

        self.socket.close()

    #приватный метод для подготовки данных к записи в файл и выводу на экран
    def __prepareDataToWrite(self, data):
        '''

        :param data: - полученные данные

        :return:
        result - подготовленные данные
        willShow - флаг, определяющий, будут ли данные выводиться на экран

        При отправлении данных с telnet-клиента putty в конце пакета добавляется не rf, а lfrf,
        поэтому в обработке пакета рассматривается два случая: длина пакета - 24, последний символ rf;

        Длина пакета  - 25, последние два символа lfrf
        '''

        error = False                   # флаг ошибки

        if len(data) == 25:             # длина пакета 25
            if data[23:25] != '\r\n':   # последние два символа не соответствует

                error = True            # поднимается флаг ошибки

        elif len(data) == 24:           # длина пакета 24
            if data[23] != '\r':        # последний символ не соответствует
                error = True            # поднимается флаг ошибки

        else:                           # если длина пакета не соответствует
            error = True                # поднимается флаг ошибки


        if not error:                   # если флаг ошибки не поднят

            data = data[:23]        # отбрасывает служебные символы/символ
            data_list = data.split(' ')     # делим данные по символу пробела


            if len(data_list) == 4:  # если список размерностью 4, работаем дальше
                re_patterns = [r'\d{4}', r'.{2}', r'\d\d[:]\d\d[:]\d\d[.]\d{3}', r'\d{2}'] # паттерны регулярных выражений

                for i in range(4):
                    if re.fullmatch(re_patterns[i], data_list[i]) == None:           # если элемент не соответсвует паттерну
                        error = True                                                 # поднимается флаг
                        break                                                        # останавливается цикл

            else:                   # размер списка не соответствует
                error = True        # поднимается флаг ошибки

        willShow = False  # флаг, определяющий, будут ли данные выводиться на экран
        result = ''  # обработанный пакет
        if not error:

            time_list = data_list[2].split(':')     # разделяем время для отброса долей секунд
            time_list[2] = "{}".format(int(float(time_list[2])*10)/10.)     # отбрасываем все, кроме десятых
            time_ = ":".join(time_list)              # объединение времени в строку

            result = 'спортсмен, нагрудный номер {} прошел отсечку {} в {}'\
                .format(data_list[0],data_list[1],time_)  # результирующая строка

            if data_list[3] == '00':
                willShow = True
        return result, willShow



class mainFrame(wx.Frame):
    """
    Класс mainFrame наследует класс wx.Frame
    """

    # конструктор класса
    def __init__(self, title, size):

        super().__init__(parent=None, title=title, size=size)      # кноструктор родительского класса
        #panel = mainPanel(self)
        self.panel = wx.Panel(self)

        gs = wx.GridBagSizer(10, 5)  # создание сайзера

        # добавление текста к окнам ui
        gs.Add(wx.StaticText(self.panel, label="Сообщение для отправки"), pos=(0, 0), span=(1,2), flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        gs.Add(wx.StaticText(self.panel, label="Принятое сообщение"), pos=(0, 2), span=(1,2), flag=wx.ALIGN_CENTER | wx.TOP, border=10 )

        # создание окон для ввода и вывода сообщений
        self.textReceived = wx.TextCtrl(self.panel, value="", style=wx.TE_MULTILINE | wx.TE_READONLY )
        self.textToSend = wx.TextCtrl(self.panel, value="", style=wx.TE_MULTILINE)

        # добавление окон в сайзер
        gs.Add(self.textToSend, pos=(1, 0), span=(2, 2), flag=wx.EXPAND | wx.ALL, border=5)
        gs.Add(self.textReceived, pos=(1, 2), span=(2, 2), flag=wx.EXPAND | wx.ALL, border=5)

        # создание кнопок для отправки пакета и выхода из программы
        bt_send = wx.Button(self.panel, label="Отправить сообщение", id=wx.ID_ANY, size=(160,25))
        bt_exit = wx.Button(self.panel, label="Выход", id=wx.ID_ANY, size=(160,25))

        # добавление кнопок в сайзер
        gs.Add(bt_send, pos=(3, 0), span=(1,2), flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        gs.Add(bt_exit, pos=(3, 2),  span=(1,2), flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        # растягиваем некоторые столбцы и строки сайзера для красивого размещения аиджетов на экране
        gs.AddGrowableRow(2)
        gs.AddGrowableCol(1)
        gs.AddGrowableCol(2)


        self.panel.SetSizer(gs)                         #устанавливаем сайзер

        pub.subscribe(self.updateDisplay, "update")     # выставляем функцию обработки обновления интерфейса при получении пакета по tcp


        self.server = sockThread()                      # поток сервера

        self.Bind(wx.EVT_BUTTON, self.onSendMsg, bt_send)     # биндим обработчик нажатия кнопки отправки данных
        self.Bind(wx.EVT_BUTTON, self.onExit, bt_exit)  # биндим обработчик нажатия кнопки отправки данных
        self.Show()                                     # отображие фрейма

    # обработчик нажатия кнопки отправки данных
    def onSendMsg(self, event):
        """
        Отправляет пакет на сервер, запущенный в потоке sockThread
        """


        message =  self.textToSend.GetValue().encode('utf-8') # получение сообщения из окна и преобразование его в байт

        if message:                                       # если не пуста строка
            if message[-1] != b'\r' and len(message) > 1: # если последний символ не равен возврату коретки и длина сообщения больше 1
                if message[-1] == 10 and message[-2] != 13: # если последний символ "перенос" строки и предпоследний сивол не "возврат каретки"
                    message = message[:-1] + b'\r'                          # замена последнего символа на "возврат коретки"

                else:
                    message += b'\r'                              # иначе добавление возврата коретки

            client = socket.socket(socket.AF_INET,
                               socket.SOCK_STREAM)  # создание клиентского сокета
            try:
                client.connect(('127.0.0.1', 8888))             # подключение к хосту
                client.send(message)                            # отправка сообщения

            except socket.error:
                pass
            finally:
                client.close()                                  # закрытие сокета

    def onExit(self, event):
        self.Destroy()
    #обновляет окно принятых данных
    def updateDisplay(self, msg):

        self.textReceived.SetValue(msg)