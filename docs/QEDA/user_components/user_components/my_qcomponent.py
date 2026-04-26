# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit
from qiskit_metal.toolbox_metal import math_and_overrides
from qiskit_metal.qlibrary.core import QComponent
from qiskit_metal.draw import LineString
from qiskit_metal.qlibrary.core.qroute import QRouteLead, QRoutePoint, QRoute
from shapely.geometry import CAP_STYLE, JOIN_STYLE
from qiskit_metal.qlibrary.user_components.cpw import generate_cpw_from_line
import math
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from ... import config

if not config.is_building_docs():
    from qiskit_metal import is_true


class MyQComponent(QComponent):
    """
    This class is a template
	Use this class as a blueprint to put together for your components - have fun
    
    .. meta::
        My QComponent

    """

    # Edit these to define your own template options for creation
    # Default drawing options
    default_options = Dict(width='500um', height='300um')
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='component')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # EDIT HERE - Replace the following with your code
        # Create some raw geometry
        # Use autocompletion for the `draw.` module (use tab key)
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.orientation)
        geom = {'my_polygon': rect}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)


class TransmonPocketRoundTeeth(BaseQubit):
    """Transmon pocket with 'Teeth' connection pads.

    Inherits `BaseQubit` class

    Description:
        Create a standard pocket transmon qubit for a ground plane with teeth
        Here we use the 'Teeth' shape which ones connected to the top pad and one connection pad.

    Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')

    Pocket:
        * pad_gap            - the distance between the two charge islands, which is also the
          resulting 'length' of the pseudo junction
        * inductor_width     - width of the pseudo junction between the two charge islands
          (if in doubt, make the same as pad_gap). Really just for simulating
          in HFSS / other EM software
        * pad_width          - the width (x-axis) of the charge island pads, except the circle radius from both sides
        * pad_height         - the size (y-axis) of the charge island pads
        * pocket_width       - size of the pocket (cut out in ground) along x-axis
        * pocket_height      - size of the pocket (cut out in ground) along y-axis
        * coupled_pad_gap    - the distance between the two teeth shape
        * coupled_pad_width  - the width (x-axis) of the teeth shape on the island pads
        * coupled_pad_height - the size (y-axis) of the teeth shape on the island pads


    Connector lines:
        * pad_gap        - space between the connector pad and the charge island it is
          nearest to
        * pad_width      - width (x-axis) of the connector pad
        * pad_height     - height (y-axis) of the connector pad
        * pad_cpw_shift  - shift the connector pad cpw line by this much away from qubit
        * pad_cpw_extent - how long should the pad be - edge that is parallel to pocket
        * cpw_width      - center trace width of the CPW line
        * cpw_gap        - dielectric gap width of the CPW line
        * cpw_extend     - depth the connector line extends into ground (past the pocket edge)
        * pocket_extent  - How deep into the pocket should we penetrate with the cpw connector
          (into the ground plane)
        * pocket_rise    - How far up or down relative to the center of the transmon should we
          elevate the cpw connection point on the ground plane
        * loc_W / H      - which 'quadrant' of the pocket the connector is set to, +/- 1 (check
          if diagram is correct)


    Sketch:
        Below is a sketch of the qubit
        ::

                 +1              0             +1
                _________________________________
            -1  |                |               |  +1      Y
                |           | | |_| | |          |          ^
                |        ___| |_____| |____      |          |
                |       /     island       \     |          |----->  X
                |       \__________________/     |
                |                |               |
                |  pocket        x               |
                |        ________|_________      |
                |       /                  \     |
                |       \__________________/     |
                |                                |
                |                                |
            -1  |________________________________|   +1

                 -1                            -1

    .. image::
        transmon_pocket_teeth.png

    .. meta::
        Transmon Pocket Teeth

    """

    # _img = 'transmon_pocket1.png'

    # Default drawing options
    default_options = Dict(
        pad_gap='30um',
        inductor_width='30um',
        pad_width='400um',
        pad_height='90um',
        pad_fillet='10um',
        pocket_width='650um',
        pocket_height='650um',
        pocket_fillet='10um',
        line_pad_width='4um',
        line_pad_height='40um',
        line_pad_fillet='1um',
        # coupled_pad belongs to the teeth part. Teeth will have same height/width and are symmetric.
        coupled_pad_height='150um',
        coupled_pad_width='20um',
        coupled_pad_gap='50um',  # One can arrange the gap between the teeth.
        # orientation = 90 has dipole aligned along the +X axis, while 0 aligns to the +Y axis

        _default_connection_pads=Dict(
            pad_gap='15um',
            pad_width='20um',
            pad_height='150um',
            pad_cpw_shift='0um',
            pad_cpw_extent='25um',
            cpw_width='10um',
            cpw_gap='6um',
            # : cpw_extend: how far into the ground to extend the CPW line from the coupling pads
            cpw_extend='100um',
            pocket_extent='5um',
            pocket_rise='0um',
            loc_W='+1',  # width location  only +-1 or 0,
            loc_H='+1',  # height location  only +-1 or 0
        ))
    """Default drawing options"""

    component_metadata = Dict(short_name='Pocket',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Transmon pocket with teeth pads."""

    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """Define the way the options are turned into QGeometry.

        The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed
        information, such as layer, subtract, etc.
        """
        self.make_pocket()
        self.make_connection_pads()

    def make_pocket(self):
        """Makes standard transmon in a pocket."""

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        #  pcop = self.p.coupled_pads[name]  # parser on connector options

        # since we will reuse these options, parse them once and define them as variables
        pad_width = p.pad_width
        pad_height = p.pad_height
        pad_gap = p.pad_gap
        coupled_pad_height = p.coupled_pad_height
        coupled_pad_width = p.coupled_pad_width
        coupled_pad_gap = p.coupled_pad_gap
        pocket_radius = p.pocket_fillet
        line_pad_width = p.line_pad_width
        line_pad_height = p.line_pad_height
        line_pad_fillet = p.line_pad_fillet

        # make the pads as rectangles (shapely polygons)
        pad = draw.rectangle(pad_width, pad_height)

        pad_top = draw.translate(pad, 0, +(pad_height + pad_gap) / 2.)
        # Here, you make your pads round. Not sharp shape on the left and right sides and also this should be the
        # same for the bottom pad as the top pad.
        circ_left_top = draw.Point(-pad_width / 2., +(pad_height + pad_gap) /
                                   2.).buffer(pad_height / 2,
                                              resolution=16,
                                              cap_style=CAP_STYLE.round)
        circ_right_top = draw.Point(pad_width / 2., +(pad_height + pad_gap) /
                                    2.).buffer(pad_height / 2,
                                               resolution=16,
                                               cap_style=CAP_STYLE.round)
        # In here you create the teeth part and then you union them as one with the pad. Teeth only belong to top pad.
        coupled_pad = draw.rectangle(coupled_pad_width,
                                     coupled_pad_height + pad_height)
        coupler_pad_round = draw.Point(0., (coupled_pad_height + pad_height) /
                                       2).buffer(coupled_pad_width / 2,
                                                 resolution=16,
                                                 cap_style=CAP_STYLE.round)
        coupled_pad = draw.union(coupled_pad, coupler_pad_round)
        coupled_pad_left = draw.translate(
            coupled_pad, -(coupled_pad_width / 2. + coupled_pad_gap / 2.),
            +coupled_pad_height / 2. + pad_height + pad_gap / 2. -
            pad_height / 2)
        coupled_pad_right = draw.translate(
            coupled_pad, (coupled_pad_width / 2. + coupled_pad_gap / 2.),
            +coupled_pad_height / 2. + pad_height + pad_gap / 2. -
            pad_height / 2)
        pad_top_tmp = draw.union([circ_left_top, pad_top, circ_right_top])
        # The coupler pads are only created if low_W=0 and low_H=+1
        for name in self.options.connection_pads:
            if self.options.connection_pads[name][
                'loc_W'] == 0 and self.options.connection_pads[name][
                'loc_H'] == +1:
                pad_top_tmp = draw.union([
                    circ_left_top, coupled_pad_left, pad_top, coupled_pad_right,
                    circ_right_top
                ])
        pad_top_tmp = self.round_corner(p.pad_fillet, pad_top_tmp)
        line_pad_top = draw.rectangle(line_pad_width, line_pad_height, xoff=0, yoff=line_pad_height / 2 + line_pad_fillet)
        line_pad_top = self.round_corner(line_pad_fillet, line_pad_top)
        pad_top_tmp = draw.union(pad_top_tmp, line_pad_top)
        pad_top = pad_top_tmp
        # Round part for the bottom pad. And again you should unite all of them.
        pad_bot = draw.translate(pad, 0, -(pad_height + pad_gap) / 2.)
        line_pad_bot = draw.rectangle(line_pad_width, line_pad_height-0.007, xoff=0.01, yoff=-0.007-(line_pad_height-0.007) / 2 - line_pad_fillet)
        line_pad_bot = self.round_corner(line_pad_fillet, line_pad_bot)
        pad_bot = draw.union(pad_bot, line_pad_bot)

        circ_left_bot = draw.Point(-pad_width / 2, -(pad_height + pad_gap) /
                                   2.).buffer(pad_height / 2,
                                              resolution=16,
                                              cap_style=CAP_STYLE.round)
        circ_right_bot = draw.Point(pad_width / 2, -(pad_height + pad_gap) /
                                    2.).buffer(pad_height / 2,
                                               resolution=16,
                                               cap_style=CAP_STYLE.round)
        pad_bot = draw.union([pad_bot, circ_left_bot, circ_right_bot])

        rect_jj = draw.LineString([(0, -pad_gap / 2), (0, +pad_gap / 2)])
        # the draw.rectangle representing the josephson junction
        # rect_jj = draw.rectangle(p.inductor_width, pad_gap)

        rect_pk = draw.rectangle(p.pocket_width, p.pocket_height)
        rect_pk = self.round_corner(pocket_radius, rect_pk)

        # Rotate and translate all qgeometry as needed.
        # Done with utility functions in Metal 'draw_utility' for easy rotation/translation
        # NOTE: Should modify so rotate/translate accepts qgeometry, would allow for
        # smoother implementation.
        polys = [rect_jj, pad_top, pad_bot, rect_pk]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [rect_jj, pad_top, pad_bot, rect_pk] = polys

        # Use the geometry to create Metal qgeometry
        self.add_qgeometry('poly', dict(pad_top=pad_top, pad_bot=pad_bot))
        self.add_qgeometry('poly', dict(rect_pk=rect_pk), subtract=True)
        # self.add_qgeometry('poly', dict(
        #     rect_jj=rect_jj), helper=True)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=p.inductor_width)

    def make_connection_pads(self):
        """Makes standard transmon in a pocket."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes n individual connector.

        Args:
            name (str) : Name of the connector
        """

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        pc = self.p.connection_pads[name]  # parser on connector options

        # define commonly used variables once
        cpw_width = pc.cpw_width
        cpw_extend = pc.cpw_extend
        pad_width = pc.pad_width
        pad_height = pc.pad_height
        pad_cpw_shift = pc.pad_cpw_shift
        pocket_rise = pc.pocket_rise
        pocket_extent = pc.pocket_extent

        loc_W = float(pc.loc_W)
        loc_W, loc_H = float(pc.loc_W), float(pc.loc_H)
        if float(loc_W) not in [-1., +1., 0] or float(loc_H) not in [-1., +1.]:
            self.logger.info(
                'Warning: Did you mean to define a transmon qubit with loc_W and'
                ' loc_H that are not +1, -1, or 0? Are you sure you want to do this?'
            )

        # Define the geometry
        # Connector pad

        if float(loc_W) != 0:
            connector_pad = draw.rectangle(pad_width, pad_height,
                                           -pad_width / 2, pad_height / 2)
            # Connector CPW wire
            connector_wire_path = draw.wkt.loads(f"""LINESTRING (\
                0 {pad_cpw_shift + cpw_width / 2}, \
                {pc.pad_cpw_extent}                           {pad_cpw_shift + cpw_width / 2}, \
                {(p.pocket_width - p.pad_width) / 2 - pocket_extent} {pad_cpw_shift + cpw_width / 2 + pocket_rise}, \
                {(p.pocket_width - p.pad_width) / 2 + cpw_extend}    {pad_cpw_shift + cpw_width / 2 + pocket_rise}\
                                            )""")
        else:
            connector_pad = draw.rectangle(pad_width, pad_height, 0,
                                           pad_height / 2)
            connector_pad = self.round_corner(0.002, connector_pad)
            connector_wire_path = draw.LineString(
                [[0, pad_height],
                 [
                     0,
                     (p.pocket_height / 2 - p.pad_height - p.pad_gap / 2 -
                      pc.pad_gap) + cpw_extend
                 ]])

        # Position the connector, rotate and translate
        objects = [connector_pad, connector_wire_path]

        if loc_W == 0:
            loc_Woff = 1
        else:
            loc_Woff = loc_W

        objects = draw.scale(objects, loc_Woff, loc_H, origin=(0, 0))
        objects = draw.translate(
            objects,
            loc_W * (p.pad_width) / 2.,
            loc_H * (p.pad_height + p.pad_gap / 2 + pc.pad_gap))
        objects = draw.rotate_position(objects, p.orientation,
                                       [p.pos_x, p.pos_y])
        [connector_pad, connector_wire_path] = objects

        self.add_qgeometry('poly', {f'{name}_connector_pad': connector_pad})
        self.add_qgeometry('path', {f'{name}_wire': connector_wire_path},
                           width=cpw_width)
        self.add_qgeometry('path', {f'{name}_wire_sub': connector_wire_path},
                           width=cpw_width + 2 * pc.cpw_gap,
                           subtract=True)

        ############################################################

        # add pins
        points = np.array(connector_wire_path.coords)
        self.add_pin(name,
                     points=points[-2:],
                     width=cpw_width,
                     input_as_norm=True)


class TransmonCrossRound(BaseQubit):
    default_options = Dict(
        cross_width='16um',
        cross_length='136um',
        cross_gap='16um',
        radius='10um',
        rect_width='16um',
        rect_height='32um',
        jj_pad_width='8um',
        jj_pad_height='6um',
        jj_etch_length='4um',
        jj_etch_pad1_width='2um',
        jj_etch_pad2_width='5um',
        jj_pad2_height='8um',
        chip='main',
        _default_connection_pads=Dict(
            connector_type='0',  # 0 = Claw type, 1 = gap type
            claw_length='30um',
            ground_spacing='5um',
            claw_width='10um',
            claw_gap='6um',
            connector_location=
            '0'  # 0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
        ))
    """Default options."""

    component_metadata = Dict(short_name='CrossRound',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Simple Metal Transmon Cross with round corner."""

    ##############################################MAKE######################################################
    # define fillet radius
    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_pocket()
        self.make_connection_pads()

    ###################################TRANSMON#############################################################

    def make_pocket(self):
        """Makes a basic Crossmon, 4 arm cross."""

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap
        radius = p.radius
        rect_width = p.rect_width
        rect_height = p.rect_height
        jj_pad_width = p.jj_pad_width
        jj_pad_height = p.jj_pad_height
        jj_etch_length = p.jj_etch_length
        jj_etch_pad1_width = p.jj_etch_pad1_width
        jj_etch_pad2_width = p.jj_etch_pad2_width
        jj_pad2_height = p.jj_pad2_height

        # access to chip name
        chip = p.chip

        # Creates the cross and the etch equivalent.
        cross_line = draw.unary_union([
            draw.LineString([(0, cross_length), (0, -cross_length)]),
            draw.LineString([(cross_length, 0), (-cross_length, 0)])
        ])

        cross = cross_line.buffer(cross_width / 2, cap_style=2)

        rect1 = draw.rectangle(rect_width, rect_height, -cross_length - rect_width / 2.0, 0)
        rect2 = draw.rectangle(rect_width, rect_height, cross_length + rect_width / 2.0, 0)

        cross = draw.unary_union([cross, rect1, rect2])

        cross_etch = cross.buffer(cross_gap, cap_style=2, join_style=2)

        cross = self.round_corner(radius, cross)
        cross_etch = self.round_corner(2 * radius, cross_etch)

        # draw junction pad part

        jj_pad = draw.rectangle(jj_pad_width, jj_pad_height, 0, -cross_length - jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(jj_etch_pad1_width, jj_etch_length / 2, 0,
                                      -cross_length - jj_pad_height + jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(jj_etch_pad2_width, jj_etch_length / 2, 0,
                                      -cross_length - jj_pad_height + jj_etch_length * 0.75)

        jj_etch_pad = draw.unary_union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)

        cross = draw.unary_union([cross, jj_pad])

        jj_pad2 = draw.rectangle(jj_etch_pad1_width, jj_pad2_height,
                                 -(cross_width / 8 + cross_gap / 4 + jj_etch_pad1_width / 2),
                                 -cross_length - cross_gap + jj_pad2_height / 2)
        jj_top_pad2 = draw.rectangle(jj_etch_pad1_width + 1e-3, jj_etch_pad1_width,
                                     -(cross_width / 8 + cross_gap / 4 + (jj_etch_pad1_width + 1e-3) / 2),
                                     -cross_length - cross_gap + jj_pad2_height - jj_etch_pad1_width / 2)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])

        cross_etch = draw.subtract(cross_etch, jj_pad2)

        # The junction/SQUID
        # rect_jj = draw.rectangle(cross_width, cross_gap)
        # rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)
        rect_jj = draw.LineString([(0, -cross_length),
                                   (0, -cross_length - cross_gap)])

        # rotate and translate
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross, cross_etch, rect_jj] = polys

        # generate qgeometry
        self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        self.add_qgeometry('poly',
                           dict(cross_etch=cross_etch),
                           subtract=True,
                           chip=chip)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=cross_width,
                           chip=chip)

    ############################CONNECTORS##################################################################################################

    def make_connection_pads(self):
        """Goes through connector pads and makes each one."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes individual connector pad.

        Args:
            name (str) : Name of the connector pad
        """

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap
        radius = p.radius

        # access to chip name
        chip = p.chip

        pc = self.p.connection_pads[name]  # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        g_s = pc.ground_spacing
        con_loc = pc.connector_location

        claw_cpw = draw.box(0, -c_w / 2, -4 * c_w, c_w / 2)

        if pc.connector_type == 0:  # Claw connector
            t_claw_height = 2 * c_g + 2 * c_w + 2 * g_s + \
                            2 * cross_gap + cross_width  # temp value

            claw_base = draw.box(-c_w, -(t_claw_height) / 2, c_l,
                                 t_claw_height / 2)
            claw_subtract = draw.box(0, -t_claw_height / 2 + c_w, c_l,
                                     t_claw_height / 2 - c_w)
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.shapely.ops.unary_union([claw_base, claw_cpw])
            connector_etcher = draw.buffer(connector_arm, c_g)
        else:
            connector_arm = claw_cpw
            connector_etcher = draw.buffer(connector_arm, c_g)

        connector_arm = self.round_corner(radius, connector_arm)
        # connector_etcher = self.round_corner(radius,connector_etcher)

        # revise the end from round into flat
        revised_rect = draw.rectangle(c_w / 4, c_w, -4 * c_w + c_w / 8, 0)
        connector_arm = draw.unary_union([connector_arm, revised_rect])
        connector_etcher = draw.buffer(connector_arm, c_g)

        # Making the pin for  tracking (for easy connect functions).
        # Done here so as to have the same translations and rotations as the connector. Could
        # extract from the connector later, but since allowing different connector types,
        # this seems more straightforward.
        port_line = draw.LineString([(-4 * c_w, -c_w / 2), (-4 * c_w, c_w / 2)])

        claw_rotate = 0
        if con_loc > 135:
            claw_rotate = 180
        elif con_loc > 45:
            claw_rotate = -90

        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        polys = draw.translate(polys, -(cross_length + cross_gap + g_s + c_g),
                               0)
        polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        # Generates qgeometry for the connector pads
        self.add_qgeometry('poly', {f'{name}_connector_arm': connector_arm},
                           chip=chip)
        self.add_qgeometry('poly',
                           {f'{name}_connector_etcher': connector_etcher},
                           subtract=True,
                           chip=chip)

        self.add_pin(name, port_line.coords, c_w)


