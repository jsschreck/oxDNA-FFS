#!/bin/sh

# Set the executable file; if the first argument is given, that is 
# the executable; otherwise, use the default
if [ ! -z ${1} ]
  then
    EXE=${1}
  else
    EXE=here
  fi

# Set various variables which will be useful later in the script 
WDIR=${SGE_O_WORKDIR}
[ -z ${WDIR} ] && WDIR=${PWD}
[ -z ${JOB_ID} ] && JOB_ID=${RANDOM}
STDOUT=schermo-${JOB_ID}
STDERR=stderr-${JOB_ID}
TDIR=/tmp/$USER/$JOB_ID
PYTHONPATH=${PYTHONPATH}:/users/jpkd/jschreck/CUDADNA/UTILS

echo "STARTING..."
echo "EXECUTABLE: ${EXE}"
echo -n "USER:" $USER "JOB:" $JOB_ID "on: "; hostname
echo "TDIR: ${TDIR}"
echo "WDIR: ${WDIR}"

echo ${JOB_ID} > running

# Copy the directory in a "safe" way, that is it tries ten times
# with increasing time lags in between trials. If it fails ten times
# the script dies 
mkdir -m 775 -p ${TDIR}
cd ${TDIR}
i=0
while ! cp -r ${WDIR}/* ./
do
    if [ ${i} -gt 10 ] 
      then
        echo "Failed too many times to copy files; Aborting"
        exit 1
      fi
    let i=i+1
    SEC=$[${i}*10]
    echo "Error Copying Files, retrying for the ${i} time in ${SEC} seconds..."
    sleep ${SEC}
done
echo "Copied all relevant files, running..." 

# Start the job. If it returns anything non-zero, the script complains and
# exits.
echo "Job starting at `date`"
if ! ${EXE} >${STDOUT} 2>${STDERR}
    then
    echo "ERROR RUNNING PROGRAM! DYING! `date`";
    exit 2
fi

echo "Job completed at `date`"

# Copies back the directory, always in a "safe" way
i=0
while ! cp -r ./* ${WDIR}
do
    if [ ${i} -gt 10 ] 
      then
        echo "Failed too many times to copy back; Aborting"
        exit 3
      fi
    let i=i+1
    SEC=$[${i}*10]
    echo "Error copying back, retrying for the ${i} time in ${SEC} seconds..."
    sleep ${SEC}
done

# Remove the temporary directory from scratch. If the script gets here,
# it means that the files have been successifully copied back to the 
# directory where the job was started
echo "Removing leftover directory"
cd ${WDIR}
rm -fr ${TDIR}

echo ${JOB_ID} > finished
rm running

echo "All Done"

