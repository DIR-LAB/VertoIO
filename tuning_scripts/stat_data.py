class Stat_Data:
    def __init__(self, module_name, no_of_samples=0, sample_min=0, sample_max=0, samples_sum=0):
        self.module_name = module_name
        self.no_of_samples = no_of_samples
        self.sample_min = sample_min
        self.sample_max = sample_max
        self.samples_sum = samples_sum

    def save_data(self, no_of_samples, sample_min, sample_max, samples_sum):
        self.no_of_samples = no_of_samples
        self.sample_min = sample_min
        self.sample_max = sample_max
        self.samples_sum = samples_sum

    def is_empty(self):
        return self.no_of_samples == 0

    def get_average(self):
        if self.no_of_samples == 0:
            return 0
        return self.samples_sum / self.no_of_samples

    def show_data(self):
        print('no_of_samples:', self.no_of_samples)
        print('sample_min:', self.sample_min)
        print('sample_max:', self.sample_max)
        print('samples_sum:', self.samples_sum)

    def construct_params_list(self):
        return [self.no_of_samples, self.sample_min, self.sample_max, self.samples_sum]
