/*
 * Copyright (c) 2021-2024 LAAS-CNRS
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Lesser General Public License as published by
 *   the Free Software Foundation, either version 2.1 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Lesser General Public License for more details.
 *
 *   You should have received a copy of the GNU Lesser General Public License
 *   along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * SPDX-License-Identifier: LGLPV2.1
 */

/**
 * @brief  This file it the main entry point of the
 *         OwnTech Power API. Please check the OwnTech
 *         documentation for detailed information on
 *         how to use Power API: https://docs.owntech.org/
 *
 * @author Clément Foucher <clement.foucher@laas.fr>
 * @author Luiz Villa <luiz.villa@laas.fr>
 */


#include "comm_protocol.h"

extern float32_t V1_low_value;
extern float32_t V2_low_value;
extern float32_t I1_low_value;
extern float32_t I2_low_value;
extern float32_t I_high_value;
extern float32_t V_high_value;

extern float32_t T1_value;
extern float32_t T2_value;


extern float32_t V1_max;
extern float32_t V2_max;

extern float32_t kp;
extern float32_t Ti;
extern float32_t Td;
extern float32_t N;
extern float32_t upper_bound;
extern float32_t lower_bound;
extern float32_t V_ref;
extern float32_t Ts;

extern uint16_t dead_time_max;
extern uint16_t dead_time_min;
extern int16_t phase_shift_max;
extern int16_t phase_shift_min;


extern Pid pid1;
extern Pid pid2;
extern Pid pid3;


#ifdef CONFIG_SHIELD_OWNVERTER

extern float32_t V3_low_value;
extern float32_t I3_low_value;
extern float32_t V3_max;
extern float32_t T3_value;

#endif


extern float32_t duty_cycle;
bool is_downloading;
bool enable_acq;
extern uint32_t num_trig_ratio_point;
extern uint16_t NB_DATAS;

extern Rs485Communication rs485;

float32_t reference_value = 0.0;

// Declare the tracking variable struct
TrackingVariables tracking_vars[] = {
    {"V1", &V1_low_value, V1_LOW},
    {"V2", &V2_low_value, V2_LOW},
    {"VH", &V_high_value, V_HIGH},
    {"I1", &I1_low_value, I1_LOW},
    {"I2", &I2_low_value, I2_LOW},
    {"IH", &I_high_value, I_HIGH}
#ifdef CONFIG_SHIELD_OWNVERTER
    ,{"V3", &V3_low_value, V3_LOW},
     {"I3", &I3_low_value, I3_LOW}
#endif
};

PowerLegSettings power_leg_settings[] = {
    //   LEG_OFF      ,   CAPA_OFF      , DRIVER_OFF      ,  BUCK_MODE_ON,  BOOST_MODE_ON
    {{BOOL_SETTING_OFF, BOOL_SETTING_OFF, BOOL_SETTING_OFF,  BOOL_SETTING_OFF,  BOOL_SETTING_OFF}, {LEG1, LEG1},  &V1_low_value, "V1", reference_value, 0.1},
    {{BOOL_SETTING_OFF, BOOL_SETTING_OFF, BOOL_SETTING_OFF,  BOOL_SETTING_OFF,  BOOL_SETTING_OFF}, {LEG2, LEG2},  &V2_low_value, "V2", reference_value,  0.1}
#ifdef CONFIG_SHIELD_OWNVERTER
    ,{{BOOL_SETTING_OFF, BOOL_SETTING_OFF, BOOL_SETTING_OFF,  BOOL_SETTING_OFF,  BOOL_SETTING_OFF}, {LEG3, LEG3},  &V3_low_value, "V3", reference_value, frequency_value, 0.1}
#endif
};

cmdToSettings_t power_settings[] = {
    {"_l", boolSettingsHandler},
    {"_c", boolSettingsHandler},
    {"_v", boolSettingsHandler},
    {"_b", boolSettingsHandler},
    {"_t", boolSettingsHandler},
    {"_r", referenceHandler},
    {"_p", phaseShiftHandler},
    {"_x", deadTimeRisingHandler},
    {"_z", deadTimeFallingHandler},
    {"_d", dutyHandler},
    {"_f", frequencyHandler},
};

