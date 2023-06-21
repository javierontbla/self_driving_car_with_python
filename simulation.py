# Código tomado de NeuralNine | Florian Dedov (con pequeñas modificaciones)
# A continuación se muestra el enlace al repositorio de Florian:
# https://github.com/NeuralNine/ai-car-simulation

import math
import sys
import neat
import pygame

# dimensiones de ventana e imagen de auto
WIDTH = 1600
HEIGHT = 900
CAR_WIDTH = 80 
CAR_HEIGHT = 80
BORDER_COLOR = (255, 255, 255, 255) # color de fondo

map_file = "mapa1.png"

class Car:
    def __init__(self):
        # cargar imagen del auto y convertirla a un sprite de Pygame
        self.sprite = pygame.image.load('car.png').convert()
        self.sprite = pygame.transform.scale(self.sprite, (CAR_WIDTH, CAR_HEIGHT))
        self.rotated_sprite = self.sprite 

        # atributos del auto
        self.position = [800, 800] 
        self.angle = 0
        self.speed = 0
        self.speed_set = False 
        self.center = [self.position[0] + CAR_WIDTH / 2, self.position[1] + CAR_HEIGHT / 2] # calcular centro
        self.radars = [] # lista de sensores (5)
        self.drawing_radars = [] # lista de radares dibujados
        self.alive = True # checar si el auto sigue vivo
        self.distance = 0 # distancia total recorrida por el auto
        self.time = 0 # tiempo transcurrido

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position) # dibujar sprite
        self.draw_radar(screen) # dibujar sensores (opcional)

    def draw_radar(self, screen):
        # dibujar sensores del auto (opcional)
        # este método es solo para visualizar los sensores
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 255, 0), position, 5)

    def check_collision(self, game_map):
        # inicialmente el auto sigue vivo
        self.alive = True

        for point in self.corners:
            # el método get_at() retorna el color en el pixel correspondiente
            # si el auto toca algun pixel blanco, el vehículo salió de la pista
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break

    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # mientras las coordenadas del auto no sean el color blanco (fuera de la pista) continuar
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # calcular distancias a los bordes de la pista
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])
    
    def update(self, game_map):
        # inicializar velocidad a 20
        if not self.speed_set:
            self.speed = 20
            self.speed_set = True

        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # aumentar distancia y tiempo si el auto sigue vivo
        self.distance += self.speed
        self.time += 1
        
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], WIDTH - 120)

        # calcular nuevo centro
        self.center = [int(self.position[0]) + CAR_WIDTH / 2, int(self.position[1]) + CAR_HEIGHT / 2]

        # calcula las coordenadas de las cuatro esquinas de la imagen del auto
        # para saber si ha habido algún contacto con algún pixel blanco
        length = CAR_WIDTH // 2
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        self.check_collision(game_map) # checar si ha habido alguna colisión
        self.radars.clear() # el método clear reinicia la lista

        # de -90 a 120 grados, checar radar
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

    def get_data(self):
        # Get Distances To Border
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def is_alive(self):
        return self.alive # checar si el auto sigue vivo

    def get_reward(self):
        # retornar una recompensa en base a la distancia recorrida
        return self.distance / (CAR_WIDTH / 2)

    def rotate_center(self, image, angle):
        # rota la imagen (del auto) para simular que esta recorriendo el circuito
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image

# contador de generaciones
current_generation = 0

def run_simulation(genomes, config):
    nets = []
    cars = []

    # inicializar ventana de Pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # por cada auto creado, crear una nueva red neuronal
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        cars.append(Car())

    # crear un reloj para llevar un conteo del tiempo recorrido
    # y establecer las fuentes del texto
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Roboto", 32)
    alive_font = pygame.font.SysFont("Roboto", 24)
    game_map = pygame.image.load(map_file).convert()

    # llevar un conteo de cuantas generaciones llevamos
    global current_generation 
    current_generation += 1

    # loop principal (infinito) que mantiene la ventana de Pygame corriendo
    while True:
        # cerrar ventana presionando la tecla Esc
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit(0)

        # por cada auto activar red neuronal
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10 # Left
            elif choice == 1:
                car.angle -= 10 # Right
            elif choice == 2:
                if(car.speed - 2 >= 12):
                    car.speed -= 2 # Slow Down
            else:
                car.speed += 2 # Speed Up
        
        # checar si el auto (de manera individual) sigue vivo, si es así, incrementar aptitud
        # esto quiere decir que esa generación podría ser la mejor
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
                car.update(game_map)
                genomes[i][1].fitness += car.get_reward()

        # si la variable still_alive es 0, significa
        # que ningún auto sobrevivió con esos parámetros
        # es necesario modificar la red neuronal
        if still_alive == 0:
            break

        # dibujar los autos que siguen vivos
        screen.blit(game_map, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(screen)
        
        # mostrar información
        text = generation_font.render("Generación: " + str(current_generation), True, (0,0,0))
        text_rect = text.get_rect()
        text_rect.left = 20
        text_rect.top = 20
        screen.blit(text, text_rect)

        text = alive_font.render("¿Cuántos autos siguen vivos? " + str(still_alive), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.left = 20
        text_rect.top = 50
        screen.blit(text, text_rect)

        # crear la ventana
        pygame.display.flip()
        clock.tick(60) # establecer 60 fps

# esta condicional se ejecuta siempre que se corre el programa
if __name__ == "__main__":
    
    # cargar configuración de red neuronal
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # crar población con la configuración establecida
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    # correr una simulación con una máximo de 1000 generaciones
    population.run(run_simulation, 1000)
