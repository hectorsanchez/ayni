# -*- coding: utf-8 -*-
# Ayni
#
# Copyright 2009 - Gcoop <info@gcoop.coop>
# License: GPLv3 (see http://www.gnu.org/licenses/gpl.html)

import pygame
import scene
import common
import map
import mouse
import pipe
import group
import messages
import level_complete
import particles
import end
import menu


class PlayingGameState:
    "Represeta un estado interno del juego: mientras el usuario juega."

    def __init__(self, game):
        self.game = game

    def update(self):
        pass

class EndingLevelGameState:
    "Representa el estado interno del juego cuando termina correctamente."

    def __init__(self, game):
        self.game = game
        self.counter = 0

    def update(self):
        self.counter += 1
            
        if self.counter > 300:
            world = self.game.world
            level = world.next_level(self.game.level) 

            if self.game.modo_editor:
                import editor
                self.game.world.change_scene(editor.Editor(self.game.world, self.game.level))
            else:
                if level:
                    world.change_scene(Game(world, level))
                else:
                    world.change_scene(end.End(world))


class Game(scene.Scene):
    """Es la escena principal del juego, donde el usuario puede
       interactuar con los trabajadores, el mouse y las piezas."""

    def __init__(self, world, level=1, modo_editor=False):
        pygame.mixer.music.stop()
        scene.Scene.__init__(self, world)
        self.sprites = group.Group()
        self.messages = messages.Messages(self.sprites)
        self.map = map.Map(self, self.sprites, self.messages, world.audio, level)
        self._draw_background_and_map()
        self.change_state(PlayingGameState(self))
        self.level = level
        self.modo_editor = modo_editor

        if modo_editor:
            self.agregar_boton_para_regresar_al_editor()

        #self._create_a_pipe()
        self._create_mouse_pointer()
        self.sprites.sort_by_z()

    def agregar_boton_para_regresar_al_editor(self):
        from editor import ItemBoton

        regresar = common.load("regresar.png", True)
        imagen_bloque = common.load("bloque.png", True)
        item = ItemBoton(regresar, imagen_bloque.convert_alpha(), self.regresar_al_editor, 0, 0)
        self.sprites.add(item)

    def _create_mouse_pointer(self):
        self.mouse = mouse.MousePointer(self.sprites)
        self.sprites.add(self.mouse)

    def _draw_background_and_map(self):
        "Imprime y actualiza el fondo de pantalla para usar dirtyrectagles mas adelante."
        self.background = common.load("background.jpg", False)
        self.map.draw_over(self.background)
        self.world.screen.blit(self.background, (0, 0))

        # actualiza toda la pantalla.
        pygame.display.flip()

    def update(self):
        self.state.update()
        self.sprites.update()

    def draw(self, screen):
        self.sprites.clear(screen, self.background)
        pygame.display.update(self.sprites.draw(screen))

    def on_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            self.mouse.on_click(x, y)

            if self.modo_editor:
                # Detecta si el usuario quiere regresar al editor
                if x < 75 and y < 75:
                    self.regresar_al_editor()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.modo_editor:
                    self.regresar_al_editor()
                else:
                    self.world.change_scene(menu.Menu(self.world))

    def regresar_al_editor(self):
        import editor
        self.world.change_scene(editor.Editor(self.world, self.level))

    def on_pipe_put(self):
        "Evento que activa la pieza cuando se suelta en un placeholder."

        if self.map.all_pipes_are_in_correct_placeholders():
            for x in self.map.players:
                x.show_end_level_animation()
            
            self.show_level_complete_message()
            self.change_state(EndingLevelGameState(self))

    def show_level_complete_message(self):
        "Muestra el mensaje de texto que dice 'nivel completado...'"
        self.sprites.add(level_complete.LevelComplete())

    def create_working_particles_effect(self, rect):
        particle = particles.Particles(rect)
        self.sprites.add(particle)

    def change_state(self, new_state):
        self.state = new_state