// testSensiSettings_t testSensi_settings[] = {
//     {"_p", kpHandler},
//     {"_i", tiHandler},
//     {"_d", tdHandler},
//     {"_n", nHandler},
//     {"_u", upperHandler},
//     {"_l", lowerHandler},
//     {"_r", vrefHandler},
// };

cmdToState_t default_commands[] = {
    {"_i", IDLE},
    {"_f", POWER_OFF},
    {"_o", POWER_ON},
};

scopeToCommand_t scope_commands[] = {
    {"_a", ENABLE_ACQUISITION},
    {"_r", READ_SCOPE},
};


tester_states_t mode = IDLE;
scope_commands_t action;

uint8_t num_tracking_vars = sizeof(tracking_vars)/sizeof(tracking_vars[0]);
uint8_t num_power_settings =  NUM_OF_SETTINGS;
uint8_t num_default_commands = sizeof(default_commands)/sizeof(default_commands[0]);
uint8_t num_scope_commands = sizeof(scope_commands)/sizeof(scope_commands[0]);
uint8_t num_testSensi_settings =  sizeof(testSensi_settings)/sizeof(testSensi_settings[0]);

ConsigneStruct_t tx_consigne;
ConsigneStruct_t rx_consigne;
uint8_t* buffer_tx = (uint8_t*)&tx_consigne;
uint8_t* buffer_rx =(uint8_t*)&rx_consigne;

uint8_t status;
uint32_t counter_time=0;

/* analog test parameters*/
uint16_t analog_value;
uint16_t analog_value_ref=1000;

/* Sync test parameters*/
uint8_t ctrl_slave_counter=0;


uint8_t received_serial_char;
uint8_t received_char;
char bufferstr[255]={};
bool print_done = false;

/* RS485 test parameters*/
uint8_t rs485_send;
uint8_t rs485_receive;

/* Sync test parameters*/
uint8_t sync_master_counter = 0;

/* CAN Bus test parameters*/
bool can_test_ctrl_enable;
uint16_t can_test_reference_value;

uint16_t CAN_Bus_receive;
uint16_t CAN_Bus_receive_ref = 3000;
bool CAN_Bus_bool_receive;


/* BOOL value for testing */
bool test_start = false; // start the test after a certain period of time
bool RS485_success = false;
bool Sync_success = false;
bool Analog_success = false;
bool Can_success = false;


void initial_handle(uint8_t received_char)
{
    switch (received_char)
    {
        case 'd':
            console_read_line();
            printk("d buffer str = %s\n", bufferstr);
            defaultHandler();
            // spin.led.turnOn();
            break;
        case 's':
            console_read_line();
            printk("s buffer str = %s\n", bufferstr);
            powerLegSettingsHandler();
            // counter = 0;
            break;
        case 'k':
            console_read_line();
            printk("k buffer str = %s\n", bufferstr);
            calibrationHandler();
            break;
        case 'o': // 'o' for oscilloscope -> scope command ('a' or 'r')
            console_read_line();
            printk("0 buffer str = %s\n", bufferstr);
            scopeHandler();
            break;
        // case 'f': // 'o' for oscilloscope -> scope command ('a' or 'r')
        //     console_read_line();
        //     printk("0 buffer str = %s\n", bufferstr);
        //     frequencyHandler();
        //     break;
        // case 't': // 'o' for oscilloscope -> scope command ('a' or 'r')
        //     console_read_line();
        //     printk("buffer str = %s\n", bufferstr);
        //     testSensiHandler();
        // case 'r':
        //     is_downloading = true;
        //     break;
        // case 'a':
            // enable_acq = !(enable_acq);
            // break;
        // case 'c':
        //     num_trig_ratio_point = (num_trig_ratio_point + 1) % NB_DATAS;
        default:
            break;
    }
}

