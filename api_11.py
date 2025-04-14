import sys
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QStyleFactory
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPalette, QColor, QCursor
from ui_11 import Ui_MainWindow
import re


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # загружаем интерфейс
        self.setMouseTracking(True)
        self.spn = 0.01  # масштаб
        # self.camera = [0.0, 0.0]
        self.camera = [55.796181, 49.105549]  # координаты камеры
        self.current_coord = []  # координаты метки
        self.pt = ''
        self.theme = 'dark'  # тема

        self.lightTheme = QPalette(QColor("#cfcfcf"))  # светлая тема
        self.darkTheme = QPalette(QColor("#424242"))  # темная тема
        self.setPalette(self.darkTheme)

        self.part3 = '' # фильтр

        self.findButton.clicked.connect(self.find_by_address)
        self.clearButton.clicked.connect(self.check_coords)
        self.themeButtonGroup.buttonClicked.connect(self.changeTheme)  # выбор темы
        self.lineEdit.returnPressed.connect(self.find)  # поиск
        self.postIndexCheckBox.clicked.connect(self.find)
        self.mapTypeComboBox.currentIndexChanged.connect(self.chooseStyle) # выбор типа карты
        QTimer.singleShot(100, self.show_map)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cursor_position)
        self.timer.start(100)  # Обновление каждые 100 мс
    
    def update_cursor_position(self):
        cursor_pos = QCursor.pos()
        self.mouse_coords = [cursor_pos.x(), cursor_pos.y()]
        # self.coords_label.setText(f'x={cursor_pos.x()}, y={cursor_pos.y()}')
     
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if (835 <= self.mouse_coords[0] <= 1355) and (345 <= self.mouse_coords[1] <= 715):
                new_coord = [0, 0]
                # new_coord[0] = str(self.camera[0] - ((self.mouse_coords[1] - 532)) * 0.00003)
                # new_coord[1] = str(self.camera[1] + ((self.mouse_coords[0] - 1095)) * 0.00005)
                new_coord[0] = str(self.camera[0] - ((self.mouse_coords[1] - 532)) * self.spn * 0.003)
                new_coord[1] = str(self.camera[1] + ((self.mouse_coords[0] - 1095)) * self.spn * 0.005)
                self.show_object(address=new_coord)

    def show_map(self, address=0):
        # получаем данные введенные пользователем
        if address == 0:
            address = self.lineEdit.text()
        # проверяем что пользователь что-то ввел
        if len(address) != 0:
            # ищем координаты по паттерну
            sp = re.findall(r"\d*\.\d*", address)

            # если это новый запрос
            if not self.current_coord:
                # если пользователь ввел координаты
                if len(sp) == 2:
                    self.current_coord = sp.copy()  # координатам текущей метки присваиваем полученные координаты
                    self.camera = list(map(float, sp))  # координатам камеры присваиваем полученные координаты

                    # адрес запроса
                    self.pt = f'&pt={str(self.current_coord[1])},{str(self.current_coord[0])}'
                    part1 = f'https://static-maps.yandex.ru/v1?lang=ru_RU&ll={str(self.camera[1])},{str(self.camera[0])}&'
                    part2 = f'spn={str(self.spn)},{str(self.spn)}&theme={self.theme}' + self.pt
                    part4 = '&apikey=ffc0b51c-c15b-47a7-a368-80493d99e48c'
                    map_request = part1 + part2 + self.part3 + part4

                    # делаем запрос
                    response = requests.get(map_request)
                    if not response:
                        self.statusBar().showMessage('Неверный запрос.')
                        print('1', "Http статус:", response.status_code, "(", response.reason, ")")
                        QTimer.singleShot(3000, self.statusBar().clearMessage)

                    # сохраняем изображение из запроса в файле
                    map_file = "map.png"
                    with open(map_file, "wb") as file:
                        file.write(response.content)
                    # отображаем изображение на экране
                    self.pixmap = QPixmap(map_file)
                    self.label.setPixmap(self.pixmap.scaled((self.label.size())))
                    api_key = "8013b162-6b42-4997-9691-77b7074026e0"
                    server_address = 'http://geocode-maps.yandex.ru/1.x/?'
                    geocoder_request = f'{server_address}apikey={api_key}&geocode={str(self.camera[1])},{str(self.camera[0])}&format=json'
                    # делаем запрос
                    response = requests.get(geocoder_request)
                    # если удачно
                    if response:
                        # парсим запрос
                        json_response = response.json()

                        # получаем нужные нам данные
                        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0][
                            "GeoObject"]  # гео.объект
                        toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                        toponym_coodrinates = toponym["Point"]["pos"]  # координаты гео.объекта
                        if self.postIndexCheckBox.isChecked():
                            try:
                                post_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
                                self.addressLabel.setText(toponym_address + '\n' + 'Почтовый индекс: ' + post_code)
                            except Exception:
                                self.addressLabel.setText(toponym_address)
                        else:
                            self.addressLabel.setText(toponym_address)
                else:
                    # адрес запроса
                    api_key = "8013b162-6b42-4997-9691-77b7074026e0"
                    server_address = 'http://geocode-maps.yandex.ru/1.x/?'
                    geocoder_request = f'{server_address}apikey={api_key}&geocode={address}&format=json'

                    # делаем запрос
                    response = requests.get(geocoder_request)
                    # если удачно
                    if response:
                        # парсим запрос
                        json_response = response.json()

                        # получаем нужные нам данные
                        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"]
                        if toponym:
                            toponym = toponym[0]["GeoObject"]  # гео.объект
                            toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                            toponym_coodrinates = toponym["Point"]["pos"]  # координаты гео.объекта
                            if self.postIndexCheckBox.isChecked():
                                try:
                                    post_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
                                    self.addressLabel.setText(toponym_address + '\n' + 'Почтовый индекс: ' + post_code)
                                except Exception:
                                    self.addressLabel.setText(toponym_address)
                            else:
                                self.addressLabel.setText(toponym_address)
                            sp = toponym_coodrinates.split(' ')  # разделяем полученные координаты на два значения
                            sp.reverse()  # меняем местами longitude и latitude

                            # если это новый запрос
                            if not self.current_coord:
                                self.current_coord = sp.copy()  # координатам текущей метки присваиваем полученные координаты
                                self.camera = list(map(float, sp))  # координатам камеры присваиваем полученные координаты

                            # адрес запроса
                            self.pt = f'&pt={str(self.current_coord[1])},{str(self.current_coord[0])}'
                            part1 = f'https://static-maps.yandex.ru/v1?lang=ru_RU&ll={str(self.camera[1])},{str(self.camera[0])}&'
                            part2 = f'spn={str(self.spn)},{str(self.spn)}&theme={self.theme}' + self.pt
                            part4 = '&apikey=ffc0b51c-c15b-47a7-a368-80493d99e48c'
                            map_request = part1 + part2 + self.part3 + part4

                            # делаем запрос
                            response = requests.get(map_request)
                            if not response:
                                self.statusBar().showMessage('Неверный запрос.')
                                QTimer.singleShot(3000, self.statusBar().clearMessage)

                            # сохраняем изображение из запроса в файле
                            map_file = "map.png"
                            with open(map_file, "wb") as file:
                                file.write(response.content)
                            # отображаем изображение на экране
                            self.pixmap = QPixmap(map_file)
                            self.label.setPixmap(self.pixmap.scaled((self.label.size())))
                        else:
                            self.statusBar().showMessage('Неверный запрос.')
                            print('2', "Http статус:", response.status_code, "(", response.reason, ")")
                            QTimer.singleShot(3000, self.statusBar().clearMessage)
                            
                    else:
                        self.statusBar().showMessage('Неверный запрос.')
                        print('3', "Http статус:", response.status_code, "(", response.reason, ")")
                        QTimer.singleShot(3000, self.statusBar().clearMessage)
            else:
                # адрес запроса
                self.pt = f'&pt={str(self.current_coord[1])},{str(self.current_coord[0])}'
                part1 = f'https://static-maps.yandex.ru/v1?lang=ru_RU&ll={str(self.camera[1])},{str(self.camera[0])}&'
                part2 = f'spn={str(self.spn)},{str(self.spn)}&theme={self.theme}' + self.pt
                part4 = '&apikey=ffc0b51c-c15b-47a7-a368-80493d99e48c'
                map_request = part1 + part2 + self.part3 + part4

                # делаем запрос
                response = requests.get(map_request)
                if not response:
                    self.statusBar().showMessage('Неверный запрос.')
                    print('4', "Http статус:", response.status_code, "(", response.reason, ")")
                    QTimer.singleShot(3000, self.statusBar().clearMessage)

                # сохраняем изображение из запроса в файле
                self.statusBar().showMessage('')
                map_file = "map.png"
                with open(map_file, "wb") as file:
                    file.write(response.content)
                # отображаем изображение на экране
                self.pixmap = QPixmap(map_file)
                self.label.setPixmap(self.pixmap.scaled((self.label.size())))
        else:
            # адрес запроса
            part1 = f'https://static-maps.yandex.ru/v1?lang=ru_RU&ll={str(self.camera[1])},{str(self.camera[0])}&'
            part2 = f'spn={str(self.spn)},{str(self.spn)}&theme={self.theme}' + self.pt
            part4 = '&apikey=ffc0b51c-c15b-47a7-a368-80493d99e48c'
            map_request = part1 + part2 + self.part3 + part4

            # делаем запрос
            response = requests.get(map_request)
            if not response:
                self.statusBar().showMessage('Неверный запрос.')
                print('5', "Http статус:", response.status_code, "(", response.reason, ")")
                QTimer.singleShot(3000, self.statusBar().clearMessage)

            # сохраняем изображение из запроса в файле
            map_file = "map.png"
            with open(map_file, "wb") as file:
                file.write(response.content)
            # отображаем изображение на экране
            self.pixmap = QPixmap(map_file)
            self.label.setPixmap(self.pixmap.scaled((self.label.size())))
        self.setFocus()

    def show_object(self, address):
        self.current_coord = address.copy()  # координатам текущей метки присваиваем полученные координаты
        self.pt = f'&pt={str(self.current_coord[1])},{str(self.current_coord[0])}'
        part1 = f'https://static-maps.yandex.ru/v1?lang=ru_RU&ll={str(self.camera[1])},{str(self.camera[0])}&'
        part2 = f'spn={str(self.spn)},{str(self.spn)}&theme={self.theme}' + self.pt
        part4 = '&apikey=ffc0b51c-c15b-47a7-a368-80493d99e48c'
        map_request = part1 + part2 + self.part3 + part4
        response = requests.get(map_request)
        if not response:
            self.statusBar().showMessage('Неверный запрос.')
            print('1', "Http статус:", response.status_code, "(", response.reason, ")")
            QTimer.singleShot(3000, self.statusBar().clearMessage)
        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)
        # отображаем изображение на экране
        self.pixmap = QPixmap(map_file)
        self.label.setPixmap(self.pixmap.scaled((self.label.size())))
        api_key = "8013b162-6b42-4997-9691-77b7074026e0"
        server_address = 'http://geocode-maps.yandex.ru/1.x/?'
        geocoder_request = f'{server_address}apikey={api_key}&geocode={str(self.current_coord[1])},{str(self.current_coord[0])}&format=json'
        # делаем запрос
        response = requests.get(geocoder_request)
        # если удачно
        if response:
            # парсим запрос
            json_response = response.json()

            # получаем нужные нам данные
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0][
                "GeoObject"]  # гео.объект
            toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
            toponym_coodrinates = toponym["Point"]["pos"]  # координаты гео.объекта
            if self.postIndexCheckBox.isChecked():
                try:
                    post_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
                    self.addressLabel.setText(toponym_address + '\n' + 'Почтовый индекс: ' + post_code)
                except Exception:
                    self.addressLabel.setText(toponym_address)
            else:
                self.addressLabel.setText(toponym_address)
        else:
            # адрес запроса
            api_key = "8013b162-6b42-4997-9691-77b7074026e0"
            server_address = 'http://geocode-maps.yandex.ru/1.x/?'
            geocoder_request = f'{server_address}apikey={api_key}&geocode={address}&format=json'

            # делаем запрос
            response = requests.get(geocoder_request)
            # если удачно
            if response:
                # парсим запрос
                json_response = response.json()

                # получаем нужные нам данные
                toponym = json_response["response"]["GeoObjectCollection"]["featureMember"]
                if toponym:
                    toponym = toponym[0]["GeoObject"]  # гео.объект
                    toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                    toponym_coodrinates = toponym["Point"]["pos"]  # координаты гео.объекта
                    if self.postIndexCheckBox.isChecked():
                        try:
                            post_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
                            self.addressLabel.setText(toponym_address + '\n' + 'Почтовый индекс: ' + post_code)
                        except Exception:
                            self.addressLabel.setText(toponym_address)
                    else:
                        self.addressLabel.setText(toponym_address)
                    sp = toponym_coodrinates.split(' ')  # разделяем полученные координаты на два значения
                    sp.reverse()  # меняем местами longitude и latitude

                    # если это новый запрос
                    if not self.current_coord:
                        self.current_coord = sp.copy()  # координатам текущей метки присваиваем полученные координаты
                        self.camera = list(map(float, sp))  # координатам камеры присваиваем полученные координаты

                    # адрес запроса
                    self.pt = f'&pt={str(self.current_coord[1])},{str(self.current_coord[0])}'
                    part1 = f'https://static-maps.yandex.ru/v1?lang=ru_RU&ll={str(self.camera[1])},{str(self.camera[0])}&'
                    part2 = f'spn={str(self.spn)},{str(self.spn)}&theme={self.theme}' + self.pt
                    part4 = '&apikey=ffc0b51c-c15b-47a7-a368-80493d99e48c'
                    map_request = part1 + part2 + self.part3 + part4

                    # делаем запрос
                    response = requests.get(map_request)
                    if not response:
                        self.statusBar().showMessage('Неверный запрос.')
                        QTimer.singleShot(3000, self.statusBar().clearMessage)

                    # сохраняем изображение из запроса в файле
                    map_file = "map.png"
                    with open(map_file, "wb") as file:
                        file.write(response.content)
                    # отображаем изображение на экране
                    self.pixmap = QPixmap(map_file)
                    self.label.setPixmap(self.pixmap.scaled((self.label.size())))
                else:
                    self.statusBar().showMessage('Неверный запрос.')
                    print('2', "Http статус:", response.status_code, "(", response.reason, ")")
                    QTimer.singleShot(3000, self.statusBar().clearMessage)
                    
            else:
                self.statusBar().showMessage('Неверный запрос.')
                print('3', "Http статус:", response.status_code, "(", response.reason, ")")
                QTimer.singleShot(3000, self.statusBar().clearMessage)
        self.setFocus()

    def changeTheme(self):
        if self.themeButtonGroup.checkedButton().text() == 'Темная':
            if self.theme != 'dark':  # если произошла смена темы
                self.theme = 'dark'
                self.setPalette(self.darkTheme)
                self.show_map()
        else:
            if self.theme != 'light':  # если произошла смена темы
                self.theme = 'light'
                self.setPalette(self.lightTheme)
                self.show_map()

    def clear(self):
        self.lineEdit.clear()
        self.addressLabel.clear()
        self.setFocus()
        self.current_coord = []

        self.show_map()

    def chooseStyle(self):
        match self.mapTypeComboBox.currentIndex():
            case 0:
                self.part3 = ''
            case 1:
                self.part3 = '&style=tags.any:road_1;road_2;road_3;road_4;road_5;road_6;road_7;road_unclassified;road_minor|elements:geometry|stylers[0-20].color:58e3e2|stylers[0-22].opacity:0.2'
            case 2:
                self.part3 = '&style=tags.any:transit_location|elements:label.text.fill|stylers.color:DD0000|'
            case 3:
                self.part3 = '&&style=types:polygon|tags.any:admin;urban_area;poi|tags.none:park|stylers.color:f9f7aa'
        self.show_map()
        self.setFocus()


    def find(self):
        if self.lineEdit.text():
            self.show_map()
        else:
            api_key = "8013b162-6b42-4997-9691-77b7074026e0"
            server_address = 'http://geocode-maps.yandex.ru/1.x/?'
            geocoder_request = f'{server_address}apikey={api_key}&geocode={str(self.current_coord[1])},{str(self.current_coord[0])}&format=json'
            # делаем запрос
            response = requests.get(geocoder_request)
            # если удачно
            if response:
                # парсим запрос
                json_response = response.json()

                # получаем нужные нам данные
                toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0][
                    "GeoObject"]  # гео.объект
                toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                toponym_coodrinates = toponym["Point"]["pos"]  # координаты гео.объекта
                if self.postIndexCheckBox.isChecked():
                    try:
                        post_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
                        self.addressLabel.setText(toponym_address + '\n' + 'Почтовый индекс: ' + post_code)
                    except Exception:
                        self.addressLabel.setText(toponym_address)
                else:
                    self.addressLabel.setText(toponym_address)
        self.setFocus()
    
    def find_by_address(self):
        if self.lineEdit.text():

            self.current_coord = []

            self.show_map()
            self.lineEdit.setText('')
            self.setFocus()

    def keyPressEvent(self, event):
        # изменение масштаба
        print(event.key())
        if event.key() in [Qt.Key.Key_PageUp, Qt.Key.Key_PageDown]:
            if event.key() == Qt.Key.Key_PageUp:
                self.spn /= 2
            elif event.key() == Qt.Key.Key_PageDown:
                self.spn = min(64, self.spn * 2)
            self.show_map()
        # перемещение камеры
        elif event.key() in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            k = 0.1  # коэффициент перемещения
            match event.key():
                case Qt.Key.Key_Up:  # вверх
                    self.camera[0] = min(85, self.camera[0] + k * self.spn)
                case Qt.Key.Key_Down:  # вниз
                    self.camera[0] = max(-85, self.camera[0] - k * self.spn)
                case Qt.Key.Key_Left:  # влево
                    self.camera[1] -= 2 * k * self.spn
                    # обработка выхода за пределы карты
                    if self.camera[1] <= -180:
                        self.camera[1] = 360 + self.camera[1]  # перемещаем камеру на точку с другой стороны
                case Qt.Key.Key_Right:  # вправо
                    self.camera[1] += 2 * k * self.spn
                    # обработка выхода за пределы карты
                    if self.camera[1] >= 180:
                        self.camera[1] = -180 + (self.camera[1] - 180)  # перемещаем камеру на точку с другой стороны
            self.show_map()

    def resizeEvent(self, event):
        self.label.setPixmap(self.label.pixmap().scaled((self.label.size())))
    
    def check_coords(self):
        print(self.camera)
        self.setFocus()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    styles = QStyleFactory.keys()
    # if "windows11" in styles:
    #     app.setStyle('windows11')
    if "Fusion" in styles:
        app.setStyle('Fusion')
    # elif "Windows" in styles:
    #     app.setStyle('Windows')
    # elif "windowsvista" in styles:
    #     app.setStyle('windowsvista')
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())