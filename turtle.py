from math import sin, cos, pi

#-------------------------------------------------------------------------------
# La classe représentant une tortue avec sa position, son orientation, et le
# statut du crayon (abaissé ou relevé)

# __init__ est le constructeur (par défaut) de la classe
# self joue le rôle de this en Java. Son nom est arbitraire mais standard. Il
# faut le passer explicitement en premier argument de toutes les méthodes en
# Python.

class Turtle:
    def __init__(self, out):
        self.x = 500
        self.y = 300
        self.angle = 0
        self.pendown = True
        self.color = '#1f56d2'
        # self.output représente le fichier SVG dans lequel on écrit
        self.output = out

    def hello(self):
        print(f'Bonjour, je suis une tortue, actuellement en position ({self.x}, {self.y}) !')

    # TODO compléter ici les méthodes de turtle: forward, right, set_pen et set_color
    # En particulier dans forward, il faudra faire le tracé si le crayon est baissé avec
    # l'instruction suivante :

    def forward(self, number):
        dx = cos(self.angle)*number
        dy = sin(self.angle)*number
        self.x += cos(self.angle)*number
        self.y += sin(self.angle)*number
        return self.output.write(f'<line x1 = "{int(self.x - dx)}" y1 = "{int(self.y - dy)}" x2 = "{int(self.x)}" y2 = "{int(self.y)}" style = "stroke:{self.color}"/>\n')

        
    def right(self, a):
        self.angle += a*pi/180
        #return self.output.write(f'<line x1 = "{int(self.x)}" y1 = "{int(self.y)}" x2 = "{int(self.x + dx)}" y2 = "{int(self.y + dy)}" style = "stroke:{self.color}"/>\n')
 
        
    def set_color(self, col):
        self.color = col
        #return self.output.write(f'<line x1 = "{int(self.x)}" y1 = "{int(self.y)}" x2 = "{int(self.x + dx)}" y2 = "{int(self.y + dy)}" style = "stroke:{self.color}"/>\n')

        
    def penDown(self):
        self.pendown = True
        #return self.output.write(f'<line x1 = "{int(self.x)}" y1 = "{int(self.y)}" x2 = "{int(self.x + dx)}" y2 = "{int(self.y + dy)}" style = "stroke:{self.color}"/>\n')

    
    def penUp(self):
        self.pendown = False
        #return self.output.write(f'<line x1 = "{int(self.x)}" y1 = "{int(self.y)}" x2 = "{int(self.x + dx)}" y2 = "{int(self.y + dy)}" style = "stroke:{self.color}"/>\n')


