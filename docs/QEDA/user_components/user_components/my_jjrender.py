
from qiskit_metal.toolbox_metal import math_and_overrides
from qiskit_metal.qlibrary.core import QComponent
from collections import  OrderedDict
import  math
import pyEPR as epr
from qiskit_metal.analyses.quantization import EPRanalysis
import numpy as np
import qiskit_metal as metal
from pyEPR.ansys import set_property, parse_units
from qiskit_metal.draw.utility import to_vec3D


def add_custom_junction_flipchip(design,hfss,qlist=[0,1,2,3]):
    table = design.qgeometry.tables['junction']
    n=0
    origin = [0.0, 0.0, 0.0]
    for qd, qgeom in table.iterrows():
        if qd in qlist:
                coords = list(qgeom.geometry.coords)
                angle = -math.atan((coords[1][0] - coords[0][0]) / (coords[1][1] - coords[0][1]))
                angle = math.degrees(angle)
                pos = [parse_units(coords[1][0] + coords[0][0])/2, parse_units(coords[1][1] + coords[0][1])/2, parse_units(design.get_chip_z(qgeom.chip))]
                xsize = parse_units(qgeom.width)
                ysize = parse_units(math.hypot(coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]))
                # print(math.degrees(angle),pos,xsize,ysize)
                name = 'rect'+str(n)
                rect = hfss.modeler.draw_rect_center(pos=origin, x_size=xsize, y_size=ysize,name=name)
                hfss.modeler._modeler.Rotate([
                    "NAME:Selections",
                    "Selections:="	, rect,
                    "NewPartsModelFlag:="	, "Model"
                ],
                    [
                        "NAME:RotateParameters",
                        "RotateAxis:="		, "Z",
                        "RotateAngle:="		, str(angle ) +"deg"
                    ])
                hfss.modeler.translate(name=rect,vector=pos)
                endpoints =to_vec3D(parse_units(coords), parse_units(design.get_chip_z(qgeom.chip)))
                hfss.modeler._make_lumped_rlc(r=qgeom['hfss_resistance'], l=qgeom['hfss_inductance'],
                                              c=qgeom['hfss_capacitance'],
                                              start=endpoints[0], end=endpoints[1], obj_arr=["Objects:=", [rect]])
                poly_jj = hfss.modeler.draw_polyline([endpoints[0], endpoints[1]], closed=False, **dict(color=(128, 0, 128)))
                poly_jj = poly_jj.rename("JJ_" +str(n) + "_")
                poly_jj.show_direction = True
                n= n+1

# ----------------------------------------------------------------------------------------------------------------------

def add_custom_junction_flipchip_Copy(design,hfss,qlist=[0,1,2,3],
                                    jj_direction = '+'):
    table = design.qgeometry.tables['junction']
    n=0
    origin = [0.0, 0.0, 0.0]
    for qd, qgeom in table.iterrows():
        if qd in qlist:
                coords = list(qgeom.geometry.coords)
                angle = -math.atan((coords[1][0] - coords[0][0]) / (coords[1][1] - coords[0][1]))
                angle = math.degrees(angle)
                pos = [parse_units(coords[1][0] + coords[0][0])/2, parse_units(coords[1][1] + coords[0][1])/2, parse_units(design.get_chip_z(qgeom.chip))]
                xsize = parse_units(qgeom.width)
                ysize = parse_units(math.hypot(coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]))
                # print(math.degrees(angle),pos,xsize,ysize)
                name = 'rect'+str(n)
                rect = hfss.modeler.draw_rect_center(pos=origin, x_size=xsize, y_size=ysize,name=name)
                hfss.modeler._modeler.Rotate([
                    "NAME:Selections",
                    "Selections:="	, rect,
                    "NewPartsModelFlag:="	, "Model"
                ],
                    [
                        "NAME:RotateParameters",
                        "RotateAxis:="		, "Z",
                        "RotateAngle:="		, str(angle ) +"deg"
                    ])
                hfss.modeler.translate(name=rect,vector=pos)
                endpoints =to_vec3D(parse_units(coords), parse_units(design.get_chip_z(qgeom.chip)))
                hfss.modeler._make_lumped_rlc(r=qgeom['hfss_resistance'], l=qgeom['hfss_inductance'],
                                              c=qgeom['hfss_capacitance'],
                                              start=endpoints[0], end=endpoints[1], obj_arr=["Objects:=", [rect]])
                if jj_direction == '+': # 默认的电流方向
                    poly_jj = hfss.modeler.draw_polyline([endpoints[0], endpoints[1]], closed=False, **dict(color=(128, 0, 128)))
                else:    # 电流调整为反方向
                    poly_jj = hfss.modeler.draw_polyline([endpoints[1], endpoints[0]], closed=False, **dict(color=(128, 0, 128)))
                poly_jj = poly_jj.rename("JJ_" +str(n) + "_")
                poly_jj.show_direction = True
                n= n+1

# ----------------------------------------------------------------------------------------------------------------------

def add_custom_junction_arrays_flipchip(design,hfss,
                                        Q_num = 0,
                                        Q_real = [15, 16, 14, 22],
                                        delta_x = 0,
                                        delta_y = 0,
                                        ):
    table = design.qgeometry.tables['junction']

    for qd, qgeom in table.iterrows():
        coords = list(qgeom.geometry.coords)
        angle = -math.atan((coords[1][0] - coords[0][0]) / (coords[1][1] - coords[0][1]))
        angle = math.degrees(angle)
        pos = [coords[1][0] + coords[0][0], coords[1][1] + coords[0][1] + delta_x, parse_units(design.get_chip_z(qgeom.chip)) + delta_y] #坐标修正
        xsize = parse_units(qgeom.width)
        ysize = parse_units(math.hypot(coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]))
        # print(math.degrees(angle),pos,xsize,ysize)
        rect = hfss.modeler.draw_rect_center(pos=pos, x_size=xsize, y_size=ysize)
        rect.name = f'Rectangle_3_{Q_num}'  # 矩形重命名
        print(f'rect = {rect}, rect.name = {rect.name}')
        hfss.modeler._modeler.Rotate([
            "NAME:Selections",
            "Selections:="	, rect,
            "NewPartsModelFlag:="	, "Model"
        ],
            [
                "NAME:RotateParameters",
                "RotateAxis:="		, "Z",
                "RotateAngle:="		, str(angle ) +"deg"
            ])
        endpoints =to_vec3D(parse_units(coords), parse_units(design.get_chip_z(qgeom.chip)))
        hfss.modeler._make_lumped_rlc(r=qgeom['hfss_resistance'], l=qgeom['hfss_inductance'],
                                      c=qgeom['hfss_capacitance'],
                                      start=endpoints[0], end=endpoints[1], obj_arr=["Objects:=", [rect]])

        poly_jj = hfss.modeler.draw_polyline([endpoints[0], endpoints[1]], closed=False, **dict(color=(128, 0, 128)), )
        # poly_jj = poly_jj.rename("JJ_" + name + "_")
        # poly_jj = poly_jj.rename(f'Polyline3_{Q_num}')  # 修改结中电流方向的名称
        # print(f'确实：poly_jj = {poly_jj}')
        poly_jj.show_direction = True












