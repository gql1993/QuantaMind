import gdspy


def gds_generator_flipchip(indium_options, original_gds_path, output_gds_path, target_cell_name, new_layer_number,
                           new_layer_number1, new_datatype_number):
    data_list = indium_options
    original_gds_path = original_gds_path  # 您原始GDS文件的路径
    output_gds_path = output_gds_path  # 处理后输出GDS文件的路径
    target_cell_name = target_cell_name  # 您想将圆圈添加到的单元名称 (如果此单元在原GDS中不存在，则会新建一个)
    new_layer_number = new_layer_number  # 新建图层的图层号 (例如：100)
    new_layer_number1 = new_layer_number1
    new_datatype_number = new_datatype_number  # 新建图层的数据类型号 (例如：0)

    print(f"正在加载GDS文件: {original_gds_path} ...")
    try:
        # 读取现有的GDS文件
        # gds_lib = gdspy.read_gds(original_gds_path)
        gds_lib = gdspy.GdsLibrary(infile=original_gds_path)
    except FileNotFoundError:
        print(f"错误: 原始GDS文件 '{original_gds_path}' 未找到。请检查文件路径是否正确。")
        exit()
    except Exception as e:
        print(f"加载GDS文件 '{original_gds_path}' 时发生错误: {e}")
        print("如果您是想创建一个全新的GDS文件而不是在现有文件基础上修改，请调整代码逻辑。")
        exit()
    print("GDS文件加载成功。")

    # 检查目标单元是否已存在于库中
    if target_cell_name in gds_lib.cells:
        cell = gds_lib.cells[target_cell_name]
        print(f"将圆圈添加到现有单元: '{target_cell_name}'")
    else:
        cell = gds_lib.new_cell(target_cell_name)
        print(f"未找到单元 '{target_cell_name}'，已新建该单元。")

    print(f"开始添加圆圈到单元 '{target_cell_name}' 的图层 {new_layer_number}:{new_datatype_number} ...")
    print(f"开始添加圆圈到单元 '{target_cell_name}' 的图层 {new_layer_number1}:{new_datatype_number} ...")
    for item in data_list:
        center_x, center_y = data_list[item]['center_pos']
        radius = data_list[item]['radius']
        item_name = data_list[item]['name']  # 获取name用于打印信息

        # 创建圆形 (gdspy.Round)
        # gdspy.Round 的参数包括: center=(x, y), radius=半径, layer=图层号, datatype=数据类型号
        # 注意: gdspy中的坐标和半径单位将遵循GDS文件本身定义的数据库单位 (通常是微米)
        circle = gdspy.Round(
            center=(center_x, center_y),
            radius=radius,
            layer=new_layer_number,
            datatype=new_datatype_number
        )
        cell.add(circle)
        circle1 = gdspy.Round(
            center=(center_x, center_y),
            radius=radius,
            layer=new_layer_number1,
            datatype=new_datatype_number
        )
        cell.add(circle1)
        print(f"  已添加圆 '{item_name}': 中心 ({center_x}, {center_y}), 半径 {radius}")

    print("所有圆圈添加完毕。")

    print(f"正在保存修改后的GDS到: {output_gds_path} ...")
    try:
        gds_lib.write_gds(output_gds_path)
        print("处理完成！")
        print(f"新的GDS文件已成功保存为: {output_gds_path}")
    except Exception as e:
        print(f"保存GDS文件 '{output_gds_path}' 时发生错误: {e}")


def gds_generator(indium_options, original_gds_path, output_gds_path, target_cell_name, new_layer_number,
                           new_datatype_number):
    data_list = indium_options
    original_gds_path = original_gds_path  # 您原始GDS文件的路径
    output_gds_path = output_gds_path  # 处理后输出GDS文件的路径
    target_cell_name = target_cell_name  # 您想将圆圈添加到的单元名称 (如果此单元在原GDS中不存在，则会新建一个)
    new_layer_number = new_layer_number  # 新建图层的图层号 (例如：100)
    new_datatype_number = new_datatype_number  # 新建图层的数据类型号 (例如：0)

    print(f"正在加载GDS文件: {original_gds_path} ...")
    try:
        # 读取现有的GDS文件
        # gds_lib = gdspy.read_gds(original_gds_path)
        gds_lib = gdspy.GdsLibrary(infile=original_gds_path)
    except FileNotFoundError:
        print(f"错误: 原始GDS文件 '{original_gds_path}' 未找到。请检查文件路径是否正确。")
        exit()
    except Exception as e:
        print(f"加载GDS文件 '{original_gds_path}' 时发生错误: {e}")
        print("如果您是想创建一个全新的GDS文件而不是在现有文件基础上修改，请调整代码逻辑。")
        exit()
    print("GDS文件加载成功。")

    # 检查目标单元是否已存在于库中
    if target_cell_name in gds_lib.cells:
        cell = gds_lib.cells[target_cell_name]
        print(f"将圆圈添加到现有单元: '{target_cell_name}'")
    else:
        cell = gds_lib.new_cell(target_cell_name)
        print(f"未找到单元 '{target_cell_name}'，已新建该单元。")

    print(f"开始添加圆圈到单元 '{target_cell_name}' 的图层 {new_layer_number}:{new_datatype_number} ...")
    for item in data_list:
        center_x, center_y = data_list[item]['center_pos']
        radius = data_list[item]['radius']
        item_name = data_list[item]['name']  # 获取name用于打印信息

        # 创建圆形 (gdspy.Round)
        # gdspy.Round 的参数包括: center=(x, y), radius=半径, layer=图层号, datatype=数据类型号
        # 注意: gdspy中的坐标和半径单位将遵循GDS文件本身定义的数据库单位 (通常是微米)
        circle = gdspy.Round(
            center=(center_x, center_y),
            radius=radius,
            layer=new_layer_number,
            datatype=new_datatype_number
        )
        cell.add(circle)
    print("所有圆圈添加完毕。")

    print(f"正在保存修改后的GDS到: {output_gds_path} ...")
    try:
        gds_lib.write_gds(output_gds_path)
        print("处理完成！")
        print(f"新的GDS文件已成功保存为: {output_gds_path}")
    except Exception as e:
        print(f"保存GDS文件 '{output_gds_path}' 时发生错误: {e}")
