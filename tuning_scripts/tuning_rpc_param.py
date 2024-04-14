import os
import sys
import copy
import time
import pickle
import datetime
import rpc_utils
import tuning_utils
import tuning_config
import client_snapshot
import tuning_rpc_param_read
import tuning_rpc_param_write

strtg_type = 0
obsvn_cnt = -1

def tune_params(result_folder_path, wld_name, cur_snap: client_snapshot.Client_Snapshot, prev_snap: client_snapshot.Client_Snapshot, record_dur, seq_length, explor_config_list_all, read_model, read_feats, write_model, write_feats):
    print('record_dur: ', record_dur)

    # Before this function call, populate_snapshot() has already been called.
    # We need to derive and save the features before moving ahead with tuning.
    rpc_utils.save_features(cur_snap, prev_snap, record_dur)

    client_feats_df_dict_read, client_feats_df_dict_write = tuning_utils.extract_client_feats_df_dict(cur_snap, prev_snap, record_dur, seq_length, obsvn_cnt)
    client_feats_df_dict_read = tuning_utils.build_seq_df_dict(cur_snap, prev_snap, seq_length, client_feats_df_dict_read)
    client_feats_df_dict_write = tuning_utils.build_seq_df_dict(cur_snap, prev_snap, seq_length, client_feats_df_dict_write)
    issues_ratio = cur_snap.llite_snapshot.max_ra_issues_to_total_ratio
    prev_issues_ratio = prev_snap.llite_snapshot.max_ra_issues_to_total_ratio

    for osc_name in cur_snap.osc_names:
        tun_time = time.time()
        print("osc_name: ", osc_name)

        cur_osc_snap = cur_snap.osc_snapshots[osc_name]
        prev_osc_snap = prev_snap.osc_snapshots[osc_name]

        if tuning_utils.is_osc_samples_io_inactive(cur_osc_snap, prev_osc_snap):
            print("No I/O Activity observed for: ", osc_name)
            if cur_osc_snap.has_applied_lowest == True and cur_osc_snap.has_changed_lowest == False:
                rpc_utils.apply_default_config(cur_osc_snap)
            # print('Tuning Time: ', int((time.time() - tun_time) * 1000), ' miliseconds for OSC: ', cur_osc_snap.osc_name)
            continue

        if cur_osc_snap.ost_read_rpc_bytes_data.samples_sum > cur_osc_snap.ost_write_rpc_bytes_data.samples_sum:
            # <<<<<<<<< READ-SPECIFIC CHANGE >>>>>>>>>>>
            if issues_ratio > tuning_config.max_ra_issues_ratio_thrshld:
                print("Presence of High Max RA violation issue;  where issues_ratio: ", issues_ratio)
                if cur_osc_snap.has_applied_lowest == True and cur_osc_snap.has_changed_lowest == False:
                    rpc_utils.apply_default_config(cur_osc_snap)
                elif cur_osc_snap.ra_issue_switch_flag == True:
                    cur_osc_snap.ra_issue_switch_flag = False
                    rpc_utils.apply_best_config(cur_osc_snap, [prev_osc_snap.osc_rpc_configuration_current.mppr_value, prev_osc_snap.osc_rpc_configuration_current.mrif_value])
                # print('Tuning Time: ', int((time.time() - tun_time) * 1000), ' miliseconds for OSC: ', cur_osc_snap.osc_name)
                continue

            if cur_osc_snap.has_applied_lowest == False:
                if strtg_type > 0 and strtg_type < len(tuning_config.strategies)-1:
                    rpc_utils.apply_lowest_config(cur_osc_snap)
                else:
                    rpc_utils.apply_default_config(cur_osc_snap)
                    cur_osc_snap.has_changed_lowest = True
                cur_osc_snap.has_applied_lowest = True
                # print('Tuning Time: ', int((time.time() - tun_time) * 1000), ' miliseconds for OSC: ', cur_osc_snap.osc_name)
                continue

            if prev_issues_ratio > tuning_config.max_ra_issues_ratio_thrshld:
                if cur_osc_snap.ra_issue_switch_flag == False:
                    cur_osc_snap.ra_issue_switch_flag = True
                else:
                    cur_osc_snap.ra_issue_switch_flag = False

            if strtg_type > 0 and strtg_type < len(tuning_config.strategies)-1:
                tuning_rpc_param_read.predict_vals(result_folder_path, wld_name, cur_osc_snap, client_feats_df_dict_read[osc_name], read_model, read_feats, explor_config_list_all, seq_length, obsvn_cnt, strtg_type)
            print('Tuning Time: ', int((time.time() - tun_time) * 1000), ' miliseconds for OSC: ', cur_osc_snap.osc_name)

        else:
            if cur_osc_snap.has_applied_lowest == False:
                if strtg_type > 0 and strtg_type < len(tuning_config.strategies)-1:
                    rpc_utils.apply_lowest_config(cur_osc_snap)
                else:
                    rpc_utils.apply_default_config(cur_osc_snap)
                    cur_osc_snap.has_changed_lowest = True
                cur_osc_snap.has_applied_lowest = True
                # print('Tuning Time: ', int((time.time() - tun_time) * 1000), ' miliseconds for OSC: ', cur_osc_snap.osc_name)
                continue

            if strtg_type > 0 and strtg_type < len(tuning_config.strategies)-1:
                tuning_rpc_param_write.predict_vals(result_folder_path, wld_name, cur_osc_snap, client_feats_df_dict_write[osc_name], write_model, write_feats, explor_config_list_all, seq_length, obsvn_cnt, strtg_type)

    cur_snap.store_params_to_csv(result_folder_path, wld_name, record_dur, obsvn_cnt, strtg_type)