void frame_POWER_OFF()
{
    printk("{%u,%u,%u,%u}:", RS485_success,
                                Sync_success,
                                Analog_success,
                                Can_success);
    printk("[%d,%d,%d,%d,%d]:", power_leg_settings[LEG1].settings[0],
                                power_leg_settings[LEG1].settings[1],
                                power_leg_settings[LEG1].settings[2],
                                power_leg_settings[LEG1].settings[3],
                                power_leg_settings[LEG1].settings[4]);
    printk("%f:", power_leg_settings[LEG1].duty_cycle);
    printk("%f:", power_leg_settings[LEG1].reference_value);
    printk("%s:", power_leg_settings[LEG1].tracking_var_name);
    printk("%f:", tracking_vars[LEG1].address[0]);
    printk("[%d,%d,%d,%d,%d]:", power_leg_settings[LEG2].settings[0],
                                power_leg_settings[LEG2].settings[1],
                                power_leg_settings[LEG2].settings[2],
                                power_leg_settings[LEG2].settings[3],
                                power_leg_settings[LEG2].settings[4]);
    printk("%f:", power_leg_settings[LEG2].duty_cycle);
    printk("%f:", power_leg_settings[LEG2].reference_value);
    printk("%s:", power_leg_settings[LEG2].tracking_var_name);
    printk("%f:", tracking_vars[LEG2].address[0]);
#ifdef CONFIG_SHIELD_OWNVERTER
    printk("[%d,%d,%d,%d,%d]:", power_leg_settings[LEG3].settings[0],
                                power_leg_settings[LEG3].settings[1],
                                power_leg_settings[LEG3].settings[2],
                                power_leg_settings[LEG3].settings[3],
                                power_leg_settings[LEG3].settings[4]);
    printk("%f:", power_leg_settings[LEG3].duty_cycle);
    printk("%f:", power_leg_settings[LEG3].reference_value);
    printk("%s:", power_leg_settings[LEG3].tracking_var_name);
    printk("%f:", tracking_vars[LEG3].address[0]);
#endif
    printk("\n");
}

void frame_POWER_ON()
{
    printk("%f:", power_leg_settings[LEG1].duty_cycle);
    printk("%f:", V1_low_value);
    printk("%f:", I1_low_value);
    printk("%f:", V1_max);
    printk("%f:", T1_value);
    printk("%f:", power_leg_settings[LEG2].duty_cycle);
    printk("%f:", I2_low_value);
    printk("%f:", V2_low_value);
    printk("%f:", V2_max);
    printk("%f:", T2_value);
#ifdef CONFIG_SHIELD_OWNVERTER
    printk("%f:", power_leg_settings[LEG3].duty_cycle);
    printk("%f:", I3_low_value);
    printk("%f:", V3_low_value);
    printk("%f:", V3_max);
    printk("%f:", T3_value);
#endif
    printk("%f:", V_high_value);
    printk("%f:", I_high_value);
    printk("{%d:%d:%d:%d}", analog_value ,
                            can_test_ctrl_enable,
                            can_test_reference_value,
                            rx_consigne.test_RS485);
    printk("\n");
}

void console_read_line()
{
    for (uint8_t i = 0; received_char != '\n'; i++)
    {
        received_char = console_getchar();
        if (received_char == '\n')
        {
            if (bufferstr[i-1] == '\r')
            {
                bufferstr[i-1] = '\0';
            }
            else
            {
                bufferstr[i] = '\0';
            }
        }
        else
        {
            bufferstr[i] = received_char;
        }
    }
}

// void kpHandler(uint8_t test_leg, uint8_t setting_position){
//       if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
//     {
//         // Extract the duty cycle value from the protocol message
//         kp = atof(bufferstr + 9);

//     } else {
//         printk("Invalid protocol format: %s\n", bufferstr);
//     }
// }

// void tiHandler(uint8_t test_leg, uint8_t setting_position){
//       if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
//     {
//         // Extract the duty cycle value from the protocol message
//         Ti = atof(bufferstr + 9);

//     } else {
//         printk("Invalid protocol format: %s\n", bufferstr);
//     }
// }

// void tdHandler(uint8_t test_leg, uint8_t setting_position){
//       if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
//     {
//         // Extract the duty cycle value from the protocol message
//         Td = atof(bufferstr + 9);

//     } else {
//         printk("Invalid protocol format: %s\n", bufferstr);
//     }
// }

// void nHandler(uint8_t test_leg, uint8_t setting_position){
//       if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
//     {
//         // Extract the duty cycle value from the protocol message
//         N = atof(bufferstr + 9);

//     } else {
//         printk("Invalid protocol format: %s\n", bufferstr);
//     }
// }

// void upperHandler(uint8_t test_leg, uint8_t setting_position){
//       if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
//     {
//         // Extract the duty cycle value from the protocol message
//         upper_bound = atof(bufferstr + 9);

//     } else {
//         printk("Invalid protocol format: %s\n", bufferstr);
//     }
// }

