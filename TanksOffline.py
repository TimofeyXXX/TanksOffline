import datetime
import os
import copy
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
tanks_group = pygame.sprite.Group()
enemy_t_group = pygame.sprite.Group()
spawner_group = pygame.sprite.Group()


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
        self.is_dead = False
        self.step = 32
        self.lifes = 3
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.move_step = 4
        self.side = 'u'
        super().__init__(player_group, all_sprites, tanks_group)
        self.image = load_image('hero.png', '#FFFFFF')
        self.r_image = load_image('hero_r.png', '#FFFFFF')
        self.l_image = load_image('hero_l.png', '#FFFFFF')
        self.u_image = load_image('hero_u.png', '#FFFFFF')
        self.d_image = load_image('hero_d.png', '#FFFFFF')
        self.rect = self.image.get_rect().move(
            self.step * self.pos_x, self.step * self.pos_y)

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

    def respawn(self):
        self.rect = self.image.get_rect().move(
            self.step * self.pos_x, self.step * self.pos_y)
        self.lifes -= 1
        self.is_dead = False

    def sprite_update(self):
        if pygame.sprite.spritecollideany(self, enemy_group):
            self.is_dead = True


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


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, side):
        self.reload = 0
        self.is_dead = False
        self.step = 32
        self.step_m = 4
        self.sides = ['r', 'l', 'u', 'd']
        self.move_step = self.step_find(side)
        self.side = side
        super().__init__(enemy_group, all_sprites, tanks_group, enemy_t_group)
        self.image = load_image('enemy.png', '#FFFFFF')
        self.r_image = load_image('enemy_r.png', '#FFFFFF')
        self.l_image = load_image('enemy_l.png', '#FFFFFF')
        self.u_image = load_image('enemy_u.png', '#FFFFFF')
        self.d_image = load_image('enemy_d.png', '#FFFFFF')
        if side == 'r':
            self.image = self.r_image
        elif side == 'l':
            self.image = self.l_image
        elif side == 'u':
            self.image = self.u_image
        elif side == 'd':
            self.image = self.d_image
        self.rect = self.image.get_rect().move(
            self.step * pos_x, self.step * pos_y)

    def step_find(self, size):
        step = ' '
        if size == 'r':
            step = 0, self.step_m
        elif size == 'l':
            step = 0, -self.step_m
        elif size == 'u':
            step = -self.step_m, 0
        elif size == 'd':
            step = self.step_m, 0
        return step

    def action(self):
        if self.reload >= 50:
            bullet = Bullet(self.rect.x, self.rect.y, self.side, 'p')
            self.reload = 0
        else:
            self.reload += 1
        if self.can_move(self.side):
            self.move(self.side)
        else:
            r = copy.deepcopy(self.sides)
            r.remove(self.side)
            options = []
            for si in r:
                if self.can_move(si):
                    options.append(si)
            if len(options) != 0:
                self.move(options[random.randint(0, len(options) - 1)])

    def can_move(self, side):
        step = self.step_find(side)
        self.rect.x += step[1]
        self.rect.y += step[0]
        group = tanks_group.copy()
        group.remove(self)
        if not pygame.sprite.spritecollideany(self, wall_group) and \
                not pygame.sprite.spritecollideany(self, group):
            res = True
        else:
            res = False
        self.rect.x -= step[1]
        self.rect.y -= step[0]
        return res

    def move(self, side):
        self.move_step = self.step_find(self.side)
        if side != self.side:
            self.side = side
            if side == 'r':
                self.image = self.r_image
            elif side == 'l':
                self.image = self.l_image
            elif side == 'u':
                self.image = self.u_image
            elif side == 'd':
                self.image = self.d_image
        else:
            step = self.step_find(side)
            self.rect.x += step[1]
            self.rect.y += step[0]

    def sprite_update(self):
        if pygame.sprite.spritecollideany(self, player_group):
            self.is_dead = True


class Spawner(pygame.sprite.Sprite):
    def __init__(self, x, y, num, r, maxy):
        super().__init__(spawner_group, all_sprites)
        self.timer = 0
        self.num = num
        self.x_pos = x
        self.y_pos = y
        self.al_tanks = 0
        self.maxy_tanks = maxy
        self.r = r

    def s_update(self):
        if self.num > 0 and self.al_tanks < self.maxy_tanks and self.timer == 0:
            Enemy(self.x_pos, self.y_pos, self.r)
            self.al_tanks += 1
            self.num -= 1
            self.timer = 15
        elif self.timer > 0:
            self.timer -= 1


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, side, target):
        self.step = 32
        self.step_side = 0, -10
        self.is_dead = False
        self.target = target
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
        if pygame.sprite.spritecollideany(self, wall_group):
            self.is_dead = True
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
        spawners = []
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
                elif level[y][x] == '4':
                    Tile('empty', x, y)
                    Spawner(x, y, 4, 'r', 2)
                elif level[y][x] == '5':
                    Tile('empty', x, y)
                    Spawner(x, y, 4, 'l', 2)
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
    enemy_group.draw(screen)
    for enemy in enemy_t_group:
        enemy.action()
    for sp in spawner_group:
        sp.s_update()
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
                    bullet = Bullet(player.rect.x, player.rect.y, side, 'e')
                    player.reload = 0
    for sprit in tanks_group:
        sprit.sprite_update()
    for sprit in bullets_group:
        sprit.bullet_update()
    if player.is_dead:
        player.respawn()
        if player.lifes == 0:
            running = False
    for sprit in tanks_group:
        if sprit.is_dead and sprit in enemy_group:
            enemy_t_group.remove(sprit)
            enemy_group.remove(sprit)
            tanks_group.remove(sprit)
            for sp in spawner_group:
                sp.al_tanks -= 1
    for sprit in bullets_group:
        if sprit.is_dead:
            for wall in wall_group:
                wall.wall_update()
                if wall.is_dead:
                    wall_group.remove(wall)
            if sprit.target == 'p':
                bullets_group.remove(sprit)
                player_group.remove(sprit)
            elif sprit.target == 'e':
                bullets_group.remove(sprit)
                enemy_group.remove(sprit)
            bullets_group.remove(sprit)
            player_group.remove(sprit)
            enemy_group.remove(sprit)
        if pygame.sprite.spritecollideany(sprit, player_group) and sprit.target == 'p' or \
                pygame.sprite.spritecollideany(sprit, enemy_group) and sprit.target == 'e':
            sprit.is_dead = True
    clock.tick(fps)
    pygame.display.flip()
