from pathlib import Path
import ymmsl

config = ymmsl.load(Path('from_python.ymmsl'))

config.settings['d'] = 0.12

ymmsl.save(config, Path('out.ymmsl'))


