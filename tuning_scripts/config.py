osc_proc_path = '/proc/fs/lustre/osc/'
osc_sys_fs_path = '/sys/fs/lustre/osc/'
osc_sys_kernel_path = '/sys/kernel/debug/lustre/osc/'
llite_sys_kernel_path = '/sys/kernel/debug/lustre/llite/'

osc_list_of_names_fetch_cmd = ['lctl', 'list_param', 'osc.*']
llite_fs_fetch_cmd = ['lctl', 'list_param', 'llite.*']

mppr_str = 'max_pages_per_rpc'
mdm_str = 'max_dirty_mb'
mrif_str = 'max_rpcs_in_flight'

# default rpc parameters configuration
default_mppr_value = 1024
default_mrif_value = 8
default_mdm_value = 2000

# rpc parameters highest limit
mppr_highest_limit = 1024
mrif_highest_limit = 256
mdm_highest_limit = 2000

# rpc parameters lowest limit
mppr_lowest_limit = 1
mrif_lowest_limit = 1
mdm_lowest_limit = 1

client_page_size_in_bytes = 4096
megabytes_to_bytes = 1024*1024

decentered_thrshld = 0.03
overlapped_write_thrshld = 3

stat_name_list = [
    'observation_no',

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
    'max_ra_issues_to_total_ratio',

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
    'pending_write_pages'
]

feature_name_list = [
    'is_dist_centered',
    'avg_pages_per_write_rpc',
    'write_avg_xfer_speed',
    'write_max_xfer_speed',
    'write_obsrvbl_caching_rate',
    'used_pct_dirty_cache',
    'waittime_to_mrif_ratio',
    'avg_waittime',
    'write_rpc_generation_rate',
    'osc_obsrvl_total_data_cached',
    'all_osc_obsrvl_total_data_cached',
    'pct_estimated_write_xfer',
    'avg_write_rpc_latency_per_unit_data',
    'avg_write_rpc_waittime',
    'avg_rpcs_in_flight',
    'is_overlapped_write',
    'osc_total_write_perf',
    'actual_record_duration'
]

stat_summary_list = [
    'which observation it is (start from 1)',

    'max_pages_per_rpc (mppr)',
    'max_rpcs_in_flight (mrif)',
    'max_dirty_mb (mdm)',

    'total count of llite layer read IOs',
    'minimum size of llite layer read IOs',
    'maximum size of llite layer read IOs',
    'total size of all llite layer read IOs',
    'total count of llite layer write IOs',
    'minimum size of llite layer write IOs',
    'maximum size of llite layer write IOs',
    'total size of all llite layer write IOs',
    'the ratio of max readahead issues to total pages ratio',

    'total count of OSC layer read RPCs',
    'minimum size of OSC layer read RPCs',
    'maximum size of OSC layer read RPCs',
    'total size of all OSC layer read RPCs',
    'total count of OSC layer read RPCs',
    'minimum time spent by OSC layer read RPCs',
    'maximum time spent by OSC layer read RPCs',
    'total time spent by all OSC layer read RPCs',

    'total count of OSC layer write RPCs',
    'minimum size of OSC layer write RPCs',
    'maximum size of OSC layer write RPCs',
    'total size of all OSC layer write RPCs',
    'total count of OSC layer write RPCs',
    'minimum time spent by OSC layer write RPCs',
    'maximum time spent by OSC layer write RPCs',
    'total time spent by all OSC layer write RPCs',

    'total count of completed RPCs whose waittime got recorded',
    'minimum waittime recorded among all completed RPCs',
    'maximum waittime recorded among all completed RPCs',
    'total amount of waittime recorded for all completed RPCs',
    'total count of issued RPCs',
    'minimum RPCs in the air observed among all issued RPCs',
    'maximum RPCs in the air observed among all issued RPCs',
    'total RPCs in the air observed for all issued RPCs',

    'current amount of dirty pages (in bytes) in dirty page cache',
    'current amount of grants (in bytes)',
    'current amount of read RPCs in air',
    'pending amount of read pages waiting to be cached',
    'current amount of write RPCs in air',
    'pending amount of write pages waiting to be cached',
]

feature_summary_list = [
    'is pages_per_rpc distribution centered: Centered(+1), Decentered(-1), Empty(0)',
    'average pages observed among issued write RPCs',
    'average transfer speed of write RPCs',
    'maximum transfer speed of write RPCs',
    'observable caching rate of write pages in dirty page cache (exclude caching that happens through updating of pages in cache)',
    'percentages of dirty page cache that is occupied',
    'ratio of avg_waittime to max_rpcs_in_flight',
    'average of waittime for all completed RPCs',
    'how fast data is being utilized to generate RPCs',
    'total amount of observable data (excludes in-cache update) that was cached in this OSC',
    'all OSC total amount of observable data (excludes in-cache update) that was cached',
    'percentage of estimated llite layer write bytes that have been completed xferr through this OSC layer',
    'the average amount of latency observed during write RPC communication for a unit (in Page, size = 4kB) of data',
    'average of waittime for completed write RPCs',
    'average number of observed RPCs in flight',
    'whether we have overlap of caching write operations',
    'Estimated amount of LLITE layer writes served by this OSC',
    'actual snapshot record duration'
]
