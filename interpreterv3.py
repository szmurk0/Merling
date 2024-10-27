import re

def tokenize(code):
    tokens = []
    token_specification = [
        ('NUMBER',    r'\d+(\.\d*)?'),    
        ('ASSIGN',    r'->'),             
        ('ID',        r'[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ_]\w*'),  
        ('WHEN',      r'when'),             
        ('OP',        r'[+\-*/]'),        
        ('GTE',       r'>='),              
        ('LTE',       r'<='),             
        ('GT',        r'>'),               
        ('LT',        r'<'),                
        ('LPAREN',    r'\('),              
        ('RPAREN',    r'\)'),              
        ('LBRACE',    r'\{'),              
        ('RBRACE',    r'\}'),              
        ('STRING',    r'"([^"\\]*(\\.[^"\\]*)*)?"'),  
        ('PRINT',     r'print'),          
        ('INPUT',     r'input'),  
        ('FUNCTION',  r'function'),  
        ('COMMA',     r','),  
        ('SKIP',      r'[ \t]+'),         
        ('MISMATCH',  r'.'),               
        ('OTHERWISE', r'otherwise'),  
        ('FALLBACK',  r'fallback'),   
    ]
    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)

    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
        elif kind == 'ID':
            if value == 'print':
                kind = 'PRINT'
            elif value == 'input':
                kind = 'INPUT'
            elif value == 'function':
                kind = 'FUNCTION'
        elif kind == 'STRING':
            value = value[1:-1]  # Usuń cudzysłowy
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'Niespodziewany znak: {value}')
        tokens.append((kind, value))
    return tokens

def parse(tokens):
    instructions = []
    functions = {}  # Słownik do przechowywania definicji funkcji
    i = 0

    while i < len(tokens):
        token_type, token_value = tokens[i]

        if token_type == 'FUNCTION':
            # Obsługuje definicję funkcji
            i += 1
            if i < len(tokens) and tokens[i][0] == 'ID':
                function_name = tokens[i][1]
                i += 1
                if i < len(tokens) and tokens[i][0] == 'LPAREN':
                    i += 1
                    parameters = []
                    while i < len(tokens) and tokens[i][0] != 'RPAREN':
                        if tokens[i][0] == 'ID':
                            parameters.append(tokens[i][1])
                        i += 1
                        if i < len(tokens) and tokens[i][0] == 'COMMA':  # Obsługuje przecinki
                            i += 1
                    if i < len(tokens) and tokens[i][0] == 'RPAREN':
                        i += 1  # Pomijaj zamykający nawias
                    else:
                        raise SyntaxError("Oczekiwany zamykający nawias ')' po definicji funkcji")
                    if i < len(tokens) and tokens[i][0] == 'LBRACE':
                        i += 1
                        body = []
                        while i < len(tokens) and tokens[i][0] != 'RBRACE':
                            body.append(tokens[i])
                            i += 1
                        if i < len(tokens) and tokens[i][0] == 'RBRACE':
                            i += 1  # Pomijaj zamykający nawias klamrowy
                            functions[function_name] = {'params': parameters, 'body': body}
                        else:
                            raise SyntaxError("Oczekiwany zamykający nawias klamrowy '}' po definicji funkcji")
                    else:
                        raise SyntaxError("Oczekiwany otwierający nawias klamrowy '{' po definicji funkcji")
                else:
                    raise SyntaxError("Oczekiwany otwierający nawias '(' po nazwie funkcji")
            else:
                raise SyntaxError("Oczekiwany identyfikator po 'function'")

        elif token_type == 'ID':
            # Obsługuje wywołanie funkcji
            if i + 1 < len(tokens) and tokens[i + 1][0] == 'LPAREN':
                function_name = token_value
                i += 2
                args = []
                while i < len(tokens) and tokens[i][0] != 'RPAREN':
                    args.append(tokens[i])
                    i += 1
                    if i < len(tokens) and tokens[i][0] == 'COMMA':  # Obsługuje przecinki
                        i += 1
                if i < len(tokens) and tokens[i][0] == 'RPAREN':
                    i += 1  # Pomijaj zamykający nawias
                else:
                    raise SyntaxError("Oczekiwany zamykający nawias ')' po wywołaniu funkcji")
                instructions.append({'type': 'call', 'function': function_name, 'args': args})
            else:
                # Obsługuje przypisanie
                if i + 1 < len(tokens) and tokens[i + 1][0] == 'ASSIGN':
                    var_name = token_value
                    i += 2
                    expr = []
                    while (i < len(tokens) and 
                           not (tokens[i][0] == 'ID' and i + 1 < len(tokens) and tokens[i + 1][0] == 'ASSIGN') and 
                           tokens[i][0] not in ('PRINT', 'INPUT', 'WHEN', 'FALLBACK', 'OTHERWISE')):
                        expr.append(tokens[i])
                        i += 1
                    instructions.append({'type': 'assign', 'var': var_name, 'expr': expr})
                    continue

        elif token_type == 'PRINT':
            # Obsługuje instrukcję print
            i += 1
            if i < len(tokens) and tokens[i][0] == 'LPAREN':
                i += 1
                expr = []
                while i < len(tokens) and tokens[i][0] != 'RPAREN':
                    expr.append(tokens[i])
                    i += 1
                if i < len(tokens) and tokens[i][0] == 'RPAREN':
                    i += 1  # Pomijaj zamykający nawias
                else:
                    raise SyntaxError("Oczekiwany zamykający nawias ')' po 'print'")
                instructions.append({'type': 'print', 'expr': expr})
            else:
                raise SyntaxError("Oczekiwany otwierający nawias '(' po 'print'")

        elif token_type == 'INPUT':
            # Obsługuje instrukcję input
            i += 1
            if i < len(tokens) and tokens[i][0] == 'LPAREN':
                i += 1
                if i < len(tokens) and tokens[i][0] == 'STRING':
                    prompt = tokens[i][1]  # Pobierz prompt
                    i += 1
                    if i < len(tokens) and tokens[i][0] == 'RPAREN':
                        i += 1  # Pomijaj zamykający nawias
                    else:
                        raise SyntaxError("Oczekiwany zamykający nawias ')' po 'input'")
                    instructions.append({'type': 'input', 'prompt': prompt})
                else:
                    raise SyntaxError("Oczekiwany argument typu string dla 'input'")
            else:
                raise SyntaxError("Oczekiwany otwierający nawias '(' po 'input'")

        else:
            # Jeśli token nie pasuje do żadnego z oczekiwanych typów, zgłoś błąd
            raise SyntaxError(f"Niespodziewany token: {token_value}")

        i += 1

    return instructions

