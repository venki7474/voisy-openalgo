import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sandbox.order_manager import OrderManager

def test_order_manager():
    om = OrderManager('testuser')
    assert om is not None
