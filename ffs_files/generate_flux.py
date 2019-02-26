#!/usr/bin/env python

'''
setting up the files:
start from last_conf.dat, must have t = 0
in input file
restart_step_counter = 0
refresh_velocity = 0

1) write lambda_0 forwards condition to conditions.txt
2) launch job
3) when job dies, assume that it stopped appropriately, save last_conf and write lambda_{-1} backwards condition to conditions.txt
4) launch job
5) repeat
'''

import sys, os, random, glob 
import subprocess
import shutil
import os.path
import time
import string

from tempfile import mkstemp
from shutil import move
from os import remove, close


pwd = os.getcwd()
launch_command = './oxDNA'
input_file = 'input_flux'
log_file_name = 'GEN_FLUX.log'
condition_fname = 'conditions.txt'
stdout_file = 'stdout.log'

lambda_minus1 = float(sys.argv[1])
lambda_0 = float(sys.argv[2])
astateloc = str(sys.argv[3])
save_loc = str(sys.argv[4])
desired_success_count = int(sys.argv[5])
restart = int(sys.argv[6])
node_string = str(sys.argv[7])



def get_time(fileName):
    f = open(fileName, 'r')
    f = f.readline().strip().split(' ')[2] # time is the 3rd element
    return float(f)

def write_condition(filename, condition_strings):
    condition_file = open(filename, "w")
    condition_file.write("condition1 = {\n")
    condition_file.write("invader_bonds_dist %s\n" %  condition_string)
    condition_file.write("}\n")
    condition_file.write("condition2 = {\n")
    condition_file.write("invader_bonds >= 1 \n")
    condition_file.write("}\n")
    condition_file.close()

stop_final = 0
launch_count = 0

log_file = open(log_file_name, "a", 1) # line buffering
outfile = open('stdout.log', 'w')
equilA_path = astateloc+"/RUN*"
possible_inits = glob.glob(equilA_path)
equilibrated_astate = random.choice(possible_inits)
shutil.copy(equilibrated_astate, "last_conf.dat")
equil_starting_time = get_time(equilibrated_astate)
log_file.write("The equilibrated A-state selected was %s, time = %s \n" % (equilibrated_astate,equil_starting_time) )

#shutil.copy("equilibrated_astate.conf", "last_conf.dat")
condition_string = "< %f" % lambda_0
write_condition(condition_fname, condition_string)
launch = subprocess.Popen([launch_command, input_file],stdout=outfile, stderr=outfile)
launch.wait()

forward_time = get_time("last_conf.dat")
unique_identifier = random.choice(string.letters)
success_count = int(subprocess.Popen("ls %s | wc -l" % save_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") )
conf_save_name = "%s/RUN_lastconf_at_mindist_LT_%f_%s_N%d.dat" % (save_loc, lambda_0, node_string, success_count)
shutil.copy("last_conf.dat", conf_save_name)
log_file.write("crossed lambda_{0} going forwards at t = %s, dist %s, saved conf = %s\n" % (forward_time, condition_string, conf_save_name) )
success_count += 1
launch_count += 1

outfile.close()
os.system('rm -f stdout.log')

while success_count < desired_success_count:
    outfile = open('stdout.log', 'w')
    condition_string = ">= %f" % lambda_minus1
    write_condition(condition_fname, condition_string)
    launch = subprocess.Popen([launch_command, input_file],stdout=outfile, stderr=outfile)
    launch.wait()
    outfile.close()
    outfile = open('stdout.log', "r")
    ################################### Go backwards
    for line in outfile.readlines():
        words = line.rstrip().split()
        if words[0:2] == ["INFO:", "Reached"] and len(words) == 3:
            #print words
            condition_ind = int(words[2][9:]) # strip away the leading 9 characters: "condition"
            
    if condition_ind == 2:
            log_file.write("Failed: We had a duplex form, so starting over")
            #Move last successful flux traj. back here and move loop forward. 
            last_saved_conf = subprocess.Popen("ls %s -lrth | tail -n 1" % save_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n").split(":")[1].split(" ")[1]
            shutil.copy(last_saved_conf, "last_conf.dat")

            #shutil.copy("%s/RUN_lastconf_at_mindist_LT_%f_N%d.dat" % (save_loc, lambda_0, success_count-1), "last_conf.dat")
            launch_count += 1
            outfile.close()
            os.system('rm -f stdout.log')
            continue 
    else:
        backward_time = get_time("last_conf.dat")
        log_file.write("crossed lambda_{-1} going backwards at t = %s, dist %s\n" % (backward_time,condition_string) )
        #shutil.copy("last_conf.dat", "%s/RUN_debug_conf_at_mindist_GEQ_%f_N%d.dat" % (save_loc, lambda_minus1, success_count))
        launch_count += 1
    ################################### Go forwards
    outfile.seek(0)
    outfile.close()
    outfile = open('stdout.log', "w")
    condition_string = "< %f" % lambda_0
    write_condition(condition_fname, condition_string)
    launch = subprocess.Popen([launch_command, input_file],stdout=outfile, stderr=outfile)
    launch.wait()
    ###################################
    outfile.close()
    outfile = open('stdout.log', "r")
    for line in outfile.readlines():
        words = line.rstrip().split()
        if words[0:2] == ["INFO:", "Reached"] and len(words) == 3:
            condition_ind = int(words[2][9:]) # strip away the leading 9 characters: "condition"
    if condition_ind == 2:
            log_file.write("Failed: We had a duplex form, so starting over")
            #Move last successful flux traj. back here and move loop forward. 
            last_saved_conf = subprocess.Popen("ls %s -lrth | tail -n 1" % save_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n").split(":")[1].split(" ")[1]
            shutil.copy(last_saved_conf, "last_conf.dat")
            launch_count += 1
            outfile.close()
            os.system('rm -f stdout.log')
            continue 
    else:
        forward_time = get_time("last_conf.dat")
        unique_identifier = random.choice(string.letters)
        success_count = int(subprocess.Popen("ls %s | wc -l" % save_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") )
        conf_save_name = "%s/RUN_lastconf_at_mindist_LT_%f_%s_N%d.dat" % (save_loc, lambda_0, node_string, success_count)
        log_file.write("crossed lambda_{0} going forwards at t = %s, dist %s, saved conf = %s\n" % (forward_time, condition_string, conf_save_name) )
        shutil.copy("last_conf.dat", conf_save_name)
        success_count += 1
        launch_count += 1

        outfile.close()
        os.system('rm -f stdout.log')