// void lowerHandler(uint8_t test_leg, uint8_t setting_position){
//       if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
//     {
//         // Extract the duty cycle value from the protocol message
//         lower_bound = atof(bufferstr + 9);

//     } else {
//         printk("Invalid protocol format: %s\n", bufferstr);
//     }
// }

// void vrefHandler(uint8_t test_leg, uint8_t setting_position){
//       if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
//         strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
//     {
//         // Extract the duty cycle value from the protocol message
//         V_ref = atof(bufferstr + 9);

//     } else {
//         printk("Invalid protocol format: %s\n", bufferstr);
//     }
// }

void phaseShiftHandler(uint8_t power_leg, uint8_t setting_position){
    // Check if the bufferstr starts with "_d_"
    if (strncmp(bufferstr, "_LEG1_p_", 8) == 0 || 
        strncmp(bufferstr, "_LEG2_p_", 8) == 0 || 
        strncmp(bufferstr, "_LEG3_p_", 8) == 0) 
    {
        // Extract the phase shift value from the protocol message
        int16_t phase_shift = atoi(bufferstr + 8);
        printk("\n");
        printk("phase shift value = %d", phase_shift);
        printk("\n");

        // Check if the phase shift value is within the valid range (min-max)
        if (phase_shift >= phase_shift_min && phase_shift <= phase_shift_max) {
            // Update the duty cycle variable
            shield.power.setPhaseShift((leg_t)power_leg, phase_shift);
            power_leg_settings[power_leg].phase_shift = phase_shift;
        } else {
            printk("Invalid phase shift value: %d\n", phase_shift);
        }
    } else {
        printk("Invalid protocol format: %s\n", bufferstr);
    }

}

void frequencyHandler(uint8_t power_leg, uint8_t setting_position){
    // Check if the bufferstr starts with "_f_"
    if (strncmp(bufferstr, "_LEG1_f_", 8) == 0 || 
        strncmp(bufferstr, "_LEG2_f_", 8) == 0 || 
        strncmp(bufferstr, "_LEG3_f_", 8) == 0) 
    {
        // Extract the frequency value from the protocol message
        uint32_t frequency = atoi(bufferstr + 8);
        printk("\n");
        printk("frequency value = %d", frequency);
        printk("\n");

        hrtim_tu_number_t unit = PWMA; // all units have the same frequency, so we take PWMA as reference

        // Check if the frequency value is within the valid range (min-max)
        uint32_t min_freq = spin.pwm.getFrequencyMin(unit);
        uint32_t max_freq = spin.pwm.getFrequencyMax(unit);
        if (frequency >= min_freq && frequency <= max_freq) {
            // Update the frequency variable
            spin.pwm.setFrequency(frequency);
            power_leg_settings[power_leg].frequency = frequency;
        } else {
            printk("Invalid frequency value: %d\n", frequency);
            printk("Min frequency value: %d\n", min_freq);
            printk("Max frequency value: %d\n", max_freq);
        }
    } else {
        printk("Invalid protocol format: %s\n", bufferstr);
    }

}

void deadTimeRisingHandler(uint8_t power_leg, uint8_t setting_position){
    // Check if the bufferstr starts with "_d_"
    if (strncmp(bufferstr, "_LEG1_x_", 8) == 0 || 
        strncmp(bufferstr, "_LEG2_x_", 8) == 0 || 
        strncmp(bufferstr, "_LEG3_x_", 8) == 0) 
    {

        // Extract the duty cycle value from the protocol message
        uint16_t dead_time_rising = atoi(bufferstr + 8);

        // Check if the duty cycle value is within the valid range (min-max)
        if (dead_time_rising >= dead_time_min && dead_time_rising <= dead_time_max) {
            // Update the duty cycle variable
            shield.power.setDeadTime((leg_t) power_leg, 
                                      dead_time_rising, 
                                      power_leg_settings[power_leg].dead_time_falling);

            power_leg_settings[power_leg].dead_time_rising = dead_time_rising;           
        } else {
            printk("Invalid dead time value: %d\n", dead_time_rising);
        }
    } else {
        printk("Invalid protocol format: %s\n", bufferstr);
    }

}

