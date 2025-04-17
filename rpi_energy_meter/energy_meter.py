"""
module that acts as the main 
"""


from .config import load_config, write_config, read_total_kwh, save_total_kwh
from .logging import logger
from .utils import *
from .samples import *
from .plotting import *
from .influxv2_interface import infv2db
from box import Box
from textwrap import dedent

from typing import Any, Union
import argparse
import logging
import pickle
import timeit

class RpiEnergyMeter():
    
    def __init__(self, config: Any, verbose: bool) -> None:
        self.config = load_config(config)
        self.verbose = verbose

    def run(self, command: Union[Any, None], **kwargs):

        if self.verbose:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)

        if command is None:
            logger.debug("No command provided. Running normal mode")
            command = ""

        # from rpi_energy_meter.mcp3008 import MCP3008
        # logger.debug(f"... Initializing ADC instances for {self.config.PHASES.COUNT} Phases")
        # ADC = [MCP3008(bus=0, device=i) for i in range(self.config.PHASES.COUNT)]

        from rpi_energy_meter.mcp3008 import MCP3008_2
        logger.debug(f"... Initializing ADC instances for {self.config.PHASES.COUNT} Phases")
        ADC = [MCP3008_2(device=i) for i in range(self.config.PHASES.COUNT)]

        logger.debug(f"... Initializing Measurement instances for {self.config.PHASES.COUNT} Phases")
        MEASUREMENTS = [SAMPLES(self.config, i+1, totals=read_total_kwh(self.config)[i]) for i in range(self.config.PHASES.COUNT)]

        if command.lower() == "speedtest":
            # This mode is intended to measure the performance of the measurement process
            while True:
                try:
                    for i in range(self.config.PHASES.COUNT):
                        # collect_data(self.config, i+1, ADC[i], MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES)
                        collect_data2(self.config, i+1, ADC[i], MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES)
                        # generate_data(self.config, MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES) # Only for testing
                except KeyboardInterrupt:
                    # for _ in ADC:
                    #     _.close 
                    sys.exit()

        if command.lower() == "debug":
            # This mode is intended to take a look at the raw CT sensor data.  It will take ADC_SAMPLES samples from each CT sensor, plot them to a single chart, write the chart to an HTML file located in /var/www/html/, and then terminate.
            # It also stores the samples to a file located in ./data/samples/last-debug.pkl so that the sample data can be read when this program is started in 'phase' mode.

            for i in range(self.config.PHASES.COUNT):
                # Time sample collection
                start = timeit.default_timer()
                # collect_data(self.config, i+1, ADC[i], MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES)
                collect_data2(self.config, i+1, ADC[i], MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES)
                # generate_data(self.config, MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES) # Only for testing

                stop = timeit.default_timer()
                duration = stop - start

                # Calculate Sample Rate in Kilo-Samples Per Second.
                sample_count = 8 * self.config.GENERAL.ADC_SAMPLES

                sample_rate = round((sample_count / duration) / 1000, 2)

                logger.debug(f"Finished Collecting Samples for Phase {i+1}. Sample Rate: {sample_rate} KSPS")
                logger.debug(f"Calculating Values for Phase {i+1}.")

                MEASUREMENTS[i].calculate_power(i+1, self.config)

                logger.debug(f"Writing debug files to disk for Phase {i+1}.")
                # Save samples with pickle to disk
                with open('./last-debug-phase'+str(i+1)+'.pkl', 'wb') as f:
                    pickle.dump(MEASUREMENTS[i], f)

                if "title" not in kwargs:
                    title = f"Phase_{i+1}"
                else:
                    title = f"{title} Phase_{str(i+1)}"

                title = title.replace(" ","_")
                logger.debug("Building plot.")
                print_results(self.config, i+1, ADC[i], MEASUREMENTS[i].power)
                dump_data(i+1, MEASUREMENTS[i])
                plot_data(MEASUREMENTS[i], title, sample_rate=sample_rate)
                ip = get_ip()
            if ip:
                logger.info(f"Chart created! Visit http://{ip}/{title}.html to view the chart. Or, simply visit http://{ip} to view all the charts created using 'debug' and/or 'calibration' mode.")
            else:
                logger.info("Chart created! I could not determine the IP address of this machine. Visit your device's IP address in a webrowser to view the list of charts you've created using 'debug' and/or 'calibration' mode.")

            sys.exit()


        if command.lower() == "calibration":
            # This mode is intended to be used for correcting the phase error in your CT sensors. Please ensure that you have a purely resistive load running through your CT sensors - that means no electric fans and no digital circuitry!
            while True:
                try:
                    phase_num = int(input("\nWhich PHASE are you calibrating on? Enter the number Phase [1 - 3]: "))
                    ct_num = int(input("\nWhich CT number are you calibrating? Enter the number of the CT label [1 - 6]: "))
                    if phase_num not in range(1, 4):
                        logger.error("Please choose PHASE from 1, 2 or 3.")
                    elif ct_num not in range(1, 7):
                        logger.error("Please choose from CT numbers 1, 2, 3, 4, 5, or 6.")
                    else:
                        phase_selection = phase_num - 1
                        ct_selection = ct_num - 1
                        break
                except ValueError:
                    logger.error("Please enter an integer! Acceptable choices are: 1, 2, 3, 4, 5, 6.")

            cont = input(dedent(f"""
                #------------------------------------------------------------------------------#
                # IMPORTANT: Make sure that current transformer {ct_selection + 1} is installed over          #
                #            a purely resistive load and that the load is turned on            #
                #            before continuing with the calibration!                           #
                #------------------------------------------------------------------------------#

                Continue? [Y/Yes/n/no]: """))

            if cont.lower() in ['n', 'no']:
                logger.info("\nCalibration Aborted.\n")
                sys.exit()

            # collect_data(self.config, phase_selection+1, ADC[phase_selection], MEASUREMENTS[phase_selection], self.config.GENERAL.ADC_SAMPLES)
            collect_data2(self.config, phase_selection+1, ADC[phase_selection], MEASUREMENTS[phase_selection], self.config.GENERAL.ADC_SAMPLES)
            # generate_data(self.config, MEASUREMENTS[phase_selection], self.config.GENERAL.ADC_SAMPLES) # Only for testing

            results = MEASUREMENTS[phase_selection].calculate_power(phase_selection+1, self.config)

            # Get the current power factor and check to make sure it is not negative. If it is, the CT is installed opposite to how it should be.
            pf = results[ct_selection]['PF']
            initial_pf = pf
            if pf < 0:
                logger.info(dedent('''
                    Current transformer is installed backwards. Please reverse the direction that it is attached to your load. \n
                    (Unclip it from your conductor, and clip it on so that the current flows the opposite direction from the CT's perspective) \n
                    Press ENTER to continue when you've reversed your CT.'''))
                input("[ENTER]")
                # Check to make sure the CT was reversed properly by taking another batch of samples/calculations:
                # collect_data(self.config, phase_selection+1, ADC[i], MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES)
                collect_data2(self.config, phase_selection+1, ADC[i], MEASUREMENTS[i], self.config.GENERAL.ADC_SAMPLES)
                # generate_data(self.config, MEASUREMENTS[phase_selection], self.config.GENERAL.ADC_SAMPLES)  # Only for testing
                results = MEASUREMENTS[phase_selection].calculate_power(phase_selection+1, self.config)
                pf = results[ct_selection]['PF']
                if pf < 0:
                    logger.info(dedent("""It still looks like the current transformer is installed backwards.  Are you sure this is a resistive load?\n
                        Please consult the project documentation on https://github.com/david00/rpi-power-monitor/wiki and try again."""))
                    sys.exit()

            # Initialize phasecal values
            previous_pf = 0
            new_pf = pf

            old_wave = copy(MEASUREMENTS[phase_selection].samples)
            phaseshift = MEASUREMENTS[phase_selection].calculate_phaseshift(ct=ct_selection)
            print(f"Alt {phaseshift}")

            MEASUREMENTS[phase_selection].shift_phase(ct=ct_selection, amount=phaseshift)
            phaseshift_neu = MEASUREMENTS[phase_selection].calculate_phaseshift(ct=ct_selection)
            print(f"Neu {phaseshift_neu}")
            
            report_title = f'CT{ct_num}-phase-correction-result'
            plot_data(MEASUREMENTS[phase_selection].samples, report_title, ct_selection, old_wave)
            logger.info(f"file written to {report_title}.html")
            sys.exit()

        # Normal mode from here
        logger.debug(f"Initializing InfluxDBv2 instance")
        DB = infv2db(
            token = self.config.INFLUX.token,
            organization = self.config.INFLUX.organization,
            bucket = self.config.INFLUX.bucket,
            host = self.config.INFLUX.host,
            port = self.config.INFLUX.port
        )


        logger.info("Starting Raspberry Pi Power Monitor")
        logger.info("... Press Ctrl-c to quit...")
        
        # The following empty dictionaries will hold the respective calculated values at the end of each polling cycle, which are then averaged prior to storing the value to the DB.
        rms_voltages = [[] for _ in range(self.config.PHASES.COUNT)]
        ct_currents = [[dict(power=[], pf=[], current=[]) for ct in range(6)] for phase in range(self.config.PHASES.COUNT)]
        averages = [0 for _ in range(self.config.PHASES.COUNT)]  # Counter for aggregate function
        time_energy = [0.00 for _ in range(self.config.PHASES.COUNT)]
        timestamp = [0 for _ in range(self.config.PHASES.COUNT)]
        round_start = 0.0

        while True:
            try:
                if averages[0] == 0:
                    logger.info(f"Starting new round")
                    round_start = time.time()

                for phase in range(self.config.PHASES.COUNT):
                    if averages[phase] == 0:
                        time_energy[phase] = time.time()
                        timestamp[phase] = int(time.time() * 1000)  # Miliseconds timestamp as integer

                    # Average 5 readings before sending to db (0 to 4)
                    if averages[phase] < 5:
                        # collect_data(self.config, phase+1, ADC[phase], MEASUREMENTS[phase], self.config.GENERAL.ADC_SAMPLES)
                        collect_data2(self.config, phase+1, ADC[phase], MEASUREMENTS[phase], self.config.GENERAL.ADC_SAMPLES)
                        # generate_data(self.config, MEASUREMENTS[phase], self.config.GENERAL.ADC_SAMPLES) # Only for testing

                        for y in range(self.config.CTS.get(str(phase+1)).COUNT):
                            MEASUREMENTS[phase].shift_phase(ct=y)
                        results = MEASUREMENTS[phase].calculate_power(phase+1, self.config)

                        rms_voltages[phase].append(results[0]['Voltage'])
                        for ct in range(self.config.CTS.get(str(phase+1)).COUNT):
                            ct_currents[phase][ct]['current'].append(results[ct]['Current'])
                            ct_currents[phase][ct]['power'].append(results[ct]['Watts'])
                            ct_currents[phase][ct]['pf'].append(results[ct]['PF'])

                        averages[phase] += 1

                    else:  # Calculate the average, send the result to InfluxDB, and reset the dictionaries for the next sets of data.
                        time_energy_end = time.time()
                        timestamp[phase] = int(timestamp[phase] + ((time.time() * 1000 - timestamp[phase]) / 2))
                        points = []
                        points.append(to_point(phase+1, rms_voltages[phase], averages[phase], "voltage", timestamp[phase]))
                        for ct in range(self.config.CTS.get(str(phase+1)).COUNT):
                            energy = ((sum(ct_currents[phase][ct]['power']) / averages[phase]) * (time_energy_end - time_energy[phase])) / (60 * 60 * 1000)
                            MEASUREMENTS[phase]._energy[ct]['Total'] += energy
                            points.append(to_point(phase+1, MEASUREMENTS[phase]._energy[ct]['Total'], 1, "total_" + str(ct+1), timestamp[phase]))
                            points.append(to_point(phase+1, ct_currents[phase][ct], averages[phase], "current_" + str(ct+1), timestamp[phase]))

                        DB.write(points)

                        #  Reset instances to empty
                        rms_voltages[phase] = []
                        ct_currents[phase] = [dict(power=[], pf=[], current=[]) for ct in range(self.config.CTS.get(str(phase+1)).COUNT)]
                        averages[phase] = 0

                        if logger.level == logging.DEBUG:
                            print_results(self.config, phase+1, ADC[phase], MEASUREMENTS[phase].power)

                if averages[2] == 5:
                    round_took = time.time() - round_start
                    logger.info(f"Stopped the Round. Took {round_took} seconds to do the Round :)")
                    save_total_kwh(self.config, MEASUREMENTS)
                    write_config("config.toml", self.config)


            except KeyboardInterrupt:
                DB.close()
                save_total_kwh(MEASUREMENTS)
                write_config("config.toml", self.config)
                # for _ in ADC:
                #     _.close 
                sys.exit()



if __name__ == "__main__":
    run()
