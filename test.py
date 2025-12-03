import os
import sys

try:
    from cnf import LogicParser, DIMACSGenerator, convert_to_nnf, eliminate_implications, distribute_or_over_and
except ImportError:
    print("Error: 'cnf.py' modülü bulunamadı. Lütfen aynı dizinde olduğundan emin olun.")
    sys.exit(1)

def run_test_suite():
    base_dir = "test_suite"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"'{base_dir}' folder created for test cases.\n")

    test_cases = [
        {
            "id": 1,
            "desc": "Alphanumeric Variables",
            "formula": "x1 v x2 ^ ~var3"
        },
        {
            "id": 2,
            "desc": "Operator Precedence (Implies vs Or)",
            "formula": "A -> B v C"
        },
        {
            "id": 3,
            "desc": "Deep Nesting & De Morgan",
            "formula": "~((A v B) ^ (C v D))"
        },
        {
            "id": 4,
            "desc": "Biconditional Chain",
            "formula": "(A <-> B) ^ C"
        },
        {
            "id": 5,
            "desc": "Complex Distribution",
            "formula": "(A ^ B) v (C ^ D)"
        }
    ]

    print("Creating test files\n")

    for case in test_cases:
        case_id = case["id"]
        formula = case["formula"]
        desc = case["desc"]
        
        test_dir = os.path.join(base_dir, f"Test_{case_id}")
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        
        print(f"Test {case_id}: {desc}")
        print(f"  Formül: {formula}")

        input_path = os.path.join(test_dir, "p_logic_in.txt")
        with open(input_path, "w") as f:
            f.write(formula)
        print(f"  -> input: {input_path}")

        try:
            parser = LogicParser()
            ast = parser.parse(formula)
            step1 = eliminate_implications(ast)
            step2 = convert_to_nnf(step1)
            cnf_ast = distribute_or_over_and(step2)            
            generator = DIMACSGenerator(cnf_ast)
            dimacs_output = generator.generate()
            
            output_path = os.path.join(test_dir, "dimacs_out.cnf")
            with open(output_path, "w") as f:
                f.write(f"c Formula: {formula}\n")
                f.write(dimacs_output)
            print(f"  -> Çıktı oluşturuldu: {output_path}")
            
        except Exception as e:
            print(f"  -> error: {e} \n")

    print("\n Check the 'test_suite' folder for all test cases.")

if __name__ == "__main__":
    run_test_suite()