"""
Notification Configuration Rules
=================================
Centralized configuration for notification recipient rules.

This allows easy customization of who receives notifications without code changes.
"""

from dataclasses import dataclass
from typing import Optional, Callable, List
from enum import Enum


class NotificationRule(Enum):
    """Notification event types."""

    # Task notifications
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"

    # Checklist notifications
    CHECKLIST_CREATED = "checklist_created"
    CHECKLIST_UPDATED = "checklist_updated"
    CHECKLIST_DELETED = "checklist_deleted"

    # Conversation notifications
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_UPDATED = "conversation_updated"
    CONVERSATION_DELETED = "conversation_deleted"


@dataclass
class RecipientConfig:
    """Configuration for who receives each notification type."""

    include_assignee: bool = True
    include_creator: bool = True
    include_actor_managers: bool = True
    include_assignee_managers: bool = False
    include_creator_managers: bool = False
    include_previous_assignee: bool = False
    exclude_actor: bool = False  # Set True to prevent self-notifications

    # Optional: Custom filter function
    custom_filter: Optional[Callable] = None


# DEFAULT CONFIGURATIONS (preserves existing behavior)
NOTIFICATION_CONFIGS = {

    NotificationRule.TASK_CREATED: RecipientConfig(
        include_assignee=True,
        include_creator=False,  # Creator is the actor
        include_actor_managers=True,
        include_assignee_managers=True,
        exclude_actor=False  # Keep existing behavior - creator gets notified
    ),

    NotificationRule.TASK_UPDATED: RecipientConfig(
        include_assignee=True,
        include_creator=True,
        include_actor_managers=True,
        include_assignee_managers=True,
        include_previous_assignee=True,
        exclude_actor=False  # Keep existing behavior
    ),

    NotificationRule.TASK_DELETED: RecipientConfig(
        include_assignee=True,
        include_creator=True,
        include_actor_managers=True,
        include_assignee_managers=True,
        exclude_actor=False
    ),

    NotificationRule.TASK_COMPLETED: RecipientConfig(
        include_creator=True,
        include_creator_managers=True,
        include_assignee_managers=True,
        include_assignee=False,  # Assignee is usually the completer
        exclude_actor=True
    ),

    NotificationRule.TASK_ASSIGNED: RecipientConfig(
        include_assignee=True,
        include_actor_managers=True,
        include_assignee_managers=True,
        include_previous_assignee=True,
        exclude_actor=True
    ),

    NotificationRule.CHECKLIST_CREATED: RecipientConfig(
        include_assignee=True,
        include_actor_managers=True,
        include_assignee_managers=False,
        exclude_actor=True
    ),

    NotificationRule.CHECKLIST_UPDATED: RecipientConfig(
        include_assignee=True,
        include_actor_managers=True,
        exclude_actor=True
    ),

    NotificationRule.CHECKLIST_DELETED: RecipientConfig(
        include_assignee=True,
        include_actor_managers=True,
        exclude_actor=True
    ),

    NotificationRule.CONVERSATION_CREATED: RecipientConfig(
        include_assignee=True,
        include_actor_managers=True,
        exclude_actor=True
    ),

    NotificationRule.CONVERSATION_UPDATED: RecipientConfig(
        include_assignee=True,
        include_actor_managers=False,
        exclude_actor=True
    ),
}


def get_notification_recipients(
    rule: NotificationRule,
    current_user_id: int,
    task_assigned_to_id: Optional[int],
    task_created_by_id: Optional[int],
    previous_assignee_id: Optional[int],
    get_manager_ids_func: Callable,
    db,
    config_override: Optional[RecipientConfig] = None
) -> List[int]:
    """
    Get notification recipients based on configurable rules.

    This function preserves existing business logic while making it configurable.

    Args:
        rule: Notification rule enum
        current_user_id: User performing the action
        task_assigned_to_id: Current task assignee
        task_created_by_id: Task creator
        previous_assignee_id: Previous assignee (for reassignments)
        get_manager_ids_func: Function to get manager hierarchy
        db: Database session
        config_override: Optional custom config (overrides default)

    Returns:
        List of validated user IDs to notify
    """
    from utils.notification_helpers import SafeNotificationRecipients

    config = config_override or NOTIFICATION_CONFIGS.get(rule, RecipientConfig())
    recipients = SafeNotificationRecipients(db)

    # Add recipients based on config
    if config.include_assignee and task_assigned_to_id:
        recipients.add(task_assigned_to_id)

    if config.include_creator and task_created_by_id:
        recipients.add(task_created_by_id)

    if config.include_actor_managers:
        try:
            managers = get_manager_ids_func(current_user_id, db)
            recipients.add_many(managers)
            recipients.add(current_user_id)  # Include actor
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error getting actor managers: {str(e)}")

    if config.include_assignee_managers and task_assigned_to_id:
        try:
            assignee_managers = get_manager_ids_func(task_assigned_to_id, db)
            recipients.add_many(assignee_managers)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error getting assignee managers: {str(e)}")

    if config.include_creator_managers and task_created_by_id:
        try:
            creator_managers = get_manager_ids_func(task_created_by_id, db)
            recipients.add_many(creator_managers)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error getting creator managers: {str(e)}")

    if config.include_previous_assignee and previous_assignee_id:
        recipients.add(previous_assignee_id)

    # Exclude actor if configured
    if config.exclude_actor:
        recipients.exclude(current_user_id)

    # Apply custom filter if provided
    recipient_list = recipients.validate_and_get()
    if config.custom_filter:
        try:
            recipient_list = config.custom_filter(recipient_list, db)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error applying custom filter: {str(e)}")

    return recipient_list
