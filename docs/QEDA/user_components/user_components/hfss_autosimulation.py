# -*- coding: utf-8 -*-

# This code is customized by Bin Yang
#
# (C) Copyright 量子科技长三角产业创新中心 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import qiskit_metal as metal
from qiskit_metal import designs
from qiskit_metal import MetalGUI, Dict
from qiskit_metal.qlibrary.user_components.my_qcomponent import MyTunableCoupler01, MyTunableCoupler02, \
    MyTunableCoupler03, TransmonCrossRound_v1, TransmonCrossRound_v2
from qiskit_metal.qlibrary.couplers.tunable_coupler_01 import TunableCoupler01
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from collections import OrderedDict
from qiskit_metal.analyses.quantization import EPRanalysis
from qiskit_metal.qlibrary.user_components.save_load import *
from qiskit_metal.analyses.em.cpw_calculations import guided_wavelength
import numpy as np
import tempfile


def find_resonator_length(frequency, line_width, line_gap, N):
    [lambdaG, etfSqrt, q] = guided_wavelength(frequency * 10 ** 9, line_width * 10 ** -6, line_gap * 10 ** -6,
                                              500 * 10 ** -6, 100 * 10 ** -9, 10)
    return lambdaG / N * 10 ** 3


def hfss_grad(design, gui, meander_name, tar_freq, initial_length, convergence_limit=1e-3, mode=1,
              design_name='resonator_freq', render_qcomps=[],open_terminations=[],render_ignored_jjs=[],port_list=[]):
    tar_freq = tar_freq
    total_length = initial_length
    sim_freq = tar_freq + 1e-2
    n = 0
    while abs(sim_freq - tar_freq) > convergence_limit:
        design.components[meander_name].options.total_length = str(total_length) + 'mm'
        gui.rebuild()

        eig_qres = EPRanalysis(design, "hfss")
        hfss = eig_qres.sim.renderer
        hfss.start()
        hfss.new_ansys_design(design_name + str(tar_freq) + 'v' + str(n), 'eigenmode')
        render_qcomps = render_qcomps
        open_terminations = open_terminations
        render_ignored_jjs = render_ignored_jjs
        box_plus_buffer = True
        # eig_qres.setup.junctions.jj.rect = 'JJ_rect_Lj_'+str(qubit_name)+'_rect_jj'
        # eig_qres.setup.junctions.jj.line = 'JJ_Lj_'+str(qubit_name)+'_rect_jj_'

        hfss.render_design(selection=render_qcomps,
                           open_pins=open_terminations,
                           # port_list=[(tee_name, 'prime_start', 50), (tee_name, 'prime_end', 50)],
                           port_list=port_list,
                           jj_to_port=[],
                           ignored_jjs=render_ignored_jjs,
                           box_plus_buffer=True)

        pinfo = hfss.pinfo
        setup = hfss.pinfo.setup
        setup.n_modes = 2
        setup.passes = 17
        setup.delta_f = 0.01
        setup.min_freq = '2GHz'
        setup.analyze()

        eig_qres.sim.convergence_t, eig_qres.sim.convergence_f, _ = hfss.get_convergences()
        sim_freq1 = eig_qres.sim.convergence_f['re(Mode(' + str(1) + ')) [g]'].get(
            list(eig_qres.sim.convergence_f['re(Mode(' + str(1) + ')) [g]'].keys())[-1])
        sim_freq2 = eig_qres.sim.convergence_f['re(Mode(' + str(2) + ')) [g]'].get(
            list(eig_qres.sim.convergence_f['re(Mode(' + str(2) + ')) [g]'].keys())[-1])
        solutions = setup.get_solutions()
        fn = tempfile.mktemp()
        solutions._solutions.ExportEigenmodes(solutions.parent.solution_name, "", fn)
        data = np.genfromtxt(fn, dtype='str')
        if mode == 1:
            if float(data[0][5]) > float(data[1][5]) and sim_freq2 < 10:
                sim_freq = sim_freq2
            else:
                sim_freq = sim_freq1
        else:
            if float(data[0][5]) > float(data[1][5]):
                sim_freq = sim_freq1
            else:
                sim_freq = sim_freq2

        words = f"{n}th cycle is  complete, the lowest frequency is {sim_freq},the total length is {total_length}\n"
        print(words)
        folder_name = 'data'
        if not os.path.exists(folder_name):
            # Create the folder if it does not exist
            os.makedirs(folder_name)
            print(f"Folder '{folder_name}' created.")
        with open('data/'+design_name + str(tar_freq) + '.txt', "w") as file:
            # Write the words to the file
            file.write(words)
        tar_length = find_resonator_length(frequency=sim_freq, line_width=10, line_gap=5, N=4)
        tar_length1 = find_resonator_length(frequency=sim_freq - 1e-3, line_width=10, line_gap=5, N=4)
        if abs(tar_freq - sim_freq) < 0.01:
            l_r = 0.5
        else:
            l_r = 1
        grad = l_r * (tar_length - tar_length1) / 1e-3
        delta_length = grad * (tar_freq - sim_freq)
        original_length = total_length
        total_length = total_length + delta_length
        n = n + 1
    return original_length