def eval_expression(expr, variables):
    stack = []
    operators = []

    for token_type, token_value in expr:
        if token_type == 'NUMBER':
            stack.append(token_value)
        elif token_type == 'ID':
            if token_value in variables:
                stack.append(variables[token_value])
            else:
                raise KeyError(f"Zmienne '{token_value}' nie zdefiniowane")
        elif token_type == 'STRING':
            stack.append(token_value)
        elif token_type == 'OP':
            while (operators and operators[-1] in ('*', '/') and token_value in ('+', '-')) or \
                  (operators and operators[-1] == token_value):
                right = stack.pop()
                left = stack.pop()
                op = operators.pop()
                if op == '+':
                    stack.append(str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right)
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
            stack.append(str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right)
        elif op == '-':
            stack.append(left - right)
        elif op == '*':
            stack.append(left * right)
        elif op == '/':
            stack.append(left / right)

    return stack[0]

def eval_instructions(instructions, variables, functions):
    for instruction in instructions:
        if instruction['type'] == 'assign':
            var_name = instruction['var']
            expr = instruction['expr']
            value = eval_expression(expr, variables)
            variables[var_name] = value
        elif instruction['type'] == 'print':
            expr = instruction['expr']
            value = eval_expression(expr, variables)
            print(value)
        elif instruction['type'] == 'input':
            prompt = instruction['prompt']
            user_input = input(prompt + " ")
            variables['input_value'] = user_input  # Przechowuj wartość w zmiennej
        elif instruction['type'] == 'call':
            function_name = instruction['function']
            args = instruction['args']
            if function_name in functions:
                func = functions[function_name]
                param_names = func['params']
                func_body = func['body']
                if len(args) != len(param_names):
                    raise ValueError(f"Funkcja '{function_name}' oczekuje {len(param_names)} argumentów, ale otrzymała {len(args)}")
                local_variables = {}
                for param_name, arg in zip(param_names, args):
                    local_variables[param_name] = eval_expression([arg], variables)
                eval_instructions(func_body, local_variables, functions)

def main():
    # Wczytaj kod z pliku program.txt
    with open('program.txt', 'r') as file:
        code = file.read()

    tokens = tokenize(code)
    instructions = parse(tokens)
    variables = {}
    functions = {}
    eval_instructions(instructions, variables, functions)

if __name__ == "__main__":
    main()