class TransmonCrossRound_v1(BaseQubit):
    """
    Description:
        A revised xmon based on TransmonCrossRound for simulation purpose, should have some bugs
    """
    default_options = Dict(
        cross_width='16um',
        cross_length='138um',
        cross_length1='170um',
        cross_length2='162um',
        cross_gap='16um',
        cross_gap2='18um',
        radius='1um',
        rect_width='16um',
        rect_height='0um',
        jj_pad_width='8um',
        jj_pad_height='6um',
        jj_etch_length='4um',
        jj_etch_pad1_width='2um',
        jj_etch_pad2_width='5um',
        jj_pad2_height='8um',
        chip='main',
        _default_connection_pads=Dict(
            connector_type='0',  # 0 = Claw type, 1 = gap type
            claw_length='60um',
            ground_spacing='3um',
            claw_width='8um',
            claw_gap='4um',
            coupling_width='20um',
            coupling_gap='5um',
            coupling_top_width='10um',
            xyline_location='0',  # 0 => 'up_left' , 1 => 'up_right' , 2 => 'down_left' ,3 = 'down_right'
            zline_direction='0',  # 0 => 'left', 1 => 'right'
            connector_location=
            '0'  # 0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
        ))
    """Default options."""

    component_metadata = Dict(short_name='TransmonCrossRound_v1',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Simple Metal Transmon Cross with round corner."""

    ##############################################MAKE######################################################
    # define fillet radius
    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_pocket()
        self.make_connection_pads()

    ###################################TRANSMON#############################################################

    def make_pocket(self):
        """Makes a basic Crossmon, 4 arm cross."""

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap
        radius = p.radius
        rect_width = p.rect_width
        rect_height = p.rect_height
        jj_pad_width = p.jj_pad_width
        jj_pad_height = p.jj_pad_height
        jj_etch_length = p.jj_etch_length
        jj_etch_pad1_width = p.jj_etch_pad1_width
        jj_etch_pad2_width = p.jj_etch_pad2_width
        jj_pad2_height = p.jj_pad2_height
        # cross_length1 = cross_length+0.032
        # cross_length2 = cross_length+0.024
        # cross_gap2 = cross_gap+0.002
        cross_length1 = p.cross_length1
        cross_length2 = p.cross_length2
        cross_gap2 = p.cross_gap2

        # access to chip name
        chip = p.chip

        # Creates the cross and the etch equivalent.
        cross_line = draw.unary_union([
            draw.LineString([(0, cross_length1), (0, -cross_length2)]),
            draw.LineString([(cross_length, 0), (-cross_length, 0)])
        ])

        cross = cross_line.buffer(cross_width / 2, cap_style=2)

        rect1 = draw.rectangle(rect_width, rect_height, -cross_length - rect_width / 2.0, 0)
        rect2 = draw.rectangle(rect_width, rect_height, cross_length + rect_width / 2.0, 0)

        cross = draw.unary_union([cross, rect1, rect2])

        cross_etch = cross.buffer(cross_gap, cap_style=2, join_style=2)

        # revision
        rect_etch1 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    cross_length + rect_width + 0.75 * cross_gap, 0)
        rect_etch2 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    -(cross_length + rect_width + 0.75 * cross_gap), 0)
        rect_plus = draw.rectangle(cross_gap * 2 + cross_width, cross_gap2 - cross_gap, 0,
                                   -cross_length2 - cross_gap - (cross_gap2 - cross_gap) / 2)
        rect_etch = draw.unary_union([rect_etch1, rect_etch2])
        cross_etch = draw.subtract(cross_etch, rect_etch)
        cross_etch = draw.unary_union([cross_etch, rect_plus])

        # corner rounding (fillet)
        cross = self.round_corner(radius, cross)
        cross_etch = self.round_corner(2 * radius, cross_etch)

        # draw junction pad part

        jj_pad = draw.rectangle(jj_pad_width, jj_pad_height, 0, -cross_length2 - jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(jj_etch_pad1_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(jj_etch_pad2_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length * 0.75)

        jj_etch_pad = draw.unary_union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)

        cross = draw.unary_union([cross, jj_pad])

        jj_pad2 = draw.rectangle(jj_etch_pad1_width, jj_pad2_height,
                                 -(cross_width / 8 + cross_gap / 4 + jj_etch_pad1_width / 2),
                                 -cross_length2 - cross_gap2 + jj_pad2_height / 2)
        jj_top_pad2 = draw.rectangle(jj_etch_pad1_width + 1e-3, jj_etch_pad1_width,
                                     -(cross_width / 8 + cross_gap / 4 + (jj_etch_pad1_width + 1e-3) / 2),
                                     -cross_length2 - cross_gap2 + jj_pad2_height - jj_etch_pad1_width / 2)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])

        cross_etch = draw.subtract(cross_etch, jj_pad2)

        # The junction/SQUID
        # rect_jj = draw.rectangle(cross_width, cross_gap)
        # rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)
        rect_jj = draw.LineString([(0, -cross_length2 - jj_pad_height), (0, -cross_length2 - cross_gap2)
                                   ])

        # rotate and translate
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross, cross_etch, rect_jj] = polys

        # generate qgeometry
        self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        self.add_qgeometry('poly',
                           dict(cross_etch=cross_etch),
                           subtract=True,
                           chip=chip)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=jj_pad_width,
                           chip=chip)

    ############################CONNECTORS##################################################################################################

    def make_connection_pads(self):
        """Goes through connector pads and makes each one."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes individual connector pad.

        Args:
            name (str) : Name of the connector pad
        """

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_length1 = p.cross_length1
        cross_length2 = p.cross_length2
        cross_gap = p.cross_gap
        cross_gap2 = p.cross_gap2
        radius = p.radius

        # access to chip name
        chip = p.chip

        pc = self.p.connection_pads[name]  # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        g_s = pc.ground_spacing
        con_loc = pc.connector_location
        xy_loc = pc.xyline_location
        c_w1 = pc.coupling_width
        c_g1 = pc.coupling_gap
        c_w2 = pc.coupling_top_width
        direction = pc.zline_direction

        claw_cpw = draw.box(0, -c_w / 2, -4 * c_w, c_w / 2)

        if pc.connector_type == 0:  # Claw connector
            t_claw_height = 2 * c_g1 + 2 * c_w1 + 2 * g_s + \
                            2 * cross_gap + cross_width  # temp value

            claw_base = draw.box(-c_w2, -(t_claw_height) / 2, c_l,
                                 t_claw_height / 2)
            claw_subtract = draw.box(0, -t_claw_height / 2 + c_w1, c_l,
                                     t_claw_height / 2 - c_w1)
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.unary_union([claw_base, claw_cpw])

            connector_etcher = draw.buffer(claw_base, c_g1)
            # connector_rect_etch = draw.rectangle(0.003,t_claw_height+2*c_g1,-c_w2-c_g1+0.0015,0)
            # connector_etcher = draw.subtract(connector_etcher,connector_rect_etch)
            claw_cpw_etcher = draw.buffer(claw_cpw, c_g)
            connector_etcher = draw.unary_union([connector_etcher, claw_cpw_etcher])

            # connector_arm = self.round_corner(radius, connector_arm)
            # # connector_etcher = self.round_corner(radius,connector_etcher)
            #
            # # revise the end from round into flat
            # revised_rect = draw.rectangle(c_w / 4, c_w, -4 * c_w + c_w / 8, 0)
            # connector_arm = draw.unary_union([connector_arm, revised_rect])
        # connector_etcher = draw.buffer(connector_arm, c_g)
        elif pc.connector_type == 4:
            if direction == 0:
                fl_cpw_line = draw.LineString([(-4*c_w,0),(-c_w/2,0),(-c_w/2,2.5*c_w)])
            else:
                # fl_cpw = draw.box(-c_w,-2.5*c_w,0,c_w/2)
                fl_cpw_line = draw.LineString([(-4 * c_w, 0), (-c_w / 2, 0), (-c_w / 2, -2.5 * c_w)])
            # connector_arm = draw.unary_union([fl_cpw,claw_cpw])
            connector_arm = fl_cpw_line.buffer(c_w/2, cap_style=2,join_style=2)
            # connector_etcher = draw.buffer(connector_arm, c_g1, cap_style=3)
            connector_etcher = fl_cpw_line.buffer(c_g1+c_w/2, cap_style=2,join_style=2)
        else:
            connector_arm = claw_cpw
            connector_etcher = draw.buffer(connector_arm, c_g1)

        # Making the pin for  tracking (for easy connect functions).
        # Done here so as to have the same translations and rotations as the connector. Could
        # extract from the connector later, but since allowing different connector types,
        # this seems more straightforward.
        port_line = draw.LineString([(-4 * c_w, -c_w / 2), (-4 * c_w, c_w / 2)])

        claw_rotate = 0
        if con_loc >= 270:
            claw_rotate = 90
        elif 180 <= con_loc < 270:
            claw_rotate = 180
        elif 45 <= con_loc < 180:
            claw_rotate = 270

        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        if pc.connector_type == 2:
            if xy_loc == 0:
                polys = draw.translate(polys, -(cross_gap + cross_width / 2 + g_s + c_g1),
                                       0.89 * cross_length1)
            if xy_loc == 1:
                polys = draw.rotate(polys, 180, origin=(0, 0))
                polys = draw.translate(polys, cross_gap + cross_width / 2 + g_s + c_g1,
                                       0.89 * cross_length1)

            if xy_loc == 2:
                polys = draw.translate(polys, -(cross_gap + cross_width / 2 + g_s + c_g1),
                                       -0.89 * cross_length2)
            if xy_loc == 3:
                polys = draw.rotate(polys, 180, origin=(0, 0))
                polys = draw.translate(polys, cross_gap + cross_width / 2 + g_s + c_g1,
                                       -0.89 * cross_length1)

        else:
            polys = draw.translate(polys, -(cross_length + cross_gap + g_s + c_g1),
                                   0)
            if claw_rotate == 180:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))

            elif claw_rotate == 270:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
                polys = draw.translate(polys, 0, cross_length1 - cross_length)
            elif claw_rotate == 90:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
                polys = draw.translate(polys, 0, cross_length-cross_length2+cross_gap-cross_gap2)
            else:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))

        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        # Generates qgeometry for the connector pads
        # if pc.connector_type != 1:
        self.add_qgeometry('poly', {f'{name}_connector_arm': connector_arm},
                           chip=chip)
        self.add_qgeometry('poly',
                           {f'{name}_connector_etcher': connector_etcher},
                           subtract=True,
                           chip=chip)

        self.add_pin(name, port_line.coords, c_w)


class TransmonCrossRound_v2(BaseQubit):
    """
    Description:
        A revised xmon based on TransmonCrossRound for simulation purpose, should have some bugs
    """
    default_options = Dict(
        cross_width='16um',
        cross_length_left='138um',
        cross_length_right='138um',
        cross_length_up='170um',
        cross_length_down='162um',
        cross_gap='16um',
        cross_gap2='18um',
        radius='10um',
        rect_width='16um',
        rect_height='32um',
        jj_pad_width='8um',
        jj_pad_height='6um',
        jj_etch_length='4um',
        jj_etch_pad1_width='2um',
        jj_etch_pad2_width='5um',
        jj_pad2_height='8um',
        chip='main',
        _default_connection_pads=Dict(
            connector_type='0',  # 0 = Claw type, 1 = gap type
            claw_length='60um',
            ground_spacing='3um',
            claw_width='8um',
            claw_gap='4um',
            coupling_width='20um',
            coupling_gap='5um',
            coupling_top_width='10um',
            xyline_location='0',  # 0 => 'up_left' , 1 => 'up_right' , 2 => 'down_left' ,3 = 'down_right'
            zline_direction='0',  # 0 => 'left', 1 => 'right'
            connector_location=
            '0'  # 0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
        ))
    """Default options."""

    component_metadata = Dict(short_name='TransmonCrossRound_v2',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Simple Metal Transmon Cross with round corner."""

    ##############################################MAKE######################################################
    # define fillet radius
    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_pocket()
        self.make_connection_pads()

    ###################################TRANSMON#############################################################

    def make_pocket(self):
        """Makes a basic Crossmon, 4 arm cross."""

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        cross_width = p.cross_width
        cross_length3 = p.cross_length_left
        cross_length4 = p.cross_length_right
        cross_length1 = p.cross_length_up
        cross_length2 = p.cross_length_down
        cross_gap = p.cross_gap
        radius = p.radius
        rect_width = p.rect_width
        rect_height = p.rect_height
        jj_pad_width = p.jj_pad_width
        jj_pad_height = p.jj_pad_height
        jj_etch_length = p.jj_etch_length
        jj_etch_pad1_width = p.jj_etch_pad1_width
        jj_etch_pad2_width = p.jj_etch_pad2_width
        jj_pad2_height = p.jj_pad2_height
        cross_gap2 = p.cross_gap2

        # access to chip name
        chip = p.chip

        # Creates the cross and the etch equivalent.
        cross_line = draw.unary_union([
            draw.LineString([(0, cross_length1), (0, -cross_length2)]),
            draw.LineString([(cross_length4, 0), (-cross_length3, 0)])
        ])

        cross = cross_line.buffer(cross_width / 2, cap_style=2)

        rect1 = draw.rectangle(rect_width, rect_height, -cross_length3 - rect_width / 2.0, 0)
        rect2 = draw.rectangle(rect_width, rect_height, cross_length4 + rect_width / 2.0, 0)

        cross = draw.unary_union([cross, rect1, rect2])

        cross_etch = cross.buffer(cross_gap, cap_style=2, join_style=2)

        # revision
        rect_etch1 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    cross_length4 + rect_width + 0.75 * cross_gap, 0)
        rect_etch2 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    -(cross_length3 + rect_width + 0.75 * cross_gap), 0)
        rect_plus = draw.rectangle(cross_gap * 2 + cross_width, cross_gap2 - cross_gap, 0,
                                   -cross_length2 - cross_gap - (cross_gap2 - cross_gap) / 2)
        rect_etch = draw.unary_union([rect_etch1, rect_etch2])
        cross_etch = draw.subtract(cross_etch, rect_etch)
        cross_etch = draw.unary_union([cross_etch, rect_plus])

        # corner rounding (fillet)
        cross = self.round_corner(radius, cross)
        cross_etch = self.round_corner(2 * radius, cross_etch)

        # draw junction pad part

        jj_pad = draw.rectangle(jj_pad_width, jj_pad_height, 0, -cross_length2 - jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(jj_etch_pad1_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(jj_etch_pad2_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length * 0.75)

        jj_etch_pad = draw.unary_union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)

        cross = draw.unary_union([cross, jj_pad])

        jj_pad2 = draw.rectangle(jj_etch_pad1_width, jj_pad2_height,
                                 -(cross_width / 8 + cross_gap / 4 + jj_etch_pad1_width / 2),
                                 -cross_length2 - cross_gap2 + jj_pad2_height / 2)
        jj_top_pad2 = draw.rectangle(jj_etch_pad1_width + 1e-3, jj_etch_pad1_width,
                                     -(cross_width / 8 + cross_gap / 4 + (jj_etch_pad1_width + 1e-3) / 2),
                                     -cross_length2 - cross_gap2 + jj_pad2_height - jj_etch_pad1_width / 2)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])

        cross_etch = draw.subtract(cross_etch, jj_pad2)

        # The junction/SQUID
        # rect_jj = draw.rectangle(cross_width, cross_gap)
        # rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)
        rect_jj = draw.LineString([(0, -cross_length2 - jj_pad_height), (0, -cross_length2 - cross_gap2)
                                   ])

        # rotate and translate
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross, cross_etch, rect_jj] = polys

        # generate qgeometry
        self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        self.add_qgeometry('poly',
                           dict(cross_etch=cross_etch),
                           subtract=True,
                           chip=chip)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=jj_pad_width,
                           chip=chip)

    ############################CONNECTORS##################################################################################################

    def make_connection_pads(self):
        """Goes through connector pads and makes each one."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes individual connector pad.

        Args:
            name (str) : Name of the connector pad
        """

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        cross_width = p.cross_width
        cross_length3 = p.cross_length_left
        cross_length4 = p.cross_length_right
        cross_length1 = p.cross_length_up
        cross_length2 = p.cross_length_down
        cross_gap = p.cross_gap
        cross_gap2 = p.cross_gap2
        radius = p.radius

        # access to chip name
        chip = p.chip

        pc = self.p.connection_pads[name]  # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        g_s = pc.ground_spacing
        con_loc = pc.connector_location
        xy_loc = pc.xyline_location
        c_w1 = pc.coupling_width
        c_g1 = pc.coupling_gap
        c_w2 = pc.coupling_top_width
        direction = pc.zline_direction

        claw_cpw = draw.box(0, -c_w / 2, -4 * c_w, c_w / 2)

        if pc.connector_type == 0:  # Claw connector
            t_claw_height = 2 * c_g1 + 2 * c_w1 + 2 * g_s + \
                            2 * cross_gap + cross_width  # temp value

            claw_base = draw.box(-c_w2, -(t_claw_height) / 2, c_l,
                                 t_claw_height / 2)
            claw_subtract = draw.box(0, -t_claw_height / 2 + c_w1, c_l,
                                     t_claw_height / 2 - c_w1)
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.unary_union([claw_base, claw_cpw])

            connector_etcher = draw.buffer(claw_base, c_g1)

            claw_cpw_etcher = draw.buffer(claw_cpw, c_g)
            connector_etcher = draw.unary_union([connector_etcher, claw_cpw_etcher])

        elif pc.connector_type == 4:
            if direction == 0:
                fl_cpw = draw.box(-c_w, -c_w / 2, 0, 2.5 * c_w)
            else:
                fl_cpw = draw.box(-c_w, -2.5 * c_w, 0, c_w / 2)
            connector_arm = draw.unary_union([fl_cpw, claw_cpw])
            connector_etcher = draw.buffer(connector_arm, c_g1)

        else:
            connector_arm = claw_cpw
            connector_etcher = draw.buffer(connector_arm, c_g1)

        # Making the pin for  tracking (for easy connect functions).
        # Done here so as to have the same translations and rotations as the connector. Could
        # extract from the connector later, but since allowing different connector types,
        # this seems more straightforward.
        port_line = draw.LineString([(-4 * c_w, -c_w / 2), (-4 * c_w, c_w / 2)])

        claw_rotate = 0
        if con_loc >= 270:
            claw_rotate = 90
        elif 180 <= con_loc < 270:
            claw_rotate = 180
        elif 45 <= con_loc < 180:
            claw_rotate = 270

        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        if pc.connector_type == 2:
            if xy_loc == 0:
                polys = draw.translate(polys, -(cross_gap + cross_width / 2 + g_s + c_g1),
                                       0.8 * cross_length1)
            if xy_loc == 1:
                polys = draw.rotate(polys, 180, origin=(0, 0))
                polys = draw.translate(polys, cross_gap + cross_width / 2 + g_s + c_g1,
                                       0.8 * cross_length1)

            if xy_loc == 2:
                polys = draw.translate(polys, -(cross_gap + cross_width / 2 + g_s + c_g1),
                                       -0.8 * cross_length2)
            if xy_loc == 3:
                polys = draw.rotate(polys, 180, origin=(0, 0))
                polys = draw.translate(polys, cross_gap + cross_width / 2 + g_s + c_g1,
                                       -0.8 * cross_length1)

        else:
            polys = draw.translate(polys, -(cross_length3 + cross_gap + g_s + c_g1),
                                   0)
            if claw_rotate == 180:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
                polys = draw.translate(polys, cross_length4 - cross_length3, 0)
            elif claw_rotate == 270:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
                polys = draw.translate(polys, 0, cross_length1 - cross_length3)
            elif claw_rotate == 90:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
                polys = draw.translate(polys, 0, cross_length3 - cross_length2 + cross_gap - cross_gap2)
            else:
                polys = draw.rotate(polys, claw_rotate, origin=(0, 0))

        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        # Generates qgeometry for the connector pads
        # if pc.connector_type != 1:
        self.add_qgeometry('poly', {f'{name}_connector_arm': connector_arm},
                           chip=chip)
        self.add_qgeometry('poly',
                           {f'{name}_connector_etcher': connector_etcher},
                           subtract=True,
                           chip=chip)

        self.add_pin(name, port_line.coords, c_w)

class TransmonCrossRound_coupler(BaseQubit):
    """
    Description:
        A revised xmon based on TransmonCrossRound for simulation purpose, should have some bugs
    """
    default_options = Dict(
        cross_width='16um',
        cross_length='138um',
        cross_gap='16um',
        radius='10um',
        rect_width='16um',
        rect_height='32um',
        jj_pad_width='8um',
        jj_pad_height='6um',
        jj_etch_length='4um',
        jj_etch_pad1_width='2um',
        jj_etch_pad2_width='5um',
        jj_pad2_height='8um',
        chip='main',
        _default_connection_pads=Dict(
            connector_type='0',  # 0 = Claw type, 1 = gap type
            claw_length='60um',
            ground_spacing='3um',
            claw_width='8um',
            claw_gap='4um',
            coupling_width='20um',
            coupling_gap='5um',
            coupling_top_width='4um',
            connector_location=
            '0'  # 0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
        ))
    """Default options."""

    component_metadata = Dict(short_name='TransmonCrossRound_coupler',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Simple Metal Transmon Cross with round corner."""

    ##############################################MAKE######################################################
    # define fillet radius
    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_pocket()
        self.make_connection_pads()

    ###################################TRANSMON#############################################################

    def make_pocket(self):
        """Makes a basic Crossmon, 4 arm cross."""

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap
        radius = p.radius
        rect_width = p.rect_width
        rect_height = p.rect_height
        jj_pad_width = p.jj_pad_width
        jj_pad_height = p.jj_pad_height
        jj_etch_length = p.jj_etch_length
        jj_etch_pad1_width = p.jj_etch_pad1_width
        jj_etch_pad2_width = p.jj_etch_pad2_width
        jj_pad2_height = p.jj_pad2_height
        cross_length1 = cross_length + 0.032
        cross_length2 = cross_length + 0.024
        cross_gap2 = cross_gap + 0.002

        # access to chip name
        chip = p.chip

        # Creates the cross and the etch equivalent.
        cross_line = draw.unary_union([
            draw.LineString([(0, cross_length1), (0, -cross_length2)]),
            draw.LineString([(cross_length, 0), (-cross_length, 0)])
        ])

        cross = cross_line.buffer(cross_width / 2, cap_style=2)

        rect1 = draw.rectangle(rect_width, rect_height, -cross_length - rect_width / 2.0, 0)
        rect2 = draw.rectangle(rect_width, rect_height, cross_length + rect_width / 2.0, 0)

        cross = draw.unary_union([cross, rect1, rect2])

        cross_etch = cross.buffer(cross_gap, cap_style=2, join_style=2)

        # revision
        rect_etch1 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    cross_length + rect_width + 0.75 * cross_gap, 0)
        rect_etch2 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    -(cross_length + rect_width + 0.75 * cross_gap), 0)
        rect_plus = draw.rectangle(cross_gap * 2 + cross_width, 0.002, 0, -cross_length2 - cross_gap - 0.001)
        rect_etch = draw.unary_union([rect_etch1, rect_etch2])
        cross_etch = draw.subtract(cross_etch, rect_etch)
        cross_etch = draw.unary_union([cross_etch, rect_plus])

        # corner rounding (fillet)
        cross = self.round_corner(radius, cross)
        cross_etch = self.round_corner(2 * radius, cross_etch)

        # draw junction pad part

        jj_pad = draw.rectangle(jj_pad_width, jj_pad_height, 0, -cross_length2 - jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(jj_etch_pad1_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(jj_etch_pad2_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length * 0.75)

        jj_etch_pad = draw.unary_union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)

        cross = draw.unary_union([cross, jj_pad])

        jj_pad2 = draw.rectangle(jj_etch_pad1_width, jj_pad2_height,
                                 -(cross_width / 8 + cross_gap / 4 + jj_etch_pad1_width / 2),
                                 -cross_length2 - cross_gap2 + jj_pad2_height / 2)
        jj_top_pad2 = draw.rectangle(jj_etch_pad1_width + 1e-3, jj_etch_pad1_width,
                                     -(cross_width / 8 + cross_gap / 4 + (jj_etch_pad1_width + 1e-3) / 2),
                                     -cross_length2 - cross_gap2 + jj_pad2_height - jj_etch_pad1_width / 2)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])

        cross_etch = draw.subtract(cross_etch, jj_pad2)

        # The junction/SQUID
        # rect_jj = draw.rectangle(cross_width, cross_gap)
        # rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)
        rect_jj = draw.LineString([(0, -cross_length2 - jj_pad_height), (0, -cross_length2 - cross_gap2)
                                   ])

        # rotate and translate
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross, cross_etch, rect_jj] = polys

        # # generate qgeometry
        # self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        # self.add_qgeometry('poly',
        #                    dict(cross_etch=cross_etch),
        #                    subtract=True,
        #                    chip=chip)
        # self.add_qgeometry('junction',
        #                    dict(rect_jj=rect_jj),
        #                    width=jj_pad_width,
        #                    chip=chip)

    ############################CONNECTORS##################################################################################################

    def make_connection_pads(self):
        """Goes through connector pads and makes each one."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes individual connector pad.

        Args:
            name (str) : Name of the connector pad
        """

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        cross_width = p.cross_width
        cross_length = p.cross_length
        # cross_length1 = cross_length+0.032
        cross_gap = p.cross_gap
        radius = p.radius

        # access to chip name
        chip = p.chip

        pc = self.p.connection_pads[name]  # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        g_s = pc.ground_spacing
        con_loc = pc.connector_location
        c_w1 = pc.coupling_width
        c_g1 = pc.coupling_gap
        c_w2 = pc.coupling_top_width

        claw_cpw = draw.box(0, -c_w / 2, -4 * c_w, c_w / 2)

        if pc.connector_type == 0:  # Claw connector
            t_claw_height = 2 * c_g1 + 2 * c_w1 + 2 * g_s + \
                            2 * cross_gap + cross_width  # temp value

            claw_base = draw.box(-c_w2, -(t_claw_height) / 2, c_l,
                                 t_claw_height / 2)
            claw_subtract = draw.box(0, -t_claw_height / 2 + c_w1, c_l,
                                     t_claw_height / 2 - c_w1)
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.unary_union([claw_base, claw_cpw])

            connector_etcher = draw.buffer(claw_base, c_g1)
            # connector_rect_etch = draw.rectangle(0.003,t_claw_height+2*c_g1,-c_w2-c_g1+0.0015,0)
            # connector_etcher = draw.subtract(connector_etcher,connector_rect_etch)
            claw_cpw_etcher = draw.buffer(claw_cpw, c_g)
            connector_etcher = draw.unary_union([connector_etcher, claw_cpw_etcher])
        else:
            connector_arm = claw_cpw
            connector_etcher = draw.buffer(connector_arm, c_g)

        connector_arm = self.round_corner(radius, connector_arm)
        # connector_etcher = self.round_corner(radius,connector_etcher)

        # revise the end from round into flat
        revised_rect = draw.rectangle(c_w / 4, c_w, -4 * c_w + c_w / 8, 0)
        connector_arm = draw.unary_union([connector_arm, revised_rect])
        # connector_etcher = draw.buffer(connector_arm, c_g)

        # Making the pin for  tracking (for easy connect functions).
        # Done here so as to have the same translations and rotations as the connector. Could
        # extract from the connector later, but since allowing different connector types,
        # this seems more straightforward.
        port_line = draw.LineString([(-4 * c_w, -c_w / 2), (-4 * c_w, c_w / 2)])

        claw_rotate = 0
        if con_loc > 135:
            claw_rotate = 180
        elif con_loc > 45:
            claw_rotate = -90

        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        polys = draw.translate(polys, -(cross_length + cross_gap + g_s + c_g),
                               0)
        if claw_rotate == -90:
            polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
            polys = draw.translate(polys, 0, 0.033)
        else:
            polys = draw.rotate(polys, claw_rotate, origin=(0, 0))

        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        # Generates qgeometry for the connector pads
        self.add_qgeometry('poly', {f'{name}_connector_arm': connector_arm},
                           chip=chip)
        self.add_qgeometry('poly',
                           {f'{name}_connector_etcher': connector_etcher},
                           subtract=True,
                           chip=chip)

        self.add_pin(name, port_line.coords, c_w)


class TransmonCrossRound_v2(BaseQubit):
    """
    Description:
        A revised xmon based on TransmonCrossRound for simulation purpose, should have some bugs
    """
    default_options = Dict(
        cross_width='16um',
        cross_length='138um',
        cross_length1='170um',
        cross_length2='162um',
        tilt_length='100um',
        cross_gap='16um',
        cross_gap2='18um',
        radius='10um',
        rect_width='16um',
        rect_height='32um',
        jj_pad_width='8um',
        jj_pad_height='6um',
        jj_etch_length='4um',
        jj_etch_pad1_width='2um',
        jj_etch_pad2_width='5um',
        jj_pad2_height='8um',
        chip='main',
        _default_connection_pads=Dict(
            connector_type='0',  # 0 = Claw type, 1 = gap type
            claw_length='55um',
            ground_spacing='3um',
            claw_width='8um',
            claw_gap='4um',
            coupling_width='20um',
            coupling_gap='5um',
            coupling_top_width='4um',
            connector_location=
            '0'  # 0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
        ))
    """Default options."""

    component_metadata = Dict(short_name='TransmonCrossRound_v2',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Simple Metal Transmon Cross with round corner."""

    ##############################################MAKE######################################################
    # define fillet radius
    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_pocket()
        self.make_connection_pads()

    ###################################TRANSMON#############################################################

    def make_pocket(self):
        """Makes a basic Crossmon, 4 arm cross."""

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap
        radius = p.radius
        rect_width = p.rect_width
        rect_height = p.rect_height
        jj_pad_width = p.jj_pad_width
        jj_pad_height = p.jj_pad_height
        jj_etch_length = p.jj_etch_length
        jj_etch_pad1_width = p.jj_etch_pad1_width
        jj_etch_pad2_width = p.jj_etch_pad2_width
        jj_pad2_height = p.jj_pad2_height
        # cross_length1 = cross_length+0.032-0.016
        # cross_length2 = cross_length+0.024-0.016
        # cross_gap2 = cross_gap+0.002
        cross_length1 = p.cross_length1
        cross_length2 = p.cross_length2
        cross_gap2 = p.cross_gap2
        tilt_length = p.tilt_length

        # access to chip name
        chip = p.chip

        # Creates the cross and the etch equivalent.
        cross_line = draw.unary_union([
            draw.LineString([(0, cross_length1), (0, -cross_length2)]),
            draw.LineString([(cross_length, 0), (-cross_length, 0)]),
            draw.LineString([(tilt_length * math.cos(45 * math.pi / 180), tilt_length * math.sin(45 * math.pi / 180)), (
                -tilt_length * math.cos(45 * math.pi / 180), -tilt_length * math.sin(45 * math.pi / 180))]),
            draw.LineString([(tilt_length * math.cos(135 * math.pi / 180), tilt_length * math.sin(135 * math.pi / 180)),
                             (-tilt_length * math.cos(135 * math.pi / 180),
                              -tilt_length * math.sin(135 * math.pi / 180))])
        ])

        cross = cross_line.buffer(cross_width / 2, cap_style=2)

        rect1 = draw.rectangle(rect_width, rect_height, -cross_length - rect_width / 2.0, 0)
        rect2 = draw.rectangle(rect_width, rect_height, cross_length + rect_width / 2.0, 0)

        cross = draw.unary_union([cross, rect1, rect2])

        cross_etch = cross.buffer(cross_gap, cap_style=2, join_style=2)

        # revision
        rect_etch1 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    cross_length + rect_width + 0.75 * cross_gap, 0)
        rect_etch2 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    -(cross_length + rect_width + 0.75 * cross_gap), 0)
        rect_plus = draw.rectangle(cross_gap * 2 + cross_width, 0.002, 0, -cross_length2 - cross_gap - 0.001)
        rect_etch = draw.unary_union([rect_etch1, rect_etch2])
        cross_etch = draw.subtract(cross_etch, rect_etch)
        cross_etch = draw.unary_union([cross_etch, rect_plus])

        # corner rounding (fillet)
        cross = self.round_corner(radius, cross)
        cross_etch = self.round_corner(2 * radius, cross_etch)

        # draw junction pad part

        jj_pad = draw.rectangle(jj_pad_width, jj_pad_height, 0, -cross_length2 - jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(jj_etch_pad1_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(jj_etch_pad2_width, jj_etch_length / 2, 0,
                                      -cross_length2 - jj_pad_height + jj_etch_length * 0.75)

        jj_etch_pad = draw.unary_union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)

        cross = draw.unary_union([cross, jj_pad])

        jj_pad2 = draw.rectangle(jj_etch_pad1_width, jj_pad2_height,
                                 -(cross_width / 8 + cross_gap / 4 + jj_etch_pad1_width / 2),
                                 -cross_length2 - cross_gap2 + jj_pad2_height / 2)
        jj_top_pad2 = draw.rectangle(jj_etch_pad1_width + 1e-3, jj_etch_pad1_width,
                                     -(cross_width / 8 + cross_gap / 4 + (jj_etch_pad1_width + 1e-3) / 2),
                                     -cross_length2 - cross_gap2 + jj_pad2_height - jj_etch_pad1_width / 2)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])

        cross_etch = draw.subtract(cross_etch, jj_pad2)

        # The junction/SQUID
        # rect_jj = draw.rectangle(cross_width, cross_gap)
        # rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)
        rect_jj = draw.LineString([(0, -cross_length2 - jj_pad_height), (0, -cross_length2 - cross_gap2)
                                   ])

        # rotate and translate
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross, cross_etch, rect_jj] = polys

        # generate qgeometry
        self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        self.add_qgeometry('poly',
                           dict(cross_etch=cross_etch),
                           subtract=True,
                           chip=chip)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=jj_pad_width,
                           chip=chip)

    ############################CONNECTORS##################################################################################################

    def make_connection_pads(self):
        """Goes through connector pads and makes each one."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes individual connector pad.

        Args:
            name (str) : Name of the connector pad
        """

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_length1 = p.cross_length1
        cross_gap = p.cross_gap
        radius = p.radius
        # rect_width = p.rect_width

        # access to chip name
        chip = p.chip

        pc = self.p.connection_pads[name]  # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        g_s = pc.ground_spacing
        con_loc = pc.connector_location
        c_w1 = pc.coupling_width
        c_g1 = pc.coupling_gap
        c_w2 = pc.coupling_top_width

        claw_cpw = draw.box(0, -c_w / 2, -4 * c_w, c_w / 2)

        if pc.connector_type == 0:  # Claw connector
            t_claw_height = 2 * c_g1 + 2 * c_w1 + 2 * g_s + \
                            2 * cross_gap + cross_width  # temp value

            claw_base = draw.box(-c_w2, -(t_claw_height) / 2, c_l,
                                 t_claw_height / 2)
            claw_subtract = draw.box(0, -t_claw_height / 2 + c_w1, c_l,
                                     t_claw_height / 2 - c_w1)
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.unary_union([claw_base, claw_cpw])

            connector_etcher = draw.buffer(claw_base, c_g1)
            # connector_rect_etch = draw.rectangle(0.003,t_claw_height+2*c_g1,-c_w2-c_g1+0.0015,0)
            # connector_etcher = draw.subtract(connector_etcher,connector_rect_etch)
            claw_cpw_etcher = draw.buffer(claw_cpw, c_g)
            connector_etcher = draw.unary_union([connector_etcher, claw_cpw_etcher])
        else:
            connector_arm = claw_cpw
            connector_etcher = draw.buffer(connector_arm, c_g)

        connector_arm = self.round_corner(radius, connector_arm)
        # connector_etcher = self.round_corner(radius,connector_etcher)

        # revise the end from round into flat
        revised_rect = draw.rectangle(c_w / 4, c_w, -4 * c_w + c_w / 8, 0)
        connector_arm = draw.unary_union([connector_arm, revised_rect])
        # connector_etcher = draw.buffer(connector_arm, c_g)

        # Making the pin for  tracking (for easy connect functions).
        # Done here so as to have the same translations and rotations as the connector. Could
        # extract from the connector later, but since allowing different connector types,
        # this seems more straightforward.
        port_line = draw.LineString([(-4 * c_w, -c_w / 2), (-4 * c_w, c_w / 2)])

        claw_rotate = 0
        if con_loc > 135:
            claw_rotate = 180
        elif con_loc > 45:
            claw_rotate = -90

        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        polys = draw.translate(polys, -(cross_length + cross_gap + g_s + c_g1),
                               0)
        if claw_rotate == -90:
            polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
            # polys = draw.translate(polys, 0, 0.033-0.016)
            polys = draw.translate(polys, 0, cross_length1 - cross_length)
        else:
            polys = draw.rotate(polys, claw_rotate, origin=(0, 0))

        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        # Generates qgeometry for the connector pads
        self.add_qgeometry('poly', {f'{name}_connector_arm': connector_arm},
                           chip=chip)
        self.add_qgeometry('poly',
                           {f'{name}_connector_etcher': connector_etcher},
                           subtract=True,
                           chip=chip)

        self.add_pin(name, port_line.coords, c_w)


