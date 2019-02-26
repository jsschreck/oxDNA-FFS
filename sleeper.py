import subprocess, os, sys, time, shutil, errno, argparse
from tempfile import mkstemp
from shutil import move
from os import remove, close
import os.path


pwd = os.getcwd()

'''
Calculate the rate of duplex formation for strand displacement system with toehold 7. 
Supply launch script for cluster with the line 'EXE='. 
User must specify which interfaces to cross. See shoot.py and generate_flux.py for inputs.
'''

def prepare_launch_script(k, x):
	name = 'launch.sh' 
	os.system('chmod +x %s' % name)
	replace(name, 'EXE=here','EXE=%s' % x) 
	return name  

def prepare_relaunch_script(k, x):
	name = 'launch.sh' 
	os.system('chmod +x %s' % name)
	replace(name, '%s' % k,'%s' % x) 
	return name   

def replace(file_path, pattern, subst):
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(file_path)
    for line in old_file:
        new_file.write(line.replace(pattern, subst))
    new_file.close()
    close(fh)
    old_file.close()
    remove(file_path)
    move(abs_path, file_path)

def poll(pid):
	proc = subprocess.Popen("qstat | grep %s | awk '{print $1}' " % pid, shell=True, stdout=subprocess.PIPE).communicate()[0]
	if proc:
		return 1
	else:
		return 0

