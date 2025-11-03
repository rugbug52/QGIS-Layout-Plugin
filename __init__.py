from .main import QGISLayoutPlugin

def classFactory(iface):
    return QGISLayoutPlugin(iface)