class New_Transmon_Cross(BaseQubit):
    """
    Inherits 'BaseQubit' class.

    """

    # Edit these to define your own tempate options for creation
    # Default drawing options
    default_options = Dict(cross_length_x='1340um',
                           cross_length_y='1340um',
                           gap='30um',
                           cross_height='80um',
                           cross_inside_width='20um',
                           pad_width='40um',
                           pad_height='40um',
                           pad_distance='20um',
                           jj_pad_width='10um',
                           jj_pad_height='9um',
                           jj_etch_length='4um',
                           jj_etch_pad1_width='4um',
                           jj_etch_pad2_width='7um',
                           round_corner_radius='10um',
                           inner_corner_radius='20um',
                           chip='main',
                           pos_x='0um',
                           pos_y='0um',
                           orientation='0',
                           layer='1')
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='new_transmon_c',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_path='True',
                              _qgeometry_table_junction='True'
                              )
    """Component metadata"""

    def round_corner(self, radius, line):
        # line1 = line.buffer(1,cap_style=2)
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        cross_length_x = p.cross_length_x / 2
        cross_length_y = p.cross_length_y / 2
        start_point = cross_length_x - p.pad_width / 2 - p.pad_distance
        end_point = cross_length_y - p.pad_width / 2 - p.pad_distance
        mid_point = p.cross_height / 2
        jj_pad_width = p.jj_pad_width
        jj_etch_length = p.jj_etch_length
        jj_etch_pad1_width = p.jj_etch_pad1_width
        jj_etch_pad2_width = p.jj_etch_pad2_width
        num_interpolation = 5
        point_space = (start_point - mid_point) / num_interpolation
        chip = p.chip
        radius = p.round_corner_radius
        inner_radius = p.inner_corner_radius
        gap = p.gap
        cross_gap = gap + p.cross_inside_width / 2

        # draw two islands

        # first_point = start_point-point_space
        # second_point = start_point-2*point_space
        # third_point = start_point- 3*point_space
        # fourth_point = start_point-4*point_space
        point0 = (-start_point, 0)
        # point1 = (-first_point,0)
        # point2 = (-second_point,0)
        # point3 = (-third_point,0)
        # point4 = (-fourth_point,0)
        point1 = (-mid_point, 0)
        point2 = (0, mid_point)
        # point7 = (0,fourth_point)
        # point8 = (0,third_point)
        # point9 = (0,second_point)
        # point10 = (0,first_point)
        point3 = (0, end_point)

        line = LineString([point0, point1, point2, point3])
        line0 = line.buffer(p.cross_inside_width / 2, cap_style=3, join_style=1)
        line0 = self.round_corner(radius * p.pad_width / p.cross_height, line0)
        length_island = draw.shapely.length(LineString([point1, point2]))

        # Joesphon Junction draw
        skew_line = LineString([point1, point2])
        island1_mid_point = draw.shapely.line_interpolate_point(skew_line, length_island / 2)
        island2_mid_point = draw.shapely.transform(island1_mid_point, lambda x: -x)
        jj_pad1_end_coord = (-mid_point / 2 + (p.jj_pad_height + p.cross_inside_width / 2) * math.sqrt(2.0) / 2.0,
                             mid_point / 2 - (p.jj_pad_height + p.cross_inside_width / 2) * math.sqrt(2.0) / 2.0)
        jj_pad2_end_coord = (mid_point / 2 - (p.jj_pad_height + p.cross_inside_width / 2) * math.sqrt(2.0) / 2.0,
                             -mid_point / 2 + (p.jj_pad_height + p.cross_inside_width / 2) * math.sqrt(2.0) / 2.0)
        rect_jj_pad1_referenceLine = LineString([island1_mid_point, jj_pad1_end_coord])
        rect_jj_pad1_referenceLine_buffer = rect_jj_pad1_referenceLine.buffer(jj_pad_width / 2, cap_style=2)
        # length_jj = draw.shapely.length(rect_jj)
        epsilon = 1e-4
        rect_jj_pad1_intersect_point1 = draw.shapely.line_interpolate_point(rect_jj_pad1_referenceLine,
                                                                            -jj_etch_length / 2)
        rect_jj_pad1_intersect_point1_epsilon = draw.shapely.line_interpolate_point(rect_jj_pad1_referenceLine,
                                                                                    -jj_etch_length / 2 + epsilon)
        rect_jj_pad1_intersect_point2 = draw.shapely.line_interpolate_point(rect_jj_pad1_referenceLine, -jj_etch_length)
        rect_jj_pad1_polygon1 = LineString([rect_jj_pad1_intersect_point1, jj_pad1_end_coord]).buffer(
            jj_etch_pad1_width / 2, cap_style=2)
        rect_jj_pad1_polygon2 = LineString(
            [rect_jj_pad1_intersect_point2, rect_jj_pad1_intersect_point1_epsilon]).buffer(jj_etch_pad2_width / 2,
                                                                                           cap_style=2)
        jj_pad = draw.unary_union([rect_jj_pad1_polygon1, rect_jj_pad1_polygon2])
        jj_pad_etch = draw.subtract(rect_jj_pad1_referenceLine_buffer, jj_pad)
        pad1 = draw.rectangle(p.pad_width, p.pad_height, start_point, 0)
        pad1 = self.round_corner(radius * p.pad_width / p.cross_height, pad1)
        pad2 = draw.rectangle(p.pad_height, p.pad_width, 0, end_point)
        pad2 = self.round_corner(radius * p.pad_width / p.cross_height, pad2)
        component_leg1 = draw.unary_union([line0, jj_pad_etch, pad1, pad2])
        component_leg2 = draw.rotate(component_leg1, -180, origin=(0, 0))

        # draw cross line outside
        ref = cross_gap + inner_radius

        cross_line = draw.unary_union([
            draw.LineString([(0, cross_length_y), (0, -cross_length_y)]),
            draw.LineString([(cross_length_x, 0), (-cross_length_x, 0)])
        ])
        # cross_etch = cross_line.buffer(p.cross_height/ 2, cap_style=2)
        cross = draw.unary_union([component_leg1, component_leg2])
        cross_etch = cross_line.buffer(cross_gap, cap_style=2)
        cross_etch = self.round_corner(radius, cross_etch)

        center = np.array([(ref, ref)])
        circle = draw.Point(center).buffer(inner_radius)
        box = draw.box(minx=cross_gap - epsilon, miny=cross_gap - epsilon, maxx=ref, maxy=ref)
        res1 = box.difference(circle)
        res2 = draw.shapely.transform(res1, lambda x: x * [-1, 1])
        res3 = draw.shapely.transform(res1, lambda x: -x)
        res4 = draw.shapely.transform(res1, lambda x: x * [1, -1])
        cross_etch = draw.unary_union([res1, res2, res3, res4, cross_etch])

        pad_etch1 = draw.box(start_point - p.pad_width / 2 - gap, -(p.pad_height / 2 + gap), cross_length_x,
                             p.pad_height / 2 + gap)
        pad_etch1 = self.round_corner(radius, pad_etch1)
        pad_etch2 = draw.rotate(pad_etch1, 90, origin=(0, 0))
        pad_etch2 = draw.translate(pad_etch2, yoff=cross_length_y - cross_length_x)
        pad_etch3 = draw.rotate(pad_etch1, 180, origin=(0, 0))
        pad_etch4 = draw.rotate(pad_etch1, -90, origin=(0, 0))
        pad_etch4 = draw.translate(pad_etch4, yoff=cross_length_x - cross_length_y)
        cross_etch = draw.unary_union([pad_etch1, pad_etch2, pad_etch3, pad_etch4, cross_etch])

        rect_jj_pad1_intersect_point2_symmetry = draw.shapely.transform(rect_jj_pad1_intersect_point2, lambda x: -x)
        # rect_jj =draw.LineString([rect_jj_pad1_intersect_point2, rect_jj_pad1_intersect_point2_symmetry])                      ##old junction area
        rect_jj = draw.LineString([jj_pad1_end_coord, jj_pad2_end_coord])

        # etch_area = draw.subtract(cross,positive_area)
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [cross, cross_etch, rect_jj] = polys
        connector_pin_right = draw.LineString(
            [(cross_length_x, -p.cross_height / 2), (cross_length_x, p.cross_height / 2)])

        # add qgeometry
        self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        self.add_qgeometry('poly',
                           dict(cross_etch=cross_etch),
                           subtract=True,
                           chip=chip)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=p.jj_pad_width,
                           chip=chip)

        # add pins
        self.add_pin('pin_right', connector_pin_right.coords, width=p.cross_height)


class XmonFlipChip01(BaseQubit):
    """
    Description:
        A revised xmon based on TransmonCrossRound for simulation purpose, should have some bugs
    """
    default_options = Dict(
        cross_width='16um',
        cross_length='138um',
        cross_length1='138um',
        # cross_length2='162um',
        cross_gap='16um',
        # cross_gap2='18um',
        radius='10um',
        rect_width='16um',
        rect_height='32um',
        jj_pos_x='0.5',
        jj_pad_width='8um',
        jj_pad_height='6um',
        jj_etch_length='4um',
        jj_etch_pad1_width='2um',
        jj_etch_pad2_width='5um',
        jj_pad2_height='8um',
        chip='main',
    )
    """Default options."""

    component_metadata = Dict(short_name='xmon_flipchip',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')
    """Component metadata"""

    TOOLTIP = """Simple Metal Transmon Cross with round corner."""

    ##############################################MAKE######################################################
    # define fillet radius
    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_pocket()
        # self.make_connection_pads()

    ###################################TRANSMON#############################################################

    def make_pocket(self):
        """Makes a basic Crossmon, 4 arm cross."""

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap
        radius = p.radius
        rect_width = p.rect_width
        rect_height = p.rect_height
        jj_pad_width = p.jj_pad_width
        jj_pad_height = p.jj_pad_height
        jj_etch_length = p.jj_etch_length
        jj_etch_pad1_width = p.jj_etch_pad1_width
        jj_etch_pad2_width = p.jj_etch_pad2_width
        jj_pad2_height = p.jj_pad2_height
        cross_length1 = p.cross_length1
        # cross_length2 = p.cross_length2
        # cross_gap2 = p.cross_gap2

        # access to chip name
        chip = p.chip

        # Creates the cross and the etch equivalent.
        cross_line = draw.unary_union([
            draw.LineString([(0, cross_length1), (0, -cross_length1)]),
            draw.LineString([(cross_length, 0), (-cross_length, 0)])
        ])

        cross = cross_line.buffer(cross_width / 2, cap_style=2)

        rect1 = draw.rectangle(rect_width, rect_height, -cross_length - rect_width / 2.0, 0)
        rect2 = draw.rectangle(rect_width, rect_height, cross_length + rect_width / 2.0, 0)
        rect3 = draw.rectangle(rect_height, rect_width, 0, -cross_length1 - rect_width / 2.0)
        rect4 = draw.rectangle(rect_height, rect_width, 0, cross_length1 + rect_width / 2.0)

        cross = draw.unary_union([cross, rect1, rect2, rect3, rect4])
        cross_etch = cross.buffer(cross_gap, cap_style=2, join_style=2)

        # revision
        rect_etch1 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    cross_length + rect_width + 0.75 * cross_gap, 0)
        rect_etch2 = draw.rectangle(cross_gap / 2, cross_gap * 2 + rect_height,
                                    -(cross_length + rect_width + 0.75 * cross_gap), 0)
        rect_etch3 = draw.rectangle(cross_gap * 2 + rect_height, cross_gap / 2,
                                    0, cross_length + rect_width + 0.75 * cross_gap)
        rect_etch4 = draw.rectangle(cross_gap * 2 + rect_height, cross_gap / 2,
                                    0, -(cross_length + rect_width + 0.75 * cross_gap))
        # rect_plus = draw.rectangle(cross_gap * 2 + cross_width, cross_gap2 - cross_gap, 0,
        #                            -cross_length2 - cross_gap - (cross_gap2 - cross_gap) / 2)
        rect_etch = draw.unary_union([rect_etch1, rect_etch2, rect_etch3, rect_etch4])
        cross_etch = draw.subtract(cross_etch, rect_etch)
        # cross_etch = draw.unary_union([cross_etch, rect_plus])

        # corner rounding (fillet)
        cross = self.round_corner(radius, cross)
        cross_etch = self.round_corner(2 * radius, cross_etch)

        # draw junction pad part
        jj_pos_x = p.jj_pos_x * cross_length
        jj_pos_y = cross_width / 2

        jj_pad = draw.rectangle(jj_pad_width, jj_pad_height, jj_pos_x, jj_pos_y + jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(jj_etch_pad1_width, jj_etch_length / 2, jj_pos_x,
                                      jj_pos_y + jj_pad_height - jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(jj_etch_pad2_width, jj_etch_length / 2, jj_pos_x,
                                      jj_pos_y + jj_pad_height - jj_etch_length * 0.75)

        jj_etch_pad = draw.unary_union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)

        cross = draw.unary_union([cross, jj_pad])

        jj_pad2 = draw.rectangle(jj_etch_pad1_width, jj_pad2_height,
                                 -(cross_width / 8 + cross_gap / 4 + jj_etch_pad1_width / 2),
                                 jj_pos_y + cross_gap - jj_pad2_height / 2)
        jj_top_pad2 = draw.rectangle(jj_etch_pad1_width + 1e-3, jj_etch_pad1_width,
                                     -(cross_width / 8 + cross_gap / 4 + (jj_etch_pad1_width + 1e-3) / 2),
                                     jj_pos_y + cross_gap - jj_pad2_height + jj_etch_pad1_width / 2)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])
        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])
        jj_pad2 = draw.translate(jj_pad2, jj_pos_x)

        cross_etch = draw.subtract(cross_etch, jj_pad2)

        # The junction/SQUID
        # rect_jj = draw.rectangle(cross_width, cross_gap)
        # rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)
        rect_jj = draw.LineString([(jj_pos_x, jj_pos_y + jj_pad_height), (jj_pos_x, jj_pos_y + cross_gap)
                                   ])

        # rotate and translate
        polys = [cross, cross_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross, cross_etch, rect_jj] = polys

        # generate qgeometry
        self.add_qgeometry('poly', dict(cross=cross), chip=chip)
        self.add_qgeometry('poly',
                           dict(cross_etch=cross_etch),
                           subtract=True,
                           chip=chip)
        self.add_qgeometry('junction',
                           dict(rect_jj=rect_jj),
                           width=jj_pad_width,
                           chip=chip)


class MyReadoutRes01(QComponent):
    '''
    The base ReadoutResFC class

    Inherits the QComponent class

    Readout resonator for the flipchip dev. Written for the flipchip tutorial.

    The device consists of the following shapes combined together:
        - a circle centered at ('pos_x', 'pos_y') with a radius of 'readout_radius', followed by
        - a straight line (length= 'readout_l1') at a 45 degree angle, followed by
        - a 45 degree arc, followed by
        - a vertical line (length = 'readout_l2'), followed by
        - a 90 degree arc, followed by
        - a horizontal line (length = 'readout_l3'), followed by
        - a 180 degree arc, followed by
        - a horizontal line (length = 'readout_l4'), followed by
        - 5 meandering horizontal lines (length = 'readout_l5') separated 180 degree arcs.

    The arc has a bend radius of 'readout_cpw_turnradius',
        it is measured from the center of the cpw to the center of rotation.
    The lines and arcs will form a cpw with a signal linewidth of 'readout_cpw_width', and
        signal-to-ground separation of 'readout_cpw_gap'.

    One of the ways to adjust this design to your needs:
    - change the coupling to the qubit by varying the 'readout_radius',
    - couple the resonator to the feedthrough transmission line via
        the horizontal section with this length 'readout_l3',
    - adjust the frequency of the resonator by varying 'readout_l5'.

    '''

    default_options = Dict(pos_x='0 um',
                           pos_y='0 um',
                           readout_radius='50 um',
                           readout_cpw_width='5 um',
                           readout_cpw_gap='5 um',
                           readout_cpw_turnradius='50 um',
                           vertical_start_length='40 um',
                           vertical_end_length='200 um',
                           horizontal_start_length01='400 um',
                           # horizontal_start_length02 = '400 um',
                           horizontal_end_length='500 um',
                           total_length='4000 um',
                           arc_step='1 um',
                           meander_round='5',
                           orientation='0',
                           layer='1',
                           layer_subtract='2',
                           inverse=False,
                           mirror=False,
                           subtract=True,
                           chip='main',
                           _default_connection_pads=Dict())
    ''' Default drawing options ?? '''
    component_metadata = Dict(short_name='myreadoutres01',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='False')
    ''' Component metadata '''

    ##########################
    def make(self):
        ''' Make the head for readout res'''
        self.make_ro()

    ##########################

    def make_ro(self):
        '''
        Create the head of the readout resonator.
        Contains: the circular patch for coupling,
            the 45 deg line,
            the 45 deg arc,
            a short straight segment (of length w) for smooth subtraction
        '''
        # access to parsed values from the user option
        p = self.p

        # access to chip name
        chip = p.chip

        # local variables
        r = p.readout_radius
        w = p.readout_cpw_width
        g = p.readout_cpw_gap
        turnradius = p.readout_cpw_turnradius
        N = p.meander_round
        l_1 = 0
        l_2 = p.vertical_start_length
        l_3 = p.horizontal_start_length01

        total_length = p.total_length
        left_length = l_2 + p.vertical_end_length \
                      + l_3 + p.horizontal_end_length + (N + 2.5) * np.pi * turnradius
        if (total_length <= left_length):
            l_4 = 0
        l_4 = (total_length - left_length) / (N + 1)
        l_5 = l_4
        l_6 = p.vertical_end_length
        l_7 = p.horizontal_end_length

        # create the coupling patch in term of a circle
        cppatch = draw.Point(0, 0).buffer(r)

        # create the extended arm
        ## useful coordinates
        eps0 = 1e-2
        x_3, y_3 = 0, r - eps0
        x_4, y_4 = x_3, y_3 + l_2 + eps0
        x_5, y_5 = x_4 + turnradius, y_4
        # coord_x2 = draw.Point(x_2,y_2)
        coord_init1 = draw.Point(x_4, y_4)
        coord_center1 = draw.Point(x_5, y_5)
        x_6, y_6 = x_5, y_5 + turnradius
        x_7, y_7 = x_5 + l_3, y_6
        x_8, y_8 = x_7, y_7 + turnradius
        coord_x6 = draw.Point(x_6, y_6)
        coord_init2 = draw.Point((x_7, y_7))
        coord_center2 = draw.Point((x_8, y_8))

        arc2 = self.arc(coord_init2, coord_center2, np.pi)

        x_9, y_9 = x_8, y_8 + turnradius
        x_10, y_10 = x_8 - l_4, y_9
        x_11, y_11 = x_10, y_10 + turnradius
        coord_x9 = draw.Point((x_9, y_9))
        coord_init3 = draw.Point((x_10, y_10))
        coord_center3 = draw.Point((x_11, y_11))

        line11 = draw.LineString([(x_9, y_9), (x_10, y_10)])

        arc3 = self.arc(coord_init3, coord_center3, -np.pi)
        x_12, y_12 = x_11, y_11 + turnradius
        x_13, y_13 = x_12 + l_5, y_12

        # line12 = draw.LineString([(x_12, y_12), (x_13, y_13)])
        # x_14, y_14 = x_13, y_13 + turnradius
        # coord_x12 = draw.Point(x_12,y_12)
        # coord_init4 = draw.Point((x_13, y_13))
        # coord_center4 = draw.Point((x_14, y_14))
        # arc4 = self.arc(coord_init4, coord_center4, np.pi)

        # x_15,y_15 = x_13, y_13+4*2*turnradius
        # x_16,y_16 = x_15,y_15 + turnradius
        # x_17,y_17 = x_16+turnradius, y_16
        # coord_init5 = draw.Point(x_15,y_15)
        # coord_center5 = draw.Point(x_16,y_16)
        geometry_list = []
        round_num = math.ceil((N - 1) / 2) + 1
        for i in range(int(N - 1)):
            geometry_list.append(draw.translate(line11, 0, (i + 1) * 2 * turnradius))
            if (i % 2 == 0):
                geometry_list.append(draw.translate(arc2, 0, (i + 2) * 2 * turnradius))
            else:
                geometry_list.append(draw.translate(arc3, 0, (i + 1) * 2 * turnradius))

        geometry_list.append(draw.translate(line11, 0, N * 2 * turnradius))

        if ((N - 1) % 2 == 0):
            x_15, y_15 = x_13, y_13 + (N - 1) * 2 * turnradius
            x_16, y_16 = x_15, y_15 + turnradius
            x_17, y_17 = x_16 + turnradius, y_16
            coord_init5 = draw.Point(x_15, y_15)
            coord_center5 = draw.Point(x_16, y_16)
            geometry_list.append(self.arc(coord_init5, coord_center5, np.pi / 2))
        else:
            x_15, y_15 = x_12, y_12 + (N - 1) * 2 * turnradius
            x_16, y_16 = x_15, y_15 + turnradius
            x_17, y_17 = x_16 - turnradius, y_16
            coord_init5 = draw.Point(x_15, y_15)
            coord_center5 = draw.Point(x_16, y_16)
            geometry_list.append(self.arc(coord_init5, coord_center5, -np.pi / 2))

        x_18, y_18 = x_17, y_17 + l_6
        x_19, y_19 = x_18 + turnradius, y_18
        coord_init6 = draw.Point((x_18, y_18))
        coord_center6 = draw.Point((x_19, y_19))
        x_20, y_20 = x_19, y_19 + turnradius
        x_21, y_21 = x_20 + l_7, y_20

        geometry_list0 = [
            # draw.LineString([(0, 0), coord_init]),
            # arc(coord_init, coord_center, -np.pi / 4),
            draw.LineString([(x_3, y_3), (x_4, y_4)]),
            self.arc(coord_init1, coord_center1, -np.pi / 2),
            draw.LineString([(x_6, y_6), (x_7, y_7)]),
            arc2,
            draw.LineString([(x_9, y_9), (x_10, y_10)]), arc3, line11,
            # draw.translate(line12, 0, 2 * turnradius),
            # draw.translate(arc3, 0, 4 * turnradius),
            # draw.translate(line12, 0, 4 * turnradius),
            # draw.translate(arc4, 0, 4 * turnradius),
            # draw.translate(line12, 0, 6 * turnradius),
            # draw.translate(arc3, 0, 8 * turnradius),
            # draw.translate(line12, 0, 8 * turnradius),
            # arc(coord_init5,coord_center5,np.pi/2),
            draw.LineString([(x_17, y_17), (x_18, y_18)]),
            self.arc(coord_init6, coord_center6, -np.pi / 2),
            draw.LineString([(x_20, y_20), (x_21, y_21)])
        ]
        full_shape = geometry_list + geometry_list0
        cparm_line = draw.unary_union(full_shape)
        cparm = cparm_line.buffer(w / 2, cap_style=2, join_style=1)

        ## fix the gap resulting from buffer
        eps = 1e-3
        cparm = draw.Polygon(cparm.exterior)
        cparm = cparm.buffer(eps, join_style=2).buffer(-eps, join_style=2)

        # create combined objects for the signal line and the etch
        ro = draw.unary_union([cppatch, cparm])
        ro_etch = ro.buffer(g, cap_style=2, join_style=2)
        # x_15, y_15 = x_14, y_14 + 7 * turnradius
        x_22, y_22 = x_21 + g / 2, y_21

        port_line = draw.LineString([(x_21, y_21 + w / 2),
                                     (x_21, y_21 - w / 2)])
        subtract_patch = draw.LineString([(x_22, y_22 - w / 2 - g - eps),
                                          (x_22, y_22 + w / 2 + g + eps)
                                          ]).buffer(g / 2, cap_style=2)
        ro_etch = ro_etch.difference(subtract_patch)

        # inverse and mirror
        [ro, ro_etch, port_line] = draw.shapely.transform([ro, ro_etch, port_line], lambda x: -x)
        if (p.inverse == True):
            [ro, ro_etch, port_line] = draw.shapely.transform([ro, ro_etch, port_line], lambda x: -x)
        if (p.mirror == True):
            [ro, ro_etch, port_line] = draw.shapely.transform([ro, ro_etch, port_line], lambda x: x * [-1, 1])
            port_line = draw.LineString([port_line.coords[1], port_line.coords[0]])
        # rotate and translate
        polys = [ro, ro_etch, port_line]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        # update each object
        [ro, ro_etch, port_line] = polys

        # generate QGeometry
        self.add_qgeometry('poly', dict(ro=ro), chip=chip, layer=p.layer)
        self.add_qgeometry('poly',
                           dict(ro_etch=ro_etch),
                           chip=chip,
                           layer=p.layer_subtract,
                           subtract=p.subtract)

        # generate pins
        self.add_pin('readout', port_line.coords, width=w, gap=g, chip=chip)

        return x_21, y_21

    def arc(self, coord_init, coord_center, angle):
        '''
        Generate x,y coordinates (in terms of shapely.geometry.Point()) of an arc with:
        a specified initial point, rotation center, and
        rotation direction (specified by angle in radian (float or integer), positive is ccw).

        coord_init, and coord_center should be shapely.geometry.Point object
        '''
        # access to parse values from the user option
        p = self.p

        # local variable
        r = p.readout_cpw_turnradius
        step = p.arc_step

        # determine step number
        step_angle = step / r if angle >= 0 else -step / r
        step_N = abs(int(angle / step_angle))
        # laststep_flag = True if angle % step_angle != 0 else False
        laststep_flag = bool(angle % step_angle != 0)

        # generate coordinate
        coord = [coord_init]
        point = coord_init
        for i in range(step_N):
            point = draw.rotate(point,
                                step_angle,
                                origin=coord_center,
                                use_radians=True)
            coord.append(point)
        if laststep_flag:
            point = draw.rotate(coord_init,
                                angle,
                                origin=coord_center,
                                use_radians=True)
            coord.append(point)
        coord = draw.LineString(coord)
        return coord


