from maps.mapapi import map_request
from maps.geocoder import get_ll_span
import sys
import os
import pygame
import pygame_gui


class Map:
    def __init__(self, screen, manager, width, height):
        self.screen = screen
        self.manager = manager
        self.width = width
        self.height = height
        self.params = {'ll': (36.192640, 51.730894), 'spn': (0.05, 0.05), 'l': 'map', 'pt': None}
        self.start_coords = (36.192640, 51.730894)
        self.start_spn = (0.05, 0.05)
        self.main_long, self.main_lat = 36.192640, 51.730894
        self.map_file = "map.png"
        self.info_loaded = False
        self.request()

    def init_ui(self):
        manager, width, height = self.manager, self.width, self.height
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 0, 100, 30), manager=manager, text="Координаты:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 50, 100, 30), manager=manager, text="Масштаб:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 100, 100, 30), manager=manager, text="Поиск:")

        self.change_map = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(
            options_list=['map', 'sat', 'sat,skl'],
            starting_option='map',
            relative_rect=pygame.Rect(490, 0, 110, 40),
            manager=manager
        )

        self.coords_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 0, width / 2 + 50, height / 2),
            manager=manager)
        self.spn_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 50, width / 2 + 50, height / 2),
                                                             manager=manager)
        self.search_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 100, width / 2 + 50, height / 2),
            manager=manager)

        self.search_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 150), (110, 40)),
                                                          text='Искать',
                                                          manager=manager)

        self.clean_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((490, 150), (110, 40)),
                                                         text='Сброс',
                                                         manager=manager)
        self.update_ui()

    def coord_to_string(self, coord):
        return ','.join(map(str, coord))

    def string_to_coord(self, string):
        return tuple(map(float, string.split(',')))

    def move(self, move):
        moves = {pygame.K_LEFT: self.move_left, pygame.K_RIGHT: self.move_right, pygame.K_UP: self.move_up,
                 pygame.K_DOWN: self.move_down}
        if move not in moves:
            return
        long, lat = self.params['ll']
        long_spn, lat_spn = self.params['spn']
        new_long, new_lat = moves[move](long, lat, long_spn, lat_spn)
        self.params['ll'] = new_long, new_lat
        self.update_ui()
        self.on_search()

    def move_right(self, long, lat, long_spn, lat_spn):
        new_long = min(long + long_spn * 2, 179)
        return new_long, lat

    def move_left(self, long, lat, long_spn, lat_spn):
        new_long = max(long - long_spn * 2, -179)
        return new_long, lat

    def move_up(self, long, lat, long_spn, lat_spn):
        new_lat = min(lat + lat_spn, 85)
        return long, new_lat

    def move_down(self, long, lat, long_spn, lat_spn):
        new_lat = max(lat - lat_spn, -85)
        return long, new_lat

    def scale_up(self, key=None):
        k = 2
        self.params['spn'] = tuple(map(lambda x: max(x / k, 0.0015625), self.params['spn']))
        self.update_ui()
        self.on_search()

    def scale_down(self, key=None):
        k = 2
        self.params['spn'] = tuple(map(lambda x: min(x * k, 51.2), self.params['spn']))
        self.update_ui()
        self.on_search()

    def update_ui(self):
        self.coords_input.set_text(self.coord_to_string(self.params['ll']))
        self.spn_input.set_text(self.coord_to_string(self.params['spn']))

    def update_change_map(self, change):
        self.params['l'] = change

    def update_data(self):
        self.params['ll'] = self.string_to_coord(self.coords_input.get_text())
        self.params['spn'] = self.string_to_coord(self.spn_input.get_text())

    def request(self):
        spn = self.coord_to_string(self.params['spn'])
        ll = self.coord_to_string(self.params['ll'])
        pt = self.params['pt']
        if pt != None:
            image = map_request(ll, self.params['l'], spn=spn, pt=pt)
        else:
            image = map_request(ll, self.params['l'], spn=spn)
        self.update_map(image)

    def update_map(self, image):
        try:
            with open(self.map_file, "wb") as file:
                file.write(image)
        except IOError as ex:
            print("Ошибка записи временного файла:", ex)
            sys.exit(2)
        self.info_loaded = True

    def on_search(self):
        self.update_data()
        self.request()

    def get_coordinates_at_address(self):
        adress = self.search_input.get_text()
        if adress != '' and adress != 'Не найдено':
            coordinates, spn = get_ll_span(adress)
            if coordinates != None:
                self.coords_input.text = coordinates
                self.spn_input.text = spn
                self.params['pt'] = f"{coordinates},pm2rdm"
            else:
                self.search_input.text = 'Не найдено'

    def on_key_pressed(self, key):
        valid_actions = {pygame.K_PAGEUP: self.scale_up, pygame.K_PAGEDOWN: self.scale_down,
                         pygame.K_LEFT: self.move, pygame.K_RIGHT: self.move, pygame.K_UP: self.move,
                         pygame.K_DOWN: self.move}
        if key in valid_actions:
            valid_actions[key](key)

    def clean_coords(self):
        self.change_map = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(
            options_list=['map', 'sat', 'sat,skl'],
            starting_option='map',
            relative_rect=pygame.Rect(490, 0, 110, 40),
            manager=self.manager
        )
        self.change_map.rebuild()
        self.params['l'] = 'map'
        self.params['spn'] = self.start_spn
        self.params['ll'] = self.start_coords
        self.params['pt'] = None
        self.search_input.set_text('')
        self.update_ui()
        self.on_search()

    def set_main_coords(self):
        long, lat = self.string_to_coord(self.coords_input.get_text())
        if not (-179 <= long <= 179) or not (-85 <= lat <= 85):
            self.coords_input.set_text(self.coord_to_string(self.params['ll']))
        else:
            self.main_long, self.main_lat = self.string_to_coord(self.coords_input.get_text())

    def on_event(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.search_button:
                    self.set_main_coords()
                    self.get_coordinates_at_address()
                    self.on_search()
                if event.ui_element == self.clean_button:
                    self.clean_coords()
        elif event.type == pygame.KEYUP:
            self.on_key_pressed(event.key)

    def draw(self):
        if self.info_loaded:
            self.screen.blit(pygame.image.load(self.map_file), (0, 200))

    def __del__(self):
        if os.path.isfile(self.map_file):
            os.remove(self.map_file)
