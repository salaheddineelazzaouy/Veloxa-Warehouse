from rest_framework.throttling import UserRateThrottle


class StockMutationThrottle(UserRateThrottle):
    scope = "stock_mutations"
    rate = "60/minute"


class BackorderThrottle(UserRateThrottle):
    scope = "backorder"
    rate = "120/minute"
