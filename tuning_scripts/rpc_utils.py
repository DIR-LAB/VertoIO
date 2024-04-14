import config
import random
import subprocess

def is_empty_dist(osc_dist):
    # Even the empty dist should have at least one rows.
    if len(osc_dist) == 1:
        for key in osc_dist:
            if osc_dist[key][0] == 0:
                return True

    for key in osc_dist:
        if osc_dist[key][0] != 0:
            return False
    return True

def is_dist_centered_around_param(osc_dist, param_value, param_majority_percentage):
    # dist is a dict of tuples: (rpc_count, % of total rpc_count, cumulative %)
    # the key of the dict is param value factored by 2

    for key in osc_dist:
        if key == param_value:
            if osc_dist[key][2] - osc_dist[key][1] > param_majority_percentage:
                return False
            return True

def is_distribution_centered(cur_osc_snap):
    avg_pages_per_rpc = cur_osc_snap.ost_write_rpc_bytes_data.get_average() / config.client_page_size_in_bytes
    cur_osc_mppr_value = cur_osc_snap.osc_rpc_configuration_current.mppr_value

    if avg_pages_per_rpc == 0 or is_empty_dist(cur_osc_snap.write_ppr_dist) == True:
        return True

    if avg_pages_per_rpc >= ((100-config.decentered_thrshld)/100)*cur_osc_mppr_value and is_dist_centered_around_param(cur_osc_snap.write_ppr_dist, cur_osc_mppr_value, config.decentered_thrshld) == True:
        return True

    return False

def get_write_obsrvbl_caching_rate(cur_osc_snap, prev_osc_snap, record_dur):
    osc_obsrvl_total_data_cached = cur_osc_snap.cur_dirty_bytes + cur_osc_snap.ost_write_rpc_bytes_data.samples_sum - prev_osc_snap.cur_dirty_bytes
    write_obsrvbl_caching_rate = int(osc_obsrvl_total_data_cached / record_dur)

    return write_obsrvbl_caching_rate, osc_obsrvl_total_data_cached

def get_write_RPC_gnrn_rate(cur_osc_snap, prev_osc_snap, record_dur):
    # The combination for current is [Pending IO Data + RPCs In Flight Data + Transferred Data]
    cur_avg_write_bytes_in_rpc = cur_osc_snap.ost_write_rpc_bytes_data.get_average()
    cur_total_gnrntd_data = (cur_osc_snap.cur_write_rif * cur_avg_write_bytes_in_rpc) + cur_osc_snap.ost_write_rpc_bytes_data.samples_sum

    prev_rif_data = prev_osc_snap.cur_write_rif * prev_osc_snap.ost_write_rpc_bytes_data.get_average()

    cur_actual_gnrntd_data  = cur_total_gnrntd_data - prev_rif_data
    write_RPC_gnrn_rate = int(cur_actual_gnrntd_data / record_dur)

    return write_RPC_gnrn_rate

def get_write_avg_xfer_speed(cur_osc_snap):
    if cur_osc_snap.ost_write_rpc_usec_data.samples_sum == 0:
        write_avg_xfer_speed = 0
    else:
        write_avg_xfer_speed = int((cur_osc_snap.ost_write_rpc_bytes_data.samples_sum / cur_osc_snap.ost_write_rpc_usec_data.samples_sum) * 1000000)

    return write_avg_xfer_speed

def get_avg_write_rpc_latency_per_unit_data(cur_osc_snap):
    avg_pages_per_write_rpc = cur_osc_snap.ost_write_rpc_bytes_data.get_average() / config.client_page_size_in_bytes
    avg_rpcs_in_flight = cur_osc_snap.osc_req_active_data.get_average()
    if avg_pages_per_write_rpc == 0 or avg_rpcs_in_flight == 0:
        return 0

    avg_write_rpc_waittime = cur_osc_snap.ost_write_rpc_usec_data.get_average()
    avg_write_rpc_latency_per_unit_data = (avg_write_rpc_waittime / (avg_pages_per_write_rpc * avg_rpcs_in_flight))

    return avg_write_rpc_latency_per_unit_data

