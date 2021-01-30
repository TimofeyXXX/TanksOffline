import datetime
import os
import random
import sqlite3
import sys
import time
import tkinter
import traceback

import pygame
from PyQt5.QtWidgets import QApplication

pygame.init()

root = tkinter.Tk()
root.withdraw()
WIDTH, HEIGHT = root.winfo_screenwidth(), root.winfo_screenheight()
screen_size = WIDTH, HEIGHT
clock = pygame.time.Clock()
fps = 30
pygame.key.set_repeat(200, 70)
screen = pygame.display.set_mode(screen_size)

all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
bullets_group = pygame.sprite.Group()
wall_group = pygame.sprite.Group()
grass_group = pygame.sprite.Group()


def load_image(name, colorkey=None):
    fullname = os.path.join('paints', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey != None:
        image.set_colorkey(colorkey)
    return image


tile_images = {
    'wall': load_image('field_1.png'),
    'empty': load_image('field_0.png'),
    'brick': load_image('field_2.png'),
    'b_wall': load_image('field_3.png')
}

tile_width = tile_height = 50


def terminate():
    pygame.quit()
    sys.exit()


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        self.reload = 0
        self.step = 32
        self.move_step = 4
        self.side = 'u'
        super().__init__(player_group, all_sprites)
        self.image = load_image('hero.png', '#FFFFFF')
        self.r_image = load_image('hero_r.png', '#FFFFFF')
        self.l_image = load_image('hero_l.png', '#FFFFFF')
        self.u_image = load_image('hero_u.png', '#FFFFFF')
        self.d_image = load_image('hero_d.png', '#FFFFFF')
        self.rect = self.image.get_rect().move(
            self.step * pos_x, self.step * pos_y)

    def turn_move(self, move_side):
        step = 0, 0
        if move_side != self.side:
            if move_side == 'r':
                self.image = self.r_image
            elif move_side == 'l':
                self.image = self.l_image
            elif move_side == 'u':
                self.image = self.u_image
            elif move_side == 'd':
                self.image = self.d_image
        else:
            if move_side == 'r':
                step = 0, 4
            elif move_side == 'l':
                step = 0, -4
            elif move_side == 'u':
                step = -4, 0
            elif move_side == 'd':
                step = 4, 0
            self.rect.x += step[1]
            self.rect.y += step[0]
            if pygame.sprite.spritecollideany(self, wall_group):
                self.rect.x -= step[1]
                self.rect.y -= step[0]
        self.side = move_side


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        self.type = tile_type
        self.step = 32
        self.is_dead = False
        self.b_wall = load_image('field_3.png')
        super().__init__(tiles_group, all_sprites)
        if self.type == "wall" or self.type == "brick":
            super().__init__(wall_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            self.step * pos_x, self.step * pos_y)

    def wall_update(self):
        if pygame.sprite.spritecollideany(self, bullets_group) and self.type == 'brick':
            self.is_dead = True
            self.image = self.b_wall


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, side, target):
        self.step = 32
        self.step_side = 0, -10
        self.is_dead = False
        self.image = load_image('bullet_u.png', '#FFFFFF')
        self.r_image = load_image('bullet_r.png', '#FFFFFF')
        self.l_image = load_image('bullet_l.png', '#FFFFFF')
        self.u_image = load_image('bullet_u.png', '#FFFFFF')
        self.d_image = load_image('bullet_d.png', '#FFFFFF')
        self.rect = self.image.get_rect().move(
            x + self.step - self.image.get_rect().x - 4, y)
        if target == 'p':
            super().__init__(enemy_group, all_sprites, bullets_group)
        else:
            super().__init__(player_group, all_sprites, bullets_group)
        if side == 'r':
            self.rect = self.image.get_rect().move(x + self.step * 1.5, y + self.step - 4)
            self.image = self.r_image
            self.step_side = 10, 0
        elif side == 'l':
            self.rect = self.image.get_rect().move(x, y + self.step - 4)
            self.image = self.l_image
            self.step_side = -10, 0
        elif side == 'u':
            self.rect = self.image.get_rect().move(x + self.step - 4, y)
            self.image = self.u_image
            self.step_side = 0, -10
        elif side == 'd':
            self.rect = self.image.get_rect().move(x + self.step - 4, y + self.step * 1.5)
            self.image = self.d_image
            self.step_side = 0, 10

    def bullet_update(self):
        self.rect.x, self.rect.y = self.rect.x + self.step_side[0], \
                                   self.rect.y + self.step_side[1]
        if pygame.sprite.spritecollideany(self, wall_group):
            self.is_dead = True


class Game():
    def __init__(self):
        self.level_map = []
        self.level_num = 1
        self.step = 32
        self.field_size = self.step * 36, self.step * 24

    def generate_level(self):
        level = self.level_map
        new_player, x, y = None, None, None
        for y in range(len(level)):
            for x in range(len(level[y])):
                if level[y][x] == '0':
                    Tile('empty', x, y)
                elif level[y][x] == '1':
                    Tile('wall', x, y)
                elif level[y][x] == '2':
                    Tile('brick', x, y)
                elif level[y][x] == '3':
                    Tile('empty', x, y)
                    new_player = Player(x, y)
        # вернем игрока, а также размер поля в клетках
        return new_player

    def load_level(self, num):
        filename = f'map_level{str(num)}.txt'
        filename = "maps/" + filename
        # читаем уровень, убирая символы перевода строки
        with open(filename, 'r') as mapFile:
            self.level_map = [line.strip() for line in mapFile]


game = Game()
game.load_level(1)
player = game.generate_level()
side = ''

running = True
while running:
    screen.fill("black")
    tiles_group.draw(screen)
    player_group.draw(screen)
    bullets_group.draw(screen)
    player.reload += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                side = 'l'
                player.turn_move(side)
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                side = 'r'
                player.turn_move(side)
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                side = 'u'
                player.turn_move(side)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                side = 'd'
                player.turn_move(side)
            if event.key == pygame.K_SPACE:
                if player.reload >= 10:
                    bullet = Bullet(player.rect.x, player.rect.y, side, 'p')
                    player.reload = 0
    for sprit in bullets_group:
        if sprit.is_dead:
            for wall in wall_group:
                wall.wall_update()
                if wall.is_dead:
                    wall_group.remove(wall)
            bullets_group.remove(sprit)
        sprit.bullet_update()
    clock.tick(fps)
    pygame.display.flip()
