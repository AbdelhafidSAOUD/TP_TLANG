import itertools as it
import os
from copy import copy
from sys import argv
from turtle import Turtle
from unittest.mock import patch

import ply.lex as lex
import ply.yacc as yacc

# -------------------------------------------------------------------------------
# Classes représentant des instructions du langage logo. L'analyse va créer des
# listes de ces instructions. À la fin, on engendre le code de chacune d'elle
# en séquence pour créer l'image.


class Forward:
    def __init__(self, d):
        self.arg = d

    def code(self):
        turtle.forward(self.arg.value())

    def instantiate(self, params):
        return Forward(self.arg.instantiate(params))


class Right:
    def __init__(self, d):
        self.arg = d

    def code(self):
        turtle.right(self.arg.value())

    def instantiate(self, params):
        return Right(self.arg.instantiate(params))


class PenColor:
    def __init__(self, d):
        self.arg = d

    def code(self):
        turtle.set_color(self.arg)

    def instantiate(self, params):
        return self


class SetPen:
    def __init__(self, b):
        self.arg = b

    def code(self):
        turtle.set_pen(self.arg)

    def instantiate(self, params):
        return self


class Value:
    def __init__(self):
        self.coeff = 1

    def negate(self):
        self.coeff = -self.coeff
        return self

    def instantiate(self, params):
        return self


class Parameter(Value):
    def __init__(self, n):
        Value.__init__(self)
        self.name = n

    def instantiate(self, params):
        try:
            r = copy(params[self.name])
        except KeyError:
            print('Erreur : paramètre inconnu', self.name)
            exit(1)

        r.coeff = self.coeff
        return r


class Constant(Value):  # Constant hérite de Value
    def __init__(self, d):
        # constructeur de la class mère à appeler explicitement
        Value.__init__(self)
        self.val = d

    def value(self):
        return self.coeff * self.val


class XCor(Value):
    def __init__(self):
        Value.__init__(self)

    def value(self):
        return self.coeff * turtle.x


class YCor(Value):
    def __init__(self):
        Value.__init__(self)
        pass

    def value(self):
        return self.coeff * turtle.y


class Heading(Value):
    def __init__(self):
        Value.__init__(self)

    def value(self):
        return self.coeff * turtle.angle


# -------------------------------------------------------------------------------
# liste des mots clés, avec le nom du token associé
reserved = {
    'forward': 'FORWARD',
    'backward': 'BACKWARD',
    'left': 'LEFT',
    'right': 'RIGHT',
    'color': 'COLOR',
    'pen': 'PEN',
    'up': 'UP',
    'down': 'DOWN',
    'repeat': 'REPEAT',
    'to': 'TO',
    'end': 'END',
    'xcor': 'XCOR',
    'ycor': 'YCOR',
    'heading': 'HEADING'
}

tokens = ['NUMBER', 'CROG', 'CROD', 'NAME',
          'COL', 'PNAME'] + list(reserved.values())

t_CROG = r'\['
t_CROD = r'\]'
t_COL = r'\#[a-f0-9]{6}'
t_PNAME = r':[a-zA-Z_][a-zA-Z0-9_]*'

# Des nombres entiers; ici on a testé les débordements possibles


def t_NUMBER(t):
    r'-?[0-9]+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Valeur trop grande", t.value)
        t.value = 0
    return t


def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # la valeur associée est directement la chaîne de caractère lue
    # rien à faire pour la valeur. Par contre le nom du token change
    # si c'est un mot clé!
    # on cherche dans la liste des mots clés, et si on ne trouve pas
    # on renvoit 'NAME'
    t.type = reserved.get(t.value, 'NAME')
    if t.type == 'XCOR':
        t.value = turtle.x
    elif t.type == 'YCOR':
        t.value = turtle.y
    elif t.type == 'HEADING':
        t.value = turtle.angle

    return t


# caractères à ignorer: ici espaces, tabulations, saut de lignes
t_ignore = " \t\n"

# caractères inattendus: tout ce qui n'est pas défini avant


def t_error(t):
    print("Caractère inattendu: ", t.value[0])
    t.lexer.skip(1)  # on saute ce caractère et on passe au suivant


# instantiation de l'analyseur lexical
lexer = lex.lex()

# -------------------------------------------------------------------------------
# grammaire
# On engendre maintenant des listes d'objets représentant les instructions


