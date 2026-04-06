from pathlib import Path
import ymmsl

config = ymmsl.load(Path('macro_meso_micro.ymmsl'))

cps = config.models['macro_meso_micro_model'].components
print(cps[0].name)              # output: macro
print(cps[0].implementation)    # output: None
print(cps[0].multiplicity)      # output: []
print(cps[2].name)              # output: micro
print(cps[2].implementation)    # output: micro_model
print(cps[2].multiplicity)      # output: [5]
