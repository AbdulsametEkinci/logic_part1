import os
import sys

try:
    from cnf import LogicParser, DIMACSGenerator, convert_to_nnf, eliminate_implications, distribute_or_over_and
except ImportError:
    print("Error: Could not import 'cnf' module. Ensure 'cnf.py' is in the same directory.")
    sys.exit(1)

def process_logic_files():
    input_dir = "input_files"
    output_dir = "output_files"
            
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]

    if not files:
        print(f"No .txt files found in '{input_dir}'.")
        return

    print(f"Processing {len(files)} files...")

    for filename in files:
        input_path = os.path.join(input_dir, filename)
        #change input1 to output 1
        output_filename = filename.replace("input", "output")
        output_path = os.path.join(output_dir, os.path.splitext(output_filename)[0] + ".cnf")

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                formula = f.read().strip()
            
            if not formula:
                continue

            parser = LogicParser()
            ast = parser.parse(formula)
            ast = eliminate_implications(ast)
            ast = convert_to_nnf(ast)
            cnf_ast = distribute_or_over_and(ast)            
            
            generator = DIMACSGenerator(cnf_ast)
            dimacs_output = generator.generate()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"c Formula: {formula}\n")
                f.write(dimacs_output)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("Conversion complete. Check 'output_files' directory.")

if __name__ == "__main__":
    process_logic_files()