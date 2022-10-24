#!/usr/bin/env python3
"""
#------------------------------------------------------------------------------
#
# SCRIPT: forecast_task_05.py
#
# PURPOSE: Computes the bias correction for the NMME dataset. Based on
# FORECAST_TASK_03.sh.
#
# REVISION HISTORY:
# 24 Oct 2021: Ryan Zamora, first version
#
#------------------------------------------------------------------------------
"""

#
# Standard modules
#

import os
import sys
import argparse
import yaml

#
# Local methods
#

def _usage():
    """Print command line usage."""
    txt = "[INFO] Usage: {(sys.argv[0])}  -s fcst_syr -e fcst_eyr -m month_abbr \
                          -w cwd -n month_num -c config_file -j job_name \
                          -t ntasks -H hours -M NMME_MODEL"
    print(txt)
    print("[INFO] where")
    print("[INFO] fcst_syr: Start year of forecast")
    print("[INFO] fcst_eyr: End year of forecast")
    print("[INFO] clim_syr: Start year of the climatological period")
    print("[INFO] clim_eyr: End year of the climatological period")
    print("[INFO] month_abbr: Abbreviation of the initialization month")
    print("[INFO] month_num: Integer number of the initialization month")
    print("[INFO] lat1: Minimum latitudinal extent")
    print("[INFO] lat2: Maximum latitudinal extent")
    print("[INFO] lon1: Minimum longitudinal extent")
    print("[INFO] lon2: Maximum longitudinal extent")
    print("[INFO] nmme_model: NMME model name")
    print("[INFO] lead_months: Number of lead months")
    print("[INFO] config_file: Config file that sets up environment")
    print("[INFO] cwd: current working directory")

def _gather_ensemble_info(nmme_model):
    """Gathers ensemble information based on NMME model."""

    # Number of ensembles in the forecast (ENS_NUMF)
    # Number of ensembles in the climatology (ENS_NUMC)
    # Ensemble start index (ENS_START)
    # Ensemble end index (ENS_END)
    if nmme_model == "CFSv2":
        ens_numf = 24
        ens_numc = 12
        ens_start = 1
        ens_end = 24
    elif nmme_model == "GEOSv2":
        ens_numf = 10
        ens_numc = 4
        ens_start = 25
        ens_end = 34
    elif nmme_model == "CCM4":
        ens_numf = 10
        ens_numc = 10
        ens_start = 35
        ens_end = 44
    elif nmme_model == "GNEMO5":
        ens_numf = 10
        ens_numc = 10
        ens_start = 45
        ens_end = 54
    elif nmme_model == "CCSM4":
        ens_numf = 10
        ens_numc = 10
        ens_start = 55
        ens_end = 64
    elif nmme_model == "GFDL":
        ens_numf = 30
        ens_numc = 15
        ens_start = 65
        ens_end = 94
    else:
        print(f"[ERR] Invalid argument for nmme_model! Received {(nmme_model)}")
        sys.exit(1)

    return ens_numf, ens_numc, ens_start, ens_end

