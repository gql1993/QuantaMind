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

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.user_components.my_jjrender import add_custom_junction_flipchip
from qiskit_metal.analyses.quantization import EPRanalysis
from qiskit_metal.analyses.quantization import LOManalysis


def eigenmode_draw(design, name, render_qcomps=[], open_terminations=[], port_list=[], render_ignored_jjs=[],
                   x_buffer=0.1, y_buffer=0.1, custom_junction=False):
    """draw the components for the eigenmode in hfss
    Args:
        design (cls): design for the layout
        name (str): name of the design in the project.
        render_qcomps(str list):the components needed to render in the design
        open_terminations (Union[list, None], optional):
            List of tuples of pins that are open. Defaults to None.
        port_list (Union[list, None], optional): List of tuples of pins to be rendered as ports.
            Defaults to None.
        jj_to_port (Union[list, None], optional): List of tuples of jj's to be rendered as
            ports. Defaults to None.
        ignored_jjs (Union[list, None], optional): List of tuples of jj's that shouldn't be
            rendered. Defaults to None.
        box_plus_buffer (bool, optional): Either calculate a bounding box based on the location
            of rendered geometries or use chip size from design class. Defaults to True.

    Returns:
        (cls, cls): class of EPR and simulation render.
    """
    # save input variables to run(). This line must be the first in the method
    eig_qres = EPRanalysis(design, "hfss")
    hfss = eig_qres.sim.renderer
    hfss.start()

    hfss.new_ansys_design(name, 'eigenmode')

    # render_ignored_jjs = [('Q0', 'rect_jj')]

    # Either calculate a bounding box based on the location of
    # rendered geometries or use chip size from design class.
    box_plus_buffer = True

    hfss.options['x_buffer_width_mm'] = x_buffer  # Buffer between max/min x and edge of ground plane, in mm
    hfss.options['y_buffer_width_mm'] = y_buffer  # Buffer between max/min y and edge of ground plane, in mm

    hfss.render_design(selection=render_qcomps,
                       open_pins=open_terminations,
                       port_list=port_list,
                       jj_to_port=[],
                       ignored_jjs=render_ignored_jjs,
                       box_plus_buffer=True)
    if custom_junction:
        add_custom_junction_flipchip(design, hfss)
    return eig_qres, hfss


def eigenmode_analysis(eig_qres, n_modes=2, passes=18, delta_f=0.01, min_freq=2, l=10, c=0):
    hfss = eig_qres.sim.renderer
    pinfo = hfss.pinfo
    setup = hfss.pinfo.setup
    setup.n_modes = n_modes
    setup.passes = passes
    setup.delta_f = delta_f
    setup.min_freq = str(min_freq) + 'GHz'
    pinfo.design.set_variable('Lj', str(l) + 'nH')
    pinfo.design.set_variable('Cj', str(c) + ' fF')
    setup.analyze()
    # sim_freq1 = eig_qres.sim.convergence_f['re(Mode(' + str(1) + ')) [g]'].get(
    #     list(eig_qres.sim.convergence_f['re(Mode(' + str(1) + ')) [g]'].keys())[-1])
    # return sim_freq1


def q3d_simulation(design, name, render_qcomps=[], open_terminations=[], max_passes=18, percent_error=0.01):
    """draw the components for the eigenmode in hfss
    Args:
        design (cls): design for the layout
        name (str): name of the design in the project.
        render_qcomps(str list):the components needed to render in the design
        open_terminations (Union[list, None], optional):
            List of tuples of pins that are open. Defaults to [].

    Returns:
        (cls): simulation analysis class
    """
    # save input variables to run(). This line must be the first in the method
    c1 = LOManalysis(design, "q3d")
    c1.sim.setup.max_passes = max_passes
    c1.sim.setup.percent_error = percent_error
    c1.sim.run(name=name, components=render_qcomps, open_terminations=open_terminations)

    return c1
