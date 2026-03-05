# Run this in your backend/ folder to confirm which files are loaded
import code_gen
import tac_interpreter
print("code_gen path:", code_gen.__file__)
print("tac_interpreter path:", tac_interpreter.__file__)

# Quick array test
from code_gen import CodeGenerator
from tac_interpreter import TACInterpreter

tokens = [
    ("main","main",1,1),("(","(",1,5),(")",  ")",1,6),("{","{",1,7),
    ("word","word",2,3),("arr","identifier",2,8),("[","[",2,11),("1","num_literal",2,12),("]","]",2,13),(";",";",2,14),
    ("arr","identifier",3,3),("[","[",3,6),("0","num_literal",3,7),("]","]",3,8),("=","=",3,10),('"apple"',"word_literal",3,12),(";",";",3,19),
    ("out","out",4,3),("(","(",4,6),("arr","identifier",4,7),("[","[",4,10),("0","num_literal",4,11),("]","]",4,12),(")",  ")",4,13),(";",";",4,14),
    ("}","}",5,1),
]
gen = CodeGenerator()
gen.generate(tokens)
print("\nTAC:")
for ins in gen.tac: print(f"  {ins}")
interp = TACInterpreter()
_, events = interp.run(gen.tac, [])
print("\nEvents:", events)