def get_pct_estimated_write_xfer(cur_osc_snap):
    if cur_osc_snap.osc_obsrvl_total_data_cached == 0 or cur_osc_snap.all_osc_obsrvl_total_data_cached == 0 or cur_osc_snap.llite_write_bytes == 0:
        return 0

    ratio_obsrvl_cached_data = (cur_osc_snap.osc_obsrvl_total_data_cached / cur_osc_snap.all_osc_obsrvl_total_data_cached)
    est_share_llite = (cur_osc_snap.llite_write_bytes * ratio_obsrvl_cached_data)
    pct_estimated_write_xfer = ((cur_osc_snap.ost_write_rpc_bytes_data.samples_sum / est_share_llite) * 100.0)

    return pct_estimated_write_xfer

def get_is_overlapped_write(cur_osc_snap):
    if cur_osc_snap.pct_estimated_write_xfer <= 0:
        return 0

    if cur_osc_snap.pct_estimated_write_xfer < (100-config.overlapped_write_thrshld):
        return 1

    return 0

def save_features(cur_snap, prev_snap, record_dur):
    llite_snap = cur_snap.llite_snapshot
    all_osc_obsrvl_total_data_cached = 0

    for osc_name in cur_snap.osc_names:
        cur_osc_snap = cur_snap.osc_snapshots[osc_name]
        prev_osc_snap = prev_snap.osc_snapshots[osc_name]

        write_obsrvbl_caching_rate, osc_obsrvl_total_data_cached = get_write_obsrvbl_caching_rate(cur_osc_snap, prev_osc_snap, record_dur)
        write_RPC_gnrn_rate = get_write_RPC_gnrn_rate(cur_osc_snap, prev_osc_snap, record_dur)
        write_avg_xfer_speed = get_write_avg_xfer_speed(cur_osc_snap)
        avg_write_rpc_latency_per_unit_data = get_avg_write_rpc_latency_per_unit_data(cur_osc_snap)
        cur_osc_snap.save_write_params(write_obsrvbl_caching_rate, write_RPC_gnrn_rate, write_avg_xfer_speed, avg_write_rpc_latency_per_unit_data)

        if is_distribution_centered(cur_osc_snap) == True:
            cur_osc_snap.is_dist_centered = 1
        else:
            cur_osc_snap.is_dist_centered = 0
        cur_osc_snap.waittime_to_mrif_ratio = int(int(cur_osc_snap.osc_req_waittime_data.get_average()) / cur_osc_snap.osc_rpc_configuration_current.mrif_value)

        cur_osc_snap.osc_obsrvl_total_data_cached = osc_obsrvl_total_data_cached
        all_osc_obsrvl_total_data_cached += osc_obsrvl_total_data_cached

    for osc_name in cur_snap.osc_names:
        cur_osc_snap = cur_snap.osc_snapshots[osc_name]
        cur_osc_snap.all_osc_obsrvl_total_data_cached = all_osc_obsrvl_total_data_cached
        cur_osc_snap.llite_write_bytes = llite_snap.llite_stats_write_bytes.samples_sum

        pct_estimated_write_xfer = get_pct_estimated_write_xfer(cur_osc_snap)
        cur_osc_snap.pct_estimated_write_xfer = pct_estimated_write_xfer
        cur_osc_snap.is_overlapped_write = get_is_overlapped_write(cur_osc_snap)

def construct_explor_config_list():
    explor_config_list_all = []

    for i in range(11):
        for j in range(9):
            explor_config_list_all.append([int(pow(2, i)), int(pow(2, j))])

    return explor_config_list_all

def apply_best_config(cur_osc_snap, param_config):
    if param_config[0] == cur_osc_snap.osc_rpc_configuration_current.mppr_value and param_config[1] == cur_osc_snap.osc_rpc_configuration_current.mrif_value:
        if cur_osc_snap.has_applied_lowest == True and cur_osc_snap.has_changed_lowest == False:
            cur_osc_snap.has_changed_lowest = True
        return

    cur_osc_snap.set_mppr_value(param_config[0])
    cur_osc_snap.set_mrif_value(param_config[1])

def apply_lowest_config(cur_osc_snap):
    cur_osc_snap.set_mppr_value(config.mppr_lowest_limit)
    cur_osc_snap.set_mrif_value(config.mrif_lowest_limit)

def apply_default_config(cur_osc_snap):
    cur_osc_snap.set_mppr_value(config.default_mppr_value)
    cur_osc_snap.set_mrif_value(config.default_mrif_value)