class MyReadoutRes02(QComponent):
    '''
    The base ReadoutResFC class

    Inherits the QComponent class

    Readout resonator with polygon coupling for the flipchip dev.

    '''

    default_options = Dict(pos_x='0 um',
                           pos_y='0 um',
                           readout_coupling_width='80 um',
                           readout_coupling_height='150 um',
                           readout_cpw_width='5 um',
                           readout_cpw_gap='5 um',
                           readout_cpw_turnradius='50 um',
                           vertical_start_length='40 um',
                           vertical_end_length='200 um',
                           horizontal_start_length01='400 um',
                           # horizontal_start_length02 = '400 um',
                           horizontal_end_length='500 um',
                           total_length='4000 um',
                           arc_step='1 um',
                           meander_round='5',
                           orientation='0',
                           fillet='5 um',
                           layer='1',
                           layer_subtract='1',
                           horizontal_end_direction='1',
                           inverse=False,
                           mirror=False,
                           subtract=True,
                           chip='main',
                           )
    ''' Default drawing options ?? '''
    component_metadata = Dict(short_name='myreadoutres02',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='False')
    ''' Component metadata '''

    ##########################
    def make(self):
        ''' Make the head for readout res'''
        self.make_ro()

    ##########################
    def round_corner_rectangle(self, radius, rect):
        rect1 = rect.buffer(radius, join_style=1)
        rect1 = rect1.buffer(-2 * radius, join_style=1)
        rect1 = rect1.buffer(radius, join_style=1)
        return rect1

    def make_ro(self):
        '''
        Create the head of the readout resonator.
        Contains: the circular patch for coupling,
            the 45 deg line,
            the 45 deg arc,
            a short straight segment (of length w) for smooth subtraction
        '''
        # access to parsed values from the user option
        p = self.p

        # access to chip name
        chip = p.chip

        # local variables
        poly_w = p.readout_coupling_width
        poly_h = p.readout_coupling_height
        w = p.readout_cpw_width
        g = p.readout_cpw_gap
        turnradius = p.readout_cpw_turnradius
        N = p.meander_round
        l_1 = 0
        l_2 = p.vertical_start_length
        l_3 = p.horizontal_start_length01

        total_length = p.total_length
        left_length = l_2 + p.vertical_end_length \
                      + l_3 + p.horizontal_end_length + (N + 2.5) * np.pi * turnradius
        if (total_length <= left_length):
            l_4 = 0
        l_4 = (total_length - left_length) / (N + 1)
        l_5 = l_4
        l_6 = p.vertical_end_length
        l_7 = p.horizontal_end_length
        h_direction = p.horizontal_end_direction
        eps0 = 1e-2
        fillet = p.fillet

        # create the coupling patch in term of a circle
        cppatch = draw.rectangle(w=poly_w, h=poly_h, xoff=0, yoff=0)
        cppatch = self.round_corner_rectangle(fillet, cppatch)
        line_joint = draw.LineString([(0, poly_h / 2), (0, poly_h / 2 + 2.5 * eps0)]).buffer(w / 2, cap_style=3)
        cppatch = draw.unary_union([cppatch, line_joint])
        cppatch = self.round_corner_rectangle(0.2 * eps0, cppatch)

        # create the extended arm
        ## useful coordinates

        x_3, y_3 = 0, poly_h / 2 + 2.5 * eps0
        x_4, y_4 = x_3, y_3 + l_2 - 2.5 * eps0
        x_5, y_5 = x_4 + turnradius, y_4
        # coord_x2 = draw.Point(x_2,y_2)
        coord_init1 = draw.Point(x_4, y_4)
        coord_center1 = draw.Point(x_5, y_5)
        x_6, y_6 = x_5, y_5 + turnradius
        x_7, y_7 = x_5 + l_3, y_6
        x_8, y_8 = x_7, y_7 + turnradius
        coord_x6 = draw.Point(x_6, y_6)
        coord_init2 = draw.Point((x_7, y_7))
        coord_center2 = draw.Point((x_8, y_8))

        arc2 = self.arc(coord_init2, coord_center2, np.pi)

        x_9, y_9 = x_8, y_8 + turnradius
        x_10, y_10 = x_8 - l_4, y_9
        x_11, y_11 = x_10, y_10 + turnradius
        coord_x9 = draw.Point((x_9, y_9))
        coord_init3 = draw.Point((x_10, y_10))
        coord_center3 = draw.Point((x_11, y_11))

        line11 = draw.LineString([(x_9, y_9), (x_10, y_10)])

        arc3 = self.arc(coord_init3, coord_center3, -np.pi)
        x_12, y_12 = x_11, y_11 + turnradius
        x_13, y_13 = x_12 + l_5, y_12

        # line12 = draw.LineString([(x_12, y_12), (x_13, y_13)])
        # x_14, y_14 = x_13, y_13 + turnradius
        # coord_x12 = draw.Point(x_12,y_12)
        # coord_init4 = draw.Point((x_13, y_13))
        # coord_center4 = draw.Point((x_14, y_14))
        # arc4 = self.arc(coord_init4, coord_center4, np.pi)

        # x_15,y_15 = x_13, y_13+4*2*turnradius
        # x_16,y_16 = x_15,y_15 + turnradius
        # x_17,y_17 = x_16+turnradius, y_16
        # coord_init5 = draw.Point(x_15,y_15)
        # coord_center5 = draw.Point(x_16,y_16)
        geometry_list = []
        round_num = math.ceil((N - 1) / 2) + 1
        for i in range(int(N - 1)):
            geometry_list.append(draw.translate(line11, 0, (i + 1) * 2 * turnradius))
            if (i % 2 == 0):
                geometry_list.append(draw.translate(arc2, 0, (i + 2) * 2 * turnradius))
            else:
                geometry_list.append(draw.translate(arc3, 0, (i + 1) * 2 * turnradius))

        geometry_list.append(draw.translate(line11, 0, N * 2 * turnradius))

        if ((N - 1) % 2 == 0):
            x_15, y_15 = x_13, y_13 + (N - 1) * 2 * turnradius
            x_16, y_16 = x_15, y_15 + turnradius
            x_17, y_17 = x_16 + turnradius, y_16
            coord_init5 = draw.Point(x_15, y_15)
            coord_center5 = draw.Point(x_16, y_16)
            geometry_list.append(self.arc(coord_init5, coord_center5, np.pi / 2))
        else:
            x_15, y_15 = x_12, y_12 + (N - 1) * 2 * turnradius
            x_16, y_16 = x_15, y_15 + turnradius
            x_17, y_17 = x_16 - turnradius, y_16
            coord_init5 = draw.Point(x_15, y_15)
            coord_center5 = draw.Point(x_16, y_16)
            geometry_list.append(self.arc(coord_init5, coord_center5, -np.pi / 2))

        x_18, y_18 = x_17, y_17 + l_6

        x_19, y_19 = x_18 + int(h_direction) * turnradius, y_18
        x_20, y_20 = x_19, y_19 + turnradius
        x_21, y_21 = x_20 + int(h_direction) * l_7, y_20
        angle_arc = -1 * int(h_direction) * np.pi / 2
        # else:
        #     x_19,y_19 = x_18+turnradius,y_18
        #     x_20, y_20 = x_19 , y_19+turnradius
        #     x_21,y_21 = x_20+l_7,y_20
        #     angle_arc = -np.pi/2

        # x_19, y_19 = x_18 + turnradius, y_18
        coord_init6 = draw.Point((x_18, y_18))
        coord_center6 = draw.Point((x_19, y_19))
        # x_20, y_20 = x_19, y_19 + turnradius
        # x_21, y_21 = x_20 + l_7, y_20

        geometry_list0 = [
            # draw.LineString([(0, 0), coord_init]),
            # arc(coord_init, coord_center, -np.pi / 4),
            draw.LineString([(x_3, y_3), (x_4, y_4)]),
            self.arc(coord_init1, coord_center1, -np.pi / 2),
            draw.LineString([(x_6, y_6), (x_7, y_7)]),
            arc2,
            draw.LineString([(x_9, y_9), (x_10, y_10)]), arc3, line11,
            # draw.translate(line12, 0, 2 * turnradius),
            # draw.translate(arc3, 0, 4 * turnradius),
            # draw.translate(line12, 0, 4 * turnradius),
            # draw.translate(arc4, 0, 4 * turnradius),
            # draw.translate(line12, 0, 6 * turnradius),
            # draw.translate(arc3, 0, 8 * turnradius),
            # draw.translate(line12, 0, 8 * turnradius),
            # arc(coord_init5,coord_center5,np.pi/2),
            draw.LineString([(x_17, y_17), (x_18, y_18)]),
            self.arc(coord_init6, coord_center6, angle_arc),
            draw.LineString([(x_20, y_20), (x_21, y_21)])
        ]
        full_shape = geometry_list + geometry_list0
        cparm_line = draw.unary_union(full_shape)
        cparm = cparm_line.buffer(w / 2, cap_style=2, join_style=1)

        ## fix the gap resulting from buffer
        eps = 1e-3
        cparm = draw.Polygon(cparm.exterior)
        cparm = cparm.buffer(eps, join_style=2).buffer(-eps, join_style=2)

        # create combined objects for the signal line and the etch
        ro = draw.unary_union([cppatch, cparm])
        ro_etch = ro.buffer(g, cap_style=2, join_style=1)
        # x_15, y_15 = x_14, y_14 + 7 * turnradius
        x_22, y_22 = x_21 + int(h_direction) * (g / 2 + eps), y_21

        port_line = draw.LineString([(x_21, y_21 + w / 2),
                                     (x_21, y_21 - w / 2)])
        if (h_direction == -1):
            port_line = draw.LineString([port_line.coords[1], port_line.coords[0]])
        subtract_patch = draw.LineString([(x_22, y_22 - w / 2 - g - eps),
                                          (x_22, y_22 + w / 2 + g + eps)
                                          ]).buffer((g / 2 + eps), cap_style=2)
        ro_etch = ro_etch.difference(subtract_patch)

        # inverse and mirror
        [ro, ro_etch, port_line] = draw.shapely.transform([ro, ro_etch, port_line], lambda x: -x)
        if (p.inverse == True):
            [ro, ro_etch, port_line] = draw.shapely.transform([ro, ro_etch, port_line], lambda x: -x)
        if (p.mirror == True):
            [ro, ro_etch, port_line] = draw.shapely.transform([ro, ro_etch, port_line], lambda x: x * [-1, 1])
            port_line = draw.LineString([port_line.coords[1], port_line.coords[0]])
        # rotate and translate
        polys = [ro, ro_etch, port_line]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        # update each object
        [ro, ro_etch, port_line] = polys

        # generate QGeometry
        self.add_qgeometry('poly', dict(ro=ro), chip=chip, layer=p.layer)
        self.add_qgeometry('poly',
                           dict(ro_etch=ro_etch),
                           chip=chip,
                           layer=p.layer_subtract,
                           subtract=p.subtract)

        # generate pins
        self.add_pin('readout', port_line.coords, width=w, gap=g, chip=chip)

        return x_21, y_21

    def arc(self, coord_init, coord_center, angle):
        '''
        Generate x,y coordinates (in terms of shapely.geometry.Point()) of an arc with:
        a specified initial point, rotation center, and
        rotation direction (specified by angle in radian (float or integer), positive is ccw).

        coord_init, and coord_center should be shapely.geometry.Point object
        '''
        # access to parse values from the user option
        p = self.p

        # local variable
        r = p.readout_cpw_turnradius
        step = p.arc_step

        # determine step number
        step_angle = step / r if angle >= 0 else -step / r
        step_N = abs(int(angle / step_angle))
        # laststep_flag = True if angle % step_angle != 0 else False
        laststep_flag = bool(angle % step_angle != 0)

        # generate coordinate
        coord = [coord_init]
        point = coord_init
        for i in range(step_N):
            point = draw.rotate(point,
                                step_angle,
                                origin=coord_center,
                                use_radians=True)
            coord.append(point)
        if laststep_flag:
            point = draw.rotate(coord_init,
                                angle,
                                origin=coord_center,
                                use_radians=True)
            coord.append(point)
        coord = draw.LineString(coord)
        return coord


class MyFluxLine01(QComponent):
    """
   The flip chip flux line class

   Inherits the QComponent class

   flux line for the flip chip dev. Written for the flip chip tutorial.

   """
    default_options = Dict(pos_x='0 um',
                           pos_y='0 um',
                           l_1='8.5 um',
                           l_2='12 um',
                           l_3='28 um',
                           l_4='28 um',
                           l_5='50 um',
                           flux_cpw_width='5 um',
                           flux_cpw_gap='2.5 um',
                           # readout_cpw_turnradius='50 um',
                           # vertical_start_length = '40 um',
                           # vertical_end_length = '200 um',
                           # horizontal_start_length01= '400 um',
                           # horizontal_start_length02 = '400 um',
                           # horizontal_end_length = '500 um',
                           # total_length = '4000 um',
                           # arc_step='1 um',
                           # meander_round = '5',
                           orientation='0',
                           layer='1',
                           layer_subtract='2',
                           inverse=False,
                           mirror=False,
                           subtract=True,
                           chip='main',
                           _default_connection_pads=Dict())
    ''' Default drawing options ?? '''
    component_metadata = Dict(short_name='myfluxline01',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='False')
    ''' Component metadata '''

    def round_corner(self, radius, line):
        # line1 = line.buffer(1,cap_style=2)
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        p = self.p

        w = p.flux_cpw_width
        g = p.flux_cpw_gap
        inverse = p.inverse
        mirror = p.mirror
        orientation = p.orientation
        pos_x = p.pos_x
        pos_y = p.pos_y
        pin = Dict(middle=np.array([w / 2, -(p.l_3 / 2 + p.l_1)]), normal=np.array([0, 1]))
        pts_list = []
        z_line = QRouteLead()
        z_line.seed_from_pin(pin=pin)
        pts_list.append(np.array([w / 2, -(p.l_3 / 2 + p.l_1)]))
        z_line.go_straight(p.l_1)
        pts_list.append(z_line.get_tip().position)

        z_line.go_right(p.l_2)
        pts_list.append(z_line.get_tip().position)

        z_line.go_left(p.l_3)
        pts_list.append(z_line.get_tip().position)

        z_line.go_left(p.l_4)
        pts_list.append(z_line.get_tip().position)

        z_line.go_left(p.l_5)
        pts_list.append(z_line.get_tip().position)

        line = draw.LineString(pts_list)
        line = line.buffer(w / 2, cap_style=2, join_style=1)

        eps = 1e-3
        # line = draw.Polygon(line.exterior)
        # line = line.buffer(eps, join_style=2).buffer(-eps, join_style=2)
        line = self.round_corner(eps, line)

        # revise the end for flat
        pts_end = pts_list[-1] + [0, w / 2]
        revise_line_e = draw.LineString([pts_list[-1], pts_end])
        revise_polygon_e = revise_line_e.buffer(w / 2, cap_style=2)
        pts_start = pts_list[0] + [0, p.l_1 / 2]
        revise_line_s = draw.LineString([pts_list[0], pts_start])
        revise_polygon_s = revise_line_s.buffer(w / 2, cap_style=2)
        line = draw.unary_union([line, revise_polygon_s, revise_polygon_e])

        pts_pin0 = pts_list[-1] - [w / 2, 0]
        pts_pin1 = pts_list[-1] + [w / 2, 0]
        pin_line = draw.LineString([pts_pin1, pts_pin0])
        line_etch = line.buffer(g, cap_style=2, join_style=2)
        line_etch = self.round_corner(eps, line_etch)

        # cut the remaining etch for beginning and end
        x_s, y_s = np.array([w / 2, -(p.l_3 / 2 + p.l_1)]) - [0, g / 2]
        subtract_patch_s = draw.LineString([(x_s - w / 2 - g - eps, y_s),
                                            (x_s + w / 2 + g + eps, y_s)
                                            ]).buffer(g / 2, cap_style=2)
        line_etch = line_etch.difference(subtract_patch_s)

        x_e, y_e = pts_list[-1] - [0, g / 2]
        subtract_patch_e = draw.LineString([(x_e - w / 2 - g - eps, y_e),
                                            (x_e + w / 2 + g + eps, y_e)
                                            ]).buffer(g / 2, cap_style=2)
        line_etch = line_etch.difference(subtract_patch_e)
        line_etch = line_etch.difference(subtract_patch_s)

        if (inverse == True):
            [line, line_etch, pin_line] = draw.shapely.transform([line, line_etch, pin_line], lambda x: -x)
        if (mirror == True):
            [line, line_etch, pin_line] = draw.shapely.transform([line, line_etch, pin_line], lambda x: x * [-1, 1])
            pin_line = draw.LineString([pin_line.coords[1], pin_line.coords[0]])

        # rotate and translate
        polys = [line, line_etch, pin_line]
        polys = draw.rotate(polys, orientation, origin=(0, 0))
        polys = draw.translate(polys, pos_x, pos_y)

        # update each object
        [line, line_etch, pin_line] = polys

        # generate QGeometry
        self.add_qgeometry('poly', dict(line=line), chip=p.chip)
        self.add_qgeometry('poly',
                           dict(line_etch=line_etch),
                           chip=p.chip,
                           subtract=p.subtract)

        # generate pins
        self.add_pin('flux_pin', pin_line.coords, width=w, gap=g, chip=p.chip)


