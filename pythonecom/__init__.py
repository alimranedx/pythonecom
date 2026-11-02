"""
Easy Purchase eCommerce Platform
Version: 2.1.0 - Production Release
"""

__version__ = '2.1.0'

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
