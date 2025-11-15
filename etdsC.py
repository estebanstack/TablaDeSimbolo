class Token:
    def __init__(self, kind, lexema):
        self.kind = kind
        self.lexema = lexema

    def __repr__(self):
        return f"Token({self.kind}, {self.lexema})"


def lexer(text):
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]

        # Ignorar espacios
        if c == ' ':
            i += 1
            continue

        if c.isdigit():
            start = i
            i += 1
            dot_seen = False
            while i < len(text) and (text[i].isdigit() or (text[i] == '.' and not dot_seen)):
                if text[i] == '.':
                    dot_seen = True
                i += 1
            tokens.append(Token("NUM", text[start:i]))
            continue


        if c.isalpha() or c == '_':
            start = i
            i += 1
            while i < len(text) and (text[i].isalnum() or text[i] == '_'):
                i += 1
            tokens.append(Token("ID", text[start:i]))
            continue


        if c == '+':
            tokens.append(Token("PLUS", c))
        elif c == '-':
            tokens.append(Token("MINUS", c))
        elif c == '*':
            tokens.append(Token("MUL", c))
        elif c == '/':
            tokens.append(Token("DIV", c))
        elif c == '(':
            tokens.append(Token("LPAR", c))
        elif c == ')':
            tokens.append(Token("RPAR", c))
        else:
            raise ValueError(f"Caracter no reconocido: {c}")

        i += 1

    return tokens



class NumNode:
    def __init__(self, value):
        self.value = value
        self.tipo = None

class VarNode:
    def __init__(self, name):
        self.name = name
        self.tipo = None  # asumiremos double

class BinOpNode:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
        self.tipo = None


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def eat(self, kind):
        token = self.current()
        if token is None or token.kind != kind:
            raise SyntaxError(f"Se esperaba {kind}, se encontró {token}")
        self.pos += 1
        return token

    def parse(self):
        node = self.expr()
        if self.current() is not None:
            raise SyntaxError("Entrada inválida después de la expresión")
        return node

    def expr(self):
        node = self.term()
        while self.current() and self.current().kind in ("PLUS", "MINUS"):
            op = self.current().lexema
            if self.current().kind == "PLUS":
                self.eat("PLUS")
            else:
                self.eat("MINUS")
            node = BinOpNode(op, node, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.current() and self.current().kind in ("MUL", "DIV"):
            op = self.current().lexema
            if self.current().kind == "MUL":
                self.eat("MUL")
            else:
                self.eat("DIV")
            node = BinOpNode(op, node, self.factor())
        return node

    def factor(self):
        token = self.current()

        if token.kind == "NUM":
            self.eat("NUM")
            return NumNode(token.lexema)

        if token.kind == "ID":
            self.eat("ID")
            return VarNode(token.lexema)

        if token.kind == "LPAR":
            self.eat("LPAR")
            node = self.expr()
            self.eat("RPAR")
            return node

        raise SyntaxError("Factor inválido")


def annotate(node):
    if isinstance(node, NumNode):
        node.tipo = "double" if "." in node.value else "int"
        return node.tipo

    if isinstance(node, VarNode):
        node.tipo = "double"
        return node.tipo

    if isinstance(node, BinOpNode):
        t1 = annotate(node.left)
        t2 = annotate(node.right)
        node.tipo = "double" if (t1 == "double" or t2 == "double") else "int"
        return node.tipo


# GENERACIÓN DE TAC
temp_counter = 0

def new_temp():
    global temp_counter
    temp_counter += 1
    return f"t{temp_counter}"

def gen(node):
    if isinstance(node, NumNode):
        return [], node.value, node.tipo

    if isinstance(node, VarNode):
        return [], node.name, node.tipo

    if isinstance(node, BinOpNode):
        code = []

        left_code, left_place, left_type = gen(node.left)
        right_code, right_place, right_type = gen(node.right)

        code += left_code
        code += right_code


        if left_type == "int" and right_type == "double":
            t = new_temp()
            code.append(f"ITOR {left_place} {t}")
            left_place = t
            left_type = "double"

        elif left_type == "double" and right_type == "int":
            t = new_temp()
            code.append(f"ITOR {right_place} {t}")
            right_place = t
            right_type = "double"

        # Tipo resultado
        tipo_res = "double" if (left_type == "double" or right_type == "double") else "int"

        # Seleccionar operación
        if node.op == "+":
            op = "ADDR" if tipo_res == "double" else "ADDI"
        elif node.op == "-":
            op = "SUBR" if tipo_res == "double" else "SUBI"
        elif node.op == "*":
            op = "MULR" if tipo_res == "double" else "MULI"
        elif node.op == "/":
            op = "DIVR" if tipo_res == "double" else "DIVI"

        t = new_temp()
        code.append(f"{op} {left_place} {right_place} {t}")

        return code, t, tipo_res



if __name__ == "__main__":
    print("Generador TAC")
    expr = input("Expresión: ")

    tokens = lexer(expr)
    parser = Parser(tokens)
    ast = parser.parse()

    annotate(ast)

    temp_counter = 0
    tac, res, tipo = gen(ast)

    print("\n=== TAC ===")
    for instr in tac:
        print(instr)
    print(f"# Resultado final en {res}, tipo {tipo}")
