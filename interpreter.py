import re

def tokenize(code):
    tokens = []
    token_specification = [
        ('NUMBER',    r'\d+(\.\d*)?'),    # Liczby całkowite lub zmiennoprzecinkowe
        ('ASSIGN',    r'->'),              # Operator przypisania
        ('ID',        r'[A-Za-z_]\w*'),   # Identyfikator
        ('OP',        r'[+\-*/]'),        # Operatory arytmetyczne
        ('LPAREN',    r'\('),             # Nawias otwierający
        ('RPAREN',    r'\)'),             # Nawias zamykający
        ('STRING',    r'"([^"\\]*(\\.[^"\\]*)*)?"'),  # Stringi w cudzysłowach
        ('SHOW',      r'show'),           # Słowo kluczowe 'show'
        ('SKIP',      r'[ \t]+'),         # Pomijanie białych znaków
        ('MISMATCH',  r'.'),              # Nieznane znaki
    ]
    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
        elif kind == 'ID' and value == 'show':
            kind = 'SHOW'
        elif kind == 'STRING':
            value = value[1:-1]  # Usunięcie cudzysłowów
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'Nieoczekiwany znak: {value}')
        tokens.append((kind, value))
    return tokens

def parse(tokens):
    instructions = []
    i = 0
    while i < len(tokens):
        token_type, token_value = tokens[i]

        # Obsługuje przypisanie zmiennej
        if token_type == 'ID' and i + 1 < len(tokens) and tokens[i + 1][0] == 'ASSIGN':
            var_name = token_value
            i += 2
            expr = []
            # Zbieranie wyrażenia po przypisaniu
            while (i < len(tokens) and 
                   not (tokens[i][0] == 'ID' and i + 1 < len(tokens) and tokens[i + 1][0] == 'ASSIGN') and 
                   tokens[i][0] != 'SHOW'):
                expr.append(tokens[i])
                i += 1
            instructions.append({'type': 'assign', 'var': var_name, 'expr': expr})
            continue

        # Obsługuje instrukcję show
        elif token_type == 'SHOW':
            i += 1
            if i < len(tokens) and tokens[i][0] == 'LPAREN':
                i += 1
                expr = []
                while i < len(tokens) and tokens[i][0] != 'RPAREN':
                    expr.append(tokens[i])
                    i += 1
                if i < len(tokens) and tokens[i][0] == 'RPAREN':
                    i += 1  # Pomijanie zamykającego nawiasu
                else:
                    raise SyntaxError("Oczekiwano zamykającego nawiasu ')' po 'show'")
                instructions.append({'type': 'show', 'expr': expr})
            else:
                raise SyntaxError("Oczekiwano otwierającego nawiasu '(' po 'show'")

        else:
            raise SyntaxError(f"Nieoczekiwany token: {token_value}")

        i += 1

    return instructions


def eval_expression(expr, variables):
    stack = []
    operators = []

    for token_type, token_value in expr:
        if token_type == 'NUMBER':
            stack.append(token_value)
        elif token_type == 'ID':
            stack.append(variables[token_value])
        elif token_type == 'STRING':
            stack.append(token_value)  # Dodaj string do stosu
        elif token_type == 'OP':
            while (operators and operators[-1] in ('*', '/') and token_value in ('+', '-')) or \
                  (operators and operators[-1] == token_value):
                right = stack.pop()
                left = stack.pop()
                op = operators.pop()
                if op == '+':
                    stack.append(left + right)
                elif op == '-':
                    stack.append(left - right)
                elif op == '*':
                    stack.append(left * right)
                elif op == '/':
                    stack.append(left / right)
            operators.append(token_value)

    while operators:
        right = stack.pop()
        left = stack.pop()
        op = operators.pop()
        if op == '+':
            stack.append(left + right)
        elif op == '-':
            stack.append(left - right)
        elif op == '*':
            stack.append(left * right)
        elif op == '/':
            stack.append(left / right)

    return stack[0]

def execute(instructions):
    variables = {}
    for instruction in instructions:
        if instruction['type'] == 'assign':
            var_name = instruction['var']
            expr = instruction['expr']
            value = eval_expression(expr, variables)
            variables[var_name] = value
        elif instruction['type'] == 'show':
            expr = instruction['expr']
            value = eval_expression(expr, variables)
            print(value)

def run_from_file(filename):
    with open(filename, 'r') as file:
        code = file.read()
    
    tokens = tokenize(code)
    instructions = parse(tokens)
    execute(instructions)

# Wykonanie kodu z pliku
run_from_file('program.txt')
