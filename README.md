# TestTelecom

Добрый день!

Согласно техническому заданию разработан TCP-сервер, который:

1. Распознает формат данных типа: BBBBxNNxHH:MM:SS.zhqxGGCR,
    где BBBB - номер участника, x - пробельный символ, NN - id канала; HH - Часы, MM - минуты, SS - секунды, zhq - десятые, сотые, тысячные, 
    GG - номер группы, CR - «возврат каретки»
2. Вводит в GUI принятый пакет в виде: "спортсмен, нагрудный номер BBBB прошёл отсечку NN в «время»(до десятых, сотые и тысячные отсекаются)" в случае,
   если номер группы равен "00"
4. Производит запись пакета в файл log.txt в корневую папку приложения, вне знависимости от номера группы участника
5. Не выводит и не пишет в лог пакеты, отличные по формату от исходного.
6. Поддерживает передачу данных с помощью telnet-клиентов, таких как PuTTY



В дополнение, для наглядности, в приложении реализована клиентская часть, которая позволяет отправлять пакеты данных по TCP-протоколу внутри самого приложения.

Для реализации протокола приема-передачи данных используется стандартный фреймвор Python socket, который разворачивается по адресу 127.0.0.1:8888. 
Серверная часть приложения запущена в отдельном потоке класса sockThread, наследующего класс threading.Thread, что позволяет не блокировать UI 
приложения при ожидании покдлючения клиентов и передачи данных.

При подключении клиента сервер ожидает передачи пакета используя блокировку потока, после чего разрывает соединение. Было замечено, 
что при подключении telnet-клиента PuTTY на сервер отправляется служебный пакет в кодировке, отличной от utf8. Для решения указанной проблемы предложено 
переведение сервера в ожидание повтороной отправки пакета (пользовательского, в кодировке utf-8) в течение 60 секунд с последующим разрывом соединения (в случае, когда служебный пакат не отправляется, повторного прием данных не вызывается). После получения пакет проверяется на соответствие формату данных, обрабатывается, пишется в лог и передается в UI приложения с помощью объекта pub  библиотеки PyPubSub.

Для проверки на валидность и обработки пакета применяются регулярные выражения, написанные с использованием стандартного модуля re. 
Стоит отметить, что пакеты клиента PuTTY содержат окончание в виде "CRLF", а не "CR", поэтому обработка данного варианта пакета также была реализована.

GUI приложения написано с применением фреймворка wxPython и содержит окна ввода пакета для отправления и вывода обработанных данных; кнопку "Отправить сообщение",при нажатии на которое инициализируется socket-клинет, с помощью которого осуществляется передача строки из окна ввода на сервер; кнопку 
"Выход", завершающую работу приложения.

Для компиляции программы используется PyInstaller, дистрибутив располагается по пути /dist/TestTelecom.

---------------------------------------------------------------------
C уважением, 
Дмитрий Утев.