void deadTimeFallingHandler(uint8_t power_leg, uint8_t setting_position){
    // Check if the bufferstr starts with "_d_"
    if (strncmp(bufferstr, "_LEG1_z_", 8) == 0 || 
        strncmp(bufferstr, "_LEG2_z_", 8) == 0 || 
        strncmp(bufferstr, "_LEG3_z_", 8) == 0) 
    {
        // Extract the duty cycle value from the protocol message
        uint16_t dead_time_falling = atoi(bufferstr + 8);
        printk("\n");
        printk("dead time falling value = %d", dead_time_falling);
        printk("\n");
        

        // Check if the duty cycle value is within the valid range (min-max)
        if (dead_time_falling >= dead_time_min && dead_time_falling <= dead_time_max) {
            // Update the duty cycle variable
            shield.power.setDeadTime((leg_t) power_leg, 
                                      power_leg_settings[power_leg].dead_time_rising, 
                                      dead_time_falling);

            power_leg_settings[power_leg].dead_time_falling = dead_time_falling;
        } else {
            printk("Invalid dead time value: %d\n", dead_time_falling);
        }
    } else {
        printk("Invalid protocol format: %s\n", bufferstr);
    }

}




void dutyHandler(uint8_t power_leg, uint8_t setting_position) {
    // Check if the bufferstr starts with "_d_"
    if (strncmp(bufferstr, "_LEG1_d_", 8) == 0 || 
        strncmp(bufferstr, "_LEG2_d_", 8) == 0 || 
        strncmp(bufferstr, "_LEG3_d_", 8) == 0) 
    {
        // Extract the duty cycle value from the protocol message
        float32_t duty_value = atof(bufferstr + 8);

        // Check if the duty cycle value is within the valid range (0-100)
        if (duty_value >= 0.0 && duty_value <= 1.0) {
            // Update the duty cycle variable
            power_leg_settings[power_leg].duty_cycle = duty_value;
        } else {
            printk("Invalid duty cycle value: %.5f\n", duty_value);
        }
    } else {
        printk("Invalid protocol format: %s\n", bufferstr);
    }
}


void referenceHandler(uint8_t power_leg, uint8_t setting_position){
    const char *underscore1 = strchr(bufferstr + 6, '_');
    if (underscore1 != NULL) {
        // Find the position of the next underscore after the first underscore
        const char *underscore2 = strchr(underscore1 + 1, '_');
        if (underscore2 != NULL) {
            // Extract the variable name between the underscores
            char variable[3];
            strncpy(variable, underscore1 + 1, underscore2 - underscore1 - 1);
            variable[underscore2 - underscore1 - 1] = '\0';

            // Extract the value after the second underscore
            reference_value = atof(underscore2 + 1);

            printk("Variable: %s\n", variable);
            printk("Value: %.5f\n", reference_value);

            // Finds the tracking variable and updates the address of the tracking_variable
            for (uint8_t i = 0; i < num_tracking_vars; i++) {
                if (strcmp(variable, tracking_vars[i].name) == 0) {
                    power_leg_settings[power_leg].tracking_variable = tracking_vars[i].address;
                    power_leg_settings[power_leg].tracking_var_name = tracking_vars[i].name;
                    power_leg_settings[power_leg].reference_value = reference_value;
                    break;
                }
            }
        }
    }

}



void calibrationHandler() {
    const char *underscore1 = strchr(bufferstr + 1, '_');
    if (underscore1 != NULL) {
        // Find the position of the next underscore after the first underscore
        const char *underscore2 = strchr(underscore1 + 1, '_');
        if (underscore2 != NULL) {
            // Extract the variable name between the underscores
            char variable[3];
            strncpy(variable, bufferstr + 1, underscore1 - (bufferstr + 1));
            variable[underscore1 - (bufferstr + 1)] = '\0';

            // Find the position of the next underscore after the second underscore
            const char *underscore3 = strchr(underscore2 + 1, '_');
            if (underscore3 != NULL) {
                // Extract the gain and offset values after the second underscore
                float32_t gain = atof(underscore1 + 3); // Skip 'g_' and parse gain
                float32_t offset = atof(underscore3 + 3); // Skip 'o_' and parse offset

                // Print the parsed values
                printk("Variable: %s\n", variable);
                printk("Gain: %.8f\n", gain);
                printk("Offset: %.8f\n", offset);

                // Find the tracking variable and update its gain and offset
                // Find the tracking variable and update its gain and offset
                for (uint8_t i = 0; i < num_tracking_vars; i++) {
                    if (strcmp(variable, tracking_vars[i].name) == 0) {
                        shield.sensors.setConversionParametersLinear(tracking_vars[i].channel_reference, gain, offset);
                        int8_t err_write = shield.sensors.storeParametersInMemory(tracking_vars[i].channel_reference);
                        
                        if (err_write){ 
                            printk("Error writing parameters in permanent storage!\n");
                        }
                        
                        int8_t err_check = shield.sensors.retrieveParametersFromMemory(tracking_vars[i].channel_reference);
                        
                        printk("Check for NVS writing (0 if correct) :%d!\n",err_check);
                        printk("channel name: %s\n", tracking_vars[i].name);
                        printk("channel: %d\n", tracking_vars[i].channel_reference);
                        
                        break;
                        
                        printk("channel: %s\n", tracking_vars[i].name);
                        printk("channel: %d\n", tracking_vars[i].channel_reference);
                        break;
                    }
                    if (i>=num_tracking_vars) printk("Variable not found: %s\n", variable); //prints an error if it does not find the variable
                }
            }
        }
    }
}

