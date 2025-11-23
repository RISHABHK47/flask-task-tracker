# validations.py - Updated without assigned_to validation

from datetime import datetime
from flask import flash

class TaskValidator:
    """Validator class for task operations"""
    
    @staticmethod
    def validate_title(title):
        """Validate task title"""
        errors = []
        
        if not title:
            errors.append("Task title is required.")
            return False, errors
        
        # Remove extra whitespace
        title = title.strip()
        
        if len(title) < 3:
            errors.append("Task title must be at least 3 characters long.")
        
        if len(title) > 200:
            errors.append("Task title cannot exceed 200 characters.")
        
        # Check for valid characters (allow letters, numbers, spaces, and common punctuation)
        if not all(c.isalnum() or c.isspace() or c in '.,!?-_()[]{}:;"\'' for c in title):
            errors.append("Task title contains invalid characters.")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_description(description):
        """Validate task description"""
        errors = []
        
        if description:
            description = description.strip()
            
            if len(description) > 1000:
                errors.append("Description cannot exceed 1000 characters.")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_priority(priority):
        """Validate priority value"""
        errors = []
        
        if priority and priority not in ['Low', 'Medium', 'High']:
            errors.append(f"Invalid priority. Must be one of: Low, Medium, High.")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_due_date(due_date):
        """Validate due date"""
        errors = []
        
        if due_date:
            try:
                # Parse the date string
                date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                
                # Check if date is not in the past
                today = datetime.now().date()
                if date_obj < today:
                    errors.append("Due date cannot be in the past.")
                
                # Check if date is not too far in the future (e.g., 5 years)
                max_future_date = datetime(today.year + 5, today.month, today.day).date()
                if date_obj > max_future_date:
                    errors.append("Due date is too far in the future (max 5 years).")
                
            except ValueError:
                errors.append("Invalid date format. Please use YYYY-MM-DD format.")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_task_data(title, description=None, priority=None, due_date=None):
        """Validate all task data at once"""
        all_errors = []
        
        # Validate title (required)
        is_valid, errors = TaskValidator.validate_title(title)
        if not is_valid:
            all_errors.extend(errors)
        
        # Validate description (optional)
        is_valid, errors = TaskValidator.validate_description(description)
        if not is_valid:
            all_errors.extend(errors)
        
        # Validate priority (optional)
        is_valid, errors = TaskValidator.validate_priority(priority)
        if not is_valid:
            all_errors.extend(errors)
        
        # Validate due date (optional)
        is_valid, errors = TaskValidator.validate_due_date(due_date)
        if not is_valid:
            all_errors.extend(errors)
        
        return len(all_errors) == 0, all_errors


def sanitize_input(value):
    """Sanitize input by removing leading/trailing whitespace and preventing XSS"""
    if value is None:
        return None
    
    if isinstance(value, str):
        # Strip whitespace
        value = value.strip()
        
        # Return None if empty string after stripping
        if not value:
            return None
        
        # Basic XSS prevention (Flask's Jinja2 auto-escapes, but this is extra safety)
        # Replace potential harmful characters
        value = value.replace('<script>', '').replace('</script>', '')
        value = value.replace('javascript:', '')
        value = value.replace('onerror=', '')
        value = value.replace('onclick=', '')
        
    return value


def flash_errors(errors):
    """Flash all validation errors to the user"""
    for error in errors:
        flash(error, 'error')


def get_safe_form_data(request, field_name, default=None):
    """Safely get and sanitize form data"""
    value = request.form.get(field_name, default)
    return sanitize_input(value)