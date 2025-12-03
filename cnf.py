import re
import sys

class Node:
    pass

class Variable(Node):
    """Değişkenler: A, B, x1"""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

class UnaryOp(Node):
    """Tekli Operatör: Sadece NOT (~)"""
    def __init__(self, operand):
        self.operand = operand
    def __repr__(self):
        return f"~{self.operand}"

class BinaryOp(Node):
    """İkili Operatörler: ^, v, ->, <->"""
    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator
    def __repr__(self):
        return f"({self.left} {self.operator} {self.right})"

class LogicParser:
    def __init__(self):
        self.token_pattern = re.compile(r'\s*(<->|->|[a-zA-Z0-9]+|[v\^~()])\s*')
        self.tokens = []
        self.pos = 0

    def parse(self, text):
        self.tokens = [t for t in self.token_pattern.findall(text) if t.strip()]
        self.pos = 0
        if not self.tokens:
            raise ValueError("Boş formül.")
        ast = self._parse_iff()
        if self.pos < len(self.tokens):
            raise ValueError(f"Beklenmeyen token: {self.tokens[self.pos]}")
        return ast

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self, expected=None):
        token = self._peek()
        if expected and token != expected:
            raise ValueError(f"Beklenen: {expected}, Bulunan: {token}")
        self.pos += 1
        return token

    def _parse_iff(self):
        node = self._parse_implies()
        while self._peek() == '<->':
            op = self._consume()
            right = self._parse_implies()
            node = BinaryOp(node, right, op)
        return node

    def _parse_implies(self):
        node = self._parse_or()
        while self._peek() == '->':
            op = self._consume()
            right = self._parse_or()
            node = BinaryOp(node, right, op)
        return node

    def _parse_or(self):
        node = self._parse_and()
        while self._peek() == 'v':
            op = self._consume()
            right = self._parse_and()
            node = BinaryOp(node, right, op)
        return node

    def _parse_and(self):
        node = self._parse_not()
        while self._peek() == '^':
            op = self._consume()
            right = self._parse_not()
            node = BinaryOp(node, right, op)
        return node

    def _parse_not(self):
        if self._peek() == '~':
            self._consume()
            return UnaryOp(self._parse_not())
        return self._parse_atom()

    def _parse_atom(self):
        token = self._peek()
        if token == '(':
            self._consume()
            node = self._parse_iff()
            self._consume(')')
            return node
        elif token and re.match(r'^[a-zA-Z0-9]+$', token):
            return Variable(self._consume())
        else:
            raise ValueError(f"Beklenmeyen atom: {token}")

def eliminate_implications(node):
    """Adım 1: -> ve <-> operatörlerini kaldırır."""
    if isinstance(node, BinaryOp):
        left = eliminate_implications(node.left)
        right = eliminate_implications(node.right)
        if node.operator == '->':
            # A -> B  =>  ~A v B
            return BinaryOp(UnaryOp(left), right, 'v')
        elif node.operator == '<->':
            # A <-> B => (~A v B) ^ (~B v A)
            return BinaryOp(
                BinaryOp(UnaryOp(left), right, 'v'),
                BinaryOp(UnaryOp(right), left, 'v'),
                '^'
            )
        return BinaryOp(left, right, node.operator)
    elif isinstance(node, UnaryOp):
        return UnaryOp(eliminate_implications(node.operand))
    return node

def convert_to_nnf(node):
    """Adım 2: De Morgan ve Çift Değilleme."""
    # ~~A => A
    if isinstance(node, UnaryOp) and isinstance(node.operand, UnaryOp):
        return convert_to_nnf(node.operand.operand)
    
    # De Morgan
    if isinstance(node, UnaryOp) and isinstance(node.operand, BinaryOp):
        inner = node.operand
        if inner.operator == 'v': # ~(A v B) => ~A ^ ~B
            return BinaryOp(convert_to_nnf(UnaryOp(inner.left)), 
                            convert_to_nnf(UnaryOp(inner.right)), '^')
        elif inner.operator == '^': # ~(A ^ B) => ~A v ~B
            return BinaryOp(convert_to_nnf(UnaryOp(inner.left)), 
                            convert_to_nnf(UnaryOp(inner.right)), 'v')
                            
    if isinstance(node, BinaryOp):
        return BinaryOp(convert_to_nnf(node.left), convert_to_nnf(node.right), node.operator)
    if isinstance(node, UnaryOp):
        return UnaryOp(convert_to_nnf(node.operand))
    return node