void boolSettingsHandler(uint8_t power_leg, uint8_t setting_position)
{
    if (strncmp(bufferstr + 7, "_on", 3) == 0) {
        power_leg_settings[power_leg].settings[setting_position] = BOOL_SETTING_ON;
#ifdef CONFIG_SHIELD_TWIST
        if (setting_position == BOOL_CAPA)    shield.power.connectCapacitor((leg_t)power_leg);  //turns the capacitor switch ON
#endif
        if (setting_position == BOOL_DRIVER) shield.power.connectDriver((leg_t)power_leg) ;  
    } else if (strncmp(bufferstr + 7, "_off", 4) == 0) {
        power_leg_settings[power_leg].settings[setting_position] = BOOL_SETTING_OFF;
#ifdef CONFIG_SHIELD_TWIST
        if (setting_position == BOOL_CAPA)  shield.power.disconnectCapacitor((leg_t)power_leg);  //turns the capacitor switch ON
#endif
        if (setting_position == BOOL_DRIVER) shield.power.disconnectDriver((leg_t)power_leg) ;  
    }
    else {
        // Unknown command
        printk("Unknown power command for LEG%d leg\n", power_leg + 1);
    }
}


void defaultHandler()
{
    for(uint8_t i = 0; i < num_default_commands; i++) //iterates the default commands
    {
        if (strncmp(bufferstr, default_commands[i].cmd, strlen(default_commands[i].cmd)) == 0)
        {
            mode = default_commands[i].mode;
            print_done = false; //authorizes printing the current state once
            return;
        }
    }
    printk("unknown default command %s\n", bufferstr);
}



void scopeHandler()
{
    for(uint8_t i = 0; i < num_default_commands; i++) //iterates the default commands
    {
        if (strncmp(bufferstr, scope_commands[i].cmd, strlen(scope_commands[i].cmd)) == 0)
        {
            action = scope_commands[i].action;
            if (action == ENABLE_ACQUISITION) {
                enable_acq = !(enable_acq);
                printk("abble");
            } else if (action == READ_SCOPE) {
                is_downloading = true;
                printk("action");
            }
            print_done = false; //authorizes printing the current state once
            return;
        }
    }
    printk("unknown scope command %s\n", bufferstr);
}  


// void testSensiHandler()
// {
//     // Determine the power leg based on the received message
//     leg_t test_leg = LEG1; // Default to LEG1 
//     if (strncmp(bufferstr, "_LEG2_", strlen("_LEG2_")) == 0) {
//         test_leg = LEG2;
// #ifdef CONFIG_SHIELD_OWNVERTER
//     } else if (strncmp(bufferstr, "_LEG3_", strlen("_LEG3_")) == 0) {
//         power_leg = LEG3;    
// #endif
//     } else if (strncmp(bufferstr, "_LEG1_", strlen("_LEG1_")) == 0) {
//         test_leg = LEG1;
//     } else {
//         printk("Unknown leg identifier\n");
//         return;
//     }

//     // COMMAND EXTRACTION
//     // Find the position of the second underscore after the leg identifier
//     const char *underscore2 = strchr(bufferstr + 5, '_');
//     if (underscore2 == NULL) {
//         printk("Invalid command format\n");
//         return;
//     }
//     // Extract the command part after the leg identifier
//     char command[3];
//     strncpy(command, underscore2, 2);
//     command[2] = '\0';

