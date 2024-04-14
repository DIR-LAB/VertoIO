snap_record_duration = 0.5
strategies = ["dflt_config", "greedy_config", "optml_config"]

pct_xfer_thrshld = 80
config_prob_thrshld = 0.80
max_ra_issues_ratio_thrshld = 0.05

read_model_path = "./xgb-classifier-read-only/"
write_model_path = "./xgb-classifier-write-only/"

# s: observation settings (derived from raw data)
s_feats = [
    'ratio_of_used_cache_to_maximum_cache',
    'diff_in_ratio_of_used_cache_to_maximum_cache',
    'amount_of_rpc_transfer',
    'diff_in_amount_of_rpc_transfer',
    'avg_rpc_latency',
    'diff_in_avg_rpc_latency',
    'ratio_of_average_to_maximum_pages_per_rpc',
    'diff_in_ratio_of_average_to_maximum_pages_per_rpc',
    'ratio_of_average_to_maximum_rpc_in_flight',
    'diff_in_ratio_of_average_to_maximum_rpc_in_flight'
]
# theta: the tunnable parameters
theta = ['osc_rpc_configuration_current.mppr_value', 'osc_rpc_configuration_current.mrif_value']

raw_s_feats = [
    'osc_rpc_configuration_current.mppr_value',
    'osc_rpc_configuration_current.mrif_value',
    'osc_rpc_configuration_current.mdm_value',
    'llite_stats_read_bytes.no_of_samples',
    'llite_stats_read_bytes.sample_min',
    'llite_stats_read_bytes.sample_max',
    'llite_stats_read_bytes.samples_sum',
    'llite_stats_write_bytes.no_of_samples',
    'llite_stats_write_bytes.sample_min',
    'llite_stats_write_bytes.sample_max',
    'llite_stats_write_bytes.samples_sum',
    'ost_read_rpc_bytes_data.no_of_samples',
    'ost_read_rpc_bytes_data.sample_min',
    'ost_read_rpc_bytes_data.sample_max',
    'ost_read_rpc_bytes_data.samples_sum',
    'ost_read_rpc_usec_data.no_of_samples',
    'ost_read_rpc_usec_data.sample_min',
    'ost_read_rpc_usec_data.sample_max',
    'ost_read_rpc_usec_data.samples_sum',
    'ost_write_rpc_bytes_data.no_of_samples',
    'ost_write_rpc_bytes_data.sample_min',
    'ost_write_rpc_bytes_data.sample_max',
    'ost_write_rpc_bytes_data.samples_sum',
    'ost_write_rpc_usec_data.no_of_samples',
    'ost_write_rpc_usec_data.sample_min',
    'ost_write_rpc_usec_data.sample_max',
    'ost_write_rpc_usec_data.samples_sum',
    'osc_req_waittime_data.no_of_samples',
    'osc_req_waittime_data.sample_min',
    'osc_req_waittime_data.sample_max',
    'osc_req_waittime_data.samples_sum',
    'osc_req_active_data.no_of_samples',
    'osc_req_active_data.sample_min',
    'osc_req_active_data.sample_max',
    'osc_req_active_data.samples_sum',
    'cur_dirty_bytes',
    'cur_grant_bytes',
    'cur_read_rif',
    'pending_read_pages',
    'cur_write_rif',
    'pending_write_pages',
    'is_dist_centered',
    'avg_pages_per_write_rpc',
    'write_avg_xfer_speed',
    'write_max_xfer_speed',
    'used_pct_dirty_cache',
    'waittime_to_mrif_ratio',
    'avg_waittime',
    'write_rpc_generation_rate',
    'avg_write_rpc_latency_per_unit_data',
    'avg_write_rpc_waittime',
    'avg_rpcs_in_flight',
    'actual_record_duration',
]

raw_s_feats = [col for col in raw_s_feats if col not in theta]

# the range limit of all features
clip_bounds = {
    'ratio_of_used_cache_to_maximum_cache': (0, 1),
    'diff_in_ratio_of_used_cache_to_maximum_cache': (-1, 1),
    'amount_of_rpc_transfer': (0, 524288000),
    'diff_in_amount_of_rpc_transfer': (-524288000, 524288000),
    'avg_rpc_latency': (0, 100),
    'diff_in_avg_rpc_latency': (-100, 100),
    'ratio_of_average_to_maximum_pages_per_rpc': (0, 1024),
    'diff_in_ratio_of_average_to_maximum_pages_per_rpc': (-1024, 1024),
    'ratio_of_average_to_maximum_rpc_in_flight': (0, 10),
    'diff_in_ratio_of_average_to_maximum_rpc_in_flight': (-10, 10),
}