def distribute_or_over_and(node):
    """Adım 3: CNF Dağılımı (VE'lerin VEYA'sı)."""
    if isinstance(node, BinaryOp):
        node.left = distribute_or_over_and(node.left)
        node.right = distribute_or_over_and(node.right)
        
        if node.operator == 'v':
            # (P ^ Q) v R => (P v R) ^ (Q v R)
            if isinstance(node.left, BinaryOp) and node.left.operator == '^':
                p, q, r = node.left.left, node.left.right, node.right
                return distribute_or_over_and(BinaryOp(BinaryOp(p, r, 'v'), BinaryOp(q, r, 'v'), '^'))
            
            # P v (Q ^ R) => (P v Q) ^ (P v R)
            elif isinstance(node.right, BinaryOp) and node.right.operator == '^':
                p, q, r = node.left, node.right.left, node.right.right
                return distribute_or_over_and(BinaryOp(BinaryOp(p, q, 'v'), BinaryOp(p, r, 'v'), '^'))
    return node

def get_variables(node, var_set):
    """Ağaçtaki tüm değişken isimlerini toplar."""
    if isinstance(node, Variable):
        var_set.add(node.name)
    elif isinstance(node, UnaryOp):
        get_variables(node.operand, var_set)
    elif isinstance(node, BinaryOp):
        get_variables(node.left, var_set)
        get_variables(node.right, var_set)


class DIMACSGenerator:
    def __init__(self, cnf_root):
        self.root = cnf_root
        self.var_map = {}
        self.clauses = [] # [[1, -2], [3], ...]

    def generate(self):
        var_set = set()
        get_variables(self.root, var_set)
        sorted_vars = sorted(list(var_set))
        
        for idx, var_name in enumerate(sorted_vars, 1):
            self.var_map[var_name] = idx
        
        # traverse the CNF tree to collect clauses
        self._collect_clauses(self.root)
        
        output_lines = []
        if sorted_vars:
            vars_str = ", ".join(f"{name}={self.var_map[name]}" for name in sorted_vars)
            output_lines.append(f"c Variable Map: {vars_str}")
        else:
            output_lines.append("c Variable Map:")
        
        output_lines.append(f"p cnf {len(self.var_map)} {len(self.clauses)}")
        
        for clause in self.clauses:
            line = " ".join(map(str, clause)) + " 0"
            output_lines.append(line)
            
        return "\n".join(output_lines)

    def _collect_clauses(self, node):
        """CNF ağacını (AND zinciri) clause listesine çevirir."""
        if isinstance(node, BinaryOp) and node.operator == '^':
            self._collect_clauses(node.left)
            self._collect_clauses(node.right)
        else:
            literals = []
            self._collect_literals(node, literals)
            self.clauses.append(literals)

    def _collect_literals(self, node, literals):
        """Bir clause içindeki literalleri toplar."""
        if isinstance(node, BinaryOp) and node.operator == 'v':
            self._collect_literals(node.left, literals)
            self._collect_literals(node.right, literals)
        elif isinstance(node, UnaryOp): # ~A
            var_id = self.var_map[node.operand.name]
            literals.append(-var_id)
        elif isinstance(node, Variable): # A
            var_id = self.var_map[node.name]
            literals.append(var_id)

def main():
    print("--- BLG 345E CNF Converter ---")
    input_formula = "(A <-> B) ^ (A v ~B v C)"
    
    print(f"Input: {input_formula}\n")

    try:
        parser = LogicParser()
        ast = parser.parse(input_formula)
        
        step1 = eliminate_implications(ast)
        step2 = convert_to_nnf(step1)
        cnf_ast = distribute_or_over_and(step2)
        
        dimacs_gen = DIMACSGenerator(cnf_ast)
        result = dimacs_gen.generate()
          
        with open("dimacs_out.cnf", "w") as f:
            f.write(f"c Formula: {input_formula}\n")
            f.write(result)
            print("\nFile saved as 'dimacs_out.cnf'")

    except Exception as e:
        print(f"Error : {e}")

if __name__ == "__main__":
    main()