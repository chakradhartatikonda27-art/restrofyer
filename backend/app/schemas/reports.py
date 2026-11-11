from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SalesSummaryReport(BaseModel):
    total_sales: float
    total_orders: int
    net_sales: float
    total_tax: float
    total_discounts: float
    average_order_value: float
    sales_by_order_type: Dict[str, float]
    sales_by_payment_method: Dict[str, float]
    top_selling_items: List[Dict[str, Any]]
    daily_sales_trend: List[Dict[str, Any]]

class InventoryValuationReport(BaseModel):
    total_inventory_value: float
    total_items_count: int
    low_stock_items_count: int
    low_stock_items: List[Dict[str, Any]]

class ProfitLossReport(BaseModel):
    total_revenue: float
    cost_of_goods_sold: float # COGS
    gross_profit: float
    gross_margin_percentage: float
    total_operating_expenses: float
    net_operating_profit: float
