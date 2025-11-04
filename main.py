import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsColorUtils
from qgis.utils import iface
from qgis.core import (
    QgsLayout, QgsLayoutItem, QgsLayoutItemMap, QgsLayoutItemPage, 
    QgsLayoutGuide, QgsLayoutMeasurement, QgsUnitTypes,
    QgsLayoutPoint, QgsLayoutSize, QgsPrintLayout,
    QgsRectangle, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutItemLabel,
    QgsLayoutItemPicture, QgsLayoutItemShape, QgsUnitTypes, QgsLayerTreeLayer, QgsLegendStyle
)
from qgis.PyQt.QtCore import Qt, QRectF
from qgis.PyQt.QtGui import QColor, QFont
from qgis.utils import iface

plugin_dir = os.path.dirname(__file__)

class QGISLayoutPlugin:
    def __init__(self, iface):
        self.iface= iface

    def initGui(self):
        # Create an action (i.e. a button) with Logo
        icon = os.path.join(os.path.join(plugin_dir, 'logo.png'))
        self.action = QAction(QIcon(icon), 'Create Layouts', self.iface.mainWindow())
        # Add the action to the toolbar
        self.iface.addToolBarIcon(self.action)
        # Connect the run() method to the action
        self.action.triggered.connect(self.run)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action
        
    def run(self):
        project = QgsProject.instance()
        active_layer = iface.activeLayer()
        aspengold = QgsColorUtils.colorFromString('#ffb900')
        black = QgsColorUtils.colorFromString('#000000')
        white = QgsColorUtils.colorFromString('#ffffff')
        global_font = QFont('Arial',10)
        page_sizes = {
            'Letter': (215.9, 279.4),
            'Legal': (215.9, 355.6),
            'Ledger': (279.4, 431.8),
            'Arch C': (457.2, 609.6),
            'Arch D': (609.6, 914.4)
        }
        orientations = ['Portrait', 'Landscape']
        # Define scale factors for different page sizes
        # Format: 'Page Size': (horizontal_scale, vertical_scale)
        scale_factors = {
            'Letter': (1.0, 1.0),      # Base scale (smallest)
            'Legal': (1, 1.2727),       # Adjust independently
            'Ledger': (1.2941, 1.5455),      # Adjust independently
            'Arch C': (2.1176, 2.1818),      # Adjust independently
            'Arch D': (2.8235, 3.2727)       # Adjust independently
        }
        
        scale_num = 3000000

        extent_sel = scale_num

        layers_names = []
        for layer in QgsProject.instance().mapLayers().values():
            layers_names.append(layer.name())

        # Delete existing layouts with our naming pattern
        layouts_to_make = []
        layout_manager = project.layoutManager()
        for orientation in orientations:
            for page_size in page_sizes:
                layout_name = f"{page_size} - {orientation}"
                layouts_to_make.append(layout_name)
        
        for layout in layout_manager.layouts():
            if layout.name() in layouts_to_make: 
                layout_manager.removeLayout(layout)
            # print(f"Deleted layout: {deleted_name}")
        
        # Define bounding box (lon/lat)
        bbox_wgs84 = QgsRectangle(-98.304566, 28.495983, -89.993408, 31.903921)
        
        # Transform bbox to project CRS if needed
        project_crs = project.crs()
        wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        
        if project_crs != wgs84_crs:
            transform = QgsCoordinateTransform(wgs84_crs, project_crs, project)
            bbox_project = transform.transformBoundingBox(bbox_wgs84)
        else:
            bbox_project = bbox_wgs84
        
        first_layout = None
        
        for page_name, (width, height) in page_sizes.items():
            # Get horizontal and vertical scale factors for this page size
            h_scale, v_scale = scale_factors[page_name]
            avg_scale = (sum(scale_factors[page_name])/2)
            
            for orientation in orientations:
                # Create layout with name
                layout_name = f"{page_name} - {orientation}"
                
                layout = QgsPrintLayout(project)
                layout.initializeDefaults()
                
                # Set page size based on orientation
                page = layout.pageCollection().page(0)
                if orientation == 'Portrait':
                    page.setPageSize(QgsLayoutSize(width, height, QgsUnitTypes.LayoutMillimeters))
                    page_width, page_height = width, height
                else:  # Landscape
                    page.setPageSize(QgsLayoutSize(height, width, QgsUnitTypes.LayoutMillimeters))
                    page_width, page_height = height, width
                
                # Add guides at 10mm from edges
                margin_num = 5
                
                # Top guide (2% from top)
                top_margin = margin_num
                layout.guides().addGuide(QgsLayoutGuide(
                    Qt.Horizontal,
                    QgsLayoutMeasurement(top_margin, QgsUnitTypes.LayoutMillimeters),
                    page
                ))
                
                # Bottom guide (2% from bottom)
                bottom_margin = page_height - margin_num
                layout.guides().addGuide(QgsLayoutGuide(
                    Qt.Horizontal,
                    QgsLayoutMeasurement(bottom_margin, QgsUnitTypes.LayoutMillimeters),
                    page
                ))
                
                # Left guide (2% from left)
                left_margin = margin_num
                layout.guides().addGuide(QgsLayoutGuide(
                    Qt.Vertical,
                    QgsLayoutMeasurement(left_margin, QgsUnitTypes.LayoutMillimeters),
                    page
                ))
                
                # Right guide (2% from right)
                right_margin = page_width - margin_num
                layout.guides().addGuide(QgsLayoutGuide(
                    Qt.Vertical,
                    QgsLayoutMeasurement(right_margin, QgsUnitTypes.LayoutMillimeters),
                    page
                ))
                
            
                map_height = page_height - (2 * margin_num)
                # Add map item
                map_item = QgsLayoutItemMap(layout)
                map_item.attemptResize(QgsLayoutSize(
                    page_width - (2 * margin_num),
                    map_height,
                    QgsUnitTypes.LayoutMillimeters
                ))
                map_item.attemptMove(QgsLayoutPoint(
                    left_margin,
                    top_margin,
                    QgsUnitTypes.LayoutMillimeters
                ))
                
                # Set extent to bounding box
                map_item.zoomToExtent(bbox_project)
                map_item.setScale(float(scale_num), forceUpdate=True)
                map_item.setFrameEnabled(True)
                map_item.setFrameStrokeWidth(QgsLayoutMeasurement(1, QgsUnitTypes.LayoutMillimeters))
                map_item.setFrameStrokeColor(black)
                
                layout.addLayoutItem(map_item)
                
                # Add rectangle (scaled by horizontal and vertical factors)
                rectangle = QgsLayoutItemShape(layout)
                rectangle.setShapeType(QgsLayoutItemShape.Rectangle)
                layout.addLayoutItem(rectangle)
                rectangle.attemptResize(QgsLayoutSize(
                    80 * h_scale,  # Base width 80mm * horizontal scale
                    50 * v_scale,  # Base height 50mm * vertical scale
                    QgsUnitTypes.LayoutMillimeters
                ))
                rectangle.attemptMove(QgsLayoutPoint(
                    left_margin + (2 * avg_scale), 
                    top_margin + (2 * avg_scale), 
                    QgsUnitTypes.LayoutMillimeters
                ))
                rectangle.setFrameEnabled(True)
                rectangle.setFrameStrokeWidth(QgsLayoutMeasurement(0.5, QgsUnitTypes.LayoutMillimeters))
                rectangle.setFrameStrokeColor(aspengold)
                rectangle.setBackgroundColor(white)
                # layout.addLayoutItem(rectangle)



                # Add a title block image (Aspen Logo)
                aspen_logo = QgsLayoutItemPicture(layout)
                aspen_logo.setPicturePath(r"Z:\Images\Aspen Logo\Aspen Midstream - Logo H - s4 - 500.png")
                # scalebar.setReferencePoint(QgsLayoutItem.UpperRight)
                aspen_logo.attemptResize(QgsLayoutSize(
                    75 * h_scale, 
                    25 * v_scale, 
                    QgsUnitTypes.LayoutMillimeters
                ))
                aspen_logo.attemptMove(QgsLayoutPoint(
                    left_margin + (4 * avg_scale), 
                    top_margin + (4 * avg_scale), 
                    QgsUnitTypes.LayoutMillimeters
                ))
                layout.addLayoutItem(aspen_logo)
                
                # Add title text box (scaled)
                title_text = QgsLayoutItemLabel(layout)
                title_text.setText("[% @project_title %]")
                title_text.setFont(title_text.font())
                font = title_text.font()
                font.setPointSize(int(14 * avg_scale))
                font.setBold(True)
                title_text.setFont(font)
                title_text.attemptResize(QgsLayoutSize(
                    58 * h_scale, 
                    10 * v_scale, 
                    QgsUnitTypes.LayoutMillimeters
                ))
                title_text.setReferencePoint(QgsLayoutItem.UpperMiddle)
                title_text.attemptMove(QgsLayoutPoint(
                    aspen_logo.positionAtReferencePoint(QgsLayoutItem.LowerMiddle).x(), 
                    aspen_logo.positionAtReferencePoint(QgsLayoutItem.LowerMiddle).y() + 10, 
                    QgsUnitTypes.LayoutMillimeters
                ))
                title_text.setFrameEnabled(False)
                layout.addLayoutItem(title_text)
                




                # Add legend (scaled)
                layers_to_remove = [project.mapLayersByName('NGPLs')[0]]
                root = QgsProject.instance().layerTreeRoot()
                my_group = root.findGroup("Base")
                if my_group:
                    for child in my_group.children():
                        if isinstance(child, QgsLayerTreeLayer):
                            layer = child.layer() # Get the actual QgsMapLayer object
                            # print(f"Layer in group: {layer.name()}")
                            layers_to_remove.append(layer)
                # for i in layers_to_remove:
                    # print(i, type(i),'\n')
                legend = QgsLayoutItemLegend(layout)
                legend.setAutoUpdateModel(False)
                # legend.setLinkedMap(map_item)
                legend.setResizeToContents(True)
                for layer in layers_to_remove:
                    legend.model().rootGroup().removeLayer(layer)
                    # print('layer removed: ',layer)
                    layout.refresh()
                
                # Scale legend font
                legend.setReferencePoint(QgsLayoutItem.LowerRight)
                legend.attemptMove(QgsLayoutPoint(
                    right_margin - (2 * avg_scale), 
                    bottom_margin - (2 * avg_scale), 
                    QgsUnitTypes.LayoutMillimeters
                ))
                legend.attemptResize(QgsLayoutSize(
                    40 * h_scale, 
                    40 * v_scale, 
                    QgsUnitTypes.LayoutMillimeters
                ))
                legend_left_edge = (right_margin - 4 * avg_scale) - legend.sizeWithUnits().width() 
                legend.setFrameEnabled(True)
                legend.setFrameStrokeWidth(QgsLayoutMeasurement(0.5, QgsUnitTypes.LayoutMillimeters))
                legend.setFrameStrokeColor(aspengold)
                legend_font = global_font
                legend_font.setPointSize(int(10 * avg_scale))
                legend.rstyle(QgsLegendStyle.Title).setFont(legend_font)
                legend.rstyle(QgsLegendStyle.Group).setFont(legend_font)
                legend.rstyle(QgsLegendStyle.Subgroup).setFont(legend_font)
                legend.rstyle(QgsLegendStyle.SymbolLabel).setFont(legend_font)
                layout.addLayoutItem(legend)
                # legend.refreshItemSize()
                
                # Add scale bar (scaled)
                scalebar = QgsLayoutItemScaleBar(layout)
                scalebar.setLinkedMap(map_item)
                scalebar.setUnits(QgsUnitTypes.DistanceMiles)
                scalebar.setReferencePoint(QgsLayoutItem.LowerRight)
                scalebar.setNumberOfSegments(5)
                scalebar.setNumberOfSegmentsLeft(4)
                scalebar.setMaximumBarWidth(25 * h_scale)
                scalebar.setUnitsPerSegment(25)
                scalebar.setStyle('Double Box')
                scalebar.setHeight(3 * v_scale)
                scalebar.attemptResize(QgsLayoutSize(
                    50 * h_scale + 40, 
                    5 * v_scale + (v_scale * 5), 
                    QgsUnitTypes.LayoutMillimeters
                ))
                scalebar.attemptMove(QgsLayoutPoint(
                    legend_left_edge - (25 * h_scale), 
                    bottom_margin - (4 * avg_scale), 
                    QgsUnitTypes.LayoutMillimeters
                ))
                scalebar.setFrameEnabled(True)
                scalebar.setFrameStrokeWidth(QgsLayoutMeasurement(0.5, QgsUnitTypes.LayoutMillimeters))
                scalebar.setFrameStrokeColor(black)
                scalebar_top_point = scalebar.positionAtReferencePoint(QgsLayoutItem.UpperMiddle)
                scalebar.setBackgroundColor(white)
                scalebar.setBackgroundEnabled(True)
                scalebar.setUnitLabel("mi")
                layout.addLayoutItem(scalebar)
                
                # Add dynamic scale text (scaled)
                scale_text = QgsLayoutItemLabel(layout)
                scale_text.setReferencePoint(7)
                scale_text.setText(f"Scale = 1:{scale_num:,}")
                scale_text.setHAlign(Qt.AlignHCenter)
                scale_font = global_font
                scale_font.setPointSize(int(8 * avg_scale))
                scale_text.setFont(scale_font)
                scale_text.attemptResize(QgsLayoutSize(
                    40 * h_scale, 
                    5 * v_scale, 
                    QgsUnitTypes.LayoutMillimeters
                ))
                scale_text.attemptMove(QgsLayoutPoint(
                    scalebar_top_point.x(), 
                    scalebar_top_point.y() - (1.2 * avg_scale), 
                    QgsUnitTypes.LayoutMillimeters
                ))
                scale_text.setFrameEnabled(False)
                print(iface.mapCanvas().scale())
                layout.addLayoutItem(scale_text)
                
                # Add metadata text (scaled)
                date_text = QgsLayoutItemLabel(layout)
                date_text.setText(r"MapID: [%left(@layout_name,6)%] || RA || [%format_date(now(), 'yyyy.MM.dd')%]")
                font = date_text.font()
                font.setPointSize(int(8 * avg_scale))
                date_text.setFont(font)
                date_text.setReferencePoint(QgsLayoutItem.LowerLeft)
                date_text.attemptResize(QgsLayoutSize(
                    40 * h_scale, 
                    5 * v_scale, 
                    QgsUnitTypes.LayoutMillimeters
                ))
                date_text.attemptMove(QgsLayoutPoint(
                    left_margin + (2 * avg_scale), 
                    bottom_margin - (2 * avg_scale), 
                    QgsUnitTypes.LayoutMillimeters
                ))
                date_text.setFrameEnabled(False)
                layout.addLayoutItem(date_text)
            
                
                # Add north arrow image (scaled)
                north_arrow = QgsLayoutItemPicture(layout)
                # Use built-in QGIS north arrow SVG
                north_arrow.setPicturePath(r"Z:\Images\North arrow2 clean.png")
                north_arrow.attemptResize(QgsLayoutSize(
                    25 * h_scale, 
                    25 * v_scale, 
                    QgsUnitTypes.LayoutMillimeters
                ))
                north_arrow.attemptMove(QgsLayoutPoint(
                    page_width - (margin_num) - (15 * avg_scale),
                    top_margin + (5 * avg_scale),
                    QgsUnitTypes.LayoutMillimeters
                ))
                north_arrow.setFrameEnabled(False)
                north_arrow.setLinkedMap(map_item)
                north_arrow.setNorthMode(QgsLayoutItemPicture.GridNorth)
                layout.addLayoutItem(north_arrow)
                

                
                # Add layout to project with name
                layout_manager.addLayout(layout)
                layout.setName(layout_name)
                
                # Store first layout
                if first_layout is None:
                    first_layout = layout
                
                # print(f"Created layout: {layout_name} (h_scale: {h_scale}, v_scale: {v_scale})")
        
        # Open the first layout in the designer
        if first_layout:
            iface.openLayoutDesigner(first_layout)
            print(f"Opened layout: {first_layout.name()}")
            self.iface.messageBar().pushSuccess('nice','fuck yeeeah')