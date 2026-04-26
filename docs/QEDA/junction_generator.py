import qiskit_metal as metal
from qiskit_metal.qlibrary.user_components.writer import *
from qiskit_metal.qlibrary.user_components.my_qcomponent import *
from qiskit_metal import draw, Dict,designs,MetalGUI
import gdspy
import os
from PIL import Image


def junction_parameters(type='Single_Manhattan'):
    if type=='Single_Manhattan':
        options = Dict(pos_x='0um',
                       pos_y='0um',
                       JJ_pad_lower_width='6um',
                       JJ_pad_lower_height='8.8um',
                       JJ_pad_up_width='10um',
                       JJ_pad_up_height='5.2um',
                       finger_lower_width='0.18um',
                       finger_lower_height='7.767um',
                       finger_lower_pos='4.9um',
                       finger_up_pos='2um',
                       finger_up_width='0.18um',
                       finger_up_height='8.017um',
                       extension='2.6um',
                       orientation='90')
    elif type == 'Squid_Manhattan':
        options = Dict(pos_x='0um',
                       pos_y='0um',
                       JJ_pad_lower_width='10um',
                       JJ_pad_lower_height='11um',
                       JJ_pad_up_width='7um',
                       JJ_pad_up_height='9.0um',
                       finger_left_lower_width='0.18um',
                       finger_right_lower_width='0.18um',
                       finger_lower_height='5.8um',
                       finger_up_height='4.372um',
                       finger_up_pos='0.923um',
                       finger_left_up_width='0.18um',
                       finger_right_up_width='0.18um',
                       JJ_space='5.6um',
                       extension='1.7228um',
                       orientation='-90')
    elif type == 'SquidFlip_Manhattan':
        options = Dict(pos_x='0um',
                       pos_y='0um',
                       JJ_pad_lower_width='10um',
                       JJ_pad_lower_height='5.2um',
                       JJ_pad_up_width='5.5um',
                       JJ_pad_up_height='13.55um',
                       JJ_pad_up_width2='9um',
                       JJ_pad_up_height2='9.55um',
                       finger_left_lower_width='0.18um',
                       finger_right_lower_width='0.18um',
                       finger_lower_height='7.4um',
                       finger_up_height='7.732um',
                       finger_left_up_width='0.18um',
                       finger_right_up_width='0.18um',
                       JJ_up_pos='5um',
                       JJ_down_pos='2.357um',
                       extension='2.45um',
                       orientation='-90')
    elif type == 'Single_Dolan':
            options = Dict(pos_x='0um',
                           pos_y='0um',
                           JJ_pad_lower_width='10um',
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
    return dict(options)


def quick_crop_center(input_path, output_path):
    """快速裁剪图片中间部分"""
    with Image.open(input_path) as img:
        width, height = img.size

        # 裁剪中间70%的区域
        crop_width = int(width * 0.65)
        crop_height = int(height * 0.7)

        # 计算裁剪区域（居中）
        left = (width - crop_width) // 2
        top = (height - crop_height) // 2
        right = left + crop_width
        bottom = top + crop_height

        # 裁剪并保存
        cropped_img = img.crop((left, top, right, bottom))
        cropped_img.save(output_path)

        print(f"原始尺寸: {width} x {height}")
        print(f"裁剪后尺寸: {crop_width} x {crop_height}")
        print(f"已保存为: {output_path}")


def junction_layout(type,options):
    if not os.path.exists('gds'):
        # Create the folder if it does not exist
        os.makedirs('gds')
        print(f"Folder gds created.")
    jj_path = ''
    design = metal.designs.DesignPlanar()
    gui = metal.MetalGUI(design)
    design.overwrite_enabled = True
    if type == 'Single_Manhattan':
        jj = JJManhattan(design, 'jj_manhattan',options=options)
    elif type == 'Squid_Manhattan':
        jj = JJSquid(design,'jj_squid',options=options)
    elif type == 'SquidFlip_Manhattan':
        jj = JJSquidFlip(design,'jj_squid_flip',options=options)
    elif type == 'Single_Dolan':
        jj = JJDolan(design, 'jj_dolan',options=options)
    gui.rebuild()
    gui.autoscale()
    gui.zoom_on_components([jj.name])
    gui.screenshot()
    quick_crop_center("shot.png", "shot.png")
    a_gds = writer_planar(design,jj_path)
    a_gds.export_to_gds('gds/'+jj.name + '.gds')
    return design, gui


def gds_generator(name_list):
    for i, name in enumerate(name_list):
        globals()[f"gds{i}"]= gdspy.GdsLibrary(infile='gds/'+name+'.gds', unit=1e-03, precision=1e-13)
        globals()[f"top_main_cell{i}"] = globals()[f"gds{i}"].cells['TOP_main_1']
        globals()[f"gds{i}"].rename_cell(globals()[f"top_main_cell{i}"], 'FakeJunction_0'+str(i))
    # Create a new GDS library to hold the combined cells
    combined_gds = gdspy.GdsLibrary(unit=1e-03, precision=1e-13)
    for i in range(len(name_list)):
        combined_gds.add(globals()[f"top_main_cell{i}"])
    combined_gds.write_gds('gds/Fake_Junctions.GDS')
    print("GDS files combined successfully into 'Fake_Junctions.GDS'")