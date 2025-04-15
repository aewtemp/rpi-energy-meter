"""
module that acts as the main 
"""

from .utils import *
from .samples import *
from .plotting import *

class RpiEnergyMeter():
    

    def run():
        
        
        while True:
            try:
                pass
            except KeyboardInterrupt:
                em.stop()
                DB.close()
                save_total_kwh(MEASUREMENTS)
                with open('data/kwh.ini', 'w') as configfile:
                    config.write(configfile)
                # for _ in ADC:
                #     _.close 
                sys.exit()


if __name__ == "__main__":
    run()
