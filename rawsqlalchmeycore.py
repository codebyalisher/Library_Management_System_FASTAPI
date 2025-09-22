import os
from datetime import datetime
from typing import Optional, Any, Dict, List, Set
import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import (
    select, and_, or_, desc, func
)
from sqlalchemy.orm import Session
from models import *

# Use ORM tables for raw SQL - best of both worlds
tickets = Tickets.__table__
ticket_assignees = TicketAssignee.__table__
users = User.__table__
contacts = Contact.__table__
priorities = Priority.__table__
ticket_statuses_by_dept = TicketStatusByDept.__table__
company_departments = CompanyDepartment.__table__
departments = Department.__table__
ticket_sources = TicketSource.__table__
purposes = Purpose.__table__
sla_configurations = SlaConfiguration.__table__
contacts_phone_numbers = ContactsPhoneNumber.__table__
ticket_attachments = TicketAttachment.__table__
ticket_replies = TicketReplies.__table__
notification_types = NotificationType.__table__
user_teams = TeamUser.__table__

# ---- Helper Functions ----
async def get_all_accessible_tickets_comprehensive(async_db: Session, user_id: int) -> List[int]:
    """Get ALL tickets accessible to the user across all levels"""
    all_ticket_ids = set()
    
    # 1. Direct user assignments
    user_tickets_stmt = select(ticket_assignees.c.ticket_id).where(
        and_(ticket_assignees.c.assignee_type == 'user', ticket_assignees.c.assignee_id == user_id)
    )
    result =async_db.execute(user_tickets_stmt)
    all_ticket_ids.update([row[0] for row in result.fetchall()])
    
    # 2. Team assignments
    teams_stmt = select(user_teams.c.team_id).where(user_teams.c.user_id == user_id)
    teams_result = async_db.execute(teams_stmt)
    team_ids = [row[0] for row in teams_result.fetchall()]
    
    if team_ids:
        team_tickets_stmt = select(ticket_assignees.c.ticket_id).where(
            and_(ticket_assignees.c.assignee_type == 'team', ticket_assignees.c.assignee_id.in_(team_ids))
        )
        result = async_db.execute(team_tickets_stmt)
        all_ticket_ids.update([row[0] for row in result.fetchall()])
    
    # 3. Get user info for department/company assignments
    user_stmt = select(users).where(users.c.id == user_id)
    user_result = async_db.execute(user_stmt)
    user_info = user_result.mappings().first()
    
    if user_info:
        # 4. Department assignments (if company_department_id exists in your user model)
        if 'company_department_id' in user_info and user_info['company_department_id']:
            dept_tickets_stmt = select(ticket_assignees.c.ticket_id).where(
                and_(ticket_assignees.c.assignee_type == 'department', 
                     ticket_assignees.c.assignee_id == user_info['company_department_id'])
            )
            result = async_db.execute(dept_tickets_stmt)
            all_ticket_ids.update([row[0] for row in result.fetchall()])
        
        # 5. Company assignments (if company_id exists in your user model)
        if 'company_id' in user_info and user_info['company_id']:
            company_tickets_stmt = select(ticket_assignees.c.ticket_id).where(
                and_(ticket_assignees.c.assignee_type == 'company', 
                     ticket_assignees.c.assignee_id == user_info['company_id'])
            )
            result = async_db.execute(company_tickets_stmt)
            all_ticket_ids.update([row[0] for row in result.fetchall()])
        
        # 6. Direct ticket assignments
        direct_tickets_stmt = select(tickets.c.id).where(
            or_(tickets.c.created_by_id == user_id, tickets.c.assigned_to_id == user_id),
            tickets.c.is_deleted == 0
        )
        result = async_db.execute(direct_tickets_stmt)
        all_ticket_ids.update([row[0] for row in result.fetchall()])
    
    return list(all_ticket_ids)

