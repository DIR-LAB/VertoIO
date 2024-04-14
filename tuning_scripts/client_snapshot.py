import re
import time
import config
import subprocess
import osc_snapshot
import llite_snapshot

class Client_Snapshot:
    def __init__(self):
        self.osc_names = subprocess.run(config.osc_list_of_names_fetch_cmd, stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()
        for i in range(len(self.osc_names)):
            # osc.hasanfs-OST0000-osc-ffff977ebb01e000 ==> hasanfs-OST0000-osc-ffff977ebb01e000
            self.osc_names[i] = self.osc_names[i].split('.')[1]

        self.llite_snapshot = llite_snapshot.LLITE_Snapshot()
        self.osc_snapshots = {osc_name: osc_snapshot.OSC_Snapshot(osc_name) for osc_name in self.osc_names}


    def extract_dicts_from_stat_distribution(self, line_list, stat_matchmaker):
        read_dist = dict()
        write_dist = dict()

        for i in range(len(line_list)):
            try:
                line = line_list[i]
                stat_anchor = re.search('^' + stat_matchmaker + '(\s)*rpcs(\s)*% cum % \|(\s)*rpcs(\s)*% cum %$', line, re.IGNORECASE)
                if stat_anchor == None:
                    continue

                for j in range(i+1, len(line_list)):
                    try:
                        line_match = line_list[j]
                        dist_row_match = re.match('^(\d+):(\s)*(\d+)(\s)*(\d+)(\s)*(\d+)(\s)*\|(\s)*(\d+)(\s)*(\d+)(\s)*(\d+)$', line_match, re.IGNORECASE)
                        if dist_row_match == None:
                            return read_dist, write_dist

                        read_dist[int(dist_row_match.group(1))] = (int(dist_row_match.group(3)), int(dist_row_match.group(5)), int(dist_row_match.group(7)))
                        write_dist[int(dist_row_match.group(1))] = (int(dist_row_match.group(10)), int(dist_row_match.group(12)), int(dist_row_match.group(14)))

                    except AttributeError:
                        return read_dist, write_dist

            except AttributeError:
                stat_anchor = re.search('^' + stat_matchmaker + '(\s)*rpcs(\s)*% cum % \|(\s)*rpcs(\s)*% cum %$', line, re.IGNORECASE)

        return read_dist, write_dist

    def extract_ra_ratio_from_ra_stats(self, line_list):
        hits = misses = issues = 0

        for line in line_list:
            if "hits" in line:
                hits_match = re.search(r"hits\s+(\d+)\s+samples", line)
                if hits_match:
                    hits = float(hits_match.group(1))

            elif "misses" in line:
                misses_match = re.search(r"misses\s+(\d+)\s+samples", line)
                if misses_match:
                    misses = float(misses_match.group(1))

            elif "hit max r-a issue" in line:
                issues_match = re.search(r"hit max r-a issue\s+(\d+)\s+samples", line)
                if issues_match:
                    issues = float(issues_match.group(1))

        total_pages = hits + misses
        issues_to_total_ratio = 0

        if total_pages > 0:  # Prevent division by zero
            issues_to_total_ratio = issues / total_pages

        return issues_to_total_ratio

    def extract_stat_data_from_stats(self, line_list, attr_matchmaker):
        for line in line_list:
            try:
                attr_match = re.search('^' + attr_matchmaker + '(\s+)(\d+)(\s+)(\w+)(\s+)\[(\w+)\](\s+)(\d+)(\s+)(\d+)(\s+)(\d+)', line, re.IGNORECASE)
                no_of_samples = int(float(attr_match.group(2)))
                sample_min = int(float(attr_match.group(8)))
                sample_max = int(float(attr_match.group(10)))
                samples_sum = int(float(attr_match.group(12)))
                return no_of_samples, sample_min, sample_max, samples_sum

            except AttributeError:
                attr_match = re.search('^' + attr_matchmaker + '(\s+)(\d+)(\s+)(\w+)(\s+)\[(\w+)\](\s+)(\d+)(\s+)(\d+)(\s+)(\d+)', line, re.IGNORECASE)

        return 0, 0, 0, 0

    def extract_single_stat_data_from_stats(self, line_list, attr_matchmaker):
        for line in line_list:
            try:
                attr_match = re.search('^' + attr_matchmaker + ':(\s)+(\d)+', line, re.IGNORECASE)
                value_attr = int(float(attr_match.group(2)))
                return value_attr

            except AttributeError:
                attr_match = re.search('^' + attr_matchmaker + ':(\s)+(\d)+', line, re.IGNORECASE)

        return 0

    def save_osc_rpc_dist_stats_data(self, osc_name):
        rpc_stats_lines = []
        with open(config.osc_proc_path + osc_name + '/rpc_stats') as f:
            rpc_stats_lines = f.readlines()

        cur_read_rif = self.extract_single_stat_data_from_stats(rpc_stats_lines, 'read RPCs in flight')
        cur_write_rif = self.extract_single_stat_data_from_stats(rpc_stats_lines, 'write RPCs in flight')
        self.osc_snapshots[osc_name].save_cur_rif(cur_read_rif, cur_write_rif)

        pending_read_pages = self.extract_single_stat_data_from_stats(rpc_stats_lines, 'pending read pages')
        pending_write_pages = self.extract_single_stat_data_from_stats(rpc_stats_lines, 'pending write pages')
        self.osc_snapshots[osc_name].save_pending_pages(pending_read_pages, pending_write_pages)

        read_dist, write_dist = self.extract_dicts_from_stat_distribution(rpc_stats_lines, 'pages per rpc')
        self.osc_snapshots[osc_name].save_ppr_dist(read_dist, write_dist)

        read_dist, write_dist = self.extract_dicts_from_stat_distribution(rpc_stats_lines, 'rpcs in flight')
        self.osc_snapshots[osc_name].save_rif_dist(read_dist, write_dist)

    def save_osc_stats_data(self, osc_name):
        stats_lines = []
        with open(config.osc_sys_kernel_path + osc_name + '/stats') as f:
            stats_lines = f.readlines()

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'req_waittime')
        self.osc_snapshots[osc_name].osc_req_waittime_data.save_data(no_of_samples, sample_min, sample_max, samples_sum)

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'req_active')
        self.osc_snapshots[osc_name].osc_req_active_data.save_data(no_of_samples, sample_min, sample_max, samples_sum)

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'read_bytes')
        self.osc_snapshots[osc_name].ost_read_rpc_bytes_data.save_data(no_of_samples, sample_min, sample_max, samples_sum)

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'write_bytes')
        self.osc_snapshots[osc_name].ost_write_rpc_bytes_data.save_data(no_of_samples, sample_min, sample_max, samples_sum)

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'ost_read')
        self.osc_snapshots[osc_name].ost_read_rpc_usec_data.save_data(no_of_samples, sample_min, sample_max, samples_sum)

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'ost_write')
        self.osc_snapshots[osc_name].ost_write_rpc_usec_data.save_data(no_of_samples, sample_min, sample_max, samples_sum)

    def save_osc_rpc_params_data(self, osc_name):
        mppr_value = 0
        with open(config.osc_proc_path + osc_name + '/' + config.mppr_str) as f:
            mppr_value = int(f.read())

        mrif_value = 0
        with open(config.osc_sys_fs_path + osc_name + '/' + config.mrif_str) as f:
            mrif_value = int(f.read())

        mdm_value = 0
        with open(config.osc_sys_fs_path + osc_name + '/' + config.mdm_str) as f:
            mdm_value = int(f.read())

        self.osc_snapshots[osc_name].osc_rpc_configuration_current.save_configuration(mppr_value, mrif_value, mdm_value)

    def save_osc_params_data(self, osc_name):
        cur_dirty_bytes = 0
        with open(config.osc_sys_fs_path + osc_name + '/' + 'cur_dirty_bytes') as f:
            cur_dirty_bytes = int(f.read())

        self.osc_snapshots[osc_name].cur_dirty_bytes = cur_dirty_bytes

        cur_grant_bytes = 0
        with open(config.osc_proc_path + osc_name + '/' + 'cur_grant_bytes') as f:
            cur_grant_bytes = int(f.read())
        self.osc_snapshots[osc_name].cur_grant_bytes = cur_grant_bytes

    def save_llite_io_stats_data(self):
        stats_lines = []
        with open(config.llite_sys_kernel_path + self.llite_snapshot.llite_fs_name + '/stats') as f:
            stats_lines = f.readlines()

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'read_bytes')
        self.llite_snapshot.llite_stats_read_bytes.save_data(no_of_samples, sample_min, sample_max, samples_sum)

        no_of_samples, sample_min, sample_max, samples_sum = self.extract_stat_data_from_stats(stats_lines, 'write_bytes')
        self.llite_snapshot.llite_stats_write_bytes.save_data(no_of_samples, sample_min, sample_max, samples_sum)

    def save_llite_ra_stats_data(self):
        stats_lines = []
        with open(config.llite_sys_kernel_path + self.llite_snapshot.llite_fs_name + '/read_ahead_stats') as f:
            stats_lines = f.readlines()

        self.llite_snapshot.max_ra_issues_to_total_ratio = self.extract_ra_ratio_from_ra_stats(stats_lines)

    def populate_snapshot(self):
        # Possible improvement by implementing threading here
        for osc_name in self.osc_names:
            gen_time = time.time()
            self.save_osc_stats_data(osc_name)
            self.save_osc_rpc_dist_stats_data(osc_name)
            self.save_osc_rpc_params_data(osc_name)
            self.save_osc_params_data(osc_name)
            print('Snapshot Generation Time: ', int((time.time() - gen_time) * 1000), ' miliseconds for OSC: ', osc_name)

        self.save_llite_io_stats_data()
        self.save_llite_ra_stats_data()

    def clear_all_osc_rpc_stats_data(self):
        for osc_name in self.osc_names:
            subprocess.call('echo "" > ' + config.osc_proc_path + osc_name + '/rpc_stats', shell=True)
            subprocess.call('echo "" > ' + config.osc_sys_kernel_path + osc_name + '/stats', shell=True)

    def clear_llite_io_stats_data(self):
        subprocess.call('echo "" > ' + config.llite_sys_kernel_path + self.llite_snapshot.llite_fs_name + '/stats', shell=True)

    def clear_llite_ra_stats_data(self):
        subprocess.call('echo "" > ' + config.llite_sys_kernel_path + self.llite_snapshot.llite_fs_name + '/read_ahead_stats', shell=True)

    def clear_system_stats_data(self):
        self.clear_all_osc_rpc_stats_data()
        self.clear_llite_io_stats_data()
        self.clear_llite_ra_stats_data()

    def show_snapshot(self):
        print(subprocess.run(['lctl', 'get_param', 'osc.*.max_pages_per_rpc', 'osc.*.max_rpcs_in_flight'], stdout=subprocess.PIPE).stdout.decode('utf-8'))

        self.llite_snapshot.show_snapshot()

        for osc_name in self.osc_names:
            self.osc_snapshots[osc_name].show_snapshot()

    def construct_stats_and_features_list_per_osc(self, llite_params_list, osc_snap, record_dur, obsvn_cnt):
        params_list = []
        params_list = params_list + [obsvn_cnt]

        params_list = params_list + osc_snap.osc_rpc_configuration_current.construct_params_list()

        params_list = params_list + llite_params_list

        params_list = params_list + osc_snap.construct_stats_list()
        params_list = params_list + osc_snap.construct_features_list()

        params_list = params_list + [record_dur]

        return params_list

    def store_params_to_csv(self, result_folder_path, wld_name, record_dur, obsvn_cnt, strtg_type = 1):
        llite_params_list = self.llite_snapshot.construct_params_list()

        for osc_name in self.osc_names:
            osc_stats_features_list = self.construct_stats_and_features_list_per_osc(llite_params_list, self.osc_snapshots[osc_name], record_dur, obsvn_cnt)
            self.osc_snapshots[osc_name].write_stats_and_features_list_to_csv(result_folder_path, wld_name, osc_stats_features_list, strtg_type)
