#######################################################################
# Process GDS files, extract polygons, and arrange indium bumps, ensuring they meet minimum distance constraints
#######################################################################
import numpy as np
import gdspy
from shapely.geometry import Polygon, box
import pyclipper
from scipy.spatial import KDTree
import matplotlib.pyplot as plt
from addict import Dict


def indium_generator(gds_file, output_gds_file, target_cell_name, new_layer_number_list, new_datatype_number, coord1, coord2,
                     min_distance_points, min_distance_polygons,indium_radius_list):
    """
    Process the GDS file and arrange indium bumps

    Input:

        output_gds_file:gds file path after process
        target_cell_name: cell name the indium added
        new_layer_number_list: layer number list the indium added(the list has two numbers for flipchip)
        new_datatype_number:new layer datatype(for example 0)
        gds_file: str, the path to the GDS file.
        coord1: tuple, the starting coordinates (x1, y1) of the area.
        coord2: tuple, the ending coordinates (x2, y2) of the area.
        min_distance_points: float, the minimum distance between indium bumps.
        min_distance_polygons: float, the minimum distance between indium bumps and polygons.
        indium_radius:float, the radius of the indium

    Output:
        None
    """

    def extract_elements_optimized(gds_file, coord1, coord2):
        """
        Extract polygons from the GDS file that are within the specified rectangular area, clipping parts outside the area.

        Input:
            gds_file: str, the path to the GDS file.
            coord1: tuple, the starting coordinates (x1, y1) of the rectangular area.
            coord2: tuple, the ending coordinates (x2, y2) of the rectangular area.

        Output:
            elements: list, a list of extracted polygons.
        """
        lib = gdspy.GdsLibrary(infile=gds_file)
        x_min, y_min = min(coord1[0], coord2[0]), min(coord1[1], coord2[1])
        x_max, y_max = max(coord1[0], coord2[0]), max(coord1[1], coord2[1])
        region = box(x_min, y_min, x_max, y_max)

        elements = []

        for cell in lib.cells.values():
            for polygon in cell.get_polygons(by_spec=False):
                poly = Polygon(polygon)
                if poly.is_empty:
                    continue

                if poly.intersects(region):
                    clipped = poly.intersection(region)

                    if clipped.is_empty:
                        continue
                    elif clipped.geom_type == 'Polygon':
                        elements.append(np.array(clipped.exterior.coords))
                        for interior in clipped.interiors:
                            elements.append(np.array(interior.coords))
                    elif clipped.geom_type == 'MultiPolygon':
                        for part in clipped.geoms:
                            elements.append(np.array(part.exterior.coords))
                            for interior in part.interiors:
                                elements.append(np.array(interior.coords))

        return elements

    def preprocess_polygons(elements, margin):
        """
        Preprocess the expanded area of polygons using pyclipper.

        Input:
            elements: list, a list of polygon points.
            margin: float, the distance to expand.

        Output:
            expanded_polygons: list, a list of expanded polygons.
        """
        expanded_polygons = []
        pco = pyclipper.PyclipperOffset()

        for element in elements:
            pco.Clear()
            pco.AddPath(element.tolist(), pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            expanded = pco.Execute(margin)
            expanded_polygons.extend(expanded)

        return expanded_polygons

    def point_inside_polygons(point, expanded_polygons):
        """
        Check if a point is inside the expanded polygons.

        Input:
            point: tuple, the coordinates of the point to check.
            expanded_polygons: list, a list of expanded polygons.

        Output:
            bool, whether the point is inside the expanded polygons.
        """
        for poly in expanded_polygons:
            if pyclipper.PointInPolygon(point, poly) != 0:
                return True
        return False

    def optimized_distance_check(point, tree, expanded_polygons, min_distance_points):
        """
        Check if a point meets distance and position constraints.

        Input:
            point: tuple, the coordinates of the point to check.
            tree: KDTree, a tree of positions where indium bumps have been arranged.
            expanded_polygons: list, a list of expanded polygons.
            min_distance_points: float, the minimum distance between indium bumps.

        Output:
            bool, whether the point meets the constraints.
        """
        if tree and tree.query(point, k=1)[0] < min_distance_points:
            return False
        if point_inside_polygons(point, expanded_polygons):
            return False
        return True

    def add_indium(elements, coord1, coord2, step=100, min_distance_points=100, min_distance_polygons=80):
        """
        Arrange indium bumps within a specified area.

        Input:
            elements: list, a list of extracted polygons.
            coord1: tuple, the starting coordinates of the area.
            coord2: tuple, the ending coordinates of the area.
            step: float, the spacing of the point grid, default is 100.
            min_distance_points: float, the minimum distance between indium bumps.
            min_distance_polygons: float, the minimum distance between indium bumps and polygons.

        Output:
            indium_points: list, a list of positions where indium bumps are arranged.
        """
        x_min, y_min = min(coord1[0], coord2[0]), min(coord1[1], coord2[1])
        x_max, y_max = max(coord1[0], coord2[0]), max(coord1[1], coord2[1])

        grid_x = np.arange(x_min, x_max, step)
        grid_y = np.arange(y_min, y_max, step)

        indium_points = []
        tree = None

        expanded_polygons = preprocess_polygons(elements, min_distance_polygons)

        for x in grid_x:
            for y in grid_y:
                point = (x, y)
                if optimized_distance_check(point, tree, expanded_polygons, min_distance_points):
                    indium_points.append(point)
                    tree = KDTree(indium_points)

        return indium_points

    def plot_elements_and_indium(coord1, coord2, elements, indium_points):
        """
        Visualize the arrangement of polygons and indium bumps.

        Input:
            coord1: tuple, the starting coordinates of the area.
            coord2: tuple, the ending coordinates of the area.
            elements: list, a list of extracted polygons.
            indium_points: list, a list of positions where indium bumps are arranged.
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        rect_x = [coord1[0], coord2[0], coord2[0], coord1[0], coord1[0]]
        rect_y = [coord1[1], coord1[1], coord2[1], coord2[1], coord1[1]]
        ax.plot(rect_x, rect_y, 'r--', label="Bounding Box")

        for polygon in elements:
            polygon = np.array(polygon)
            ax.plot(polygon[:, 0], polygon[:, 1], 'b-')

        if indium_points:
            indium_x, indium_y = zip(*indium_points)
            ax.scatter(indium_x, indium_y, color='g', s=10)

        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        ax.set_aspect('equal', 'box')
        plt.title("GDS Elements and Indium Pillars")
        plt.show()

    elements = extract_elements_optimized(gds_file, coord1, coord2)
    indium_pillars = add_indium(elements, coord1, coord2, step=100,
                                min_distance_points=min_distance_points,
                                min_distance_polygons=min_distance_polygons)
    # plot_elements_and_indium(coord1, coord2, elements, indium_pillars)

    def return_indium_options(indium_positions,indium_radius):
        """
        Convert the positions of indium bumps to operational parameters.

        Input:
            indium_positions: list, a list of center positions of indium bumps.

        Output:
            options: Dict, a collection of operational parameters for indium bumps.
        """
        options = Dict()
        for pos in indium_positions:
            option = Dict(
                name="In_{}_{}".format(pos[0], pos[1]),
                type="IndiumBump",
                chip="chip0",
                outline=[],
                center_pos=pos,
                radius=indium_radius
            )
            options[option.name] = option
        return options

    options = return_indium_options(indium_pillars,indium_radius_list)
    data_list = options
    # print(data_list)
    original_gds_path = gds_file  # 您原始GDS文件的路径
    output_gds_path = output_gds_file  # 处理后输出GDS文件的路径
    target_cell_name = target_cell_name  # 您想将圆圈添加到的单元名称 (如果此单元在原GDS中不存在，则会新建一个)
    new_layer_number_list = new_layer_number_list  # 新建图层的图层号 (例如：100)
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

    for i,new_layer_number in enumerate(new_layer_number_list):
        print(f"开始添加圆圈到单元 '{target_cell_name}' 的图层 {new_layer_number}:{new_datatype_number} ...")
        for item in data_list:
            center_x, center_y = data_list[item]['center_pos']
            radius = data_list[item]['radius'][i]
            # print(radius)
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