//     // FIND THE HANDLER OF THE SPECIFIC SETTING COMMAND
//     bool verif = false;
//     for(uint8_t i = 0; i < num_testSensi_settings; i++) //iterates the default commands
//     {
//         if (strncmp(command, testSensi_settings[i].cmd, strlen(testSensi_settings[i].cmd)) == 0)
//         {
//             if (testSensi_settings[i].func != NULL)
//             {
//                 testSensi_settings[i].func(test_leg, i); //pointer to the handler function associated with the command
//                 verif = true;
//             }
            
//         }
//     }
//     if (!verif) {
//         printk("unknown power command %s\n", bufferstr);
//         return;
//     }
//     PidParams pid_params(Ts, kp, Ti, Td, N, lower_bound, upper_bound);
//     if (test_leg == LEG1){
//         pid1.init(pid_params);
//     } else if (test_leg == LEG2) {
//         pid2.init(pid_params);
// #ifdef CONFIG_SHIELD_OWNVERTER
//     } else if (test_leg == LEG3) {
//         pid3.init(pid_params);    
// #endif
//     } 
    
    
    
// }  






// Function to parse the power leg settings commands
void powerLegSettingsHandler() {

    // Determine the power leg based on the received message
    leg_t power_leg = LEG1; // Default to LEG1
    if (strncmp(bufferstr, "_LEG2_", strlen("_LEG2_")) == 0) {
        power_leg = LEG2;
#ifdef CONFIG_SHIELD_OWNVERTER
    } else if (strncmp(bufferstr, "_LEG3_", strlen("_LEG3_")) == 0) {
        power_leg = LEG3;    
#endif
    } else if (strncmp(bufferstr, "_LEG1_", strlen("_LEG1_")) != 0) {
        printk("Unknown leg identifier\n");
        return;
    }

    // COMMAND EXTRACTION
    // Find the position of the second underscore after the leg identifier
    const char *underscore2 = strchr(bufferstr + 5, '_');
    if (underscore2 == NULL) {
        printk("Invalid command format\n");
        return;
    }
    // Extract the command part after the leg identifier
    char command[3];
    strncpy(command, underscore2, 2);
    command[2] = '\0';
    printk("\n");
    printk("command found: %s", command);
    printk("\n");

    // FIND THE HANDLER OF THE SPECIFIC SETTING COMMAND
    for(uint8_t i = 0; i < num_power_settings; i++) //iterates the default commands
    {
        if (strncmp(command, power_settings[i].cmd, strlen(power_settings[i].cmd)) == 0)
        {
            if (power_settings[i].func != NULL)
            {
                power_settings[i].func(power_leg, i); //pointer to the handler function associated with the command
                printk("\n");
                printk("number of settings sought: %d" ,i);
                printk("\n");
            }
            return;
        }
    }
    printk("unknown power command %s\n", bufferstr);
}


void slave_reception_function(void)
{
    tx_consigne = rx_consigne;
    tx_consigne.test_bool_CAN  = can_test_ctrl_enable;
    tx_consigne.test_CAN = can_test_reference_value;
    tx_consigne.test_RS485 = rx_consigne.test_RS485 + 1;
    tx_consigne.test_Sync = ctrl_slave_counter;
    tx_consigne.analog_value_measure = analog_value;

    communication.rs485.startTransmission();
}

void master_reception_function(void)
{
    analog_value = rx_consigne.analog_value_measure;
    rs485_receive = rx_consigne.test_RS485;
    CAN_Bus_receive = rx_consigne.test_CAN;
    CAN_Bus_bool_receive = rx_consigne.test_bool_CAN;

    if(test_start && (rs485_receive == rs485_send + 1)) RS485_success = true;
    if(test_start && RS485_success && (analog_value - analog_value_ref > 50 || analog_value - analog_value_ref > -50)) Analog_success = true;
    if(test_start && RS485_success && (CAN_Bus_receive - CAN_Bus_receive_ref > 50 || CAN_Bus_receive - CAN_Bus_receive_ref > -50  )) Can_success = true;
    if(test_start && RS485_success && (sync_master_counter < 5 && rx_consigne.test_Sync == 10))
    {
        sync_master_counter++;
        if(sync_master_counter == 5) Sync_success = true;

    }
}


