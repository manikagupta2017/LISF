#!/usr/bin/env python3
"""
#------------------------------------------------------------------------------
#
# SCRIPT: forecast_task_08.py
#
# PURPOSE: Generate bias-corrected 6-hourly nmme forecasts using raw monthly
# forecasts, bias-corrected monthly forecasts and raw 6-hourly forecasts. Based
# on FORECAST_TASK_08.sh.
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
    txt = f"[INFO] Usage: {(sys.argv[0])} -s fcst_syr -e fcst_eyr -m month_abbr \
             -w cwd -n month_num -c config_file -j job_name -t ntasks -H hours -M NMME_MODEL"
    print(txt)
    print("[INFO] where")
    print("[INFO] fcst_syr: Start year of forecast")
    print("[INFO] fcst_eyr: End year of forecast")
    print("[INFO] month_abbr: Abbreviation of the initialization month")
    print("[INFO] month_num: Integer number of the initialization month")
    print("[INFO] lat1: Minimum latitudinal extent")
    print("[INFO] lat2: Maximum latitudinal extent")
    print("[INFO] lon1: Minimum longitudinal extent")
    print("[INFO] lon2: Maximum longitudinal extent")
    print("[INFO] nmme_model: NMME model name")
    print("[INFO] config_file: Config file that sets up environment")
    print("[INFO] job_name: SLURM job_name")
    print("[INFO] ntasks: SLURM ntasks")
    print("[INFO] hours: SLURM time hours")

def gather_ensemble_info(nmme_model):
    """Gathers ensemble information based on NMME model."""

    # Number of ensembles in the forecast (ens_num)
    # Ensemble start index (ens_start)
    # Ensemble end index (ens_end)
    if nmme_model == "CFSv2":
        ens_num = 24
        ens_start = 1
        ens_end = 24
    elif nmme_model == "GEOSv2":
        ens_num = 10
        ens_start = 25
        ens_end = 34
    elif nmme_model == "CCM4":
        ens_num = 10
        ens_start = 35
        ens_end = 44
    elif nmme_model == "GNEMO5":
        ens_num = 10
        ens_start = 45
        ens_end = 54
    elif nmme_model == "CCSM4":
        ens_num = 10
        ens_start = 55
        ens_end = 64
    elif nmme_model == "GFDL":
        ens_num = 30
        ens_start = 65
        ens_end = 94
    else:
        print(f"[ERR] Invalid argument for nmme_model! Received {nmme_model}")
        sys.exit(1)

    return ens_num, ens_start, ens_end

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
    ens_num = config['BCSD']['nof_raw_ens']
    domain = config['EXP']['domain']

    # Path for where forecast files are located:
    forcedir = f"{projdir}/bcsd_fcst/NMME"

    # Mask file
    mask_file_precip = f"{supplementary_dir}/Mask_nafpa.nc"
    mask_file_nonprecip = f"{supplementary_dir}/Mask_nafpa.nc"

    #  Calculate bias correction for different variables separately:
    obs_var = "PRECTOT"
    fcst_var = "PRECTOT"
    unit = "kg/m^2/s"
    var_type = 'PRCP'

    # Path for where forecast and bias corrected files are located:
    subdaily_raw_fcst_dir = f"{forcedir}/linked_cfsv2_precip_files/{month_abbr}01"
    monthly_raw_fcst_dir = f"{forcedir}/raw/Monthly/{month_abbr}01"
    monthly_bc_fcst_dir = f"{forcedir}/bcsd/Monthly/{month_abbr}01"

    outdir = f"{forcedir}/bcsd/6-Hourly/{month_abbr}01/{nmme_model}"

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    ens_num, ens_start, ens_end = gather_ensemble_info(nmme_model)
    print("[INFO] Processing temporal disaggregation of CFSv2 variables")
    for year in range(int(fcst_syr), (int(fcst_eyr) + 1)):
        cmd = "python"
        cmd += f" {srcdir}/temporal_disaggregation_nmme_6hourly_module.py"
        cmd += f" {obs_var}"
        cmd += f" {fcst_var}"
        cmd += f" {year}"
        cmd += f" {month_num}"
        cmd += f" {var_type}"
        cmd += f" {unit}"
        cmd += f" {lat1}"
        cmd += f" {lat2}"
        cmd += f" {lon1}"
        cmd += f" {lon2}"
        cmd += f" {nmme_model}"
        cmd += f" {ens_num}"
        cmd += f" {lead_months}"
        cmd += f" {year}"
        cmd += f" {year}"
        cmd += f" {mask_file_precip}"
        cmd += f" {mask_file_nonprecip}"
        cmd += f" {monthly_bc_fcst_dir}"
        cmd += f" {monthly_raw_fcst_dir}"
        cmd += f" {subdaily_raw_fcst_dir}"
        cmd += f" {outdir}"
        cmd += f" {ens_start}"
        cmd += f" {ens_end}"
        cmd += f" {domain}"
        cmd += f" {logdir}"
        jobfile = job_name + '_' + nmme_model + '_run.j'
        jobname = job_name + '_' + nmme_model + '_'
        utils.job_script(config_file, jobfile, jobname, ntasks, hours, cwd, in_command=cmd)

    print(f"[INFO] Wrote NMME temporal disaggregation script for: {month_abbr}")

#
# Main Method
#
if __name__ == "__main__":
    _driver()
