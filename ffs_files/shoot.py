
#!/usr/bin/env python

'''
Run a load of shots from starting configs in the directory one above to lambda_1 or lambda_minus1

NB file names are slightly wrong (LT vs EQ vs GT)!

The script will overwrite the condition file with the conditions provided

It\'s a bit trickier to get it to work with multiple op types (which this one uses). For that reason this script is not easily portable

This version creates a certain number of successes, and does not save failures

Optional command line arg sets initial seed - it is recommended that this is used, and that the seed is set to the job ID

setting up the files:
in input file
conf_file = initial.dat
restart_step_counter = 1
refresh_velocity = 0
no_stdout_energy = 0

1) launch job
2) when job dies, check that it stopped at one interface or another, and save last_conf 
3) repeat


EXAMPLE USAGE - ./shoot.py 'mindist' 'FLUX' 'mindist' 'dist' 1.2 1 100 
'''

import sys
import subprocess
import shutil
import random
import glob
import time
import os
import os.path
import string

from tempfile import mkstemp
from shutil import move
from os import remove, close

#########################
# EDIT THESE PARAMETERS #
#########################

launch_command = './oxDNA'
input_file = 'input_shoot'
sim_outfilen = "last_sim.txt"
condition_fname = 'conditions.txt'
save_up1 = False 
print_failures = False 

###### A - state #########
lambda_minus1 = sys.argv[1]  
lambda_minus1_conf_str = 'invader_bonds_dist'
back_condition_inds = [2] #Which condition(s) in conditions.txt represent the A-state?
########################## 

lambda_0_conf_str = sys.argv[2]
lambda_0_dir_loc  = sys.argv[3]

lambda_1_conf_str   = sys.argv[4]
lambda_1_dir_loc    = sys.argv[5]

lambda_1_op_type    = sys.argv[6]
lambda_1_stopping   = float(sys.argv[7])
lambda_1_dir_int    = lambda_1_dir_loc.split("/")[len(lambda_1_dir_loc.split("/"))-1]

desired_success_count = int(sys.argv[8])
restart = int(sys.argv[9])
node_string = str(sys.argv[10])

