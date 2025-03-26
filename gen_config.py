import os
import numpy as np
import multiprocessing

TAP_25D_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_TEMPLATE_DICT = {
    'quadgpu_separate':
"""
[general]
path = %s
placer_granularity = 1
initial_placement = given
decay = 0.8

[interposer]
# we will support passive, active, (photonic), and EMIB options.
intp_type = passive
intp_size = 50
link_type = nppl

[chiplets]
chiplet_count = 4
# center of each chiplet, leave some space (0.1mm is enough) for ubump around the chiplet
x = 9.2, 9.2, 40.8, 40.8
y = 9.2, 40.8, 9.2, 40.8
widths = 	18.2,	18.2,	18.2,	18.2
heights = 	18.2,	18.2,	18.2,	18.2
powers = 	%f,	%f,	%f,	%f

connections = 	0,		128,	128,	128;
				128,	0,		128, 	128;
				128,	128,	0, 		128;
				128,	128, 	128, 	0
"""
}

def calc_gpu_power(freq):
    """
        Calculate the power of GPU given the frequency.
        Assume linear relationship between voltage and frequency during DVFS.
    """
    power = 68.67 * freq ** 3 + 23.83 * freq + 32.5
    return power


def gen_quadgpu_config(config_path, output_path, freq_list):
    """
        Generate the configuration file for quad-gpu system.
        The power of each GPU is calculated based on the frequency.
    """
    power_list = [calc_gpu_power(freq) for freq in freq_list]
    config_str = CONFIG_TEMPLATE_DICT['quadgpu_separate'] % (
        output_path, power_list[0], power_list[1], power_list[2], power_list[3]
    )
    with open(config_path, 'w') as f:
        f.write(config_str)


def main():
    os.makedirs('configs/test', exist_ok=True)
    
    # homogeneous frequency for quad-gpu system
    for freq in np.arange(0.3, 1.6, 0.3):
        freq_list = [freq, freq, freq, freq]
        exp_name = 'quadgpu_separate-f_%.1f-all' % freq
        output_path = os.path.join(TAP_25D_PATH, f'output/{exp_name}/')
        config_path = os.path.join(TAP_25D_PATH, 'configs/test', f'{exp_name}.cfg')
        gen_quadgpu_config(config_path, output_path, freq_list)

    # one hot GPU on the corner
    for freq in np.arange(0.3, 1.6, 0.3):
        freq_list = [freq, 0, 0, 0]
        exp_name = 'quadgpu_separate-f_%.1f-single' % freq
        output_path = os.path.join(TAP_25D_PATH, f'output/{exp_name}/')
        config_path = os.path.join(TAP_25D_PATH, 'configs/test', f'{exp_name}.cfg')
        gen_quadgpu_config(config_path, output_path, freq_list)

    # two hot GPUs on the diagonal
    for freq in np.arange(0.3, 1.6, 0.3):
        freq_list = [freq, 0, 0, freq]
        exp_name = 'quadgpu_separate-f_%.1f-diag' % freq
        output_path = os.path.join(TAP_25D_PATH, f'output/{exp_name}/')
        config_path = os.path.join(TAP_25D_PATH, 'configs/test', f'{exp_name}.cfg')
        gen_quadgpu_config(config_path, output_path, freq_list)

    # ablation study on fine-grained frequency setting
    for i, boost in enumerate([(0,), (0, 1,), (0, 3,), (0, 1, 2,)]):
        freq_list = [1.5 if c in boost else 0.9 for c in range(4)]
        exp_name = 'quadgpu_separate-boost_%d' % i
        output_path = os.path.join(TAP_25D_PATH, f'output/{exp_name}/')
        config_path = os.path.join(TAP_25D_PATH, 'configs/test', f'{exp_name}.cfg')
        gen_quadgpu_config(config_path, output_path, freq_list)

# run all the experiments, and plot the thermal map
def run_experiment(config_file):
    exp_name = config_file[:-4]
    os.system('python config.py -c configs/test/%s' % config_file)
    os.system('python plot_thermalmap.py -d %s' % os.path.join(TAP_25D_PATH, f'output/{exp_name}'))

if __name__ == '__main__':
    main()

    config_files = os.listdir('configs/test')
    with multiprocessing.Pool() as pool:
        pool.map(run_experiment, config_files)
