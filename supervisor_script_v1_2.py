#! python3

###############################################
# supervisor_script_v1_2.py
#
# updated 18/03/2025
# > Adapted to run all json files in a folder
###############################################

import os
import time
import matplotlib.pyplot as plt

from supervisor_v2_2 import Supervisor


# -----------------------------
# Defenitions
# -----------------------------
def runner(config_path):
    # Create Supervisor instance (loads config from specified .json file)
    sup = Supervisor(config_path)
    timestamp=sup.TimeStamp()
    errors = []
    try:
        #######################################
        # 1) INITIALIZATION PHASE
        #######################################

        # Open all devices: HV power supply, DMMs, oscilloscope, microcontroller
        # To list devices use sup.list_instruments()
        sup.open_all_devices()  #This opens all the devices.

        # Setup microcontroller, oscilloscope and dmm
        # Turn on legs, set Duty, Frequency, Dead Time, etc.
        # Instead of using Shield, we now call sup.microcontroller_send_command(...)
        sup.microcontroller_setup()
        sup.oscilloscope_setup()
        sup.dmm_setup()

        time.sleep(sup.dmm_init_delay) # Wait DMM initialized
        print('Config OK')


        #######################################
        # 2) TEST PHASE
        #######################################
        # Example: HV power supply usage (we can ramp up, sweep phase, ramp down, etc.)
        # Turn on power supply
        sup.power_supply_output_change("ON", delay=sup.power_supply_output_delay)
        print('HV supply ON')

        # Ramp up voltage
        sup.power_supply_voltage_ramp_up(
            sup.VoltageWrite,
            sup.voltage_step,
            start_value=0,
            delay=sup.power_supply_ramp_delay
        )
        print("Source ramped up OK")

        # Sweep phase shift
        sup.microcontroller_sweep_phase_shift(sup.PhaseInit, sup.PhaseFinal, sup.PhaseStep)
        print("Sweep phase done OK")

        # Ramp down
        sup.power_supply_voltage_ramp_down(
            sup.VoltageWrite,
            -sup.voltage_step,
            -sup.voltage_step,
            delay=sup.power_supply_ramp_delay
        )
        print("Source ramped down OK")
    except Exception as e:
            errors.append(f"Failed to finish run: {e}")
    finally:
        try:
            # Turn off power supply
            sup.power_supply_output_change("OFF")
            print("HV power supply OFF successfully.")
        except Exception as e:
            errors.append(f"Failed to turn OFF HV power supply: {e}")


        # Return to initial Phase
        sup.microcontroller_send_command("PHASE_SHIFT", "LEG2", sup.InitialPhaseShiftPWM)

        # Turn off the legs
        sup.microcontroller_send_command("LEG", "LEG1", "OFF")
        sup.microcontroller_send_command("LEG", "LEG2", "OFF")

        # Read data from the DMM buffers
        time.sleep(1)
        voltage_data = sup.dmm_get_buffer(sup.dmm_for_voltage, wait_meas_complete=False)
        time.sleep(1)
        current_data = sup.dmm_get_buffer(sup.dmm_for_current, wait_meas_complete=False)


        #######################################
        # 3) SAVE RESULTS PHASE
        #######################################
        
        # Save raw data to CSV
        sup.export_result_to_csv(str(voltage_data),"Voltage")
        sup.export_result_to_csv(str(current_data),"Current")

        # Plot data
        plt.figure()
        plt.title("Voltage Data Points")
        plt.plot(voltage_data, marker='o', linestyle='none')
        plt.savefig(sup.result_output_path+'/01-Voltage-'+timestamp+'.svg', format='svg', dpi=300)

        plt.figure()
        plt.title("Current Data Points")
        plt.plot(current_data, marker='o', linestyle='none')
        plt.savefig(sup.result_output_path+'/02-Current-'+timestamp+'.svg', format='svg', dpi=300)

        power_data = [v * i for v, i in zip(voltage_data, current_data)]
        plt.figure()
        plt.title("Power Data Points")
        plt.plot(power_data, marker='o', linestyle='none')
        plt.savefig(sup.result_output_path+'/03-Power-'+timestamp+'.svg', format='svg', dpi=300)
        
        plt.show(block=False)
        
        plt.pause(5)
        plt.close()

        try:
            # Optionally read or save oscilloscope history
            # sup.oscilloscope_read_history_and_choose_to_save()

            # new function that deals with screenshots, csv data, and measure for each frame
            sup.oscilloscope_save_results()
        except Exception as e:
            errors.append(f"Failed to read and/or save Oscilloscope: {e}")
        

        # Attempt to close HV power supply
        try:
            sup.close_hv_power_supply()
            print("HV power supply closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close HV power supply: {e}")

        # Attempt to close DMM for current
        try:
            sup.close_dmm_for_current()
            print("DMM for current closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close DMM for current: {e}")

        # Attempt to close DMM for voltage
        try:
            sup.close_dmm_for_voltage()
            print("DMM for voltage closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close DMM for voltage: {e}")

        # Attempt to close oscilloscope
        try:
            sup.close_oscilloscope()
            print("Oscilloscope closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close oscilloscope: {e}")

        # Attempt to close microcontroller
        try:
            sup.close_microcontroller()
            print("Microcontroller closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close microcontroller: {e}")

        # # INSERT HERE CLOSE RM (class to be modified)
        # Attempt to close ressource manager
        try:
            sup.close_rm_manager()
            print("Resource Manager closed successfully.")
        except Exception as e:
            errors.append(f"Failed to close resource manager: {e}")

        # If any errors were collected, raise them as a combined RuntimeError
        if errors:
            raise RuntimeError(
                "One or more devices failed to close:\n" + "\n".join(errors)
            )
        else:
            print("All devices closed successfully. Test complete!")


def find_json_files(folder):
    json_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.relpath(os.path.join(root, file), "./"))
    return json_files


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    jsonlist = find_json_files("PhaseShift")
    for jsonfile in jsonlist:
        print(jsonfile)
        runner(jsonfile)
        print("Done!\n\n")
        time.sleep(2)