def hfss_simulation_worker(layout_func, json_file_path, meander_name, tar_freq, initial_length, convergence_limit=1e-3,
                           mode=1, design_name='resonator_freq', render_qcomps=[], open_terminations=[],
                           render_ignored_jjs=[], port_list=[], l_N=2):
    os.makedirs('log', exist_ok=True)
    try:
        log_file_path = f'log/simulation_results{tar_freq}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler()
            ]
        )
        logging.info(json_file_path)
        logging.info(f"Task for hfss_simulation_work: Starting simulation")

        # 在子进程中重新初始化 design 和 gui
        # design, gui = reinitialize_design_and_gui(json_file_path)
        design, gui = layout_func(json_file_path)
        total_length = initial_length
        sim_freq = tar_freq + 1e-2  # 初始仿真频率，略高于目标频率
        n = 0
        while abs(sim_freq - tar_freq) > convergence_limit:
            logging.info(f"Task for tar_freq {tar_freq}: Starting iteration {n}")

            # 更新meander组件的总长度
            if meander_name in design.components:
                design.components[meander_name].options.total_length = str(total_length) + 'mm'
                gui.rebuild()
            else:
                logging.warning(f"Meander component '{meander_name}' not found in design.")
                break
            time.sleep(random.randint(1, 10))
            # 执行HFSS仿真
            eig_qres = EPRanalysis(design, "hfss")
            hfss = eig_qres.sim.renderer
            hfss.start()
            hfss.new_ansys_design(design_name + str(tar_freq) + 'v' + str(n), 'eigenmode')
            render_qcomps = render_qcomps
            open_terminations = open_terminations
            render_ignored_jjs = render_ignored_jjs
            box_plus_buffer = True

            hfss.render_design(selection=render_qcomps,
                               open_pins=open_terminations,
                               port_list=port_list,
                               jj_to_port=[],
                               ignored_jjs=render_ignored_jjs,
                               box_plus_buffer=True)
            logging.info(f"Rendered design for tar_freq {tar_freq}")

            pinfo = hfss.pinfo
            setup = hfss.pinfo.setup
            # setup.n_modes = 4  #腔较多时使用，如4
            setup.n_modes = 2
            setup.passes = 5
            setup.delta_f = 0.01
            setup.min_freq = '5GHz'
            setup.analyze()
            logging.info(f"Setup analysis for tar_freq {tar_freq}")

            # 获取仿真结果
            eig_qres.sim.convergence_t, eig_qres.sim.convergence_f, _ = hfss.get_convergences()
            sim_freq_list = []
            # for i in range(1, 5): 腔较多时使用，如4
            for i in range(1, 3):
                key = f're(Mode({i})) [g]'
                freq = eig_qres.sim.convergence_f[key].get(list(eig_qres.sim.convergence_f[key].keys())[-1])
                sim_freq_list.append(freq)
            logging.info(f"Task for tar_freq {tar_freq}: sim_freq_list {sim_freq_list}")

            # 处理仿真数据以找到最低频率
            solutions = setup.get_solutions()
            fn = tempfile.mktemp()
            solutions._solutions.ExportEigenmodes(solutions.parent.solution_name, "", fn)
            data = np.genfromtxt(fn, dtype='str')
            # logging.info(f"Task for tar_freq {tar_freq}: data {data[0][5], data[1][5], data[2][5], data[3][5]}") # 腔较多时使用，如4
            logging.info(f"Task for tar_freq {tar_freq}: data {data[0][5], data[1][5]}")
            # values = [float(data[i][5]) for i in range(4)]   腔较多时使用，如4
            values = [float(data[i][5]) for i in range(2)]
            logging.info(f"Task for tar_freq {tar_freq}: values {values}")

            sorted_float_data = sorted(values)
            min1, min2 = sorted_float_data[0], sorted_float_data[1]
            logging.info(f"Task for tar_freq {tar_freq}: min1 {min1}, min2 {min2}")

            # sim_freq1 = next((sim_freq_list[i] for i in range(4) if float(data[i][5]) == min1), None)
            # sim_freq2 = next((sim_freq_list[i] for i in range(4) if float(data[i][5]) == min2), None) # 腔较多时使用，如4
            sim_freq1 = next((sim_freq_list[i] for i in range(2) if float(data[i][5]) == min1), None)
            sim_freq2 = next((sim_freq_list[i] for i in range(2) if float(data[i][5]) == min2), None)
            logging.info(f"Task for tar_freq {tar_freq}: sim_freq1 {sim_freq1}, sim_freq2 {sim_freq2}")
            if min2 / min1 > 1:
                sim_freq = sim_freq1
            elif mode == 1:
                if float(sim_freq1) < float(sim_freq2):
                    sim_freq = sim_freq1
                else:
                    sim_freq = sim_freq2
            else:
                if float(sim_freq1) > float(sim_freq2):
                    sim_freq = sim_freq1
                else:
                    sim_freq = sim_freq2

            # 更新设计参数
            words = f"{n}th cycle is complete, the lowest frequency is {sim_freq}, the total length is {total_length}\n"
            logging.info(f"Task for tar_freq {tar_freq}: {words}")
            # 使用独立的文件名，避免资源竞争
            result_file_path = f'data/{design_name}_{tar_freq}.txt'
            with open(result_file_path, "w") as file:
                file.write(words)

            # 计算新的总长度
            tar_length = find_resonator_length(frequency=sim_freq, line_width=10, line_gap=5, N=l_N)
            tar_length1 = find_resonator_length(frequency=sim_freq - 1e-3, line_width=10, line_gap=5, N=l_N)
            if abs(tar_freq - sim_freq) < 0.01:
                l_r = 0.5
            else:
                l_r = 1
            grad = l_r * (tar_length - tar_length1) / 1e-3
            delta_length = grad * (tar_freq - sim_freq)
            original_length = total_length
            total_length = total_length + delta_length
            n = n + 1

        logging.info(f"Task for tar_freq {tar_freq}: Convergence achieved. Final total length {total_length}")
        eig_qres.sim.close()
        return tar_freq, original_length
    except Exception as e:
        logging.error(f"Task for tar_freq {tar_freq} failed: {str(e)}")
        eig_qres.sim.close()
        return tar_freq, None


