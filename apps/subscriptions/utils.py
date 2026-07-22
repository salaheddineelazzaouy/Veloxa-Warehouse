from .models import Subscription


class SubscriptionLimitExceeded(Exception):
    def __init__(self, limit_key, current, max_limit):
        self.limit_key = limit_key
        self.current = current
        self.max_limit = max_limit
        super().__init__(
            f"{limit_key} limit reached ({current}/{max_limit})"
        )


def get_active_subscription(user):
    try:
        return user.subscriptions.filter(status="active").latest("created_at")
    except Subscription.DoesNotExist:
        return None


def check_subscription_limit(user, limit_key, current_usage, increment=0):
    sub = get_active_subscription(user)
    if sub is None:
        raise SubscriptionLimitExceeded(limit_key, current_usage, 0)
    plan = sub.plan
    if plan is None:
        raise SubscriptionLimitExceeded(limit_key, current_usage, 0)
    features = plan.features
    if not isinstance(features, dict):
        return
    max_limit = features.get(limit_key)
    if max_limit is None:
        return
    if isinstance(max_limit, bool):
        if not max_limit:
            raise SubscriptionLimitExceeded(limit_key, current_usage, 0)
        return
    try:
        max_limit = int(max_limit)
    except (ValueError, TypeError):
        return
    if current_usage + increment > max_limit:
        raise SubscriptionLimitExceeded(
            limit_key, current_usage + increment, max_limit
        )


def get_user_limits(user):
    sub = get_active_subscription(user)
    if sub is None or sub.plan is None:
        return {}
    return sub.plan.features
