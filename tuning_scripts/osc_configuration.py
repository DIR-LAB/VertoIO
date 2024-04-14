import config

class OSC_Configuration:
    def __init__(self, osc_name, mppr_value = config.default_mppr_value, mrif_value = config.default_mrif_value, mdm_value = config.default_mdm_value):
        self.osc_name = osc_name
        self.mppr_value = mppr_value
        self.mrif_value = mrif_value
        self.mdm_value = mdm_value

    def __eq__(self, other):
        if not isinstance(other, OSC_Configuration):
            return NotImplemented
        return self.mppr_value == other.mppr_value and self.mrif_value == other.mrif_value and self.mdm_value == other.mdm_value

    def save_configuration_instance(self, other):
        self.mppr_value = other.mppr_value
        self.mrif_value = other.mrif_value
        self.mdm_value = other.mdm_value

    def save_configuration(self, mppr_value, mrif_value, mdm_value):
        self.mppr_value = mppr_value
        self.mrif_value = mrif_value
        self.mdm_value = mdm_value

    def show_configuration(self):
        print('mppr_value:', self.mppr_value)
        print('mrif_value:', self.mrif_value)
        print('mdm_value:', self.mdm_value)

    def construct_params_list(self):
        return [self.mppr_value, self.mrif_value, self.mdm_value]
