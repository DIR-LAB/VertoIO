import config
import stat_data
import subprocess

class LLITE_Snapshot:
    def __init__(self):
        self.llite_fs_name = subprocess.run(config.llite_fs_fetch_cmd, stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()[0].split('.')[1]
        self.llite_stats_read_bytes = stat_data.Stat_Data(config.llite_sys_kernel_path + self.llite_fs_name)
        self.llite_stats_write_bytes = stat_data.Stat_Data(config.llite_sys_kernel_path + self.llite_fs_name)
        self.max_ra_issues_to_total_ratio = 0

    def show_snapshot(self):
        print('llite_fs_name: ', self.llite_fs_name)
        print('llite_stats_read_bytes: ')
        self.llite_stats_read_bytes.show_data()
        print('llite_stats_write_bytes: ')
        self.llite_stats_write_bytes.show_data()
        print(self.max_ra_issues_to_total_ratio)

    def construct_params_list(self):
        params_list = []
        params_list = params_list + self.llite_stats_read_bytes.construct_params_list()
        params_list = params_list + self.llite_stats_write_bytes.construct_params_list()
        params_list = params_list + [self.max_ra_issues_to_total_ratio]

        return params_list
