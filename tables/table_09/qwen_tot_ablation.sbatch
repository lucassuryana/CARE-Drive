#!/bin/bash
#SBATCH --job-name=qwen_tot_ablation
#SBATCH --partition=general
#SBATCH --qos=normal
#SBATCH --time=10-00:00:00
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --output=/home/nfs/lsuryana/qwen_tot_ablation.log

# Usage:
#   git clone https://github.com/lucassuryana/CARE-Drive.git ~/CARE-Drive
#   cd ~/CARE-Drive && git checkout address-reviewer-comment && git pull
#   sbatch "tables/table_09/qwen_tot_ablation.sbatch"
#
# Estimated runtime: ~6.4 hours serial (400 runs -- following time fixed at
# 24s, single (full-reasoning) text version, 2-level factorial over
# TTC/traffic behind/passenger hurry x 5 conditions x 10 runs/combination;
# every call is now full-reasoning, measured ~50-67s/run per a 120-run
# sample). Run twice (or more) at 10 runs/combination and both batches land
# in the same Excel file -- pool them by grouping on the parameter columns
# (Run_Number restarts at 1 each time, so don't key off it). --time is set
# with buffer above the single-batch estimate.
#
# QoS: normal has no MaxWall cap (per `sacctmgr show qos`) and is presumably
# the cluster's default/standard-priority tier, so it should schedule at
# least as well as infinite while still allowing the long runtime. If it
# stalls in the queue, fall back to --qos=long (7-day cap, known-working on
# this account per render_scenes.sbatch/extract_blobs.sbatch) -- the script
# saves to Excel every 120 rows and supports RESUME_FROM_RUN, so a kill at
# the wall only costs the unfinished tail, resubmittable.
#
# GPU choice: l40 (Ada Lovelace) picked over a40/v100 for inference speed;
# swap the --gres line to gpu:a40:1 or gpu:v100:1 if l40 is unavailable/busy.

source ~/.bashrc
conda activate rq2

cd ~/CARE-Drive
python "tables/table_09/Qwen_ToT_Component_Ablation.py"
