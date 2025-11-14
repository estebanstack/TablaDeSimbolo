# README.md

## 1. Gramática usada (subconjunto de C)
Se utiliza una gramática reducida del lenguaje C, suficiente para manejar:
- Funciones simples.
- Declaraciones de variables.
- Bloques `{}` con ámbitos anidados.
- Expresiones aritméticas.
- Asignaciones.

### Gramática
```
P        → FunDecl
FunDecl  → TIPO id '(' ')' Bloque
Bloque   → '{' MarcaIni DeclList StmtList MarcaFin '}'
MarcaIni → ε
MarcaFin → ε
DeclList → DeclList Decl | ε
Decl     → TIPO ListaId ';'
ListaId  → ListaId ',' idInit | idInit
idInit   → id | id '=' Exp
StmtList → StmtList Stmt | ε
Stmt     → id '=' Exp ';' | Bloque
Exp      → Exp '+' Term | Exp '-' Term | Term
Term     → Term '*' Factor | Term '/' Factor | Factor
Factor   → '(' Exp ')' | id | num
```

---

## 2. Tabla de símbolos
Cada entrada contiene:

| Campo    | Descripción                                  |
|----------|----------------------------------------------|
| nombre   | Identificador                                 |
| tipo     | `int` o `double`                              |
| ámbito   | Nivel de anidamiento                          |
| posición | Dirección o índice asignado                   |

### Operaciones necesarias
- `nuevoSimbolo(nombre, tipo, ambito)`
- `buscarSimbolo(nombre, ambito)`
- `getTipo(entrada)`
- `getPosicion(entrada)`
- `pushAmbito()`
- `popAmbito()`

`ambitoActual` controla el nivel.

---

## 3. ETDS: Esquema de Traducción Dirigida por la Sintaxis
Acciones semánticas para manejar la tabla de símbolos y el análisis de tipos.

### 3.1 Manejo de ámbitos
```
Bloque → '{' MarcaIni DeclList StmtList MarcaFin '}'

MarcaIni → ε
    { pushAmbito(); }

MarcaFin → ε
    { popAmbito(); }
```

### 3.2 Declaraciones
```
Decl → TIPO ListaId ';'
    { tipoActual = TIPO.lexema; }

idInit → id
    {
      if (buscarSimbolo(id.lexema, ambitoActual) == NULL)
          nuevoSimbolo(id.lexema, tipoActual, ambitoActual);
      else
          error("Redeclaración: " + id.lexema);
    }

idInit → id '=' Exp
    {
      if (buscarSimbolo(id.lexema, ambitoActual) == NULL)
          nuevoSimbolo(id.lexema, tipoActual, ambitoActual);
      else
          error("Redeclaración: " + id.lexema);

      if (tipoActual != Exp.tipo)
          warning("Conversión en inicialización de " + id.lexema);
    }
```

### 3.3 Factores y expresiones
```
Factor → id
    {
      e = buscarSimbolo(id.lexema, ambitoActual);
      if (e == NULL) error("No declarado: " + id.lexema);
      Factor.tipo = getTipo(e);
    }

Factor → num
    {
      Factor.tipo = (num es entero) ? "int" : "double";
    }

Exp → Exp '+' Term
    {
      Exp.tipo = (Exp1.tipo == "double" || Term.tipo == "double") ? "double" : "int";
    }
```

### 3.4 Asignación
```
Stmt → id '=' Exp ';'
    {
      e = buscarSimbolo(id.lexema, ambitoActual);
      if (e == NULL) error("No declarado: " + id.lexema);

      tipoId = getTipo(e);
      if (tipoId != Exp.tipo)
          warning("Conversión en asignación a " + id.lexema);
    }
```

---

## 4. Tabla de símbolos del ejemplo
Ejemplo utilizado:
```
int f()
{
    int a, c = 7;
    {
        double a, b;
        a = 7.3 + c;
    }
    a = 5;
    b = 3.5; // error
}
```

### Ámbito 0 (global)
| nombre | tipo | ámbito |
|--------|------|--------|
| f      | int  | 0      |

### Ámbito 1
| nombre | tipo | ámbito |
|--------|------|--------|
| a      | int  | 1      |
| c      | int  | 1      |

### Ámbito 2
| nombre | tipo   | ámbito |
|--------|--------|--------|
| a      | double | 2      |
| b      | double | 2      |

`b = 3.5;` causa error.

---

## 5. Generación de Código de Tres Direcciones (TAC)
Se usa un **AST decorado (AST_D)** donde cada nodo conoce su tipo y su ubicación.

### Atributos utilizados
- `E.lugar` → identificador o temporal donde se guarda el resultado.
- `E.cod` → lista de instrucciones.
- `E.tipo` → tipo de dato.

### Instrucciones disponibles
- `ITOR a t` → conversión de entero a real.
- `ADDR`, `SUBR`, `MULR`, `DIVR` → operaciones en real.
- `STOR x y` → `y = x`.

### Reglas principales
#### Factores
```
Factor → num
    { Factor.lugar = num.lexema; Factor.cod = ∅; }

Factor → id
    { Factor.lugar = id.lexema; Factor.cod = ∅; }
```

#### Multiplicación (ejemplo)
```
Term → Term1 '*' Factor
    {
      Term.cod = Term1.cod ∥ Factor.cod;
      lugar1 = Term1.lugar; tipo1 = Term1.tipo;
      lugar2 = Factor.lugar; tipo2 = Factor.tipo;

      if (tipo1 != tipo2) convertir con ITOR;

      t = nuevaTemp();
      op = (resultado es double) ? "MULR" : "MULI";

      Term.cod ∥= [ op lugar1 lugar2 t ];
      Term.lugar = t;
    }
```

#### Asignación
```
Stmt → id '=' Exp;
    {
      Stmt.cod = Exp.cod;

      if (var es double y Exp.tipo es int)
           insertar ITOR;

      Stmt.cod ∥= [ "STOR " + Exp.lugar + " " + id.lexema ];
    }
```

---

## 6. Ejemplo completo de TAC generado
Para la expresión:
```
a = 2.3 + 3*4.5 - 7.2*(3*4.5);
```
El TAC producido es:
```
ITOR 3 t1
MULR t1 4.5 t2
ADDR 2.3 t2 t3
ITOR 3 t4
MULR t4 4.5 t5
MULR 7.2 t5 t6
SUBR t3 t6 t7
STOR t7 a
```

---

## 7. Conclusión
Este proyecto incluye:
- Una **gramática** reducida de C.
- Un **ETDS** para construir la tabla de símbolos, administrar ámbitos y realizar análisis semántico.
- Un **generador de código de tres direcciones** basado en un AST decorado.
- Un ejemplo completo que incluye declaraciones, expresiones mixtas y conversión de tipos.

Este README.md sirve como informe, guía de implementación y sustento teórico del trabajo.