def _driver():
    """Main driver."""

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--fcst_syr', required=True, help='forecast start year')
    parser.add_argument('-e', '--fcst_eyr', required=True, help='forecast end year')
    parser.add_argument('-c', '--config_file', required=True, help='config file name')
    parser.add_argument('-m', '--month_abbr', required=True, help='month abbreviation')
    parser.add_argument('-n', '--month_num', required=True, help='month number')
    parser.add_argument('-j', '--job_name', required=True, help='job_name')
    parser.add_argument('-t', '--ntasks', required=True, help='ntasks')
    parser.add_argument('-H', '--hours', required=True, help='hours')
    parser.add_argument('-w', '--cwd', required=True, help='current working directory')
    parser.add_argument('-M', '--nmme_model', required=True, help='NMME Model')

    args = parser.parse_args()
    config_file = args.config_file
    fcst_syr = args.fcst_syr
    fcst_eyr = args.fcst_eyr
    month_abbr = args.month_abbr
    month_num = args.month_num
    job_name = args.job_name
    ntasks = args.ntasks
    hours = args.hours
    cwd = args.cwd
    nmme_model = args.nmme_model

    # load config file
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)

    # import local module
    sys.path.append(config['SETUP']['LISFDIR'] + '/lis/utils/usaf/s2s/')
    from s2s_modules.shared import utils

    # Path of the main project directory
    projdir = cwd

    # Path of the directory where all the BC codes are kept
    srcdir = config['SETUP']['LISFDIR'] + '/lis/utils/usaf/s2s/s2s_modules/bcsd_fcst/bcsd_library/'

    # Log file output directory
    logdir = cwd + '/log_files'

    # Path of the directory where supplementary files are kept
    supplementary_dir = cwd + '/bcsd_fcst/supplementary_files/'

    # domain
    lat1 = config['EXP']['domian_extent'][0].get('LAT_SW')
    lat2 = config['EXP']['domian_extent'][0].get('LAT_NE')
    lon1 = config['EXP']['domian_extent'][0].get('LON_SW')
    lon2 = config['EXP']['domian_extent'][0].get('LON_NE')
    lead_months = config['EXP']['lead_months']
    clim_syr = config['BCSD']['clim_start_year']
    clim_eyr = config['BCSD']['clim_end_year']

    # Path for where observational files are located:
    forcedir = f"{projdir}/bcsd_fcst/"
    obs_clim_indir = f"{forcedir}/USAF-LIS7.3rc8_25km/raw/Climatology"

    # Mask file
    mask_file = f"{supplementary_dir}/Mask_nafpa.nc"

    #  Calculate bias correction for different variables separately:
    obs_var = "Rainf_f_tavg"
    fcst_var = "PRECTOT"
    unit = "kg/m^2/s"
    var_type = "PRCP"

    # Path for where nmme forecast files are located:
    fcst_clim_indir = f"{forcedir}/NMME/raw/Climatology/{month_abbr}01"
    fcst_indir = f"{forcedir}/NMME/raw/Monthly/{month_abbr}01"

    # Path for where output BC forecast file are located:
    outdir = f"{forcedir}/NMME/bcsd/Monthly/{month_abbr}01"
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    print(f"[INFO] Processing forecast bias correction of NMME-{nmme_model} precip")

    ens_numf, ens_numc, ens_start, ens_end = _gather_ensemble_info(nmme_model)

    for year in range(int(fcst_syr), (int(fcst_eyr) + 1)):
        cmd = "python"
        cmd += f" {srcdir}/bias_correction_nmme_modulefast.py"
        cmd += f" {obs_var}"
        cmd += f" {fcst_var}"
        cmd += f" {var_type}"
        cmd += f" {unit}"
        cmd += f" {lat1}"
        cmd += f" {lat2}"
        cmd += f" {lon1}"
        cmd += f" {lon2}"
        cmd += f" {month_num}"
        cmd += f" {nmme_model}"
        cmd += f" {lead_months}"
        cmd += f" {ens_numc}"
        cmd += f" {ens_numf}"
        cmd += f" {year}"
        cmd += f" {year}"
        cmd += f" {clim_syr}"
        cmd += f" {clim_eyr}"     
        cmd += f" {fcst_clim_indir}"
        cmd += f" {obs_clim_indir}"
        cmd += f" {fcst_indir}"
        cmd += f" {mask_file}"
        cmd += f" {outdir}"
        cmd += f" {ens_start}"
        cmd += f" {ens_end}"
        cmd += f" {logdir}"
        jobfile = job_name + '_' + nmme_model + '_run.j'
        jobname = job_name + '_' + nmme_model + '_'
        utils.job_script(config_file, jobfile, jobname, ntasks, hours, cwd, in_command=cmd)

    print(f"[INFO] Completed writing NMME bias correction scripts for: {(month_abbr)}")

#
# Main Method
#
if __name__ == "__main__":
    _driver()
