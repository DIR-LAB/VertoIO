import copy
import math
import time
import rpc_utils
import numpy as np
import pandas as pd
import tuning_utils
import tuning_config
import osc_snapshot

def calculate_score(normalized_prob, mppr, mrif, max_mppr, max_mrif, bias_type):
    if bias_type == "low":
        # Inverse mrif normalized to 0 to 1. Lower mrif values are better.
        mrif_score = 1 - tuning_utils.normalize(np.log2(mrif), 0, np.log2(max_mrif))

        return normalized_prob + mrif_score

    # Mppr normalized to 0 to 1. Higher mppr values are better.
    mppr_score = tuning_utils.normalize(np.log2(mppr), 0, np.log2(max_mppr))

    # Mrif normalized to 0 to 1. Higher mrif values are better.
    mrif_score = tuning_utils.normalize(np.log2(mrif), 0, np.log2(max_mrif))

    return normalized_prob + (normalized_prob*mppr_score) + (normalized_prob*mrif_score)

def greedy_config(configs, probabilities, explor_config_list_all, cur_osc_snap):
    # Filter configurations based on threshold
    filtered_indices = [i for i, prob in enumerate(probabilities) if prob > tuning_config.config_prob_thrshld]
    if len(filtered_indices) == 1:
        return configs[filtered_indices[0]]

    if filtered_indices:
        scores = []

        # Normalize probabilities for filtered configurations
        min_prob = min(probabilities[i] for i in filtered_indices)
        max_prob = max(probabilities[i] for i in filtered_indices)
        normalized_probs = [tuning_utils.normalize(probabilities[i], min_prob, max_prob) for i in filtered_indices]

        # Find the maximum values for mppr and mrif in explor_config_list_all
        max_mppr = max(config[0] for config in explor_config_list_all)
        max_mrif = max(config[1] for config in explor_config_list_all)

        bias = "high"
        if cur_osc_snap.llite_write_bytes != 0 and cur_osc_snap.pct_estimated_write_xfer < tuning_config.pct_xfer_thrshld:
            bias = "low"
            if cur_osc_snap.tun_skip_cnt == 0:
                cur_osc_snap.tun_skip_cnt = 5

         # Calculate scores for each configuration after normalizing probabilities
        for i, idx in enumerate(filtered_indices):
            normalized_prob = normalized_probs[i]
            scores.append(calculate_score(normalized_prob, explor_config_list_all[idx][0], explor_config_list_all[idx][1], max_mppr, max_mrif, bias))
            print("[WRITE] Config: (", explor_config_list_all[idx][0], ', ',explor_config_list_all[idx][1], ') | Prob: ', probabilities[idx], ' | Score: ', scores[i])

        best_score_index = np.argmax(scores)
        chosen_index = filtered_indices[best_score_index]

        # Return the configuration at the chosen index
        return configs[chosen_index]
    else:
        return None

def find_best_config(probabilities, explor_config_list_all, cur_osc_snap):
    configs = list(range(len(explor_config_list_all)))

    chosen_config = greedy_config(configs, probabilities, explor_config_list_all, cur_osc_snap)

    return chosen_config

def predict_vals(result_folder_path, wld_name, cur_osc_snap: osc_snapshot.OSC_Snapshot, client_osc_feats_df_dict, model, feats, explor_config_list_all, seq_length, obsvn_cnt, strtg_type):
    # Set display options to show all rows and columns without truncation
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

    if len(client_osc_feats_df_dict) == 0:
        print("Not enough data present for: ", cur_osc_snap.osc_name, " at k: ", seq_length)
        return

    # <<<<<<<<< WRITE-SPECIFIC CHANGE >>>>>>>>>>>
    if cur_osc_snap.tun_skip_cnt != 0:
        print("Skipping Tuning for: ", cur_osc_snap.osc_name, " for having tun_skip_cnt: ", cur_osc_snap.tun_skip_cnt)
        cur_osc_snap.tun_skip_cnt -= 1
        return

    tun_time = time.time()
    cur_config_perf = client_osc_feats_df_dict.iloc[0]['target']
    min_target_pred = None
    min_target_config = None

    all_perf_pred = []
    all_write_perf_pred = []

    feats_list = client_osc_feats_df_dict[feats].iloc[0:1].values.tolist()
    for l in feats_list:
        for v in l:
            all_perf_pred.append(v)

    feats_df = copy.deepcopy(client_osc_feats_df_dict)
    row = feats_df.iloc[0]
    dfs = []

    for param_config in explor_config_list_all:
        row[tuning_config.theta[0]] = math.log2(param_config[0])
        row[tuning_config.theta[1]] = math.log2(param_config[1])
        dfs.append(row.copy())

    test_df = pd.concat(dfs, axis=1).T
    predict_time = time.time()
    preds = tuning_utils.predict(model, test_df, feats)
    print('Prediction Time: ', int((time.time() - predict_time) * 1000), ' miliseconds for OSC: ', cur_osc_snap.osc_name)
    # <<<<<<<<< WRITE-SPECIFIC CHANGE >>>>>>>>>>>
    chosen_config = find_best_config(preds.tolist(), explor_config_list_all, cur_osc_snap)

    mppr_val = cur_osc_snap.osc_rpc_configuration_current.mppr_value
    mrif_val = cur_osc_snap.osc_rpc_configuration_current.mrif_value
    
    for i, param_config in enumerate(explor_config_list_all):
        if i == chosen_config:
            min_target_pred = preds[i]
            min_target_config = param_config
        
        elif min_target_pred is None and min_target_config is None and param_config[0] == mppr_val and param_config[1] == mrif_val:
            min_target_pred = preds[i]
            min_target_config = param_config
        
        all_perf_pred.append(preds[i])
        all_write_perf_pred.append(preds[i])

    all_perf_pred.append(cur_config_perf)
    all_perf_pred.append(min_target_config)
    all_perf_pred.append(min_target_pred)
    std_dev = np.std(all_write_perf_pred)
    all_perf_pred.append(std_dev)

    all_perf_pred = [obsvn_cnt] + all_perf_pred
    cur_osc_snap.write_perf_pred_all_to_csv(result_folder_path, wld_name, all_perf_pred, explor_config_list_all, feats, strtg_type)
    rpc_utils.apply_best_config(cur_osc_snap, min_target_config)
    print('Tuning Time: ', int((time.time() - tun_time) * 1000), ' miliseconds for OSC: ', cur_osc_snap.osc_name)