def build_search_filters(
    ticket_id: Optional[str] = None,
    email: Optional[str] = None,
    status_id: Optional[int] = None,
    priority_id: Optional[int] = None,
    title: Optional[str] = None,
    tags: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    contact_id: Optional[int] = None,
    contact_type_id: Optional[int] = None,
    segmentations_id: Optional[int] = None,
    accessible_ticket_ids: List[int] = None,
    reporting_user_ids: List[int] = None,
):
    """Build WHERE conditions for ticket search"""
    conditions = []
    
    # Base condition - not deleted
    conditions.append(tickets.c.is_deleted == 0)
    
    # Access control
    access_conditions = []
    if accessible_ticket_ids:
        access_conditions.append(tickets.c.id.in_(accessible_ticket_ids))
    if reporting_user_ids:
        access_conditions.append(tickets.c.assigned_to_id.in_(reporting_user_ids))
    
    if access_conditions:
        conditions.append(or_(*access_conditions))
    
    # Search filters
    if ticket_id:
        conditions.append(tickets.c.ticket_id.ilike(f'%{ticket_id}%'))
    
    if title:
        conditions.append(tickets.c.title.ilike(f'%{title}%'))
    
    if status_id:
        conditions.append(tickets.c.ticket_status_id == status_id)
    
    if priority_id:
        conditions.append(tickets.c.priority_id == priority_id)
    
    if contact_id:
        conditions.append(tickets.c.contact_id == contact_id)
    
    if tags:
        conditions.append(tickets.c.tags.ilike(f'%{tags}%'))
    
    if email:
        email_conditions = [
            tickets.c.requested_email.ilike(f'%{email}%'),
            tickets.c.to_recipients.ilike(f'%{email}%'),
            tickets.c.cc_recipients.ilike(f'%{email}%')
        ]
        conditions.append(or_(*email_conditions))
    
    # Date filters
    if from_date:
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d")
            conditions.append(tickets.c.created_at >= start_date)
        except ValueError:
            pass
    
    if to_date:
        try:
            end_date = datetime.strptime(to_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            conditions.append(tickets.c.created_at <= end_date)
        except ValueError:
            pass
    
    # Contact type and segmentation filters (requires joining with contacts)
    if contact_type_id is not None or segmentations_id is not None:
        # Add condition to ensure contact exists
        conditions.append(tickets.c.contact_id.isnot(None))
        if contact_type_id is not None:
            # Will be handled in main query with JOIN
            pass
        if segmentations_id is not None:
            # Will be handled in main query with JOIN
            pass
    
    return and_(*conditions) if conditions else None

async def get_main_ticket_data(async_db:Session, where_conditions, contact_type_id=None, segmentations_id=None):
    """Get main ticket data with INNER JOINs for mandatory relations"""
    
    # Aliases for users in different roles
    assigned_user = users.alias("assigned_user")
    created_user = users.alias("created_user") 
    assigned_by_user = users.alias("assigned_by_user")
    parent_purpose = purposes.alias("parent_purpose")
    
    # Start with tickets table
    from_clause = tickets
    
    # INNER JOINs for mandatory relations (always present) - these improve performance
    from_clause = from_clause.join(priorities, priorities.c.id == tickets.c.priority_id)
    from_clause = from_clause.join(ticket_statuses_by_dept, ticket_statuses_by_dept.c.id == tickets.c.ticket_status_id)
    from_clause = from_clause.join(company_departments, company_departments.c.id == tickets.c.company_department_id)
    
    # LEFT JOINs for optional relations
    from_clause = from_clause.outerjoin(contacts, contacts.c.id == tickets.c.contact_id)
    # Adjust this relationship based on your actual schema
    from_clause = from_clause.outerjoin(departments, departments.c.id == company_departments.c.department_id)
    from_clause = from_clause.outerjoin(ticket_sources, ticket_sources.c.id == tickets.c.ticket_source_id)
    from_clause = from_clause.outerjoin(purposes, purposes.c.id == tickets.c.purpose_type_id)
    from_clause = from_clause.outerjoin(parent_purpose, parent_purpose.c.id == purposes.c.parent_id)
    from_clause = from_clause.outerjoin(sla_configurations, sla_configurations.c.id == tickets.c.SLA)
    from_clause = from_clause.outerjoin(assigned_user, assigned_user.c.id == tickets.c.assigned_to_id)
    from_clause = from_clause.outerjoin(created_user, created_user.c.id == tickets.c.created_by_id)
    from_clause = from_clause.outerjoin(assigned_by_user, assigned_by_user.c.id == tickets.c.assigned_by_id)
    
    # Main query with all required fields
    stmt = (
        select(
            # Ticket core fields
            tickets.c.id,
            tickets.c.ticket_id,
            tickets.c.parent_id,
            tickets.c.title,
            tickets.c.message,
            tickets.c.requested_email,
            tickets.c.contact_name,
            tickets.c.contact_phone_no,
            tickets.c.contact_ref_no,
            tickets.c.reminder_flag,
            tickets.c.reminder_datetime,
            tickets.c.schedule_at,
            tickets.c.auto_reminder,
            tickets.c.reminder_time,
            tickets.c.response_time,
            tickets.c.resolution_time,
            tickets.c.notification_type_id,
            tickets.c.to_recipients,
            tickets.c.cc_recipients,
            tickets.c.meta_data,
            tickets.c.tags,
            tickets.c.created_at,
            tickets.c.updated_at,
            tickets.c.contact_id,
            tickets.c.assigned_to_id,
            tickets.c.created_by_id,
            tickets.c.assigned_by_id,
            tickets.c.company_department_id,
            tickets.c.ticket_status_id,
            tickets.c.priority_id,
            tickets.c.ticket_source_id,
            tickets.c.purpose_type_id,
            tickets.c.SLA,
            
            # Contact info (optional)
            contacts.c.name.label("contact_db_name"),
            contacts.c.picture_url.label("contact_avatar"),
            contacts.c.contact_type_id,
            contacts.c.segmentations_id,
            
            # Priority info (INNER JOIN - mandatory)
            priorities.c.name.label("priority_name"),
            
            # Status info (INNER JOIN - mandatory)
            ticket_statuses_by_dept.c.slug.label("status_slug"),
            
            # Company Department info (INNER JOIN - mandatory)
            company_departments.c.label.label("company_department_label"),
            
            # Department info (optional)
            departments.c.name.label("department_name"),
            
            # Source info (optional)
            ticket_sources.c.name.label("source_name"),
            
            # Purpose info (optional)
            purposes.c.name.label("purpose_name"),
            purposes.c.label.label("purpose_label"),
            purposes.c.parent_id.label("purpose_parent_id"),
            purposes.c.status.label("purpose_status"),
            parent_purpose.c.name.label("parent_purpose_name"),
            parent_purpose.c.label.label("parent_purpose_label"),
            
            # SLA info (optional)
            sla_configurations.c.name.label("sla_name"),
            sla_configurations.c.response_time.label("sla_response_time"),
            sla_configurations.c.resolution_time.label("sla_resolution_time"),
            
            # User info (optional)
            assigned_user.c.name.label("assigned_to_name"),
            created_user.c.name.label("created_by_name"),
            assigned_by_user.c.name.label("assigned_by_name"),
        )
        .select_from(from_clause)
        .order_by(
            tickets.c.parent_id.asc(),  # Parents first
            desc(tickets.c.created_at)
        )
    )
    
    # Apply base WHERE conditions
    if where_conditions is not None:
        stmt = stmt.where(where_conditions)
    
    # Add contact type/segmentation filters if needed
    if contact_type_id is not None:
        stmt = stmt.where(contacts.c.contact_type_id == contact_type_id)
    
    if segmentations_id is not None:
        stmt = stmt.where(contacts.c.segmentations_id == segmentations_id)
    
    result =  async_db.execute(stmt)
    return result.mappings().all()

async def get_related_data(async_db:Session, ticket_ids: List[int]):
    """Get related data for tickets - only what's used in JSON response"""
    relations = {
        'phone_numbers': {},
        'assignees': {},
        'attachments': {},
        'replies_count': {},
        'notification_types': {}
    }
    
    if not ticket_ids:
        return relations
    
    # Phone numbers for contacts
    phone_stmt = select(
        contacts_phone_numbers.c.contact_id,
        contacts_phone_numbers.c.phone_number,
        contacts_phone_numbers.c.is_preferred
    ).where(
        contacts_phone_numbers.c.contact_id.in_(
            select(tickets.c.contact_id).where(
                and_(tickets.c.id.in_(ticket_ids), tickets.c.contact_id.isnot(None))
            )
        )
    )
    phone_result =  async_db.execute(phone_stmt)
    for row in phone_result.mappings():
        contact_id = row['contact_id']
        if contact_id not in relations['phone_numbers']:
            relations['phone_numbers'][contact_id] = []
        relations['phone_numbers'][contact_id].append(row)
    
    # Assignee users
    assignees_stmt = (
        select(
            ticket_assignees.c.ticket_id,
            ticket_assignees.c.assignee_type,
            ticket_assignees.c.assignee_id,
            users.c.name.label("user_name"),
            users.c.email.label("user_email"),
            users.c.picture.label("user_picture")
        )
        .select_from(
            ticket_assignees.outerjoin(
                users, and_(
                    ticket_assignees.c.assignee_type == 'user',
                    users.c.id == ticket_assignees.c.assignee_id
                )
            )
        )
        .where(ticket_assignees.c.ticket_id.in_(ticket_ids))
    )
    assignees_result =  async_db.execute(assignees_stmt)
    for row in assignees_result.mappings():
        ticket_id = row['ticket_id']
        if ticket_id not in relations['assignees']:
            relations['assignees'][ticket_id] = []
        relations['assignees'][ticket_id].append(row)
    
    # Attachment data
    attachments_stmt = select(
        ticket_attachments.c.ticket_id,
        ticket_attachments.c.id,
        ticket_attachments.c.file_url,
        ticket_attachments.c.uploaded_by
    ).where(ticket_attachments.c.ticket_id.in_(ticket_ids))
    
    attachments_result =  async_db.execute(attachments_stmt)
    for row in attachments_result.mappings():
        ticket_id = row['ticket_id']
        if ticket_id not in relations['attachments']:
            relations['attachments'][ticket_id] = []
        relations['attachments'][ticket_id].append(row)
    
    # Reply counts
    replies_stmt = select(
        ticket_replies.c.ticket_id,
        func.count().label('count')
    ).where(
        ticket_replies.c.ticket_id.in_(ticket_ids)
    ).group_by(ticket_replies.c.ticket_id)
    
    replies_result =  async_db.execute(replies_stmt)
    for row in replies_result:
        relations['replies_count'][row.ticket_id] = row.count
    
    # Notification types
    notification_stmt = select(
        notification_types.c.id,
        notification_types.c.name
    )
    notification_result =  async_db.execute(notification_stmt)
    relations['notification_types'] = {
        row['id']: row['name'] for row in notification_result.mappings()
    }
    
    return relations

def organize_ticket_families(tickets):
    """Organize tickets by families - parents first, then children"""
    parent_map = {}
    root_tickets = []
    
    for ticket in tickets:
        if ticket['parent_id'] is None:
            root_tickets.append(ticket)
            parent_map[ticket['id']] = []
    
    for ticket in tickets:
        if ticket['parent_id'] is not None and ticket['parent_id'] in parent_map:
            parent_map[ticket['parent_id']].append(ticket)
        elif ticket['parent_id'] is not None:
            # Orphan child
            root_tickets.append(ticket)
    
    # Build ordered list
    organized = []
    for parent in sorted(root_tickets, key=lambda x: x['created_at'], reverse=True):
        organized.append(parent)
        if parent['id'] in parent_map:
            children = sorted(parent_map[parent['id']], key=lambda x: x['created_at'])
            organized.extend(children)
    
    return organized

def serialize_ticket_data(ticket_row, relations):
    """Convert ticket row to JSON format with only required fields"""
    ticket_id = ticket_row['id']
    contact_id = ticket_row['contact_id']
    
    # Contact info
    contact_name = ticket_row['contact_db_name'] or ticket_row['contact_name']
    contact_phone_no = ticket_row['contact_phone_no']
    avatar = ticket_row['contact_avatar']
    
    # Get preferred phone if available
    if contact_id and contact_id in relations['phone_numbers']:
        phones = relations['phone_numbers'][contact_id]
        preferred = next((p for p in phones if p.get('is_preferred')), None)
        if preferred:
            contact_phone_no = preferred['phone_number']
        elif phones:
            contact_phone_no = phones[0]['phone_number']
    
    # Assignee users (only user type as per your JSON)
    assignee_users = []
    if ticket_id in relations['assignees']:
        for assignee in relations['assignees'][ticket_id]:
            if assignee['assignee_type'] == 'user' and assignee['user_name']:
                assignee_users.append({
                    'id': assignee['assignee_id'],
                    'name': assignee['user_name'],
                    'email': assignee['user_email'],
                    'avatar': assignee['user_picture'],
                    'teams': []  # Can be populated if needed
                })
    
    # Parse notification types
    notification_ids = []
    try:
        if ticket_row['notification_type_id']:
            if isinstance(ticket_row['notification_type_id'], str):
                notification_ids = json.loads(ticket_row['notification_type_id'])
            elif isinstance(ticket_row['notification_type_id'], (int, float)):
                notification_ids = [int(ticket_row['notification_type_id'])]
            elif isinstance(ticket_row['notification_type_id'], list):
                notification_ids = ticket_row['notification_type_id']
    except:
        notification_ids = []
    
    notification_names = [
        relations['notification_types'].get(nid) 
        for nid in notification_ids 
        if nid in relations['notification_types']
    ]
    
    # Parse recipients
    def parse_recipients(value):
        try:
            return json.loads(value) if value else []
        except:
            return []
    
    # Parse metadata
    meta_data = {}
    try:
        if isinstance(ticket_row['meta_data'], str):
            meta_data = json.loads(ticket_row['meta_data'])
        elif isinstance(ticket_row['meta_data'], dict):
            meta_data = ticket_row['meta_data']
    except:
        pass
    
    # Purpose serialization
    purpose = None
    if ticket_row['purpose_name']:
        purpose = {
            "id": ticket_row['purpose_type_id'],
            "name": ticket_row['purpose_name'].strip() if ticket_row['purpose_name'] else '',
            "label": ticket_row['purpose_label'] or '',
            "status": ticket_row['purpose_status'],
            "full_name": f"{ticket_row['purpose_name'].strip()} - {ticket_row['parent_purpose_name'].strip()}" if ticket_row['parent_purpose_name'] else ticket_row['purpose_name'],
            "parent_id": ticket_row['purpose_parent_id'],
            "parent_name": ticket_row['parent_purpose_name'].strip() if ticket_row['parent_purpose_name'] else '',
            "parent_label": ticket_row['parent_purpose_label'].strip() if ticket_row['parent_purpose_label'] else ''
        }
    
    # Attachments
    attachments = []
    if ticket_id in relations['attachments']:
        attachments = [
            {
                "id": att['id'],
                "file_url": att['file_url'],
                "uploaded_by": att['uploaded_by']
            }
            for att in relations['attachments'][ticket_id]
        ]
    
    return {
        "id": ticket_row['id'],
        "ticket_id": ticket_row['ticket_id'],
        "parent_id": ticket_row['parent_id'],
        "title": ticket_row['title'],
        "message": ticket_row['message'],
        "requested_email": ticket_row['requested_email'],
        "contact_name": contact_name,
        "contact_phone_no": contact_phone_no,
        "avatar": avatar,
        "company_department_id": ticket_row['company_department_id'],
        "company_department_name": ticket_row['company_department_label'],
        "department_name": ticket_row['department_name'],
        "ticket_status": {
            "id": ticket_row['ticket_status_id'],
            "name": ticket_row['status_slug']
        },
        "ticket_source": ticket_row['source_name'],
        "priority": ticket_row['priority_name'],
        "assigned_to_id": ticket_row['assigned_to_id'],
        "assigned_to": ticket_row['assigned_to_name'],
        "created_by_id": ticket_row['created_by_id'],
        "created_by": ticket_row['created_by_name'],
        "assigned_by_id": ticket_row['assigned_by_id'],
        "assigned_by": ticket_row['assigned_by_name'],
        "sla": {
            "name": ticket_row['sla_name'],
            "response_time": ticket_row['sla_response_time'],
            "resolution_time": ticket_row['sla_resolution_time']
        },
        "response_time": ticket_row['response_time'].strftime("%H:%M:%S") if ticket_row['response_time'] else None,
        "resolution_time": ticket_row['resolution_time'].strftime("%H:%M:%S") if ticket_row['resolution_time'] else None,
        "notification_types": notification_names,
        "to_recipients": parse_recipients(ticket_row['to_recipients']),
        "cc_recipients": parse_recipients(ticket_row['cc_recipients']),
        "contact_ref_no": ticket_row['contact_ref_no'],
        "reminder_flag": ticket_row['reminder_flag'],
        "reminder_datetime": ticket_row['reminder_datetime'].isoformat() if ticket_row['reminder_datetime'] else None,
        "schedule_at": ticket_row['schedule_at'].isoformat() if ticket_row['schedule_at'] else None,
        "auto_reminder": bool(ticket_row['auto_reminder']),
        "reminder_time": ticket_row['reminder_time'],
        "created_at": ticket_row['created_at'].isoformat() if ticket_row['created_at'] else None,
        "updated_at": ticket_row['updated_at'].isoformat() if ticket_row['updated_at'] else None,
        "attachments": attachments,
        "purpose": purpose,
        "meta_data": meta_data,
        "replies_count": relations['replies_count'].get(ticket_id, 0),
        "assignee_users": assignee_users
    }

