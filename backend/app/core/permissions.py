from enum import Enum
from typing import Set, Dict

class RoleEnum(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SAAS_SUPPORT = "SAAS_SUPPORT"
    TENANT_OWNER = "TENANT_OWNER"
    TENANT_ADMIN = "TENANT_ADMIN"
    BRANCH_MANAGER = "BRANCH_MANAGER"
    RESTAURANT_MANAGER = "RESTAURANT_MANAGER"
    CASHIER = "CASHIER"
    WAITER = "WAITER"
    KITCHEN_MANAGER = "KITCHEN_MANAGER"
    KITCHEN_STAFF = "KITCHEN_STAFF"
    INVENTORY_MANAGER = "INVENTORY_MANAGER"
    ACCOUNTANT = "ACCOUNTANT"
    DELIVERY_EXECUTIVE = "DELIVERY_EXECUTIVE"
    CUSTOMER = "CUSTOMER"

class Permission(str, Enum):
    # Tenant & Org Management
    MANAGE_TENANT = "tenant:manage"
    MANAGE_SUBSCRIPTION = "subscription:manage"
    MANAGE_BRANCHES = "branches:manage"
    MANAGE_USERS = "users:manage"
    MANAGE_ROLES = "roles:manage"
    
    # POS & Operations
    ACCESS_POS = "pos:access"
    CREATE_ORDER = "order:create"
    UPDATE_ORDER = "order:update"
    CANCEL_ORDER = "order:cancel"
    APPLY_DISCOUNT = "order:discount"
    PROCESS_PAYMENT = "payment:process"
    PROCESS_REFUND = "payment:refund"
    
    # Dining & Reservations
    MANAGE_TABLES = "tables:manage"
    MANAGE_RESERVATIONS = "reservations:manage"
    
    # Menu & Recipes
    VIEW_MENU = "menu:view"
    MANAGE_MENU = "menu:manage"
    MANAGE_RECIPES = "recipes:manage"
    
    # Kitchen / KDS
    ACCESS_KDS = "kds:access"
    UPDATE_KOT_STATUS = "kot:update_status"
    
    # Inventory & Procurement
    VIEW_INVENTORY = "inventory:view"
    MANAGE_INVENTORY = "inventory:manage"
    MANAGE_PURCHASES = "purchases:manage"
    MANAGE_SUPPLIERS = "suppliers:manage"
    
    # CRM & Loyalty
    VIEW_CUSTOMERS = "customers:view"
    MANAGE_CUSTOMERS = "customers:manage"
    MANAGE_LOYALTY = "loyalty:manage"
    
    # Financials & Registers
    OPERATE_CASH_REGISTER = "cash_register:operate"
    RECONCILE_CASH_REGISTER = "cash_register:reconcile"
    MANAGE_EXPENSES = "expenses:manage"
    
    # Delivery
    ACCESS_DELIVERY = "delivery:access"
    UPDATE_DELIVERY_STATUS = "delivery:update_status"
    
    # Reports
    VIEW_REPORTS_SALES = "reports:sales"
    VIEW_REPORTS_INVENTORY = "reports:inventory"
    VIEW_REPORTS_FINANCIAL = "reports:financial"
    EXPORT_REPORTS = "reports:export"

# Role-to-Permissions Mapping
ROLE_PERMISSIONS: Dict[RoleEnum, Set[Permission]] = {
    RoleEnum.SUPER_ADMIN: set(Permission),  # All permissions
    
    RoleEnum.TENANT_OWNER: {
        Permission.MANAGE_TENANT, Permission.MANAGE_SUBSCRIPTION, Permission.MANAGE_BRANCHES,
        Permission.MANAGE_USERS, Permission.MANAGE_ROLES, Permission.ACCESS_POS,
        Permission.CREATE_ORDER, Permission.UPDATE_ORDER, Permission.CANCEL_ORDER,
        Permission.APPLY_DISCOUNT, Permission.PROCESS_PAYMENT, Permission.PROCESS_REFUND,
        Permission.MANAGE_TABLES, Permission.MANAGE_RESERVATIONS, Permission.VIEW_MENU,
        Permission.MANAGE_MENU, Permission.MANAGE_RECIPES, Permission.ACCESS_KDS,
        Permission.UPDATE_KOT_STATUS, Permission.VIEW_INVENTORY, Permission.MANAGE_INVENTORY,
        Permission.MANAGE_PURCHASES, Permission.MANAGE_SUPPLIERS, Permission.VIEW_CUSTOMERS,
        Permission.MANAGE_CUSTOMERS, Permission.MANAGE_LOYALTY, Permission.OPERATE_CASH_REGISTER,
        Permission.RECONCILE_CASH_REGISTER, Permission.MANAGE_EXPENSES, Permission.ACCESS_DELIVERY,
        Permission.UPDATE_DELIVERY_STATUS, Permission.VIEW_REPORTS_SALES, Permission.VIEW_REPORTS_INVENTORY,
        Permission.VIEW_REPORTS_FINANCIAL, Permission.EXPORT_REPORTS
    },
    
    RoleEnum.TENANT_ADMIN: {
        Permission.MANAGE_BRANCHES, Permission.MANAGE_USERS, Permission.ACCESS_POS,
        Permission.CREATE_ORDER, Permission.UPDATE_ORDER, Permission.CANCEL_ORDER,
        Permission.APPLY_DISCOUNT, Permission.PROCESS_PAYMENT, Permission.PROCESS_REFUND,
        Permission.MANAGE_TABLES, Permission.MANAGE_RESERVATIONS, Permission.VIEW_MENU,
        Permission.MANAGE_MENU, Permission.MANAGE_RECIPES, Permission.ACCESS_KDS,
        Permission.UPDATE_KOT_STATUS, Permission.VIEW_INVENTORY, Permission.MANAGE_INVENTORY,
        Permission.MANAGE_PURCHASES, Permission.MANAGE_SUPPLIERS, Permission.VIEW_CUSTOMERS,
        Permission.MANAGE_CUSTOMERS, Permission.MANAGE_LOYALTY, Permission.OPERATE_CASH_REGISTER,
        Permission.RECONCILE_CASH_REGISTER, Permission.MANAGE_EXPENSES, Permission.ACCESS_DELIVERY,
        Permission.UPDATE_DELIVERY_STATUS, Permission.VIEW_REPORTS_SALES, Permission.VIEW_REPORTS_INVENTORY,
        Permission.VIEW_REPORTS_FINANCIAL, Permission.EXPORT_REPORTS
    },
    
    RoleEnum.BRANCH_MANAGER: {
        Permission.ACCESS_POS, Permission.CREATE_ORDER, Permission.UPDATE_ORDER,
        Permission.CANCEL_ORDER, Permission.APPLY_DISCOUNT, Permission.PROCESS_PAYMENT,
        Permission.PROCESS_REFUND, Permission.MANAGE_TABLES, Permission.MANAGE_RESERVATIONS,
        Permission.VIEW_MENU, Permission.ACCESS_KDS, Permission.UPDATE_KOT_STATUS,
        Permission.VIEW_INVENTORY, Permission.MANAGE_INVENTORY, Permission.VIEW_CUSTOMERS,
        Permission.MANAGE_CUSTOMERS, Permission.OPERATE_CASH_REGISTER, Permission.RECONCILE_CASH_REGISTER,
        Permission.MANAGE_EXPENSES, Permission.ACCESS_DELIVERY, Permission.UPDATE_DELIVERY_STATUS,
        Permission.VIEW_REPORTS_SALES, Permission.VIEW_REPORTS_INVENTORY
    },
    
    RoleEnum.CASHIER: {
        Permission.ACCESS_POS, Permission.CREATE_ORDER, Permission.UPDATE_ORDER,
        Permission.PROCESS_PAYMENT, Permission.MANAGE_TABLES, Permission.VIEW_MENU,
        Permission.VIEW_CUSTOMERS, Permission.MANAGE_CUSTOMERS, Permission.OPERATE_CASH_REGISTER
    },
    
    RoleEnum.WAITER: {
        Permission.ACCESS_POS, Permission.CREATE_ORDER, Permission.UPDATE_ORDER,
        Permission.MANAGE_TABLES, Permission.VIEW_MENU, Permission.ACCESS_KDS
    },
    
    RoleEnum.KITCHEN_MANAGER: {
        Permission.ACCESS_KDS, Permission.UPDATE_KOT_STATUS, Permission.VIEW_MENU,
        Permission.VIEW_INVENTORY, Permission.MANAGE_INVENTORY
    },
    
    RoleEnum.KITCHEN_STAFF: {
        Permission.ACCESS_KDS, Permission.UPDATE_KOT_STATUS, Permission.VIEW_MENU
    },
    
    RoleEnum.INVENTORY_MANAGER: {
        Permission.VIEW_INVENTORY, Permission.MANAGE_INVENTORY, Permission.MANAGE_PURCHASES,
        Permission.MANAGE_SUPPLIERS, Permission.VIEW_REPORTS_INVENTORY
    },
    
    RoleEnum.DELIVERY_EXECUTIVE: {
        Permission.ACCESS_DELIVERY, Permission.UPDATE_DELIVERY_STATUS
    },
    
    RoleEnum.CUSTOMER: {
        Permission.VIEW_MENU
    }
}