def p_instructions(p):
    '''instructions : instruction
                    | instructions instruction'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2]  # concaténation des deux listes


def p_instruction(p):
    '''instruction : FORWARD value
                   | BACKWARD value
                   | LEFT value
                   | RIGHT value
                   | PEN UP
                   | PEN DOWN
                   | PEN COLOR COL
                   | REPEAT NUMBER CROG instructions CROD'''
    global turtle
    if p[1] == 'forward':
        p[0] = [Forward(p[2])]
    elif p[1] == 'backward':
        p[0] = [Forward(p[2].negate())]
    elif p[1] == 'left':
        p[0] = [Right(p[2].negate())]
    elif p[1] == 'right':
        p[0] = [Right(p[2])]
    elif p[1] == 'pen':
        if (p[2] == 'color'):
            p[0] = [PenColor(p[3])]
        else:
            p[0] = [SetPen(p[2] == 'down')]
    elif p[1] == 'repeat':
        # En utilisant itertools, on crée une liste de p[2] répétitions de la liste p[4].
        # On fusionne ensuite toutes ces listes en une seule.
        p[0] = list(it.chain.from_iterable(it.repeat(p[4], p[2])))


def p_instruction_to(p):
    'instruction : TO NAME parameters instructions END'
    name = p[2]
    if name in procs:
        print('Erreur: fonction déjà définie :', name)
        exit(1)

    procs[name] = Procedure(p[4], p[3])
    p[0] = []


def p_instruction_to_call(p):
    'instruction : NAME values'
    name = p[1]
    if not name in procs:
        print('Erreur: fonction inconnue :', name)
        exit(1)

    proc = procs[name]
    if proc.parameters:
        if len(p[2]) < len(proc.parameters):
            print("Erreur : pas assez d'arguments pour appeler", name)
            exit(1)
        elif len(p[2]) > len(proc.parameters):
            print("Erreur : trop d'arguments pour appeler", name)
            exit(1)

        # zip produit une liste de couples à partir de deux listes
        # à partir de cette liste des couples, on crée un dictionnaire
        # où les clés sont les premières compostantes des couples, et les
        # valeurs les deuxièmes composantes.
        params = dict(zip(proc.parameters, p[2]))
        p[0] = [i.instantiate(params) for i in proc.instructions]
    else:
        p[0] = proc.instructions


def p_value_n(p):
    'value : NUMBER'
    p[0] = Constant(p[1])


def p_value_x(p):
    'value : XCOR'
    p[0] = XCor()


def p_value_y(p):
    'value : YCOR'
    p[0] = YCor()


def p_value_h(p):
    'value : HEADING'
    p[0] = Heading()


def p_value_p(p):
    'value : PNAME'
    p[0] = Parameter(p[1])

# values -> epsilon


def p_values_empty(p):
    'values : '
    p[0] = []


def p_values_list(p):
    'values : values value'
    p[0] = p[1] + [p[2]]


def p_parameters_empty(p):
    'parameters : '
    p[0] = []


def p_parameters_list(p):
    'parameters : parameters parameter'
    p[0] = p[1] + p[2]


def p_parameter(p):
    'parameter : PNAME'
    p[0] = [p[1]]


# gestion minimaliste des erreurs de syntaxe
def p_error(p):
    if p:
        print("Erreur de syntaxe :", p.value)
    else:
        print("Fin de chaîne inattendue")


# instantiation de l'analyseur syntaxique
parser = yacc.yacc()
# ------------------------------------------------------------------------------

# un nouveau dictionnaire donnant un objet de type Procedure pour chaque nom
#  de procédure
procs = {}


class Procedure:
    def __init__(self, I, P):
        self.instructions = I
        self.parameters = P

# ------------------------------------------------------------------------------


# on teste le nombre d'arguments donnés sur la ligne de commande
# la longueur de argv est 1 + ce nombre, la case argv[0] correspondant au nom du programme.
if len(argv) != 2:
    print("Utilisation: python logo.py fichier.logo")
    exit(1)

# on lit le fichier complet et on le met dans une chaîne de caractères
finput = open(argv[1], 'r')
program = finput.read()
finput.close()

output_dir = "output/"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output_name = os.path.basename(argv[1]).rsplit('.', 1)[0] + '.svg'

# maintenant on écrit les résultats dans le fichier dont le nom consiste
# en le nom du fichier logo où l'extension logo a été remplacée par svg
foutput = open(output_dir + output_name, 'w')

# une nouvelle tortue. On lui passe le fichier résultat pour qu'elle puisse
# écrire dedans
turtle = Turtle(foutput)

# entête du fichier svg
foutput.write('<?xml version="1.0" standalone="no"?>\n')
foutput.write(
    '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1/1/DTD/svg11.dtd">\n')
foutput.write(
    '<svg width="1000" height="600" version="1.1" xmlns="http://www.w3.org/2000/svg">\n')
foutput.write('<rect width="100%" height="100%" fill="white"/>')
foutput.write(f'<title>{argv[1]}</title>\n')

# ici on parse la chaîne de caractères program qui contient tout le programme logo
# l'analyse renvoit maintenant une liste d'instructions
L = parser.parse(program)

# pour chaque instruction, on engendre le code correspondant
for i in L:
    i.code()

# partie finale du fichier svg
foutput.write('</svg>')

# on n'oublie pas de fermer le fichier pour s'assurer que tout ce qui était potentiellement en attente d'écriture a été bien écrit.
foutput.close()