# def find_resonator_length(frequency, line_width, line_gap, N):
#     [lambdaG, etfSqrt, q] = guided_wavelength(frequency * 10 ** 9, line_width * 10 ** -6, line_gap * 10 ** -6,
#                                               500 * 10 ** -6, 100 * 10 ** -9, 10)
#     return lambdaG / N * 10 ** 3


# 并行谐振腔仿真
def eigenmode_parallel_simulation(layout_func, json_file_path, tar_freqs, initial_lengths, convergence_limit=1e-3,
                                  mode=1,
                                  design_name='resonator_freq', render_qcomps=[], open_terminations=[],
                                  render_ignored_jjs=[],
                                  port_list=[], meander_name=[], l_N=2, num_workers=4):
    args_list = []
    i = 0
    for jfp in json_file_path:
        args = (
            layout_func, jfp, meander_name[i], tar_freqs[i], initial_lengths[i], convergence_limit, mode, design_name,
            render_qcomps[i],
            open_terminations, render_ignored_jjs, port_list[i], l_N
        )
        logging.info(f"Task for hfss_simulation_work: {i}")
        i = i + 1
        args_list.append(args)

    print(args_list)

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for args in args_list:
            logging.info(f"Submitting task with arguments: {args}")
            futures.append(executor.submit(hfss_simulation_worker, *args))
            print(futures)
            time.sleep(10)

        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
                    logging.info(f"Task completed successfully with result: {result}")
                else:
                    logging.warning("Task returned None result.")
            except Exception as e:
                logging.error(f"Task raised an exception: {e}")

    logging.info(f"Total number of completed tasks: {len(results)}")
    return results