def enforce(pid_list, desired_success_count, file_save_loc):
	stay_put = True
	while stay_put == True:
		success_count = int(subprocess.Popen("ls %s | wc -l" % file_save_loc, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") )
		
		if success_count >= desired_success_count:
			move_forward = True

			#First kill any queued jobs
			for job in pid_list:
				try:
					qcheck = subprocess.Popen("qstat | grep %s | awk '{print $5}' " % job, shell=True, stdout=subprocess.PIPE).communicate()[0].split("\n")[:-1][0]
					if qcheck == "qw":
						os.system("qdel %s" % job)
					else:
						pass
				except:
					pass
			
			# Next, periodically check the running jobs and wait until they are all finished
			while move_forward == True:
				pids = sum( [ poll(k) for k in pidtrack] )
				if pids == 0:
					# Did the jobs finish, or just hit the wall time?
					for job in pid_list:
						walltime_count = 0 
						run_dir = subprocess.Popen("find . -name '*.e%s' " % job, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") 
						check_walltime = subprocess.Popen("cat %s 2>/dev/null | grep 'walltime'" % run_dir, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") 
						if len(check_walltime) > 0:
							walltime_count += 1
							relaunch_dir = "data/" + run_dir.split("/")[2]
							os.chdir(os.path.join(os.path.abspath(sys.path[0]), relaunch_dir ) )
							script_cmd = [line for line in open("launch.sh", 'r').readlines() if line.startswith("EXE")][0].split("\n")[:-1][0].split(" ")
							script_cmd[-2] = '1'
							get_script = prepare_relaunch_script(script_cmd,new_script_cmd)
							relaunch_name = run_dir.split("/")[3].split(".e")[0]
							launchargs = [ 'qsub','-N', relaunch_name, '%s' % get_script ]
							run = subprocess.Popen(launchargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
							#pid = run.split('.')[0]
							pid = run.split(' ')[2] #Coulson
							pid_list[ind] = pid
							os.chdir(pwd)
					if walltime_count == 0: # None hit the wall time
						move_forward = False 
					else:
						time.sleep(300) # Some did and had to be resubmitted ... taking a nap
				else:
					time.sleep(300) # There are still running jobs ... taking a nap.
			stay_put = False

		elif success_count < desired_success_count:
			for ind, job in enumerate(pid_list):
				run_dir = subprocess.Popen("find . -name '*.e%s' " % job, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") 
				check_walltime = subprocess.Popen("cat %s 2>/dev/null | grep 'walltime'" % run_dir, shell=True, stdout=subprocess.PIPE).communicate()[0].strip("\n") 
				if os.path.isfile(run_dir) and len(check_walltime) > 0:
					relaunch_dir = "data/" + run_dir.split("/")[2]
					os.chdir(os.path.join(os.path.abspath(sys.path[0]), relaunch_dir ) )
					script_cmd = [line for line in open("launch.sh", 'r').readlines() if line.startswith("EXE")][0].split("\n")[:-1][0].split(" ")
					script_cmd[-2] = '1'
					get_script = prepare_relaunch_script(script_cmd,new_script_cmd)
					relaunch_name = run_dir.split("/")[3].split(".e")[0]
					launchargs = [ 'qsub','-N', relaunch_name, '%s' % get_script ]
					run = subprocess.Popen(launchargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
					#pid = run.split('.')[0]
					pid = run.split(' ')[2] #Coulson
					pid_list[ind] = pid
					os.chdir(pwd)
				else:
					continue 

		time.sleep(300)


if __name__ == '__main__':
	
	parser = argparse.ArgumentParser()
	parser.add_argument('--nodes', type = int, default = 1,
						help = 'Number of independent qsub/slurm jobs. Default = 1')
	parser.add_argument('--run_arg', type = str, default = 'D7',
						help = 'Unique string name. Default: D7')
	parser.add_argument('--idx', type = str, default = '1',
						help = 'String to distinguish replicas. Default: 1')
	parser.add_argument('--reset', type = int, default = 0,
						help = 'Reset / restart where sims left off / died. Default: False')

	qsub_jobs 		= int(args.nodes)
	run_arg 		= str(args.run_arg)
	idx 			= str(args.idx)
	reset 			= int(args.reset)

	pidtrack = []
	log_file_name = 'timing.log'  

	####################################
	#
	# Interfaces and order parameters (editable)
	#
	####################################

	flux_and_shooting_dirs = ['FLUX', '1', '2', '3', '4', '5', '6', '7']
	loc1 = [os.path.join(pwd,'%s'.format(s)) s for s in flux_and_shooting_dirs]
	
	# Create data directories if they do not yet exist.
	for _dir in loc1:
		if not os.path.isdir(_dir):
			os.makedirs(_dir)
	data_dir_loc = os.path.join(pwd, 'data')
	if not os.path.isdir(data_dir_loc):
		os.makedirs(data_dir_loc)

	ops1 = ['mindist', 'mindist', 'mindist', 'mindist', 'mindist', 'mindist', 
			'bond', 'bond', 'bond']
	ops2 = ['mindist', 'mindist', 'mindist', 'mindist', 'mindist', 'bond', 
			'bond', 'bond', 'bond']
	name = ['invader_bonds_dist', 'invader_bonds_dist', 'invader_bonds_dist', 
			'invader_bonds_dist', 'invader_bonds_dist', 'invader_bonds', 'invader_bonds', 
			'invader_bonds', 'invader_bonds']
	
	val1 = [3, 1, 0.7, 1, 7, 27]
	val2 = ["%s" % str(k) for k in range(1,len(val)+1,1)]
	loc2 = [os.path.join(pwd,'%s'.format(k)) for k in val2]
	success_counts = [2000,1000,1000,1000,1000,1000,100]

	##################
	#
	# Flux generation
	#
	##################

	lambda_minus1 = 6.0
	lambda_0 = val1[0] 
	astateloc = os.path.join(pwd, 'EQUILIBRATED')
	fluxloc = os.path.join(pwd, 'FLUX')

	tstart = time.time()
	for k, x in enumerate(range(qsub_jobs)):

	    if reset == 0: 
	    	os.system('rm -rf data/P%s' % k)
	    	os.system('cp -r ffs_files data/P%s' % k)
	    
	    os.chdir(os.path.join(os.path.abspath(sys.path[0]), 'data/P%s' % k))
	    launcharg_for_cluster = ['python',pwd+'/data/P%s/generate_flux.py' % k, str(lambda_minus1), str(lambda_0), astateloc, fluxloc, str(success_counts[0]), str(reset), str(k)]
	    launcharg_for_cluster = " ".join(launcharg_for_cluster)
	    lfc = "'%s'" % launcharg_for_cluster
	    get_script = prepare_launch_script(x,lfc)
	    launchargs = [ 'qsub','-N','F%sQ%s.%s' % (k,run_arg,idx), '%s' % get_script ]
	    run = subprocess.Popen(launchargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
	    #pid = run.split('.')[0]
	    pid = run.split(' ')[2] # Coulson 
	    pidtrack.append(pid)
	    os.chdir(pwd)

	enforce(pidtrack, success_counts[0], 'FLUX')
	tfinish = time.time()
	log_file = open(log_file_name, "a+")
	log_file.write('It took %s seconds to generate the flux from %s simulations\n' % (tfinish-tstart, qsub_jobs))
	log_file.close()

	##################
	#
	# Shooting
	#
	##################

	start = 0
	for i in range(start,start+len(ops1)):
		pidtrack=[]
		tstart = time.time()
		for k, x in enumerate(range(start,start+qsub_jobs)):
		    if reset == 0:
		    	os.system('rm -rf data/R%s%s' % (i, k) )
		    	os.system('cp -r ffs_files data/R%s%s' % (i,k) )
		    os.chdir(os.path.join(os.path.abspath(sys.path[0]), 'data/R%s%s' % (i, k) ) )
		    launcharg_for_cluster = ['python shoot.py',str(lambda_minus1),ops1[i],loc1[i],ops2[i],loc2[i],name[i],str(val1[i]),str(success_counts[i+1]), str(reset), str(k)]
		    launcharg_for_cluster = " ".join(launcharg_for_cluster)
		    lfc = "'%s'" % launcharg_for_cluster
		    get_script = prepare_launch_script(x,lfc)
		    launchargs = ['qsub','-N','I%sR%sQ%s.%s' % (i+1,k,run_arg,idx), '%s' % get_script ]
		    run = subprocess.Popen(launchargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
		    pid = run.split(' ')[2] # Coulson 
		    #pid = run.split('.')[0]
		    pidtrack.append(pid)
		    os.chdir(pwd)
		enforce(pidtrack, success_counts[i+1], val2[i])
		tfinish = time.time()
		log_file = open(log_file_name, "a")
		log_file.write('It took %s seconds to cross the %sth interface from %s simulations\n' % (tfinish-tstart, i, qsub_jobs))
		log_file.close()
