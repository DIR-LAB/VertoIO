import os
import csv
import config
import stat_data
import subprocess
import tuning_config
import osc_configuration

class OSC_Snapshot:
    def __init__(self, osc_name):
        self.osc_name = osc_name

        self.osc_rpc_configuration_current = osc_configuration.OSC_Configuration(osc_name)

        self.ost_read_rpc_bytes_data = stat_data.Stat_Data(config.osc_sys_kernel_path + osc_name)
        self.ost_read_rpc_usec_data = stat_data.Stat_Data(config.osc_sys_kernel_path + osc_name)

        self.ost_write_rpc_bytes_data = stat_data.Stat_Data(config.osc_sys_kernel_path + osc_name)
        self.ost_write_rpc_usec_data = stat_data.Stat_Data(config.osc_sys_kernel_path + osc_name)

        self.osc_req_waittime_data = stat_data.Stat_Data(config.osc_sys_kernel_path + osc_name)
        self.osc_req_active_data = stat_data.Stat_Data(config.osc_sys_kernel_path + osc_name)

        self.cur_dirty_bytes = 0
        self.cur_grant_bytes = 0
        self.cur_read_rif = 0
        self.pending_read_pages = 0
        self.cur_write_rif = 0
        self.pending_write_pages = 0

        self.is_dist_centered = 0
        self.write_avg_xfer_speed = 0
        self.write_obsrvbl_caching_rate = 0
        self.waittime_to_mrif_ratio = 0
        self.write_RPC_gnrn_rate = 0
        self.osc_obsrvl_total_data_cached = 0
        self.all_osc_obsrvl_total_data_cached = 0
        self.pct_estimated_write_xfer = 0
        self.avg_write_rpc_latency_per_unit_data = 0
        self.is_overlapped_write = 0

        self.read_ppr_dist = dict()
        self.write_ppr_dist = dict()

        self.read_rif_dist = dict()
        self.write_rif_dist = dict()

        self.llite_write_bytes = 0
        self.tun_skip_cnt = 0
        self.has_applied_lowest = False
        self.has_changed_lowest = False
        self.ra_issue_switch_flag = False

        self.seq_data = {}
        for idx, header in enumerate(config.stat_name_list + config.feature_name_list):
            self.seq_data[header] = []

    def save_cur_rif(self, cur_read_rif, cur_write_rif):
        self.cur_read_rif = cur_read_rif
        self.cur_write_rif = cur_write_rif

    def save_pending_pages(self, pending_read_pages, pending_write_pages):
        self.pending_read_pages = pending_read_pages
        self.pending_write_pages = pending_write_pages

    def save_ppr_dist(self, read_ppr_dist, write_ppr_dist):
        self.read_ppr_dist = read_ppr_dist
        self.write_ppr_dist = write_ppr_dist

    def save_rif_dist(self, read_rif_dist, write_rif_dist):
        self.read_rif_dist = read_rif_dist
        self.write_rif_dist = write_rif_dist

    def save_write_params(self, write_obsrvbl_caching_rate, write_RPC_gnrn_rate, write_avg_xfer_speed, avg_write_rpc_latency_per_unit_data):
        self.write_obsrvbl_caching_rate = write_obsrvbl_caching_rate
        self.write_RPC_gnrn_rate = write_RPC_gnrn_rate
        self.write_avg_xfer_speed = write_avg_xfer_speed
        self.avg_write_rpc_latency_per_unit_data = avg_write_rpc_latency_per_unit_data

    def show_dict(self, dict_element):
        for key in dict_element:
            print(key, ': ', dict_element[key])

    def show_snapshot(self):
        print('osc_name: ', self.osc_name)

        print('osc_rpc_configuration_current: ')
        self.osc_rpc_configuration_current.show_configuration()

        print('ost_read_rpc_bytes_data: ')
        self.ost_read_rpc_bytes_data.show_data()
        print('ost_read_rpc_usec_data: ')
        self.ost_read_rpc_usec_data.show_data()

        print('ost_write_rpc_bytes_data: ')
        self.ost_write_rpc_bytes_data.show_data()
        print('ost_write_rpc_usec_data: ')
        self.ost_write_rpc_usec_data.show_data()

        print('osc_req_waittime_data: ')
        self.osc_req_waittime_data.show_data()
        print('osc_req_active_data: ')
        self.osc_req_active_data.show_data()

        print('cur_dirty_bytes: ', self.cur_dirty_bytes)
        print('cur_grant_bytes: ', self.cur_grant_bytes)
        print('cur_read_rif: ', self.cur_read_rif)
        print('pending_read_pages: ', self.pending_read_pages)
        print('cur_write_rif: ', self.cur_write_rif)
        print('pending_write_pages: ', self.pending_write_pages)

        print('is_dist_centered: ', self.is_dist_centered)
        print('write_avg_xfer_speed: ', self.write_avg_xfer_speed, ' B/sec')
        print('write_obsrvbl_caching_rate: ', self.write_obsrvbl_caching_rate, ' B/sec')
        print('waittime_to_mrif_ratio: ', self.waittime_to_mrif_ratio)
        print('write_RPC_gnrn_rate: ', self.write_RPC_gnrn_rate, ' B/sec')
        print('osc_obsrvl_total_data_cached: ', self.osc_obsrvl_total_data_cached, ' Bytes')
        print('all_osc_obsrvl_total_data_cached: ', self.all_osc_obsrvl_total_data_cached, ' Bytes')
        print('pct_estimated_write_xfer: ', self.pct_estimated_write_xfer)
        print('avg_write_rpc_latency_per_unit_data: ', self.avg_write_rpc_latency_per_unit_data, ' usec')
        print('is_overlapped_write: ', self.is_overlapped_write)

        print('read_ppr_dist: ')
        self.show_dict(self.read_ppr_dist)
        print('write_ppr_dist: ')
        self.show_dict(self.write_ppr_dist)

        print('read_rif_dist: ')
        self.show_dict(self.read_rif_dist)
        print('write_rif_dist: ')
        self.show_dict(self.write_rif_dist)

        print('llite_write_bytes: ', self.llite_write_bytes, ' Bytes')

    def construct_stats_list(self):
        params_list = []
        params_list = params_list + self.ost_read_rpc_bytes_data.construct_params_list()
        params_list = params_list + self.ost_read_rpc_usec_data.construct_params_list()

        params_list = params_list + self.ost_write_rpc_bytes_data.construct_params_list()
        params_list = params_list + self.ost_write_rpc_usec_data.construct_params_list()

        params_list = params_list + self.osc_req_waittime_data.construct_params_list()
        params_list = params_list + self.osc_req_active_data.construct_params_list()

        params_list = params_list + [self.cur_dirty_bytes]
        params_list = params_list + [self.cur_grant_bytes]
        params_list = params_list + [self.cur_read_rif]
        params_list = params_list + [self.pending_read_pages]
        params_list = params_list + [self.cur_write_rif]
        params_list = params_list + [self.pending_write_pages]

        return params_list

    def construct_features_list(self):
        params_list = []
        params_list = params_list + [self.is_dist_centered]
        params_list = params_list + [self.ost_write_rpc_bytes_data.get_average() / config.client_page_size_in_bytes]
        params_list = params_list + [self.write_avg_xfer_speed]
        params_list = params_list + [(self.osc_rpc_configuration_current.mrif_value * self.write_avg_xfer_speed)]
        params_list = params_list + [self.write_obsrvbl_caching_rate]
        params_list = params_list + [((self.cur_dirty_bytes / config.megabytes_to_bytes) / self.osc_rpc_configuration_current.mdm_value) * 100]
        params_list = params_list + [self.waittime_to_mrif_ratio]
        params_list = params_list + [self.osc_req_waittime_data.get_average()]
        params_list = params_list + [self.write_RPC_gnrn_rate]
        params_list = params_list + [self.osc_obsrvl_total_data_cached]
        params_list = params_list + [self.all_osc_obsrvl_total_data_cached]
        params_list = params_list + [self.pct_estimated_write_xfer]
        params_list = params_list + [self.avg_write_rpc_latency_per_unit_data]
        params_list = params_list + [self.ost_write_rpc_usec_data.get_average()]
        params_list = params_list + [self.osc_req_active_data.get_average()]
        params_list = params_list + [self.is_overlapped_write]
        params_list = params_list + [((self.ost_write_rpc_bytes_data.samples_sum * 100.0) / self.pct_estimated_write_xfer) if self.pct_estimated_write_xfer != 0 else 0]

        return params_list

    def append_line_to_csv(self, filename, params_list):
        with open(filename, "a") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([param for param in params_list])

    def write_stats_and_features_list_to_csv(self, result_folder_path, wld_name, params_list, strtg_type = 1):
        script_dir = os.path.abspath(os.path.dirname(__file__))

        dirname = os.path.dirname(os.path.join(script_dir, result_folder_path))
        osc_csv_filename = os.path.join(dirname, 'all_wld_csvs_with_system_stats_and_features', wld_name + "_" + self.osc_name + "_sheet_" + tuning_config.strategies[strtg_type] + ".csv")
        osc_specific_csv_filename = os.path.join(script_dir, result_folder_path, wld_name + "_" + self.osc_name + "_sheet_" + tuning_config.strategies[strtg_type] + ".csv")

        if not os.path.exists(osc_csv_filename):
            self.append_line_to_csv(osc_csv_filename, config.stat_name_list + config.feature_name_list)
            self.append_line_to_csv(osc_csv_filename, config.stat_summary_list + config.feature_summary_list)
        if not os.path.exists(osc_specific_csv_filename):
            self.append_line_to_csv(osc_specific_csv_filename, config.stat_name_list + config.feature_name_list)
            self.append_line_to_csv(osc_specific_csv_filename, config.stat_summary_list + config.feature_summary_list)

        self.append_line_to_csv(osc_csv_filename, params_list)
        self.append_line_to_csv(osc_specific_csv_filename, params_list)

    def get_perf_pred_all_header(self, explor_config_list, feats):
        modified_config_list = []
        modified_config_list.append("observation_no")

        for name in feats:
            modified_config_list.append(name)

        for conf in explor_config_list:
            modified_config_list.append(str(conf) + "_perf")

        modified_config_list.append("cur_perf")
        modified_config_list.append("best_config")
        modified_config_list.append("best_config_perf_pred")
        modified_config_list.append("std_dev")

        return modified_config_list

    def write_perf_pred_all_to_csv(self, result_folder_path, wld_name, params_list, explor_config_list, feats, strtg_type = 1):
        script_dir = os.path.abspath(os.path.dirname(__file__))
        osc_csv_filename = os.path.join(script_dir, result_folder_path, wld_name + "_" + self.osc_name + "_sheet_" + tuning_config.strategies[strtg_type] + "_perf_pred_all.csv")

        if not os.path.exists(osc_csv_filename):
            self.append_line_to_csv(osc_csv_filename, self.get_perf_pred_all_header(explor_config_list, feats))

        self.append_line_to_csv(osc_csv_filename, params_list)

    def set_mppr_value(self, param_value):
        param_value = param_value if param_value >= config.mppr_lowest_limit else config.mppr_lowest_limit
        param_value = param_value if param_value <= config.mppr_highest_limit else config.mppr_highest_limit

        subprocess.call('echo ' + str(param_value) + ' > ' + config.osc_proc_path + self.osc_name + '/' + config.mppr_str, shell=True)
        print("Previous Value: ", self.osc_rpc_configuration_current.mppr_value, " ====> New Value: ", param_value)

        if self.has_applied_lowest == True and self.has_changed_lowest == False:
            self.has_changed_lowest = True

    def set_mrif_value(self, param_value):
        param_value = param_value if param_value >= config.mrif_lowest_limit else config.mrif_lowest_limit
        param_value = param_value if param_value <= config.mrif_highest_limit else config.mrif_highest_limit

        subprocess.call('echo ' + str(param_value) + ' > ' + config.osc_sys_fs_path + self.osc_name + '/' + config.mrif_str, shell=True)
        print("Previous Value: ", self.osc_rpc_configuration_current.mrif_value, " ====> New Value: ", param_value)

        if self.has_applied_lowest == True and self.has_changed_lowest == False:
            self.has_changed_lowest = True
