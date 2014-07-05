import os
import ConfigParser

cfg = ConfigParser.SafeConfigParser()
cfg.read('/etc/ghai.cfg')
cfg.read(os.getenv('HOME')+'/.ghairc')
cfg.read('.ghairc')