if __name__ == "__main__":
    # relative path from the script
    result_folder_path = sys.argv[1]
    wld_name = sys.argv[2]
    strtg_type = int(sys.argv[3])
    # value of k: 0->10
    seq_length = int(sys.argv[4])

    explor_config_list_all = rpc_utils.construct_explor_config_list()
    read_model = tuning_utils.load_model(os.path.join(tuning_config.read_model_path, f'model_{seq_length}.json'))
    with open(os.path.join(tuning_config.read_model_path, f'feats_list_{seq_length}.pkl'), 'rb') as f:
        read_feats = pickle.load(f)
    write_model = tuning_utils.load_model(os.path.join(tuning_config.write_model_path, f'model_{seq_length}.json'))
    with open(os.path.join(tuning_config.write_model_path, f'feats_list_{seq_length}.pkl'), 'rb') as f:
        write_feats = pickle.load(f)

    prev_snap = client_snapshot.Client_Snapshot()
    prev_snap.clear_system_stats_data()

    prev_snap.populate_snapshot()
    obsvn_cnt += 1
    prev_snap.store_params_to_csv(result_folder_path, wld_name, 0, obsvn_cnt, strtg_type)
    begin_time = time.time()

    time.sleep(tuning_config.snap_record_duration)

    cur_snap = client_snapshot.Client_Snapshot()
    cur_snap.populate_snapshot()
    print('Snapshot Generated: %s' % datetime.datetime.now())
    obsvn_cnt += 1

    while True:
        end_time = time.time()
        record_dur = end_time - begin_time

        tune_params(result_folder_path, wld_name, cur_snap, prev_snap, record_dur, seq_length, explor_config_list_all, read_model, read_feats, write_model, write_feats)

        #cur_snap.show_snapshot()
        cur_snap.clear_system_stats_data()
        print('Tuning + Cleanup Time: ', int((time.time() - end_time) * 1000), ' miliseconds')
        begin_time = time.time()

        time.sleep(tuning_config.snap_record_duration)

        prev_snap = copy.deepcopy(cur_snap)
        cur_snap.populate_snapshot()
        print('Snapshot Generated: %s' % datetime.datetime.now())
        obsvn_cnt += 1