class MyFluxLine02(QComponent):
    """
   The flip chip flux line class

   Inherits the QComponent class

   complete flux line for the flip chip dev(including connector). Written for the flip chip tutorial.

   """
    default_options = Dict(pos_x='0 um',
                           pos_y='0 um',
                           l_1='8.5 um',
                           l_2='12 um',
                           l_3='28 um',
                           l_4='28 um',
                           l_5='50 um',
                           flux_cpw_width='5 um',
                           flux_cpw_gap='3 um',
                           flux_cpw_width0='10 um',
                           flux_cpw_gap0='6 um',
                           end_yposition='330 um',
                           end_horizontal_length='50 um',
                           c_length='15 um',
                           angle='-45',
                           angle_end='45',
                           fillet='30 um',
                           # vertical_start_length = '40 um',
                           # vertical_end_length = '200 um',
                           # horizontal_start_length01= '400 um',
                           # horizontal_start_length02 = '400 um',
                           # horizontal_end_length = '500 um',
                           # total_length = '4000 um',
                           # arc_step='1 um',
                           # meander_round = '5',
                           orientation='0',
                           layer='1',
                           layer_subtract='1',
                           inverse=False,
                           mirror=False,
                           subtract=True,
                           chip='main',
                           _default_connection_pads=Dict())
    ''' Default drawing options ?? '''
    component_metadata = Dict(short_name='myfluxline02',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='False')
    ''' Component metadata '''

    def round_corner(self, radius, line):
        # line1 = line.buffer(1,cap_style=2)
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def vector_rotation(self, vec, angle):
        theta = np.deg2rad(angle)
        rot = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
        return np.dot(rot, vec)

    def arc(self, coord_init, coord_center, angle):
        '''
        Generate x,y coordinates (in terms of shapely.geometry.Point()) of an arc with:
        a specified initial point, rotation center, and
        rotation direction (specified by angle in radian (float or integer), positive is ccw).

        coord_init, and coord_center should be shapely.geometry.Point object
        '''
        # access to parse values from the user option
        p = self.p

        # local variable
        r = p.fillet
        step = 1e-4
        angle = np.pi * angle / 180
        coord_center = draw.Point(coord_center)

        # determine step number
        step_angle = step / r if angle >= 0 else -step / r
        step_N = abs(int(angle / step_angle))
        # laststep_flag = True if angle % step_angle != 0 else False
        laststep_flag = bool(angle % step_angle != 0)

        # generate coordinate
        coord = []
        point = draw.Point(coord_init)
        for i in range(step_N):
            point = draw.rotate(point,
                                step_angle,
                                origin=coord_center,
                                use_radians=True)

            coord.append(np.array(point.coords[0]))
        if laststep_flag:
            point = draw.rotate(draw.Point(coord_init),
                                angle,
                                origin=coord_center,
                                use_radians=True)
            coord.append(np.array(point.coords[0]))
        return coord

    def make(self):
        p = self.p

        w = p.flux_cpw_width
        g = p.flux_cpw_gap
        w0 = p.flux_cpw_width0
        g0 = p.flux_cpw_gap0
        inverse = p.inverse
        mirror = p.mirror
        orientation = p.orientation
        pos_x = p.pos_x
        pos_y = p.pos_y
        y_position = p.end_yposition
        c_length = p.c_length
        angle = p.angle
        angle_end = p.angle_end
        length1 = (p.l_3 / 2 - p.l_5 - c_length * math.cos(angle * math.pi / 180) + y_position) / (
                2 * math.cos(angle * math.pi / 180))
        length2 = length1
        length3 = p.end_horizontal_length

        pin = Dict(middle=np.array([w / 2, -(p.l_3 / 2 + p.l_1)]), normal=np.array([0, 1]))
        pts_list = []
        z_line = QRouteLead()
        z_line.seed_from_pin(pin=pin)
        pts_list.append(np.array([w / 2, -(p.l_3 / 2 + p.l_1)]))
        z_line.go_straight(p.l_1)
        pts_list.append(z_line.get_tip().position)

        z_line.go_right(p.l_2)
        pts_list.append(z_line.get_tip().position)

        z_line.go_left(p.l_3)
        pts_list.append(z_line.get_tip().position)

        z_line.go_left(p.l_4)
        pts_list.append(z_line.get_tip().position)

        if angle == 0:
            length_c1 = p.l_5
        else:
            length_c1 = p.l_5 - abs(p.fillet * (1 - math.cos(math.radians(angle))) / math.sin(math.radians(angle)))
        z_line.go_left(length_c1)
        pts_list.append(z_line.get_tip().position)

        center = z_line.get_tip().position + self.vector_rotation(z_line.get_tip().direction,
                                                                  np.sign(angle) * 90) * p.fillet

        arc_list = self.arc(z_line.get_tip().position, center, angle)
        pts_list = pts_list + arc_list
        pin1 = Dict(middle=pts_list[-1], normal=self.vector_rotation(z_line.get_tip().direction, angle))
        z_line.seed_from_pin(pin=pin1)
        if angle == 0:
            length_c2 = length1
        else:
            length_c2 = length1 - abs(p.fillet * (1 - math.cos(math.radians(angle))) / math.sin(math.radians(angle)))
        z_line.go_straight(length_c2)

        # z_line.go_left(p.l_5)
        # pts_list.append(z_line.get_tip().position)
        # 
        # z_line.go_angle(length1,angle)

        pts_list.append(z_line.get_tip().position)

        # determine four points for connector
        x_0 = pts_list[-1] + w / 2 * np.array([math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        x_1 = pts_list[-1] - w / 2 * np.array([math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        x_m = pts_list[-1] + c_length * z_line.get_tip().direction
        x_2 = x_m - w0 / 2 * np.array([math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        x_3 = x_m + w0 / 2 * np.array([math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        pts = [x_0, x_1, x_2, x_3]
        connector = draw.Polygon(pts)

        # draw second part
        pin2 = Dict(middle=x_m, normal=z_line.get_tip().direction)
        pts_list0 = []
        z_line0 = QRouteLead()

        z_line0.seed_from_pin(pin=pin2)
        pts_list0.append(z_line0.get_tip().position)

        if angle_end == 0:
            length2_c = length2
        else:
            length2_c = length2 - abs(
                p.fillet * (1 - math.cos(math.radians(angle_end))) / math.sin(math.radians(angle_end)))

        z_line0.go_straight(length2_c)
        pts_list0.append(z_line0.get_tip().position)

        center0 = z_line0.get_tip().position + self.vector_rotation(z_line0.get_tip().direction,
                                                                    np.sign(angle_end) * 90) * p.fillet

        arc_list0 = self.arc(z_line0.get_tip().position, center0, angle_end)
        pts_list0 = pts_list0 + arc_list0
        pin3 = Dict(middle=pts_list0[-1], normal=self.vector_rotation(z_line0.get_tip().direction, angle_end))
        z_line0.seed_from_pin(pin=pin3)
        if angle_end == 0:
            length3_c = length3
        else:
            length3_c = length3 - abs(
                p.fillet * (1 - math.cos(math.radians(angle_end))) / math.sin(math.radians(angle_end)))
        z_line0.go_straight(length3_c)

        # z_line0.go_straight(length2)
        # pts_list0.append(z_line0.get_tip().position)
        #
        # z_line0.go_angle(length3,angle_end)
        pts_list0.append(z_line0.get_tip().position)

        line = draw.LineString(pts_list)
        line = line.buffer(w / 2, cap_style=2, join_style=1)

        line0 = draw.LineString(pts_list0)
        line0 = line0.buffer(w0 / 2, cap_style=2, join_style=1)

        eps = 1e-3

        line = self.round_corner(eps, line)
        line0 = self.round_corner(eps, line0)
        zline0_direction_v = self.vector_rotation(z_line0.get_tip().direction, 90)

        # revise the end for flat
        pts_start0 = pts_list0[0] + 0.02 * z_line.get_tip().direction
        revise_line_s0 = draw.LineString([pts_list0[0], pts_start0])
        revise_polygon_s0 = revise_line_s0.buffer(w0 / 2, cap_style=2)
        pts_end0 = pts_list0[-1] - w0 / 2 * z_line0.get_tip().direction
        revise_line_e0 = draw.LineString([pts_list0[-1], pts_end0])
        revise_polygon_e0 = revise_line_e0.buffer(w0 / 2, cap_style=2)

        pts_start = pts_list[0] + p.l_1 / 2 * pin['normal']
        revise_line_s = draw.LineString([pts_list[0], pts_start])
        revise_polygon_s = revise_line_s.buffer(w / 2, cap_style=2)
        pts_end = pts_list[-1] - 0.02 * z_line.get_tip().direction
        revise_line_e = draw.LineString([pts_list[-1], pts_end])
        revise_polygon_e = revise_line_e.buffer(w / 2, cap_style=2)

        line = draw.unary_union([line, revise_polygon_s, revise_polygon_e, revise_polygon_s0, revise_polygon_e0])
        # line = draw.unary_union([line,revise_polygon_s,])

        pts_pin0 = pts_list0[-1] - w0 / 2 * zline0_direction_v
        pts_pin1 = pts_list0[-1] + w0 / 2 * zline0_direction_v
        pin_line = draw.LineString([pts_pin1, pts_pin0])

        line_etch = line.buffer(g, cap_style=2, join_style=2)
        line0_etch = line0.buffer(g0, cap_style=2, join_style=2)
        line_etch = self.round_corner(eps, line_etch)
        line0_etch = self.round_corner(eps, line0_etch)
        x_0_etch = pts_list[-1] + (w / 2 + g) * np.array(
            [math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        x_1_etch = pts_list[-1] - (w / 2 + g) * np.array(
            [math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        x_2_etch = x_m - (w0 / 2 + g0) * np.array([math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        x_3_etch = x_m + (w0 / 2 + g0) * np.array([math.cos(angle / 180 * math.pi), math.sin(angle / 180 * math.pi)])
        pts_etch = [x_0_etch, x_1_etch, x_2_etch, x_3_etch]
        connector_etch = draw.Polygon(pts_etch)

        line = draw.unary_union([line, line0, connector])
        line_etch = draw.unary_union([line_etch, line0_etch, connector_etch])

        # cut the remaining etch for beginning and end
        eps = 1e-3

        x_s, y_s = np.array([w / 2, -(p.l_3 / 2 + p.l_1)]) - [0, g / 2]
        subtract_patch_s = draw.LineString([(x_s - w / 2 - g - eps, y_s),
                                            (x_s + w / 2 + g + eps, y_s)
                                            ]).buffer(g / 2, cap_style=2)
        line_etch = line_etch.difference(subtract_patch_s)

        # x_e, y_e = pts_list0[-1]-[g0/2, 0]
        # subtract_patch_e = draw.LineString([(x_e, y_e- w0 / 2 - g0 - eps ),
        #                                       (x_e, y_e+ w0 / 2 + g0 + eps)
        #                                      ]).buffer(g0 / 2, cap_style=2)
        # line_etch = line_etch.difference(subtract_patch_e)

        x_e, y_e = pts_list0[-1] + z_line0.get_tip().direction * g0 / 2
        # zline0_direction_v = self.vector_rotation(z_line0.get_tip().direction,90)
        x_e1, y_e1 = np.array([x_e, y_e]) + zline0_direction_v * (w0 / 2 + g0 + eps)
        x_e2, y_e2 = np.array([x_e, y_e]) - zline0_direction_v * (w0 / 2 + g0 + eps)
        subtract_patch_e = draw.LineString([(x_e1, y_e1),
                                            (x_e2, y_e2)
                                            ]).buffer(g0 / 2, cap_style=2)

        line_etch = line_etch.difference(subtract_patch_e)
        # line_etch = line_etch.difference(subtract_patch_s)

        if (inverse == True):
            [line, line_etch, pin_line] = draw.shapely.transform([line, line_etch, pin_line], lambda x: -x)
        if (mirror == True):
            [line, line_etch, pin_line] = draw.shapely.transform([line, line_etch, pin_line], lambda x: x * [-1, 1])
            pin_line = draw.LineString([pin_line.coords[1], pin_line.coords[0]])
        # rotate and translate
        polys = [line, line_etch, pin_line]
        polys = draw.rotate(polys, orientation, origin=(0, 0))
        polys = draw.translate(polys, pos_x, pos_y)

        # update each object
        [line, line_etch, pin_line] = polys

        # generate QGeometry
        self.add_qgeometry('poly', dict(line=line), chip=p.chip)
        self.add_qgeometry('poly',
                           dict(line_etch=line_etch),
                           chip=p.chip,
                           subtract=p.subtract)

        # generate pins
        self.add_pin('flux_pin', pin_line.coords, width=w0, gap=g0, chip=p.chip)


class MyXYLine01(QComponent):
    """
   The flip chip flux line class

   Inherits the QComponent class

   flux line for the flip chip dev. Written for the flip chip tutorial.

   """
    default_options = Dict(pos_x='0 um',
                           pos_y='0 um',
                           l_1='200 um',
                           l_2='150 um',
                           l_3='50 um',
                           flux_cpw_width='5 um',
                           flux_cpw_gap='3 um',
                           flux_cpw_width0='10 um',
                           flux_cpw_gap0='6 um',
                           c_length='15 um',
                           angle='-90',
                           fillet='30 um',
                           orientation='0',
                           layer='1',
                           layer_subtract='2',
                           inverse=False,
                           mirror=False,
                           subtract=True,
                           chip='main',
                           _default_connection_pads=Dict())
    ''' Default drawing options ?? '''
    component_metadata = Dict(short_name='myxyline01',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='False')
    ''' Component metadata '''

    def round_corner(self, radius, line):
        # line1 = line.buffer(1,cap_style=2)
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def vector_rotation(self, vec, angle):
        theta = np.deg2rad(angle)
        rot = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
        return np.dot(rot, vec)

    def arc(self, coord_init, coord_center, angle):
        '''
        Generate x,y coordinates (in terms of shapely.geometry.Point()) of an arc with:
        a specified initial point, rotation center, and
        rotation direction (specified by angle in radian (float or integer), positive is ccw).

        coord_init, and coord_center should be shapely.geometry.Point object
        '''
        # access to parse values from the user option
        p = self.p

        # local variable
        r = p.fillet
        step = 1e-4
        angle = np.pi * angle / 180
        coord_center = draw.Point(coord_center)

        # determine step number
        step_angle = step / r if angle >= 0 else -step / r
        step_N = abs(int(angle / step_angle))
        # laststep_flag = True if angle % step_angle != 0 else False
        laststep_flag = bool(angle % step_angle != 0)

        # generate coordinate
        coord = []
        point = draw.Point(coord_init)
        for i in range(step_N):
            point = draw.rotate(point,
                                step_angle,
                                origin=coord_center,
                                use_radians=True)

            coord.append(np.array(point.coords[0]))
        if laststep_flag:
            point = draw.rotate(draw.Point(coord_init),
                                angle,
                                origin=coord_center,
                                use_radians=True)
            coord.append(np.array(point.coords[0]))
        return coord

    def make(self):
        p = self.p

        w = p.flux_cpw_width
        g = p.flux_cpw_gap
        w0 = p.flux_cpw_width0
        g0 = p.flux_cpw_gap0
        inverse = p.inverse
        mirror = p.mirror
        orientation = p.orientation
        pos_x = p.pos_x
        pos_y = p.pos_y
        # y_position = p.end_yposition
        c_length = p.c_length
        angle = p.angle
        l_1 = p.l_1
        l_2 = p.l_2
        l_3 = p.l_3

        # length1 = (p.l_3/2-p.l_5-c_length*math.cos(angle*math.pi/180)+y_position)/(2*math.cos(angle*math.pi/180))
        # length2 = length1
        # length3 = p.end_horizontal_length

        middle = np.array([0, 0])
        normal = np.array([-1, 0])
        pin = Dict(middle=middle, normal=normal)
        pts_list = []
        z_line = QRouteLead()
        z_line.seed_from_pin(pin=pin)
        pts_list.append(middle)

        if angle == 0:
            length_c1 = l_1
        else:
            length_c1 = l_1 - abs(p.fillet * (1 - math.cos(math.radians(angle))) / math.sin(math.radians(angle)))
        z_line.go_straight(length_c1)
        pts_list.append(z_line.get_tip().position)

        center = z_line.get_tip().position + self.vector_rotation(z_line.get_tip().direction,
                                                                  np.sign(angle) * 90) * p.fillet

        arc_list = self.arc(z_line.get_tip().position, center, angle)
        pts_list = pts_list + arc_list
        pin1 = Dict(middle=pts_list[-1], normal=self.vector_rotation(z_line.get_tip().direction, angle))
        z_line.seed_from_pin(pin=pin1)
        if angle == 0:
            length_c2 = l_2
        else:
            length_c2 = l_2 - abs(p.fillet * (1 - math.cos(math.radians(angle))) / math.sin(math.radians(angle)))
        z_line.go_straight(length_c2)

        # z_line.go_straight(l_1)
        # pts_list.append(z_line.get_tip().position)
        #
        # z_line.go_angle(l_2,angle)
        pts_list.append(z_line.get_tip().position)

        # determine four points for connector
        x_0 = pts_list[-1] + w / 2 * np.array([math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        x_1 = pts_list[-1] - w / 2 * np.array([math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        x_m = pts_list[-1] + c_length * z_line.get_tip().direction
        x_2 = x_m - w0 / 2 * np.array([math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        x_3 = x_m + w0 / 2 * np.array([math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        pts = [x_0, x_1, x_2, x_3]
        connector = draw.Polygon(pts)

        # draw second part
        pin2 = Dict(middle=x_m, normal=z_line.get_tip().direction)
        pts_list0 = []
        z_line0 = QRouteLead()

        z_line0.seed_from_pin(pin=pin2)
        pts_list0.append(z_line0.get_tip().position)

        z_line0.go_straight(l_3)
        pts_list0.append(z_line0.get_tip().position)

        line = draw.LineString(pts_list)
        line = line.buffer(w / 2, cap_style=2, join_style=1)

        line0 = draw.LineString(pts_list0)
        line0 = line0.buffer(w0 / 2, cap_style=2, join_style=1)

        eps = 1e-3
        line = self.round_corner(eps, line)
        line0 = self.round_corner(eps, line0)

        # revise the end for flat
        pts_start0 = pts_list0[0] + eps * 4 * z_line.get_tip().direction
        revise_line_s0 = draw.LineString([pts_list0[0], pts_start0])
        revise_polygon_s0 = revise_line_s0.buffer(w0 / 2, cap_style=2)
        pts_end0 = pts_list0[-1] - z_line0.get_tip().direction * eps * 4
        revise_line_e0 = draw.LineString([pts_list0[-1], pts_end0])
        revise_polygon_e0 = revise_line_e0.buffer(w0 / 2, cap_style=2)

        pts_start = pts_list[0] + normal * eps * 4
        revise_line_s = draw.LineString([pts_list[0], pts_start])
        revise_polygon_s = revise_line_s.buffer(w / 2, cap_style=2)
        pts_end = pts_list[-1] - eps * 4 * z_line.get_tip().direction
        revise_line_e = draw.LineString([pts_list[-1], pts_end])
        revise_polygon_e = revise_line_e.buffer(w / 2, cap_style=2)

        line = draw.unary_union([line, revise_polygon_s, revise_polygon_e, revise_polygon_s0, revise_polygon_e0])
        # line = draw.unary_union([line,revise_polygon_s,])

        zline0_direction_v = self.vector_rotation(z_line0.get_tip().direction, 90)
        pts_pin0 = pts_list0[-1] - w0 / 2 * zline0_direction_v
        pts_pin1 = pts_list0[-1] + w0 / 2 * zline0_direction_v
        pin_line = draw.LineString([pts_pin1, pts_pin0])
        #
        line_etch = line.buffer(g, cap_style=2, join_style=2)
        line0_etch = line0.buffer(g0, cap_style=2, join_style=2)
        line_etch = self.round_corner(eps, line_etch)
        line0_etch = self.round_corner(eps, line0_etch)
        x_0_etch = pts_list[-1] + (w / 2 + g) * np.array(
            [math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        x_1_etch = pts_list[-1] - (w / 2 + g) * np.array(
            [math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        x_2_etch = x_m - (w0 / 2 + g0) * np.array([math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        x_3_etch = x_m + (w0 / 2 + g0) * np.array([math.sin(angle / 180 * math.pi), math.cos(angle / 180 * math.pi)])
        pts_etch = [x_0_etch, x_1_etch, x_2_etch, x_3_etch]
        connector_etch = draw.Polygon(pts_etch)
        #
        line = draw.unary_union([line, line0, connector])
        line_etch = draw.unary_union([line_etch, line0_etch, connector_etch])

        # cut the remaining etch for beginning and end
        eps = 1e-3
        # x_s, y_s = middle-normal*g/2
        # normal_v =self.vector_rotation(normal,90)
        # x_s1,y_s1 = np.array([x_s,y_s])+normal_v*(w/2+g+eps)
        # x_s2,y_s2 = np.array([x_s,y_s])-normal_v*(w/2+g+eps)
        # subtract_patch_s = draw.LineString([(x_s1,y_s1 ),
        #                                       (x_s2,y_s2 )
        #                                      ]).buffer(g / 2, cap_style=2)
        # line_etch = line_etch.difference(subtract_patch_s)

        x_e, y_e = pts_list0[-1] + z_line0.get_tip().direction * g0 / 2
        # zline0_direction_v = self.vector_rotation(z_line0.get_tip().direction,90)
        x_e1, y_e1 = np.array([x_e, y_e]) + zline0_direction_v * (w0 / 2 + g0 + eps)
        x_e2, y_e2 = np.array([x_e, y_e]) - zline0_direction_v * (w0 / 2 + g0 + eps)
        subtract_patch_e = draw.LineString([(x_e1, y_e1),
                                            (x_e2, y_e2)
                                            ]).buffer(g0 / 2, cap_style=2)
        line_etch = line_etch.difference(subtract_patch_e)
        # line_etch = line_etch.difference(subtract_patch_s)

        if (inverse == True):
            [line, line_etch, pin_line] = draw.shapely.transform([line, line_etch, pin_line], lambda x: -x)
        if (mirror == True):
            [line, line_etch, pin_line] = draw.shapely.transform([line, line_etch, pin_line], lambda x: x * [-1, 1])
            pin_line = draw.LineString([pin_line.coords[1], pin_line.coords[0]])
        # rotate and translate
        polys = [line, line_etch, pin_line]
        polys = draw.rotate(polys, orientation, origin=(0, 0))
        polys = draw.translate(polys, pos_x, pos_y)

        # update each object
        [line, line_etch, pin_line] = polys

        # generate QGeometry
        self.add_qgeometry('poly', dict(line=line), chip=p.chip)
        self.add_qgeometry('poly',
                           dict(line_etch=line_etch),
                           chip=p.chip,
                           subtract=p.subtract)

        # generate pins
        self.add_pin('xy_pin', pin_line.coords, width=w0, gap=g0, chip=p.chip)


class RouteConnector(QRoute):
    """
    connect pins of two different sizes
    """
    default_options = Dict(
        layer='1',
        chip='main', )
    component_metadata = Dict(short_name='route_connector', _qgeometry_table_poly='True',
                              _qgeometry_table_junction='False')
    TOOLTIP = """ draw a polygon connecting two pins of different sizes"""

    def make(self):
        self.set_pin("start")
        self.set_pin("end")
        pin_pts = np.concatenate([self._get_connected_pin(self.options.pin_inputs.start_pin).points,
                                  self._get_connected_pin(self.options.pin_inputs.end_pin).points])
        self.make_elements(pin_pts)

    def line_extension(self, line, length):
        # specify the desired length of the extended line
        extended_length = length
        # calculate the current length of the line
        current_length = line.length

        # calculate the x- and y-distances between the line's endpoints
        dx = line.coords[1][0] - line.coords[0][0]
        dy = line.coords[1][1] - line.coords[0][1]

        # calculate the new endpoint of the extended line
        new_endpoint = (line.coords[1][0] + dx * (extended_length / current_length),
                        line.coords[1][1] + dy * (extended_length / current_length))
        return new_endpoint

    def make_elements(self, pts: np.ndarray):
        line = draw.Polygon(pts)
        line_start = draw.LineString(pts[:2])
        line_end = draw.LineString(pts[2:])
        pts_ex0 = self.line_extension(line_start, self._get_connected_pin(self.options.pin_inputs.start_pin).gap)
        pts_ex1 = self.line_extension(line_start, -(
                self._get_connected_pin(self.options.pin_inputs.start_pin).gap + line_start.length))
        pts_ex2 = self.line_extension(line_end, self._get_connected_pin(self.options.pin_inputs.end_pin).gap)
        pts_ex3 = self.line_extension(line_end,
                                      -(self._get_connected_pin(self.options.pin_inputs.end_pin).gap + line_end.length))
        pts_ex = np.array([pts_ex0, pts_ex1, pts_ex2, pts_ex3])
        line_etch = draw.Polygon(pts_ex)

        # compute actual final length
        p = self.p
        self.options._actual_length = str(
            line.length) + ' ' + self.design.get_units()

        # add the routing track to form the substrate core of the cpw
        self.add_qgeometry('poly', {'line': line}, chip=p.chip, layer=p.layer)
        self.add_qgeometry('poly', dict(line_etch=line_etch), layer=p.layer, chip=p.chip, subtract=True)


class MyConnector(QComponent):
    """
    connect pins of two different sizes
    """
    default_options = Dict(pos_x='0 um',
                           pos_y='0 um',
                           width='5 um',
                           gap='4 um',
                           width0='10 um',
                           gap0='6 um',
                           length='15 um',
                           orientation='0',
                           layer='1',
                           layer_subtract='2',
                           subtract=True,
                           chip='main', )
    component_metadata = Dict(short_name='my_connector', _qgeometry_table_poly='True',
                              _qgeometry_table_junction='False')
    TOOLTIP = """ draw a polygon connecting two pins of different sizes"""

    def make(self):
        p = self.p

        w = p.width
        g = p.gap
        w0 = p.width0
        g0 = p.gap0
        length = p.length
        orientation = p.orientation
        pos_x = p.pos_x
        pos_y = p.pos_y

        # draw polygon according to four vertex
        x_1 = np.array([length / 2, 0]) - np.array([0, w / 2])
        x_2 = np.array([length / 2, 0]) + np.array([0, w / 2])
        x_3 = np.array([-length / 2, 0]) + np.array([0, w0 / 2])
        x_4 = np.array([-length / 2, 0]) - np.array([0, w0 / 2])
        pts = np.array([x_1, x_2, x_3, x_4])
        line = draw.Polygon(pts)

        # draw etched polygon according to four vertex
        x_1_etch = np.array([length / 2, 0]) - np.array([0, w / 2 + g])
        x_2_etch = np.array([length / 2, 0]) + np.array([0, w / 2 + g])
        x_3_etch = np.array([-length / 2, 0]) + np.array([0, w0 / 2 + g0])
        x_4_etch = np.array([-length / 2, 0]) - np.array([0, w0 / 2 + g0])
        pts_etch = np.array([x_1_etch, x_2_etch, x_3_etch, x_4_etch])
        line_etch = draw.Polygon(pts_etch)

        # set pins
        pin_line = draw.LineString([x_2, x_1])
        pin_line0 = draw.LineString([x_4, x_3])

        # rotate and translate
        polys = [line, line_etch, pin_line0, pin_line]
        polys = draw.rotate(polys, orientation, origin=(0, 0))
        polys = draw.translate(polys, pos_x, pos_y)

        # update each object
        [line, line_etch, pin_line0, pin_line] = polys

        # generate QGeometry
        self.add_qgeometry('poly', dict(line=line), chip=p.chip)
        self.add_qgeometry('poly',
                           dict(line_etch=line_etch),
                           chip=p.chip,
                           subtract=p.subtract)

        # generate pins
        self.add_pin('c_pin_r', pin_line.coords, width=w, gap=g, chip=p.chip)
        self.add_pin('c_pin_l', pin_line0.coords, width=w0, gap=g0, chip=p.chip)


class MyTunableCoupler01(BaseQubit):
    """
    tunable coupler which couples between two qubits closed to each other
    """
    default_options = Dict(c_width='100um',
                           c_height='100um',
                           c_gap='16um',
                           m_width='20um',
                           m_height='60um',
                           m_etch_width='20um',
                           jj_pad_width='8um',
                           jj_pad_height='6um',
                           jj_etch_length='4um',
                           jj_etch_pad1_width='2um',
                           jj_etch_pad2_width='5um',
                           jj_sub_rect_width='100um',
                           jj_sub_rect_height='100um',
                           fl_length='10um',
                           fl_gap='2um',
                           fl_ground='3um',
                           fl_width='10um',
                           fillet='1um'
                           )

    component_metadata = Dict(short_name='my_tunable_coupler1',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    TOOLTIP = """One of the tunable couplers"""

    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """Builds the component."""
        p = self.p

        # Draw the charge island
        coupler_box = draw.rectangle(p.c_width, p.c_height, 0, 0)
        coupler_sub1 = draw.rectangle((p.c_width - p.m_width) / 2, p.m_height,
                                      -p.m_width / 2 - (p.c_width - p.m_width) / 4, 0)
        coupler_sub2 = draw.rectangle((p.c_width - p.m_width) / 2, p.m_height,
                                      p.m_width / 2 + (p.c_width - p.m_width) / 4, 0)
        coupler_sub3 = draw.rectangle((p.m_width - 2 * p.m_etch_width), p.m_height, 0, 0)
        coupler_sub = draw.union([coupler_sub1, coupler_sub2, coupler_sub3])
        coupler = draw.subtract(coupler_box, coupler_sub)
        coupler = self.round_corner(p.fillet, coupler)

        # draw subtract
        coupler_etch = coupler.buffer(p.c_gap, cap_style=2, join_style=2)
        rect_plus = draw.rectangle(p.jj_sub_rect_width, p.jj_sub_rect_height, 0,
                                   -p.c_height / 2 - p.c_gap - p.jj_sub_rect_height / 2)
        coupler_etch = draw.union([coupler_etch, rect_plus])
        coupler_etch = self.round_corner(p.fillet, coupler_etch)

        # draw Josephson Junction pad
        jj_pad = draw.rectangle(p.jj_pad_width, p.jj_pad_height, 0, -p.c_height / 2 - p.jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(p.jj_etch_pad1_width, p.jj_etch_length / 2, 0,
                                      -p.c_height / 2 - p.jj_pad_height + p.jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(p.jj_etch_pad2_width, p.jj_etch_length / 2, 0,
                                      -p.c_height / 2 - p.jj_pad_height + p.jj_etch_length * 0.75)
        jj_etch_pad = draw.union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)
        coupler = draw.union([coupler, jj_pad])

        # Draw the junction and flux line
        fl_y = -p.c_height / 2 - p.c_gap - p.jj_sub_rect_height - p.fl_ground - p.fl_gap - p.fl_width / 2
        rect_jj = draw.LineString(
            [(0, -p.c_height / 2 - p.jj_pad_height), (0, -p.c_height / 2 - p.c_gap - p.jj_sub_rect_height)
             ])

        flux_line = draw.LineString([[p.fl_length, fl_y],
                                     [0, fl_y],
                                     [0, fl_y - 0.01]])

        # rotate and translate
        polys = [coupler, coupler_etch, rect_jj, flux_line]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [coupler, coupler_etch, rect_jj, flux_line] = polys

        # Add to qgeometry
        self.add_qgeometry('poly', {
            'coupler': coupler,
        },
                           layer=p.layer)
        self.add_qgeometry('poly', {
            'coupler_subtract': coupler_etch,
        },
                           layer=p.layer,
                           subtract=True)

        self.add_qgeometry('path', {'flux_line': flux_line},
                           width=p.fl_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'flux_line_sub': flux_line},
                           width=p.fl_width + 2 * p.fl_gap,
                           subtract=True,
                           layer=p.layer)

        self.add_qgeometry('junction', dict(rect_jj=rect_jj), width=p.jj_pad_width)

        # Add pin
        self.add_pin('Flux',
                     points=np.array(flux_line.coords[-2:]),
                     width=p.fl_width,
                     input_as_norm=True)


class MyTunableCoupler02(BaseQubit):
    default_options = Dict(c_width='100um',
                           c_height='100um',
                           c_gap='16um',
                           m_width='20um',
                           jj_pad_width='8um',
                           jj_pad_height='6um',
                           jj_etch_length='4um',
                           jj_etch_pad1_width='2um',
                           jj_etch_pad2_width='5um',
                           jj_sub_rect_width='100um',
                           jj_sub_rect_height='100um',
                           fl_length='10um',
                           fl_gap='2um',
                           fl_ground='3um',
                           fl_width='10um',
                           fillet='1um'
                           )

    component_metadata = Dict(short_name='my_tunable_coupler1',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    TOOLTIP = """One of the tunable couplers"""

    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """Builds the component."""
        p = self.p

        # Draw the charge island
        coupler_box = draw.rectangle(p.c_width, p.c_height, 0, 0)
        coupler_sub = draw.rectangle(p.c_width - 2 * p.m_width, p.c_height - p.m_width, 0, -p.m_width / 2)
        coupler = draw.subtract(coupler_box, coupler_sub)

        # draw subtract
        coupler_etch = coupler.buffer(p.c_gap, cap_style=2, join_style=2)
        rect_plus = draw.rectangle(p.jj_sub_rect_width, p.jj_sub_rect_height, 0,
                                   p.c_height / 2 - p.m_width - p.c_gap - p.jj_sub_rect_height / 2)
        coupler_etch = draw.union([coupler_etch, rect_plus])
        coupler_etch = self.round_corner(p.fillet, coupler_etch)
        coupler = self.round_corner(p.fillet, coupler)

        jj_pad2 = draw.rectangle(2e-3, 6e-3,
                                 -7e-3, p.c_height / 2 - p.m_width - p.c_gap - p.jj_sub_rect_height + 3e-3)
        jj_top_pad2 = draw.rectangle(3e-3, 2e-3,
                                     -7.5e-3, p.c_height / 2 - p.m_width - p.c_gap - p.jj_sub_rect_height + 7e-3)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])

        coupler_etch = draw.subtract(coupler_etch, jj_pad2)

        # draw Josephson Junction pad
        jj_pad = draw.rectangle(p.jj_pad_width, p.jj_pad_height, 0, p.c_height / 2 - p.m_width - p.jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(p.jj_etch_pad1_width, p.jj_etch_length / 2, 0,
                                      p.c_height / 2 - p.m_width - p.jj_pad_height + p.jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(p.jj_etch_pad2_width, p.jj_etch_length / 2, 0,
                                      p.c_height / 2 - p.m_width - p.jj_pad_height + p.jj_etch_length * 0.75)
        jj_etch_pad = draw.union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)
        coupler = draw.union([coupler, jj_pad])

        # Draw the junction and flux line
        fl_y = p.c_height / 2 - p.m_width - p.c_gap - p.jj_sub_rect_height - p.fl_ground - p.fl_gap - p.fl_width / 2
        rect_jj = draw.LineString([(0, p.c_height / 2 - p.m_width - p.jj_pad_height),
                                   (0, p.c_height / 2 - p.m_width - p.c_gap - p.jj_sub_rect_height)])
        flux_line = draw.LineString([[p.fl_length, fl_y],
                                     [0, fl_y],
                                     [0, fl_y - 0.02]])

        # rotate and translate
        polys = [coupler, coupler_etch, rect_jj, flux_line]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [coupler, coupler_etch, rect_jj, flux_line] = polys

        # Add to qgeometry
        self.add_qgeometry('poly', {
            'coupler': coupler,
        },
                           layer=p.layer)
        self.add_qgeometry('poly', {
            'coupler_subtract': coupler_etch,
        },
                           layer=p.layer,
                           subtract=True)

        self.add_qgeometry('path', {'flux_line': flux_line},
                           width=p.fl_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'flux_line_sub': flux_line},
                           width=p.fl_width + 2 * p.fl_gap,
                           subtract=True,
                           layer=p.layer)

        self.add_qgeometry('junction', dict(rect_jj=rect_jj), width=p.jj_pad_width)

        # Add pin
        self.add_pin('Flux',
                     points=np.array(flux_line.coords[-2:]),
                     width=p.fl_width,
                     input_as_norm=True)


class MyTunableCoupler03(BaseQubit):
    """One of the tunable couplers Based off the implementation in
    https://arxiv.org/pdf/2011.01261.pdf.

    WIP - initial test structure

    Inherits `BaseQubit` class

    Description:
        Creates a tunable coupler, interdigitated capacitor to ground, with a junction to ground and a coupler arm.
        The shapes origin is shown with 0. X the location of the SQUID.

    ::

                            connection claw
                              _____
                X             |   |
             |       |     | | |     |       |
            |       |     | | |     |       | charge island
           |       |       |       |       |
        --------------------0--------------------

    .. image::
        TunableCoupler01.png

    .. meta::
        Tunable Coupler 01

    Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')

    BaseQubit Default Options:
        * connection_pads: empty Dict -- Currently not used, connection count is static. (WIP)
        * _default_connection_pads: empty Dict -- The default values for the (if any) connection lines of the qubit.

    Default Options:
        * c_width: '400um' -- The width (x-axis) of the interdigitated charge island
        * l_width: '20um' -- The width of lines forming the body and arms of the charge island
        * l_gap: '10um' -- The dielectric gap of the charge island to ground
        * a_height: '60um' -- The length of the arms forming the 'fingers' of the charge island
        * cp_height: '15um' -- The thickness (y-axis) of the connection claw
        * cp_arm_length: '30um' -- The length of the 'fingers' of the connection claw (Warning: can break
          the component if they are too long)
        * cp_arm_width: '6um' -- The width of the 'fingers' of the connection claw (Warning: can break
          the component if too wide)
        * cp_gap: '6um' -- The dielectric gap of the connection claw
        * cp_gspace: '3um' -- How much ground remains between the connection claw and the charge island
        * fl_width: '5um' -- Width of the flux line
        * fl_gap: '3um' -- Dielectric gap of the flux line
        * fl_length: '10um' -- Length of the flux line for mutual inductance to the SQUID
        * fl_ground: '2um' -- Amount of ground between the SQUID and the flux line
        * _default_connection_pads: Currently empty
    """

    default_options = Dict(c_width='400um',
                           l_width='20um',
                           l_gap='10um',
                           a_height='60um',
                           cp_height='15um',
                           cp_arm_length='30um',
                           cp_arm_width='6um',
                           cp_width='10um',
                           cp_gap='5um',
                           cp_length='10um',
                           cp_gspace='3um',
                           fl_width='5um',
                           fl_gap='3um',
                           fl_length='10um',
                           fl_ground='2um',
                           jj_pad_width='8um',
                           jj_pad_height='6um',
                           jj_etch_length='4um',
                           jj_etch_pad1_width='2um',
                           jj_etch_pad2_width='5um',
                           jj_sub_rect_width='100um',
                           jj_sub_rect_height='100um',
                           t_l_ratio='3',
                           fillet='1um'
                           )

    component_metadata = Dict(short_name='Pocket',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    TOOLTIP = """One of the tunable couplers"""

    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """Builds the component."""
        p = self.p

        # Draw the charge island
        btm = draw.shapely.geometry.box(-p.c_width / 2, -p.l_width / 2, 0,
                                        p.l_width / 2)

        x_spot = p.c_width / 2 - p.l_width / 2

        arm1 = draw.shapely.geometry.box(-(x_spot + p.l_width / 2),
                                         p.l_width / 2,
                                         -(x_spot - p.l_width / 2), p.a_height)
        arm2 = draw.shapely.geometry.box(-((x_spot) * 2 / 4 + p.l_width / 2),
                                         p.l_width / 2,
                                         -((x_spot) * 2 / 4 - p.l_width / 2),
                                         p.a_height)
        arm3 = draw.shapely.geometry.box(- p.l_width / 2, p.l_width / 2,
                                         0, p.a_height)

        # left_side = draw.shapely.ops.unary_union([btm, arm1, arm2, arm3])
        left_side = draw.shapely.ops.unary_union([btm, arm1, arm3])
        cap_island = draw.shapely.ops.unary_union([
            left_side,
            draw.shapely.affinity.scale(left_side,
                                        xfact=-1,
                                        yfact=1,
                                        origin=(0, 0))
        ])
        arm4 = draw.shapely.geometry.box(-p.l_width / 2, -p.l_width / 2 - p.t_l_ratio * p.a_height, p.l_width / 2,
                                         p.l_width / 2)
        cap_island = draw.union([cap_island, arm4])
        # cap_island = self.round_corner(p.fillet,cap_island)

        cap_subtract = cap_island.buffer(p.l_gap, cap_style=2, join_style=2)

        # draw Josephson Junction etch pad
        h = 18e-3 - p.l_gap
        etch_reference_point = -p.l_width / 2 - p.t_l_ratio * p.a_height - p.l_gap
        if h > 0:
            rect_plus = draw.rectangle(p.l_gap * 2 + p.l_width, h, 0, etch_reference_point - h / 2)
            cap_subtract = draw.union([cap_subtract, rect_plus])
            cap_subtract = self.round_corner(p.fillet, cap_subtract)
            etch_reference_point = -p.l_width / 2 - p.t_l_ratio * p.a_height - p.l_gap - h
        elif h < 0:
            rect_plus = draw.rectangle(p.l_gap * 2 + p.l_width, h, 0, etch_reference_point - h / 2)
            cap_subtract = draw.subtract(cap_subtract, rect_plus)
            cap_subtract = self.round_corner(p.fillet, cap_subtract)
            etch_reference_point = -p.l_width / 2 - p.t_l_ratio * p.a_height - p.l_gap - h
        # cap_subtract = self.round_corner(p.fillet, cap_subtract)
        cap_island = self.round_corner(p.fillet, cap_island)

        jj_pad2 = draw.rectangle(2e-3, 6e-3,
                                 -7e-3, etch_reference_point + 3e-3)
        jj_top_pad2 = draw.rectangle(3e-3, 2e-3,
                                     -7.5e-3, etch_reference_point + 7e-3)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])

        cap_subtract = draw.subtract(cap_subtract, jj_pad2)

        # draw Josephson Junction pad
        reference_point = -p.l_width / 2 - p.t_l_ratio * p.a_height + 1e-3
        jj_pad = draw.rectangle(p.jj_pad_width, p.jj_pad_height, 0, reference_point - p.jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(p.jj_etch_pad1_width, p.jj_etch_length / 2, 0,
                                      reference_point - p.jj_pad_height + p.jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(p.jj_etch_pad2_width, p.jj_etch_length / 2, 0,
                                      reference_point - p.jj_pad_height + p.jj_etch_length * 0.75)
        jj_etch_pad = draw.union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)
        cap_island = draw.union([cap_island, jj_pad])

        # Reference coordinates
        cpl_x = p.l_width / 2 + p.l_gap + p.cp_gspace + p.cp_gap + p.cp_arm_width
        cpl_y = p.a_height + p.l_gap + p.cp_gap + p.cp_gspace
        fl_y = etch_reference_point - p.fl_ground - p.fl_gap - p.fl_width / 2

        # Draw the junction and flux line
        rect_jj = draw.LineString([(0, reference_point - p.jj_pad_height),
                                   (0, etch_reference_point)])

        flux_line = draw.LineString([[- p.fl_length, fl_y],
                                     [0, fl_y],
                                     [0, fl_y - 0.01]])

        # Draw the connector
        con_pad = draw.shapely.geometry.box(-cpl_x, cpl_y, cpl_x, cpl_y + p.cp_height)
        con_pad1 = draw.shapely.geometry.box(-p.cp_width / 2, cpl_y + p.cp_height, p.cp_width / 2,
                                             cpl_y + p.cp_height + p.cp_length)

        con_arm_l = draw.shapely.geometry.box(-cpl_x, cpl_y - p.cp_arm_length, -cpl_x + p.cp_arm_width, cpl_y)

        con_arm_r = draw.shapely.geometry.box(cpl_x, cpl_y - p.cp_arm_length, cpl_x - p.cp_arm_width, cpl_y)

        con_body = draw.shapely.ops.unary_union([con_pad, con_pad1, con_arm_l, con_arm_r])

        con_sub = con_body.buffer(p.cp_gap, cap_style=3, join_style=2)

        con_pin = draw.LineString([[0, cpl_y + p.cp_height], [0, cpl_y + p.cp_height + p.cp_length]])

        # Rotate and translate.
        c_items = [
            cap_island, cap_subtract, rect_jj, con_body, con_sub, flux_line,
            con_pin
        ]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [
            cap_island, cap_subtract, rect_jj, con_body, con_sub, flux_line,
            con_pin
        ] = c_items

        # Add to qgeometry
        self.add_qgeometry('poly', {
            'cap_island': cap_island,
            'connector_body': con_body
        },
                           layer=p.layer)
        self.add_qgeometry('poly', {
            'cap_subtract': cap_subtract,
            'connector_sub': con_sub
        },
                           layer=p.layer,
                           subtract=True)

        self.add_qgeometry('path', {'flux_line': flux_line},
                           width=p.fl_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'flux_line_sub': flux_line},
                           width=p.fl_width + 2 * p.fl_gap,
                           subtract=True,
                           layer=p.layer)

        self.add_qgeometry('junction', dict(rect_jj=rect_jj), width=p.jj_pad_width)

        # Add pin
        self.add_pin('Control',
                     points=np.array(con_pin.coords),
                     width=p.cp_width,
                     input_as_norm=True)
        self.add_pin('Flux',
                     points=np.array(flux_line.coords[-2:]),
                     width=p.l_width,
                     input_as_norm=True)


class LongRangeTunableCoupler01(BaseQubit):
    default_options = Dict(p1_length='1mm',
                           p1_width='20um',
                           p2_length='1mm',
                           p2_width='20um',
                           coupling_width='30um',
                           coupling_length='50um',
                           finger_p_length='10um',
                           finger_p_width='50um',
                           finger_pp_length='300um',
                           finger_pp_width='50um',
                           finger_c_length='10um',
                           finger_c_width='50um',
                           finger_pc_space='3um',
                           finger_pp_space='5um',
                           finger_n='6',
                           finger_pp_n='2',
                           c_width='50um',
                           c_gap='100um',
                           c_gap1='50um',
                           pp_space='15um',
                           jj_pad_width='8um',
                           jj_pad_height='6um',
                           jj_etch_length='4um',
                           jj_etch_pad1_width='2um',
                           jj_etch_pad2_width='5um',
                           # jj_sub_rect_width='100um',
                           # jj_sub_rect_height='100um',
                           fl_length='10um',
                           fl_gap='2um',
                           fl_ground='3um',
                           fl_width='10um',
                           fillet='1um'
                           )

    component_metadata = Dict(short_name='long_range_tunable_coupler1',
                              _qgeometry_table_path='True',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    TOOLTIP = """One of the long range tunable couplers"""

    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """Builds the component."""
        p = self.p
        finger_space = p.finger_c_length + 2 * p.finger_pc_space
        c_coupler_pos_y = p.p1_width / 2 + p.finger_p_width + p.finger_pc_space + p.c_width / 2
        c_coupler_length = p.pp_space + 2 * p.finger_n * (p.finger_p_length + finger_space) - 2 * p.finger_pc_space

        # Draw the base
        p_coupler1 = draw.shapely.MultiLineString(
            [((-p.pp_space / 2, 0), (-p.pp_space / 2 - p.p1_length - p.p1_width / 2, 0),
              (-p.pp_space / 2 - p.p1_length - p.p1_width / 2, p.coupling_width / 2),
              (-p.pp_space / 2 - p.p1_length - p.p1_width / 2 - p.coupling_length, p.coupling_width / 2)),
             ((-p.pp_space / 2 - p.p1_length - p.p1_width / 2, 0),
              (-p.pp_space / 2 - p.p1_length - p.p1_width / 2, -p.coupling_width / 2),
              (-p.pp_space / 2 - p.p1_length - p.p1_width / 2 - p.coupling_length, -p.coupling_width / 2))]).buffer(
            p.p1_width / 2, cap_style=2, join_style=2)
        p_coupler2 = draw.shapely.MultiLineString(
            [((p.pp_space / 2, 0), (p.pp_space / 2 + p.p2_length + p.p2_width / 2, 0),
              (p.pp_space / 2 + p.p2_length + p.p2_width / 2, p.coupling_width / 2),
              (p.pp_space / 2 + p.p2_length + p.p2_width / 2 + p.coupling_length, p.coupling_width / 2)),
             ((p.pp_space / 2 + p.p2_length + p.p2_width / 2, 0),
              (p.pp_space / 2 + p.p2_length + p.p2_width / 2, -p.coupling_width / 2),
              (p.pp_space / 2 + p.p2_length + p.p2_width / 2 + p.coupling_length, -p.coupling_width / 2))]).buffer(
            p.p2_width / 2, cap_style=2, join_style=2)
        # p_coupler2 = draw.LineString([(p.pp_space/2, 0), (p.pp_space/2+p.p2_length, 0)]).buffer(p.p2_width/2,cap_style=2)
        # p_coupler1 = draw.rectangle(p.p1_length, p.p1_width, -p.p1_length/2-p.pp_space/4, 0)
        # p_coupler2 = draw.rectangle(p.p2_length, p.p2_width, p.p1_length/2+p.pp_space/4, 0)
        c_coupler = draw.rectangle(c_coupler_length, p.c_width, 0, c_coupler_pos_y)
        coupler_base = draw.union([p_coupler1, p_coupler2])
        coupler_all = draw.union([coupler_base, c_coupler])

        # Draw the finger
        pp_sp_width = 2 * p.finger_pp_n * (p.finger_pp_space + p.finger_pp_width)

        for i in range(int(p.finger_n)):
            finger_p1 = draw.rectangle(p.finger_p_length, p.finger_p_width,
                                       -p.pp_space / 2 - p.finger_p_length / 2 - i * (finger_space + p.finger_p_length),
                                       p.p1_width / 2 + p.finger_p_width / 2)
            finger_p2 = draw.rectangle(p.finger_p_length, p.finger_p_width,
                                       p.pp_space / 2 + p.finger_p_length / 2 + i * (finger_space + p.finger_p_length),
                                       p.p2_width / 2 + p.finger_p_width / 2)
            coupler_all = draw.union([coupler_all, finger_p1, finger_p2])
        for i in range(int(p.finger_pp_n)):
            finger_pp1 = draw.rectangle(p.finger_pp_length, p.finger_pp_width, -p.finger_pp_space / 2,
                                        -p.p1_width / 2 - p.finger_pp_space - p.finger_pp_width / 2 - 2 * i * (
                                                p.finger_pp_space + p.finger_pp_width))
            finger_pp2 = draw.rectangle(p.finger_pp_length, p.finger_pp_width, p.finger_pp_space / 2,
                                        -p.p1_width / 2 - 2 * p.finger_pp_space - 3 * p.finger_pp_width / 2 - 2 * i * (
                                                p.finger_pp_space + p.finger_pp_width))
            coupler_all = draw.union([coupler_all, finger_pp1, finger_pp2])
        finger_sp1 = draw.rectangle(p.finger_pp_width, pp_sp_width,
                                    -(p.finger_pp_length + p.finger_pp_space + p.finger_pp_width) / 2,
                                    -(p.p1_width + pp_sp_width) / 2)
        finger_sp2 = draw.rectangle(p.finger_pp_width, pp_sp_width,
                                    (p.finger_pp_length + p.finger_pp_space + p.finger_pp_width) / 2,
                                    -(p.p1_width + pp_sp_width) / 2)
        # finger_cc = draw.rectangle(p.pp_space - 2 * p.finger_pc_space, p.finger_c_width, 0,
        #                            p.p1_width / 2 + p.finger_pc_space + p.c_width / 2)
        finger_cc = draw.rectangle(p.pp_space - 2 * p.finger_pc_space, p.finger_c_width, 0,
                                   c_coupler_pos_y - p.c_width / 2 - p.finger_c_width / 2)
        coupler_all = draw.union([coupler_all, finger_sp1, finger_sp2, finger_cc])
        for i in range(int(p.finger_n)):
            finger_c1 = draw.rectangle(p.finger_c_length, p.finger_c_width,
                                       -(
                                               p.pp_space / 2 + p.finger_p_length + p.finger_pc_space + p.finger_c_length / 2 + i * (
                                               2 * p.finger_pc_space + p.finger_p_length + p.finger_c_length)),
                                       p.p1_width / 2 + p.finger_pc_space + p.finger_c_width / 2)
            finger_c2 = draw.rectangle(p.finger_c_length, p.finger_c_width,
                                       (
                                               p.pp_space / 2 + p.finger_p_length + p.finger_pc_space + p.finger_c_length / 2 + i * (
                                               2 * p.finger_pc_space + p.finger_p_length + p.finger_c_length)),
                                       p.p2_width / 2 + p.finger_pc_space + p.finger_c_width / 2)
            coupler_all = draw.union([coupler_all, finger_c1, finger_c2])

            # draw subtract
        etch_sub_length = 5e-3
        eps = 1e-4
        coupler_etch = coupler_base.buffer(p.c_gap, cap_style=2, join_style=2)
        coupler_etch_substract = draw.rectangle(p.c_gap - etch_sub_length + eps,
                                                2 * p.c_gap + p.coupling_width + p.p1_width + eps,
                                                p.pp_space / 2 + p.p1_length + p.coupling_length + p.p1_width / 2 + p.c_gap / 2 + etch_sub_length / 2 + eps / 2,
                                                0)
        coupler_etch_substract1 = draw.rectangle(2 * p.c_gap + p.coupling_length, p.c_gap - p.c_gap1,
                                                 p.pp_space / 2 + p.p1_length + p.coupling_length / 2 - eps,
                                                 (p.coupling_width + p.p1_width + p.c_gap1 + p.c_gap) / 2)
        coupler_etch_substract2 = draw.rectangle(2 * p.c_gap + p.coupling_length, p.c_gap - p.c_gap1,
                                                 p.pp_space / 2 + p.p1_length + p.coupling_length / 2 - eps,
                                                 -(p.coupling_width + p.p1_width + p.c_gap1 + p.c_gap) / 2)
        coupler_etch_substract = draw.unary_union(
            [coupler_etch_substract, coupler_etch_substract1, coupler_etch_substract2])
        coupler_etch_substract_mirror = draw.shapely.transform(coupler_etch_substract, lambda x: x * [-1, 1])
        coupler_etch = draw.subtract(coupler_etch, coupler_etch_substract)
        coupler_etch = draw.subtract(coupler_etch, coupler_etch_substract_mirror)
        # rect_plus = draw.rectangle(p.jj_sub_rect_width, p.jj_sub_rect_height, 0,
        #                            p.c_height / 2 - p.m_width - p.c_gap - p.jj_sub_rect_height / 2)
        # coupler_etch = draw.union([coupler_etch, rect_plus])
        # coupler_etch = self.round_corner(p.fillet, coupler_etch)
        # coupler = self.round_corner(p.fillet, coupler)
        #
        jj_pad2 = draw.rectangle(2e-3, 6e-3,
                                 -7e-3, p.p1_width / 2 + p.c_gap - 3e-3)
        jj_top_pad2 = draw.rectangle(3e-3, 2e-3,
                                     -7.5e-3, p.p1_width / 2 + p.c_gap - 7e-3)
        jj_pad2 = draw.unary_union([jj_top_pad2, jj_pad2])

        jj_pad2_mirror = draw.shapely.transform(jj_pad2, lambda x: x * [-1, 1])
        jj_pad2 = draw.unary_union([jj_pad2, jj_pad2_mirror])
        #
        coupler_etch = draw.subtract(coupler_etch, jj_pad2)

        # draw Josephson Junction pad
        jj_pad_pos_x = 0
        jj_pad_pos_y = p.p1_width / 2 + p.finger_p_width + p.finger_pc_space + p.c_width
        jj_pad = draw.rectangle(p.jj_pad_width, p.jj_pad_height, jj_pad_pos_x, jj_pad_pos_y + p.jj_pad_height / 2)
        jj_etch_pad1 = draw.rectangle(p.jj_etch_pad1_width, p.jj_etch_length / 2, jj_pad_pos_x,
                                      jj_pad_pos_y + p.jj_pad_height - p.jj_etch_length / 4)
        jj_etch_pad2 = draw.rectangle(p.jj_etch_pad2_width, p.jj_etch_length / 2, 0,
                                      jj_pad_pos_y + p.jj_pad_height - p.jj_etch_length * 0.75)
        jj_etch_pad = draw.union([jj_etch_pad1, jj_etch_pad2])
        jj_pad = draw.subtract(jj_pad, jj_etch_pad)
        coupler_all = draw.union([coupler_all, jj_pad])

        # Draw the junction and flux line
        fl_y = p.c_gap + p.p1_width / 2 + p.fl_ground + p.fl_gap + p.fl_width / 2
        rect_jj = draw.LineString([(jj_pad_pos_x, jj_pad_pos_y + p.jj_pad_height),
                                   (jj_pad_pos_x, p.p1_width / 2 + p.c_gap)])
        flux_line = draw.LineString([[p.fl_length, fl_y],
                                     [jj_pad_pos_x, fl_y],
                                     [jj_pad_pos_x, fl_y + 0.02]])

        # rotate and translate
        polys = [coupler_all, coupler_etch, rect_jj, flux_line]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [coupler_all, coupler_etch, rect_jj, flux_line] = polys

        # Add to qgeometry
        self.add_qgeometry('poly', {
            'coupler': coupler_all,
        },
                           layer=p.layer)
        self.add_qgeometry('poly', {
            'coupler_subtract': coupler_etch,
        },
                           layer=p.layer,
                           subtract=True)
        if p.fl_length != 0:
            self.add_qgeometry('path', {'flux_line': flux_line},
                               width=p.fl_width,
                               layer=p.layer)
            self.add_qgeometry('path', {'flux_line_sub': flux_line},
                               width=p.fl_width + 2 * p.fl_gap,
                               subtract=True,
                               layer=p.layer)

        self.add_qgeometry('junction', dict(rect_jj=rect_jj), width=p.jj_pad_width)

        # Add pin
        if p.fl_length != 0:
            self.add_pin('Flux',
                     points=np.array(flux_line.coords[-2:]),
                     width=p.fl_width,
                     input_as_norm=True)


class MyCoupledLineTee(QComponent):
    """Generates a three pin (+) structure comprised of a primary two pin CPW
    transmission line, and a secondary one pin neighboring CPW transmission
    line that is capacitively/inductively coupled to the primary. Such a
    structure can be used, as an example, for generating CPW resonator hangars
    off of a transmission line.

    Inherits QComponent class.

    ::

        +----------------------------+
        ------------------------------
        |
        |
        |
        |
        +

    .. image::
        CoupledLineTee.png

    .. meta::
        Coupled Line Tee

    Default Options:
        * prime_width: '10um' -- The width of the trace of the two pin CPW transmission line
        * prime_gap: '6um' -- The dielectric gap of the two pin CPW transmission line
        * second_width: '10um' -- The width of the trace of the one pin CPW transmission line
        * second_gap: '6um' -- The dielectric gap of the one pin CPW transmission line
        * coupling_space: '3um' -- The amount of ground plane between the two transmission lines
        * coupling_length: '100um' -- The length of parallel between the two transmission lines
          note: this includes the distance of the curved second of the second line
        * down_length: '100um' -- The length of the hanging part of the resonator, including the curved region
        * fillet: '25um'
        * mirror: False -- Flips the hanger around the y-axis
        * open_termination: True -- sets if the termination of the second line at the coupling side
          is an open to ground or short to ground
    """
    component_metadata = Dict(short_name='cpw', _qgeometry_table_path='True')
    """Component metadata"""

    # Currently setting the primary CPW length based on the coupling_length
    # May want it to be it's own value that the user can control?
    default_options = Dict(prime_width='10um',
                           prime_gap='5um',
                           second_width='10um',
                           second_gap='5um',
                           coupling_space='3um',
                           coupling_length='100um',
                           over_length='100um',
                           down_length='100um',
                           fillet='25um',
                           mirror=False,
                           open_termination=True)
    """Default connector options"""

    TOOLTIP = """Generates a three pin (+) 
    structure comprised of a primary two 
    pin CPW transmission line, and a 
    secondary one pin neighboring CPW 
    transmission line that is 
    capacitively/inductively coupled 
    to the primary."""

    def make(self):
        """Build the component."""
        p = self.p

        prime_cpw_length = p.coupling_length + 2 * p.over_length
        second_flip = 1
        if p.mirror:
            second_flip = -1

        # Primary CPW
        prime_cpw = draw.LineString([[-prime_cpw_length / 2, 0],
                                     [prime_cpw_length / 2, 0]])

        # Secondary CPW
        second_down_length = p.down_length
        second_y = -p.prime_width / 2 - p.prime_gap - p.coupling_space - p.second_gap - p.second_width / 2
        second_cpw = draw.LineString(
            [[second_flip * (-p.coupling_length / 2), second_y],
             [second_flip * (p.coupling_length / 2), second_y],
             [
                 second_flip * (p.coupling_length / 2),
                 second_y - second_down_length
             ]])

        second_termination = 0
        if p.open_termination:
            second_termination = p.second_gap

        second_cpw_etch = draw.LineString(
            [[
                second_flip * (-p.coupling_length / 2 - second_termination),
                second_y
            ], [second_flip * (p.coupling_length / 2), second_y],
                [
                    second_flip * (p.coupling_length / 2),
                    second_y - second_down_length
                ]])

        # Rotate and Translate
        c_items = [prime_cpw, second_cpw, second_cpw_etch]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [prime_cpw, second_cpw, second_cpw_etch] = c_items

        # Add to qgeometry tables
        self.add_qgeometry('path', {'prime_cpw': prime_cpw},
                           width=p.prime_width)
        self.add_qgeometry('path', {'prime_cpw_sub': prime_cpw},
                           width=p.prime_width + 2 * p.prime_gap,
                           subtract=True)
        self.add_qgeometry('path', {'second_cpw': second_cpw},
                           width=p.second_width,
                           fillet=p.fillet)
        self.add_qgeometry('path', {'second_cpw_sub': second_cpw_etch},
                           width=p.second_width + 2 * p.second_gap,
                           subtract=True,
                           fillet=p.fillet)

        # Add pins
        prime_pin_list = prime_cpw.coords
        second_pin_list = second_cpw.coords

        self.add_pin('prime_start',
                     points=np.array(prime_pin_list[::-1]),
                     width=p.prime_width,
                     input_as_norm=True)
        self.add_pin('prime_end',
                     points=np.array(prime_pin_list),
                     width=p.prime_width,
                     input_as_norm=True)
        self.add_pin('second_end',
                     points=np.array(second_pin_list[1:]),
                     width=p.second_width,
                     input_as_norm=True)


class FingerCapacitorTaper(QComponent):
    """
    A Tapered Finger Capacitor adapted from KQCircuits for Qiskit Metal.

    Includes interdigitated fingers with tapered leads to maintain impedance matching.

    Args:
        QComponent ([type]): QComponent base class
    """

    # 默认参数定义
    default_options = Dict(
        finger_number=5,  # Number of fingers
        finger_width='5um',  # Width of a finger
        finger_gap='3um',  # Gap between the fingers
        finger_length='20um',  # Length of the fingers (overlapping region)
        taper_length='60um',  # Length of the taper
        trace_width='10um',  # Width of the CPW trace (Input 'a' in KQ)
        trace_gap='6um',  # Gap of the CPW trace (Input 'b' in KQ)
        pos_x='0um',
        pos_y='0um',
        orientation='0.0',
        layer='1'
    )

    component_metadata = Dict(
        short_name='CapTaper',
        _qgeometry_table_path='True',
        _qgeometry_table_poly='True',
        _qgeometry_table_junction='False'
    )

    def make(self):
        """Builds the component."""
        p = self.p  # 解析后的参数字典

        # 1. 提取数值参数 (short_hands)
        n = int(p.finger_number)
        w = p.finger_width
        l = p.finger_length
        g = p.finger_gap
        t = p.taper_length

        # KQ 'a' mapped to trace_width, KQ 'b' mapped to trace_gap
        a = p.trace_width
        b = p.trace_gap

        # 计算手指区域的总宽度
        # total_width = n * w + (n-1) * g -> n*(w+g) - g
        total_width = float(n) * (w + g) - g

        # 2. 生成手指 (Fingers)
        # 逻辑：以 (0,0) 为中心生成手指，然后根据奇偶性左右平移
        fingers_list = []

        # 基础手指形状 (Centered at origin)
        base_finger = draw.rectangle(l, w)  # width=l, height=w

        for i in range(n):
            # Y轴偏移：从下往上排列，使整体居中
            # y_i = -total_width/2 + (当前手指底边偏移) + w/2
            y_pos = -total_width / 2 + i * (g + w) + w / 2

            # X轴偏移：奇偶交替
            # 偶数索引向左开口(连接左边)，奇数索引向右开口(连接右边)
            # KQ代码逻辑：i%2 (奇数) -> +g/2, else -g/2
            x_pos = g / 2 if i % 2 else -g / 2

            finger_poly = draw.translate(base_finger, x_pos, y_pos)
            fingers_list.append(finger_poly)

        fingers_union = unary_union(fingers_list)

        # 3. 生成金属渐变段 (Metal Tapers)
        # 左侧和右侧的金属梯形，连接手指区域和外部CPW

        # 手指区域的起始X坐标 (手指中心区域的一半)
        # KQ逻辑: (l + g) / 2
        block_half_width = (l + g) / 2

        # 右侧 Taper (Positive Metal)
        # 点顺时针: 左上 -> 右上 -> 右下 -> 左下
        taper_right_pts = [
            (block_half_width, total_width / 2),  # 连接手指区域顶部
            (block_half_width + t, a / 2),  # 连接CPW Port顶部
            (block_half_width + t, -a / 2),  # 连接CPW Port底部
            (block_half_width, -total_width / 2)  # 连接手指区域底部
        ]
        poly_taper_right = Polygon(taper_right_pts)

        # 左侧 Taper (镜像)
        poly_taper_left = draw.scale(poly_taper_right, -1, 1, origin=(0, 0))

        # 合并所有正向金属 (Conductor)
        conductor_poly = unary_union([fingers_union, poly_taper_right, poly_taper_left])

        # 4. 生成地平面掏空区域 (Ground Cutout / Gap)
        # 这是一个类似领结的形状，外扩以保持阻抗比率 (KQ: maintain a/b ratio)
        # 根据 KQ 源码: region_ground

        # 计算连接手指区域处的 Gap 宽度
        # 比例关系: gap_local / width_local = b / a
        # gap_local = width_local * (b / a)
        # Y_coord = width_local/2 + gap_local
        y_inner_corner = total_width / 2 + total_width * (b / a)
        y_outer_corner = a / 2 + b  # 标准 CPW 边缘

        gap_pts = [
            (block_half_width, y_inner_corner),
            (block_half_width + t, y_outer_corner),
            (block_half_width + t, -y_outer_corner),
            (block_half_width, -y_inner_corner),
            # 镜像到左边
            (-block_half_width, -y_inner_corner),
            (-block_half_width - t, -y_outer_corner),
            (-block_half_width - t, y_outer_corner),
            (-block_half_width, y_inner_corner)
        ]
        cutout_poly = Polygon(gap_pts)

        # 5. 旋转与定位 (Placement)
        # Qiskit Metal 处理旋转和平移的标准流程
        port_x_offset = block_half_width + t
        port_line1 = draw.LineString([[-port_x_offset, -a / 2], [-port_x_offset, a / 2]])
        port_line2 = draw.LineString([[port_x_offset, a / 2], [port_x_offset, -a / 2]])
        polys = [conductor_poly, cutout_poly, port_line1, port_line2]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [conductor_poly, cutout_poly, port_line1, port_line2] = polys

        # conductor_poly = draw.rotate(conductor_poly, p.orientation, origin=(0, 0))
        # conductor_poly = draw.translate(conductor_poly, p.pos_x, p.pos_y)
        #
        # cutout_poly = draw.rotate(cutout_poly, p.orientation, origin=(0, 0))
        # cutout_poly = draw.translate(cutout_poly, p.pos_x, p.pos_y)

        # 6. 添加几何体到表格
        self.add_qgeometry('poly', {'connector': conductor_poly}, layer=p.layer)
        self.add_qgeometry('poly', {'cutout': cutout_poly}, subtract=True, layer=p.layer)

        # 7. 添加端口 (Pins)
        # 计算端口位置 (变换后)

        # Port A (左侧)
        self.add_pin('a',
                     points=port_line1.coords,
                     width=a, input_as_norm=False)

        # Port B (右侧)
        self.add_pin('b',
                     points=port_line2.coords,
                     width=a, input_as_norm=False)

class Airbridge(QComponent):
    """airbridge class
    build airbridge on coplanar waveguide automatically
    Inherits QComponent class.
    """

    default_options = dict(
        pos_x='0 um',
        pos_y='0 um',
        pad_width='10 um',
        etch_residue='2 um',
        angle='0',
        bridge_length='33 um',
        subtract=True,
        pad_layer='1',
        etch_layer='2',
        chip='main'
    )
    """Default drawing options"""

    TOOLTIP = """A single configurable bridge"""

    def make(self):
        p = self.p  # p for parsed parameters. Access to the parsed options.
        pos_x = p.pos_x
        pos_y = p.pos_y
        pad_width = p.pad_width
        etch_r = p.etch_residue
        bridge_length = p.bridge_length
        angle = p.angle

        # create the geometry
        # unit_vector = np.array([math.sin(math.radians(angle)), -math.cos(math.radians(angle))])
        unit_vector = [math.sin(math.radians(angle)), -math.cos(math.radians(angle))]
        pad1_posx = pos_x + bridge_length / 2 * unit_vector[0]
        pad1_posy = pos_y + bridge_length / 2 * unit_vector[1]
        pad2_posx = pos_x - bridge_length / 2 * unit_vector[0]
        pad2_posy = pos_y - bridge_length / 2 * unit_vector[1]
        etch_height = bridge_length + pad_width + 2 * etch_r
        etch_width = pad_width + 2 * etch_r
        pad1 = draw.rectangle(pad_width, pad_width, pad1_posx, pad1_posy)
        pad1 = draw.rotate(pad1, angle, origin=(pad1_posx, pad1_posy))
        pad2 = draw.rectangle(pad_width, pad_width, pad2_posx, pad2_posy)
        pad2 = draw.rotate(pad2, angle, origin=(pad2_posx, pad2_posy))
        pad = draw.union([pad1, pad2])
        etch_region = draw.rectangle(etch_width, etch_height, pos_x, pos_y)
        etch_region = draw.rotate(etch_region, angle)

        # add qgeometry
        self.add_qgeometry('poly', {'pad': pad},
                           subtract=p.subtract,
                           layer=p.pad_layer,
                           chip=p.chip)
        self.add_qgeometry('poly', {'etch': etch_region},
                           subtract=False,
                           layer=p.etch_layer,
                           chip=p.chip)


class TunnelBridge(QComponent):
    """airbridge class
    build airbridge on coplanar waveguide automatically
    Inherits QComponent class.
    """

    default_options = dict(
        pier_width='16 um',
        pier_gap='7 um',
        deck_width='26 um',
        pad_edge='5um',
        pad_space='40 um',
        pad_width='10 um',
        pad_height='8 um',
        pad_distance='7 um',
        fillet='30 um',
        name='bus',
        pier_layer='3',
        deck_layer='4',
        chip='main'
    )
    """Default drawing options"""

    TOOLTIP = """A single configurable bridge"""

    def calculate_perpendicular_vector(self, dx: float, dy: float, direction: str = 'up'):
        """
        计算垂直于给定向量的单位向量

        参数:
        dx, dy: 线段方向向量
        direction: 'up' 或 'down'，表示垂直于线段的方向

        返回:
        垂直单位向量 (vx, vy)
        """
        # 计算向量长度
        length = math.sqrt(dx ** 2 + dy ** 2)

        if length == 0:
            return (0, 0)

        # 计算垂直于线段的向量（逆时针旋转90度）
        # 对于向量(dx, dy)，其垂直向量为(-dy, dx)（顺时针旋转90度）或(dy, -dx)（逆时针旋转90度）
        # 这里使用(-dy, dx)作为基础垂直向量
        vx = -dy / length
        vy = dx / length

        # 根据方向参数调整
        if direction == 'down':
            vx = -vx
            vy = -vy

        return (vx, vy)

    def generate_points_with_directions_for_segments(self,
                                                     linestring: LineString,
                                                     d1: float,
                                                     d2: float,
                                                     initial_direction='up'
                                                     ):
        """
        为LineString的每个线段独立生成点，并为每个点计算方向

        参数:
        linestring: LineString的坐标点列表
        d1: 每个线段上第一个点距离起点的距离
        d2: 后续点之间的间隔
        initial_direction: 第一个点的方向 ('up' 或 'down')

        返回:
        字典，键为线段索引，值为该线段的点信息列表
        """
        linestring = list(linestring.coords)
        if len(linestring) < 2:
            raise ValueError("LineString至少需要2个点")

        segments_points = {}
        global_point_index = 0

        # 对每个线段独立处理
        for seg_idx in range(len(linestring) - 1):
            segment_start = linestring[seg_idx]
            segment_end = linestring[seg_idx + 1]

            # 计算线段长度和方向
            x1, y1 = segment_start
            x2, y2 = segment_end
            dx = x2 - x1
            dy = y2 - y1
            segment_length = math.sqrt(dx ** 2 + dy ** 2) - d1

            # print(f"\n处理线段 {seg_idx}:")
            # print(f"  起点: ({x1:.2f}, {y1:.2f})")
            # print(f"  终点: ({x2:.2f}, {y2:.2f})")
            # print(f"  长度: {segment_length:.2f}")
            # print(f"  方向向量: ({dx:.2f}, {dy:.2f})")

            # 生成该线段上的点
            segment_points = []

            if segment_length > 0:
                # 计算单位向量
                unit_dx = dx / segment_length
                unit_dy = dy / segment_length

                # 生成点
                current_distance = d1
                local_point_index = 0  # 线段内的点索引

                while current_distance <= segment_length:
                    # 计算点的坐标
                    x = x1 + unit_dx * current_distance
                    y = y1 + unit_dy * current_distance

                    # 确定当前点的方向
                    # 注意：每个线段的第一个点都使用初始方向，然后交替
                    if local_point_index == 0:
                        # 每个线段的第一个点使用初始方向
                        direction = initial_direction
                    else:
                        # 根据全局索引或局部索引交替方向
                        # 这里使用全局索引来确保整个LineString上的点交替
                        if global_point_index % 2 == 0:
                            direction = initial_direction
                        else:
                            direction = 'down' if initial_direction == 'up' else 'up'

                    # 计算垂直于线段的方向向量
                    perpendicular_vector = self.calculate_perpendicular_vector(dx, dy, direction)
                    angle = math.atan2(dy, dx)

                    # 创建点信息
                    point_info = {
                        'global_index': global_point_index,
                        'segment_index': seg_idx,
                        'local_index': local_point_index,
                        'coordinates': (x, y),
                        'direction': direction,
                        'perpendicular_vector': perpendicular_vector,
                        'segment_vector': (dx, dy),
                        'angle': angle,
                        'segment_vector_normalized': (unit_dx, unit_dy),
                        'distance_from_segment_start': current_distance,
                    }

                    segment_points.append(point_info)

                    # 更新距离和索引
                    current_distance += d2
                    local_point_index += 1
                    global_point_index += 1

            segments_points[seg_idx] = segment_points

            # print(f"  生成了 {len(segment_points)} 个点")
            # for point_info in segment_points:
            #     vx, vy = point_info['perpendicular_vector']
            #     print(f"    点{point_info['global_index']}: "
            #           f"坐标({point_info['coordinates'][0]:.2f}, {point_info['coordinates'][1]:.2f}), "
            #           f"方向={point_info['direction']}, 方向向量=({vx:.2f}, {vy:.2f})")
            #
        return segments_points

    def make(self):
        p = self.p  # p for parsed parameters. Access to the parsed options.
        pier_width = p.pier_width
        pier_gap = p.pier_gap
        deck_width = p.deck_width
        name = p.name
        fillet = p.fillet
        design = self.design
        pad_edge = p.pad_edge
        pad_space = p.pad_space
        pad_width = p.pad_width
        pad_height = p.pad_height
        pad_distance = p.pad_distance

        raw_line = self.design.components[name].qgeometry_list()[0]
        pier_pad, etch_region = generate_cpw_from_line(raw_line, pier_width, pier_gap, fillet)
        pier = draw.subtract(etch_region, pier_pad)
        pad_points = self.generate_points_with_directions_for_segments(raw_line, pad_edge, pad_space, 'up')
        pad_total = draw.rectangle(pad_width, pad_height)
        pad_total = draw.rotate(pad_total, float(pad_points[0][0]['angle']), use_radians=True)
        pad_total = draw.translate(pad_total, pad_points[0][0]['coordinates'][0] + pad_distance *
                                   pad_points[0][0]['perpendicular_vector'][0],
                                   pad_points[0][0]['coordinates'][1] + pad_distance *
                                   pad_points[0][0]['perpendicular_vector'][1])
        for i in range(len(pad_points)):
            for j in range(len(pad_points[i])):
                # if i!=0 and j!=0:
                pad = draw.rectangle(pad_width, pad_height)
                pad = draw.rotate(pad, float(pad_points[i][j]['angle']), use_radians=True)
                pad = draw.translate(pad, pad_points[i][j]['coordinates'][0] + pad_distance *
                                     pad_points[i][j]['perpendicular_vector'][0],
                                     pad_points[i][j]['coordinates'][1] + pad_distance *
                                     pad_points[i][j]['perpendicular_vector'][1])
                pad_total = draw.union(pad_total, pad)
        deck, _ = generate_cpw_from_line(raw_line, deck_width, pier_gap, fillet)
        deck = draw.subtract(deck, pad_total)
        # add qgeometry
        self.add_qgeometry('poly', {'pier': pier},
                           subtract=False,
                           layer=p.pier_layer,
                           chip=p.chip)
        # self.add_qgeometry('path', {'deck': raw_line},
        #                    width=deck_width,
        #                    fillet=fillet,
        #                    layer=p.deck_layer,
        #                    chip=p.chip)
        self.add_qgeometry('poly', {'deck': deck},
                           subtract=False,
                           layer=p.deck_layer,
                           chip=p.chip)


class JJTaper(QComponent):
    """
    The base "JJ_Taper" inherits the "QComponent" class.

    NOTE TO USER: Please be aware that when designing with this
    qcomponent, one must take care in accounting for the junction
    qgeometry when exporting to to GDS and/or to a simulator. This
    qcomponent should not be rendered for EM simulation.

    This creates a "Taper"-style Josephson Junction consisting
    of two tapering overlapping thin metal strips, each connected to a
    larger metallic pad region.
    """
    # Default drawing options
    default_options = Dict(JJ_pad_up_height='25um',
                           JJ_pad_lower_height='25um',
                           JJ_pad_up_slope='0.45',
                           JJ_pad_lower_slope='0.45',
                           JJ_up_length='2.85um',
                           JJ_lower_length='1.32um',
                           JJ_up_linewidth='0.2um',
                           JJ_lower_linewidth='0.2um',
                           JJ_space_x='0.5um',
                           JJ_space_y='2um',
                           fillet='0.1um', )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='jj_taper')
    """Component metadata"""

    def round_corner(self, radius, line):
        line1 = line.buffer(radius, join_style=1)
        line1 = line1.buffer(-2 * radius, join_style=1)
        line1 = line1.buffer(radius, join_style=1)
        return line1

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # Define the slope and length of the side with that slope
        x0 = p.pos_x
        y0 = p.pos_y
        slope1 = p.JJ_pad_lower_slope
        slope2 = p.JJ_pad_up_slope
        height1 = p.JJ_pad_lower_height
        height2 = p.JJ_pad_up_height
        length1 = slope1 * height1
        length2 = slope2 * height2
        tx = 0.4 * 1e-3
        ty = 0
        jj_length1 = p.JJ_lower_length
        jj_length2 = p.JJ_up_length
        length_line1 = jj_length1 - tx
        length_line2 = jj_length2 - ty
        linewidth1 = p.JJ_lower_linewidth
        linewidth2 = p.JJ_up_linewidth
        x_space = p.JJ_space_x
        y_space = p.JJ_space_y
        fillet = p.fillet
        angle = p.orientation
        # Calculate the vertices of the triangle
        # Assuming the first vertex is at the origin (x0,y0)
        x11, y11 = x0, y0
        x21, y21 = x0 + length1, y0 + height1
        x31, y31 = -length1 + x0, y0 + height1

        # Create the triangle using Shapely
        triangle1 = draw.Polygon([(x11, y11), (x21, y21), (x31, y31), (x11, y11)])
        line1 = LineString([(x0, tx + y0), (x0, -length_line1 + y0)])
        line1 = line1.buffer(linewidth1 / 2, cap_style=2)
        funnel1 = draw.unary_union([triangle1, line1])
        # funnel1 = funnel1.buffer(fillet,join_style=1,cap_style=3)
        funnel1 = self.round_corner(fillet, funnel1)
        funnel1 = draw.rotate(funnel1, 90, (x0, y0))
        funnel1 = draw.translate(funnel1, xoff=-(x_space + length_line1 - 5e-5 + linewidth2 / 2) / 2, yoff=-y_space / 2)

        x12, y12 = x0, y0
        x22, y22 = x0 + length2, y0 + height2
        x32, y32 = -length2 + x0, y0 + height2
        triangle2 = draw.Polygon([(x12, y12), (x22, y22), (x32, y32), (x12, y12)])
        line2 = LineString([(-ty + x0, 5e-5 + y0), (length_line2 + x0, 5e-5 + y0)])
        line2 = line2.buffer(linewidth2 / 2, cap_style=2)
        funnel2 = draw.unary_union([triangle2, line2])
        # funnel2 = funnel2.buffer(fillet,join_style=1,cap_style=3)
        funnel2 = self.round_corner(fillet, funnel2)
        funnel2 = draw.rotate(funnel2, -90, (x0, y0))
        funnel2 = draw.translate(funnel2, xoff=(x_space + length_line1 - 5e-5 + linewidth2 / 2) / 2, yoff=y_space / 2)

        funnel = draw.union([funnel1, funnel2])
        funnel = draw.rotate(funnel, angle, (x0, y0))
        geom = {'design': funnel}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)


class JJManhattan(QComponent):
    """
    The base "JJ_Manhattan" inherits the "QComponent" class.

    NOTE TO USER: Please be aware that when designing with this
    qcomponent, one must take care in accounting for the junction
    qgeometry when exporting to to GDS and/or to a simulator. This
    qcomponent should not be rendered for EM simulation.

    This creates a "Manhattan"-style Josephson Junction consisting
    of two overlapping thin metal strips, each connected to a
    larger metallic pad region.

    """
    # Default drawing options
    default_options = Dict(JJ_pad_lower_width='10um',
                           JJ_pad_lower_height='20um',
                           JJ_pad_up_width='10um',
                           JJ_pad_up_height='20um',
                           finger_lower_width='0.18um',
                           finger_lower_height='10um',
                           finger_lower_pos='5um',
                           finger_up_pos='5um',
                           finger_up_width='0.18um',
                           finger_up_height='10um',
                           extension='1um',
                           )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='jj_manhattan')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers
        overlap = 1e-4
        jj_pad_up_pos_x = -(p.finger_up_height - overlap - p.extension - p.finger_up_width / 2 + p.JJ_pad_up_width / 2)
        jj_pad_up_pos_y = p.JJ_pad_up_height / 2 - p.finger_up_pos
        jj_pad_lower_pos_x = p.JJ_pad_lower_width / 2 - p.finger_lower_pos
        jj_pad_lower_pos_y = -(
                p.finger_lower_height - overlap - p.extension - p.finger_lower_width / 2 + p.JJ_pad_lower_height / 2)
        finger_up_pos_x = -(p.finger_up_height / 2 - p.extension)
        finger_up_pos_y = 0
        finger_lower_pos_x = 0
        finger_lower_pos_y = -(p.finger_lower_height / 2 - p.extension)

        # draw the lower pad as a rectangle
        jj_pad_up = draw.rectangle(p.JJ_pad_up_width,
                                   p.JJ_pad_up_height,
                                   jj_pad_up_pos_x,
                                   jj_pad_up_pos_y)
        jj_pad_lower = draw.rectangle(p.JJ_pad_lower_width,
                                      p.JJ_pad_lower_height,
                                      jj_pad_lower_pos_x,
                                      jj_pad_lower_pos_y)
        finger_up = draw.rectangle(p.finger_up_height, p.finger_up_width, finger_up_pos_x, finger_up_pos_y)
        finger_low = draw.rectangle(p.finger_lower_width, p.finger_lower_height, finger_lower_pos_x, finger_lower_pos_y)

        # merge the lower pad and the finger into a single object
        design1 = draw.union(jj_pad_up, finger_up)
        design2 = draw.union(jj_pad_lower, finger_low)

        final_design = draw.union([design1, design2])

        # now translate so that the design is centered on the
        # user-defined coordinates (pos_x, pos_y)
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)
        final_design = draw.rotate(final_design, angle=p.orientation, origin=(p.pos_x, p.pos_y))

        geom = {'design': final_design}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)


class JJSquidFlip(QComponent):
    """
    The base "JJ_Squid" inherits the "QComponent" class.

    NOTE TO USER: Please be aware that when designing with this
    qcomponent, one must take care in accounting for the junction
    qgeometry when exporting to to GDS and/or to a simulator. This
    qcomponent should not be rendered for EM simulation.

    This creates a "SQUID"-style Josephson Junction consisting
    of two junctions, each connected to a larger metallic pad region.

    """
    # Default drawing options
    default_options = Dict(JJ_pad_lower_width='10um',
                           JJ_pad_lower_height='20um',
                           JJ_pad_up_width='10um',
                           JJ_pad_up_height='20um',
                           JJ_pad_up_width2='12um',
                           JJ_pad_up_height2='5um',
                           finger_left_lower_width='0.18um',
                           finger_right_lower_width='0.18um',
                           finger_lower_height='10um',
                           finger_left_up_width='0.18um',
                           finger_right_up_width='0.18um',
                           finger_up_height='10um',
                           JJ_up_pos='3um',
                           JJ_down_pos='5um',
                           extension='1um', )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='jj_squid_flip')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers
        # overlap = 1e-5
        jj_pad_lower_pos_x = 0
        jj_pad_lower_pos_y = -(p.finger_lower_height - p.extension) + p.JJ_down_pos - p.JJ_pad_lower_height / 2
        jj_left_pad_up_pos_x = -(p.JJ_pad_lower_width / 2 + p.finger_lower_height - p.extension
                                 + p.JJ_up_pos - p.JJ_pad_up_width2 + p.JJ_pad_up_width / 2)
        jj_left_pad_up_pos_y = p.JJ_pad_up_height / 2
        jj_left_pad2_up_pos_x = jj_left_pad_up_pos_x + p.JJ_pad_up_width / 2 - p.JJ_pad_up_width2 / 2
        jj_left_pad2_up_pos_y = jj_left_pad_up_pos_y - p.JJ_pad_up_height / 2 + p.JJ_pad_up_height2 / 2
        finger_left_lower_pos_x = -(p.JJ_pad_lower_width / 2 + p.finger_lower_height / 2)
        finger_left_lower_pos_y = -(p.finger_up_height - p.extension)
        finger_left_up_pos_x = -(p.JJ_pad_lower_width / 2 + p.finger_lower_height - p.extension)
        finger_left_up_pos_y = -(p.finger_up_height / 2)

        jj_right_pad_up_pos_x = (p.JJ_pad_lower_width / 2 + p.finger_lower_height - p.extension
                                 + p.JJ_up_pos - p.JJ_pad_up_width2 + p.JJ_pad_up_width / 2)
        jj_right_pad_up_pos_y = p.JJ_pad_up_height / 2
        jj_right_pad2_up_pos_x = jj_right_pad_up_pos_x - p.JJ_pad_up_width / 2 + p.JJ_pad_up_width2 / 2
        jj_right_pad2_up_pos_y = jj_right_pad_up_pos_y - p.JJ_pad_up_height / 2 + p.JJ_pad_up_height2 / 2
        finger_right_lower_pos_x = p.JJ_pad_lower_width / 2 + p.finger_lower_height / 2
        finger_right_lower_pos_y = -(p.finger_up_height - p.extension)
        finger_right_up_pos_x = p.JJ_pad_lower_width / 2 + p.finger_lower_height - p.extension
        finger_right_up_pos_y = -(p.finger_up_height / 2)

        # draw the lower pad as a rectangle
        jj_left_pad_up = draw.rectangle(p.JJ_pad_up_width,
                                        p.JJ_pad_up_height,
                                        jj_left_pad_up_pos_x,
                                        jj_left_pad_up_pos_y)
        jj_left_pad2_up = draw.rectangle(p.JJ_pad_up_width2,
                                         p.JJ_pad_up_height2,
                                         jj_left_pad2_up_pos_x,
                                         jj_left_pad2_up_pos_y)
        jj_right_pad_up = draw.rectangle(p.JJ_pad_up_width,
                                         p.JJ_pad_up_height,
                                         jj_right_pad_up_pos_x,
                                         jj_right_pad_up_pos_y)
        jj_right_pad2_up = draw.rectangle(p.JJ_pad_up_width2,
                                          p.JJ_pad_up_height2,
                                          jj_right_pad2_up_pos_x,
                                          jj_right_pad2_up_pos_y)
        jj_pad_lower = draw.rectangle(p.JJ_pad_lower_width,
                                      p.JJ_pad_lower_height,
                                      jj_pad_lower_pos_x,
                                      jj_pad_lower_pos_y)
        jj_left_pad_up = draw.union(jj_left_pad_up, jj_left_pad2_up)
        jj_right_pad_up = draw.union(jj_right_pad_up, jj_right_pad2_up)
        finger_left_up = draw.rectangle(p.finger_left_up_width, p.finger_up_height, finger_left_up_pos_x,
                                        finger_left_up_pos_y)
        finger_left_low = draw.rectangle(p.finger_lower_height, p.finger_left_lower_width, finger_left_lower_pos_x,
                                         finger_left_lower_pos_y)
        finger_right_up = draw.rectangle(p.finger_right_up_width, p.finger_up_height, finger_right_up_pos_x,
                                         finger_right_up_pos_y)
        finger_right_low = draw.rectangle(p.finger_lower_height, p.finger_right_lower_width, finger_right_lower_pos_x,
                                          finger_right_lower_pos_y)

        # merge the lower pad and the finger into a single object
        design_left_up = draw.union(jj_left_pad_up, finger_left_up)
        design_right_up = draw.union(jj_right_pad_up, finger_right_up)
        design_up = draw.union(design_left_up, design_right_up)
        design_bot1 = draw.union(jj_pad_lower, finger_left_low)
        design_bot = draw.union(design_bot1, finger_right_low)

        final_design = draw.union([design_up, design_bot])

        # now translate so that the design is centered on the
        # user-defined coordinates (pos_x, pos_y)
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)
        final_design = draw.rotate(final_design, angle=p.orientation, origin=(p.pos_x, p.pos_y))

        geom = {'design': final_design}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)


class JJSquid(QComponent):
    """
    The base "JJ_SquidFlip" inherits the "QComponent" class.

    NOTE TO USER: Please be aware that when designing with this
    qcomponent, one must take care in accounting for the junction
    qgeometry when exporting to to GDS and/or to a simulator. This
    qcomponent should not be rendered for EM simulation.

    This creates a "SQUID"-style Josephson Junction consisting
    of two junctions, each connected to a larger metallic pad region.

    """
    # Default drawing options
    default_options = Dict(JJ_pad_lower_width='10um',
                           JJ_pad_lower_height='20um',
                           JJ_pad_up_width='10um',
                           JJ_pad_up_height='20um',
                           finger_left_lower_width='0.18um',
                           finger_right_lower_width='0.18um',
                           finger_lower_height='10um',
                           finger_up_pos='5um',
                           finger_left_up_width='0.18um',
                           finger_right_up_width='0.18um',
                           finger_up_height='10um',
                           JJ_space='5.6um',
                           extension='1um', )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='jj_squid')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers
        overlap = 1e-5
        jj_pad_lower_pos_x = 0
        jj_pad_lower_pos_y = -(p.finger_lower_height - overlap - p.extension + p.JJ_pad_lower_height / 2)

        jj_left_pad_up_pos_x = -(p.finger_up_height - overlap - p.extension + p.JJ_pad_up_width / 2 + p.JJ_space / 2)
        jj_left_pad_up_pos_y = p.JJ_pad_up_height / 2 - p.finger_up_pos
        finger_left_up_pos_x = -(p.finger_up_height / 2 - p.extension + p.JJ_space / 2)
        finger_left_up_pos_y = 0
        finger_left_lower_pos_x = -p.JJ_space / 2
        finger_left_lower_pos_y = -(p.finger_lower_height / 2 - p.extension)

        jj_right_pad_up_pos_x = p.finger_up_height - overlap - p.extension + p.JJ_pad_up_width / 2 + p.JJ_space / 2
        jj_right_pad_up_pos_y = p.JJ_pad_up_height / 2 - p.finger_up_pos
        finger_right_up_pos_x = p.finger_up_height / 2 - p.extension + p.JJ_space / 2
        finger_right_up_pos_y = 0
        finger_right_lower_pos_x = p.JJ_space / 2
        finger_right_lower_pos_y = -(p.finger_lower_height / 2 - p.extension)

        # draw the lower pad as a rectangle
        jj_left_pad_up = draw.rectangle(p.JJ_pad_up_width,
                                        p.JJ_pad_up_height,
                                        jj_left_pad_up_pos_x,
                                        jj_left_pad_up_pos_y)
        jj_right_pad_up = draw.rectangle(p.JJ_pad_up_width,
                                         p.JJ_pad_up_height,
                                         jj_right_pad_up_pos_x,
                                         jj_right_pad_up_pos_y)
        jj_pad_lower = draw.rectangle(p.JJ_pad_lower_width,
                                      p.JJ_pad_lower_height,
                                      jj_pad_lower_pos_x,
                                      jj_pad_lower_pos_y)
        finger_left_up = draw.rectangle(p.finger_up_height, p.finger_left_up_width, finger_left_up_pos_x,
                                        finger_left_up_pos_y)
        finger_left_low = draw.rectangle(p.finger_left_lower_width, p.finger_lower_height, finger_left_lower_pos_x,
                                         finger_left_lower_pos_y)
        finger_right_up = draw.rectangle(p.finger_up_height, p.finger_right_up_width, finger_right_up_pos_x,
                                         finger_right_up_pos_y)
        finger_right_low = draw.rectangle(p.finger_right_lower_width, p.finger_lower_height, finger_right_lower_pos_x,
                                          finger_right_lower_pos_y)

        # merge the lower pad and the finger into a single object
        design_left_up = draw.union(jj_left_pad_up, finger_left_up)
        design_right_up = draw.union(jj_right_pad_up, finger_right_up)
        design_up = draw.union(design_left_up, design_right_up)
        design_bot1 = draw.union(jj_pad_lower, finger_left_low)
        design_bot = draw.union(design_bot1, finger_right_low)

        final_design = draw.union([design_up, design_bot])

        # now translate so that the design is centered on the
        # user-defined coordinates (pos_x, pos_y)
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)
        final_design = draw.rotate(final_design, angle=p.orientation, origin=(p.pos_x, p.pos_y))

        geom = {'design': final_design}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)


class JJDolan(QComponent):
    """
    The base "JJ_Dolan" inherits the "QComponent" class.

    NOTE TO USER: Please be aware that when designing with this
    qcomponent, one must take care in accounting for the junction
    qgeometry when exporting to to GDS and/or to a simulator. This
    qcomponent should not be rendered for EM simulation.

    This creates a "Dolan"-style Josephson Junction consisting
    of two overlapping thin metal strips, each connected to a
    larger metallic pad region.

    """
    # Default drawing options
    default_options = Dict(JJ_pad_lower_width='10um',
                           JJ_pad_lower_height='20um',
                           JJ_pad_up_width='10um',
                           JJ_pad_up_height='20um',
                           JJ_pad_up_ext_width='0um',
                           JJ_pad_up_ext_height='0um',
                           finger_lower_width='0.18um',
                           finger_lower_height='10um',
                           finger_lower_pos='5um',
                           finger_up_pos='5um',
                           finger_up_width='0.18um',
                           finger_up_height='10um',
                           extension_up='1um',
                           extension_lower='1um', )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='jj_manhattan')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers
        overlap = 1e-4
        jj_pad_up_pos_x = -(
                p.finger_up_height - overlap - p.extension_up - p.finger_up_width / 2 + p.JJ_pad_up_width / 2)
        jj_pad_up_pos_y = p.JJ_pad_up_height / 2 - p.finger_up_pos
        jj_pad_lower_pos_x = p.JJ_pad_lower_width / 2 - p.finger_lower_pos
        jj_pad_lower_pos_y = -(
                p.finger_lower_height - overlap - p.extension_lower - p.finger_lower_width / 2 + p.JJ_pad_lower_height / 2)
        finger_up_pos_x = -(p.finger_up_height / 2 - p.extension_up)
        finger_up_pos_y = 0
        finger_lower_pos_x = 0
        finger_lower_pos_y = -(p.finger_lower_height / 2 - p.extension_lower)

        # draw the lower pad as a rectangle
        jj_pad_up = draw.rectangle(p.JJ_pad_up_width,
                                   p.JJ_pad_up_height,
                                   jj_pad_up_pos_x,
                                   jj_pad_up_pos_y)
        jj_pad_up_ext = draw.rectangle(p.JJ_pad_up_ext_width, p.JJ_pad_up_ext_height,
                                       jj_pad_up_pos_x + p.JJ_pad_up_ext_width / 2, jj_pad_up_pos_y
                                       + p.JJ_pad_up_height / 2 - p.JJ_pad_up_ext_height / 2)
        jj_pad_up = draw.union([jj_pad_up, jj_pad_up_ext])
        jj_pad_lower = draw.rectangle(p.JJ_pad_lower_width,
                                      p.JJ_pad_lower_height,
                                      jj_pad_lower_pos_x,
                                      jj_pad_lower_pos_y)
        finger_up = draw.rectangle(p.finger_up_height, p.finger_up_width, finger_up_pos_x, finger_up_pos_y)
        finger_low = draw.rectangle(p.finger_lower_width, p.finger_lower_height, finger_lower_pos_x, finger_lower_pos_y)

        # merge the lower pad and the finger into a single object
        design1 = draw.union(jj_pad_up, finger_up)
        design2 = draw.union(jj_pad_lower, finger_low)

        final_design = draw.union([design1, design2])

        # now translate so that the design is centered on the
        # user-defined coordinates (pos_x, pos_y)
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)
        final_design = draw.rotate(final_design, angle=p.orientation, origin=(p.pos_x, p.pos_y))

        geom = {'design': final_design}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)


class NumberComponent(QComponent):
    """带宽度的数字组件 - 使用LineString连接坐标点"""
    default_options = dict(
        number='0',
        decimal1='0',
        decimal2='0',
        width='60um',
        height='100um',
        spacing='20um',
        subtract='True',
    )

    def make(self):
        p = self.p
        number = str(int(p.number))
        # number = p.number
        decimal1 = str(int(p.decimal1))
        decimal2 = str(int(p.decimal2))
        width = p.width
        height = p.height
        pos_x = p.pos_x
        pos_y = p.pos_y
        angle = p.orientation
        spacing = p.spacing
        h = height
        w = height * 0.6

        # V字母的关键点（最左侧）
        v_width = w * 0.8
        v_offset = -w * 1.5 - spacing * 2
        points_v = {
            'v_tl': (- v_width / 2 + v_offset, h / 2),
            'v_tr': (v_width / 2 + v_offset,  h / 2),
            'v_b': (v_offset, - h / 2)
        }

        # 第一个数字的关键点（整数部分）
        digit1_offset = -w / 2 - spacing / 2
        points_digit1 = {
            'tl': (- w / 2 + digit1_offset, h / 2),
            'tm': (digit1_offset,  h / 2),
            'tr': (w / 2 + digit1_offset,  h / 2),
            'ml': (- w / 2 + digit1_offset, 0),
            'mm': (digit1_offset, 0),
            'mr': (w / 2 + digit1_offset, ),
            'bl': (- w / 2 + digit1_offset,  - h / 2),
            'bm': (digit1_offset,  - h / 2),
            'br': (w / 2 + digit1_offset,  - h / 2)
        }

        # 小数点位置
        dot_offset = spacing / 2
        dot_center = (dot_offset,  - h / 2 + height * 0.1)

        # 第二个数字的关键点（小数部分）
        digit2_offset = w / 2 + spacing * 1.5
        points_digit2 = {
            'tl': (- w / 2 + digit2_offset,  + h / 2),
            'tm': (digit2_offset,  + h / 2),
            'tr': (w / 2 + digit2_offset, 0 + h / 2),
            'ml': (- w / 2 + digit2_offset, 0),
            'mm': (digit2_offset, 0),
            'mr': (w / 2 + digit2_offset, 0),
            'bl': (- w / 2 + digit2_offset, 0 - h / 2),
            'bm': (digit2_offset, 0 - h / 2),
            'br': (w / 2 + digit2_offset, 0 - h / 2)
        }

        # 第三个数字的关键点（小数部分）
        digit3_offset = w / 2 + spacing * 4.7
        points_digit3 = {
            'tl': (- w / 2 + digit3_offset, 0 + h / 2),
            'tm': (digit3_offset, 0 + h / 2),
            'tr': (w / 2 + digit3_offset, 0 + h / 2),
            'ml': (- w / 2 + digit3_offset, 0),
            'mm': (digit3_offset, 0),
            'mr': (w / 2 + digit3_offset, 0),
            'bl': (- w / 2 + digit3_offset, 0 - h / 2),
            'bm': (digit3_offset, 0 - h / 2),
            'br': (w / 2 + digit3_offset, 0 - h / 2)
        }

        # 定义每个数字的路径
        number_paths = {
            '0': [['tl', 'tr', 'br', 'bl', 'tl']],
            '1': [['tr', 'br']],
            '2': [['tl', 'tr', 'mr', 'ml', 'bl', 'br']],
            '3': [['tl', 'tr', 'br', 'bl'], ['ml', 'mr']],
            '4': [['tl', 'ml', 'mr'], ['tr', 'br']],
            '5': [['tr', 'tl', 'ml', 'mr', 'br', 'bl']],
            '6': [['tr', 'tl', 'bl', 'br', 'mr', 'ml']],
            '7': [['tl', 'tr', 'br']],
            '8': [['tl', 'tr', 'br', 'bl', 'tl', 'ml', 'mr']],
            '9': [['bl', 'br', 'tr', 'tl', 'ml', 'mr']]
        }

        # 1. 绘制V字母
        v_path = ['v_tl', 'v_b', 'v_tr']
        coords_v = [points_v[pt] for pt in v_path]
        line_v = LineString(coords_v)
        buffered_v = line_v.buffer(width / 2, cap_style=CAP_STYLE.round, join_style=JOIN_STYLE.round)
        # self.add_qgeometry('poly',
        #                    {'v_letter': buffered_v},
        #                    subtract=p.subtract,
        #                    layer=p.layer)
        # 绘制数字
        if number in number_paths:
            for stroke_idx, path in enumerate(number_paths[number]):
                # path = number_paths[number][0]
                coords = [points_digit1[pt] for pt in path]
                line = draw.LineString(coords)
                buffered = line.buffer(width / 2, cap_style=CAP_STYLE.round, join_style=JOIN_STYLE.round)
                buffered_v = draw.union(buffered_v,buffered)

                # self.add_qgeometry('poly',
                #                    {f'digit1_stroke_{stroke_idx}': buffered},
                #                    subtract=p.subtract,
                #                    layer=p.layer)

        # 3. 绘制小数点
        dot_radius = width * 0.8  # 小数点半径
        dot = draw.Point(dot_center).buffer(dot_radius)
        buffered_v = draw.union(buffered_v,dot)

        # self.add_qgeometry('poly',
        #                    {'decimal_point': dot},
        #                    subtract=p.subtract,
        #                    layer=p.layer)

        # 4. 绘制小数点后数字
        if decimal1 in number_paths:
            for stroke_idx, path in enumerate(number_paths[decimal1]):
                coords = [points_digit2[pt] for pt in path]
                line = LineString(coords)
                buffered = line.buffer(width/2, cap_style=CAP_STYLE.round, join_style=JOIN_STYLE.round)
                buffered_v = draw.union(buffered_v, buffered)

                # self.add_qgeometry('poly',
                #                  {f'digit2_stroke_{stroke_idx}': buffered},
                #                  subtract=p.subtract,
                #                  layer=p.layer)

        if decimal2 in number_paths:
            for stroke_idx, path in enumerate(number_paths[decimal2]):
                coords = [points_digit3[pt] for pt in path]
                line = LineString(coords)
                buffered = line.buffer(width/2, cap_style=CAP_STYLE.round, join_style=JOIN_STYLE.round)
                buffered_v = draw.union(buffered_v, buffered)
        polys = draw.rotate(buffered_v, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        self.add_qgeometry('poly',
                         {f'digit_stroke': polys},
                         subtract=p.subtract,
                         layer=p.layer)


class MyCircle(QComponent):
    """A single configurable circle.

    Inherits QComponent class.

    .. image::
        CircleRaster.png

    .. meta::
        Circle Raster

    Default Options:
        * radius: '300um'
        * resolution: '16'
        * cap_style: 'round' -- Valid options are 'round', 'flat', 'square'
        * subtract: 'False'
        * helper: 'False'
    """

    default_options = dict(
        radius='500um',
        linewidth='0.1 um',
        resolution='16',
        cap_style='round',  # round, flat, square
        # join_style = 'round', # round, mitre, bevel
        # General
        subtract='False',
        helper='False')
    """Default drawing options"""

    TOOLTIP = """A single configurable circle"""

    def make(self):
        """The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc."""
        p = self.p  # p for parsed parameters. Access to the parsed options.

        # create the geometry
        center = draw.Point(p.pos_x, p.pos_y)
        radius = p.radius
        linewidth = p.linewidth
        circle = draw.shapely.LinearRing(center.buffer(radius).exterior.coords).buffer(linewidth)

        # add qgeometry
        self.add_qgeometry('poly', {'circle': circle},
                           subtract=p.subtract,
                           helper=p.helper,
                           layer=p.layer,
                           chip=p.chip)
