#!/bin/bash
#SBATCH --job-name=qwen_tot_ablation
#SBATCH --partition=general
#SBATCH --qos=infinite
#SBATCH --time=10-00:00:00
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --output=/home/nfs/lsuryana/qwen_tot_ablation.log

# Usage:
#   git clone https://github.com/lucassuryana/CARE-Drive.git ~/CARE-Drive
#   cd ~/CARE-Drive && git checkout address-reviewer-comment && git pull
#   sbatch Supplementary_R3.2/qwen_tot_ablation.sbatch
#
# Estimated runtime: ~6.5 days serial (18,000 runs; measured ~35.6s/run avg
# from a 120-run sample: ~50-67s for full-reasoning calls, ~7-9s for
# few-sentence calls). --time is set with buffer above that estimate; --qos
# infinite has no cap of its own, so this is a safety ceiling, not a target.
#
# GPU choice: l40 (Ada Lovelace) picked over a40/v100 for inference speed;
# swap the --gres line to gpu:a40:1 or gpu:v100:1 if l40 is unavailable/busy.

source ~/.bashrc
conda activate rq2

cd ~/CARE-Drive
python Supplementary_R3.2/Qwen_ToT_Component_Ablation.py