success_count = int(subprocess.Popen("ls %s | wc -l" % lambda_1_dir_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") )
lambda_0_paths = lambda_0_dir_loc+"/RUN_lastconf_at_"+lambda_0_conf_str+'*.dat'
possible_inits = glob.glob(lambda_0_paths)

log_file_name = 'SHOOT_interface_%s.log' % str(lambda_1_dir_int)
pathway_file_name = 'PATHWAYS%s.log' % lambda_1_dir_int
melting_file_name = 'MELTING%s.log' % lambda_1_dir_int


def get_time(fileName):
    f = open(fileName, 'r')
    f = f.readline().strip().split(' ')[2] # time is the 3rd element
    return float(f)
#######################################
# Write the ffs stopping condition file 
#######################################
def write_condition(filename, condition_strings):
    condition_file = open(filename, "w")
    condition_file.write("condition1 = {\n")
    condition_file.write("%s\n" %  condition_strings[0])
    condition_file.write("}\n")
    condition_file.write("condition2 = {\n")
    condition_file.write("%s\n" %  condition_strings[1])
    condition_file.write("}")
    condition_file.close()

conds = []
if len(lambda_1_op_type.split("_")) == 3:
    conds.append( '%s %s %s' % (lambda_1_op_type, '<', lambda_1_stopping))
else:
    conds.append( '%s %s %s' % (lambda_1_op_type, '>=', lambda_1_stopping))
conds.append( '%s %s %s' % (lambda_minus1_conf_str, '>=',lambda_minus1))
write_condition(condition_fname, conds)


if restart == 0:
    pathway_file = open(pathway_file_name, "w")
    pathway_file.write('Interface ID, lambda_i, lambda_i+1\n')
    pathway_file.close()

########################################
actual_count, trial_count, discarded_count = 0, 0, 0 
while success_count < desired_success_count:
    
    if restart == 1: 
        shutil.copy("last_conf.dat", "initial.dat")
        log_file = open(log_file_name, "a", 1)
        last_line_log_file = log_file.readlines()[len(log_file.readlines())-1].strip('\n')
        log_file.close()
        lambda_0_choice = last_line_log_file.split(" ")[2]
        start_time = get_time(lambda_0_choice)
    else:
        lambda_0_choice = random.choice(possible_inits)
        shutil.copy(lambda_0_choice, "initial.dat")
        start_time = get_time("initial.dat")
        
        log_file = open(log_file_name, "a", 1)
        log_file.write("STARTING from %s at t = %s ... " % (lambda_0_choice, start_time))
        log_file.close()
        
    sim_outfile = open(sim_outfilen, "w")
    launch = subprocess.Popen([launch_command, input_file],stdout=sim_outfile, stderr=sim_outfile)
    launch.wait()
    sim_outfile.close()
    sim_outfile = open(sim_outfilen, "r")
    condition_ind = -1
    for line in sim_outfile.readlines():
        words = line.rstrip().split()
        if words[0:2] == ["INFO:", "Reached"] and len(words) == 3:
            condition_ind = int(words[2][9:]) # strip away the leading 9 characters: "condition"
        elif words[0:5] == ["INFO:", "seeding", "the", "RNG", "with"]:
            this_seed = int(words[5])
    sim_outfile.close()
    if condition_ind in back_condition_inds:
        success_count = int(subprocess.Popen("ls %s | wc -l" % lambda_1_dir_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") )
        unique_identifier = random.choice(string.letters)
        stop_time = get_time("last_conf.dat")
        save_name = "%s/RUN_lastconf_at_%s_GE_%s_%s_N%d.dat" % (lambda_1_dir_loc, lambda_1_conf_str, lambda_1_stopping, node_string, success_count)
        
        log_file = open(log_file_name, "a", 1)
        log_file.write("FAIL: finished run with seed %d and stopped at condition%d when t = %s" % (this_seed, condition_ind, stop_time) )
        #melting_file = open(melting_file_name, "a")
        #melting_file.write("STARTING from %s with seed %s at t = %s ... " % (lambda_0_choice, this_seed, start_time))
        #melting_file.write("and MELTED at t = %s\n" % stop_time ) 
        log_file.close()
        #melting_file.close()

        if print_failures:
            log_file = open(log_file_name, "a", 1)
            log_file.write(" and saved to %s\n" % save_name)
            log_file.close()
            shutil.copy("last_conf.dat", save_name)
        else:
            log_file = open(log_file_name, "a", 1)
            log_file.write("\n")
            log_file.close()

    elif condition_ind == -1:
        log_file = open(log_file_name, "a", 1)
        log_file.write("ERROR: run with seed %d did not reach stopping conditions; dying now\n" % (this_seed))
        log_file.close()
        sys.exit(1)
    else:
        stop_time = get_time("last_conf.dat")        
        success_count = int(subprocess.Popen("ls %s | wc -l" % lambda_1_dir_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") )
        #unique_identifier = random.choice(string.letters)
        if len(lambda_1_op_type.split("_")) == 3:
            save_name = "%s/RUN_lastconf_at_%s_LT_%s_%s_N%d.dat" % (lambda_1_dir_loc, lambda_1_conf_str, lambda_1_stopping, node_string, success_count)
        else:
            save_name = "%s/RUN_lastconf_at_%s_GE_%s_%s_N%d.dat" % (lambda_1_dir_loc, lambda_1_conf_str, lambda_1_stopping, node_string, success_count)
        file_copy = 0
        while file_copy < 10:
            try:
                shutil.copy("last_conf.dat","temp.dat")
                shutil.copy("temp.dat", save_name)
                os.system("rm temp.dat")
                file_copy = 10
            except:
                print save_name 
                time.sleep(5)
                file_copy += 1

        if file_copy < 10:
            log_file = open(log_file_name, "a", 1)
            log_file.write("Had an unspecified error when trying to copy the file, continuing...\n")
            log_file.close()
        else:
            log_file = open(log_file_name, "a", 1)
            log_file.write("SUCCESS: finished run with seed %d and stopped at condition%d when t = %s, and saved to %s\n" % (this_seed, condition_ind, stop_time, save_name))
            log_file.close()
            pathway_file = open(pathway_file_name, "a") 
            pathway_file.write('%s: %s %s\n' % (int(lambda_1_dir_int), lambda_0_choice, save_name))
            pathway_file.close()
            success_count += 1
            actual_count += 1 

    trial_count += 1
    restart = 0 # Reset so on the next pass we start as usual

final_trial_count = trial_count - discarded_count
log_file = open(log_file_name, "a", 1)
try:
    log_file.write("FINISHED: discarded = %d; success/trial = %d/%d; prob = %f\n" % (discarded_count, actual_count, final_trial_count, float(actual_count)/final_trial_count))
except:
    log_file.write("This job did not produce any successes.")
log_file.close()
